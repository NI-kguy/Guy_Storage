"""
Magewell USB Capture Plus - LabVIEW-callable interface
======================================================

A LabVIEW-friendly wrapper around the same Magewell capture engine used by
``capture.py``. Instead of an interactive OpenCV window, every operation is a
plain module-level function that LabVIEW's **Python Node** (LabVIEW 2020+) can
call one at a time. LabVIEW handles all display; this module only configures
the device, delivers frames as a flat pixel array, and saves snapshots /
recordings on request.

Why this shape
--------------
* LabVIEW's Python Node calls a *single* function per node and can only pass /
  return numerics, strings, booleans and 1-D/2-D arrays. So every public
  function here takes/returns those simple types.
* A Python exception makes the LabVIEW node error out. Therefore every public
  function catches its own exceptions, stores the message, and returns an
  integer status code (``0`` = success, negative = error). Call
  :func:`get_last_error` to read the message.
* Module-level globals persist for the life of one LabVIEW *Python Session*
  (Open Python Session -> ... -> Close Python Session), so the open device and
  running capture are held in globals between calls.
* The Magewell SDK is imported *lazily* inside :func:`initialize` so LabVIEW can
  set the SDK path first with :func:`set_sdk_path`.

Typical LabVIEW call order
--------------------------
    set_sdk_path(r"C:\\Program Files\\MWCaptureSDK ...\\Examples\\Python\\AVCapturePY")
    set_output_dir(r"d:\\...\\output")      # optional
    set_device_index(0)                     # optional (default 0)
    set_resolution(0, 0)                    # optional (0,0 = follow signal)
    set_fps(60)                             # optional (0 = follow signal)
    initialize()                            # -> 0 on success
    open_device()                           # -> 0 on success
    get_signal_status()                     # -> [state,w,h,fps,interlaced]
    start_capture()                         # -> 0 on success
    ... loop ...
        get_frame_dims()                    # -> [width, height, channels]
        get_frame()                         # -> flat U8 RGB array (w*h*3)
        snapshot()                          # -> saved .png path (on demand)
    stop_capture()                          # -> 0
    close()                                 # -> 0

Requirements
------------
    pip install opencv-python numpy pywin32
    MWCapture SDK installed (provides the bundled ``mwcapture`` package and
    LibMWCapture.dll).
"""

import os
import sys
import threading
from ctypes import c_ubyte, create_unicode_buffer
from datetime import datetime

import cv2
import numpy as np

# ============================================================================
# Module state (persists across calls within one LabVIEW Python Session)
# ============================================================================

# Runtime configuration, set via the set_* functions before initialize/open.
_config = {
    "sdk_path": r"C:\Program Files\MWCaptureSDK 3.3.1.1556\SDKv3\Examples\Python\AVCapturePY",
    "device_index": 0,
    "width": 0,        # 0 => follow input signal
    "height": 0,       # 0 => follow input signal
    "fps": 60,         # 0 => follow input signal
    "output_dir": r"d:\dev\Guy_Storage\Home\Magewell Capture\output",
    "record_codec": "mp4v",
    "record_extension": ".mp4",
}

mw = None                 # the mwcapture.libmwcapture module (loaded lazily)
_cap = None               # MagewellCapture instance
_active_width = 0         # actual capture width after start_capture()
_active_height = 0        # actual capture height after start_capture()
_active_fps = 0.0         # actual capture fps after start_capture()
_writer = None            # cv2.VideoWriter when recording
_last_error = ""          # last error message for get_last_error()

# Filled in during initialize() once the SDK module is available.
_FAMILY_NAMES = {}
_SIGNAL_STATE_NAMES = {}
_CAPTURE_FOURCC = None

# The USB hardware scaler only outputs a fixed set of standard display modes,
# so a non-standard / portrait native size can be rejected. These landscape
# fallbacks (largest first) are tried in order when the requested size fails.
_FALLBACK_RESOLUTIONS = [
    (1920, 1080),
    (1280, 1024),
    (1280, 720),
    (1024, 768),
    (800, 600),
    (640, 480),
]


def _set_error(message):
    """Record the most recent error message and echo it to stderr."""
    global _last_error
    _last_error = str(message)
    sys.stderr.write(f"[Capture_LV] {_last_error}\n")


# ============================================================================
# Capture engine (mirrors capture.py; self-contained so capture.py is untouched)
# ============================================================================

class FrameHolder:
    """Thread-safe slot holding the most recent captured frame.

    The SDK capture thread writes frames via :meth:`set` while the LabVIEW
    thread reads the latest one via :meth:`get`. Only the newest frame is kept
    so display never lags behind.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._frame = None
        self.updated = threading.Event()

    def set(self, frame):
        """Store a new frame (called from the SDK thread) and signal waiters."""
        with self._lock:
            self._frame = frame
        self.updated.set()

    def get(self):
        """Return the most recently stored frame, or None if none yet."""
        with self._lock:
            return self._frame


class MagewellCapture:
    """Wrapper around the MWCapture SDK for a single capture channel."""

    def __init__(self):
        """Initialise the SDK instance and refresh the device list."""
        self._cap = mw.mw_capture()
        if not self._cap.mw_capture_init_instance():
            raise RuntimeError("mw_capture_init_instance() failed")
        self._cap.mw_refresh_device()
        self._channel = 0
        self._hvideo = 0
        self._holder = FrameHolder()
        self._callback_ref = None          # keep ctypes callback alive

    # -- lifecycle ----------------------------------------------------------
    def close(self):
        """Stop capture, close the channel and release the SDK instance."""
        try:
            self.stop()
            if self._channel:
                self._cap.mw_close_channel(self._channel)
                self._channel = 0
        finally:
            self._cap.mw_capture_exit_instance()

    # -- enumeration --------------------------------------------------------
    def list_devices(self):
        """Return a list of dicts describing every detected device."""
        self._cap.mw_refresh_device()
        count = self._cap.mw_get_channel_count()
        devices = []
        for i in range(count):
            info = mw.mw_cap_channel_info()
            if self._cap.mw_get_channel_info_by_index(i, info) != mw.MW_SUCCEEDED:
                continue
            devices.append(
                {
                    "index": i,
                    "family_id": info.wFamilyID,
                    "family": _FAMILY_NAMES.get(info.wFamilyID, "Unknown"),
                    "product": info.szProductName.decode(errors="replace"),
                    "serial": info.szBoardSerialNo.decode(errors="replace"),
                }
            )
        return devices

    # -- open ---------------------------------------------------------------
    def open(self, index):
        """Open the device at the given index and return its info dict."""
        devices = self.list_devices()
        if not devices:
            raise RuntimeError("No Magewell capture devices detected.")
        match = next((d for d in devices if d["index"] == index), None)
        if match is None:
            raise IndexError(f"device index {index} not found among detected devices.")
        path = create_unicode_buffer(128)
        self._cap.mw_get_device_path(index, path)
        self._channel = self._cap.mw_open_channel_by_path(path)
        if not self._channel:
            raise RuntimeError(f"Failed to open device index {index}.")
        return match

    # -- signal -------------------------------------------------------------
    def signal_status(self):
        """Return a dict describing the current input signal."""
        status = mw.mw_video_signal_status()
        if self._cap.mw_get_video_signal_status(self._channel, status) != mw.MW_SUCCEEDED:
            raise RuntimeError("mw_get_video_signal_status() failed")
        frame_duration = status.dwFrameDuration or 0
        fps = (1e7 / frame_duration) if frame_duration else 0.0
        return {
            "state": status.state,
            "state_name": _SIGNAL_STATE_NAMES.get(status.state, "UNKNOWN"),
            "width": status.cx,
            "height": status.cy,
            "fps": round(fps, 3),
            "frame_duration": frame_duration,
            "interlaced": bool(status.bInterlaced),
        }

    def video_caps(self):
        """Return the device's hardware max input / output resolution."""
        caps = mw.mw_video_caps()
        if self._cap.mw_get_video_caps(self._channel, caps) != mw.MW_SUCCEEDED:
            return None
        return {
            "max_input_width": caps.wMaxInputWidth,
            "max_input_height": caps.wMaxInputHeight,
            "max_output_width": caps.wMaxOutputWidth,
            "max_output_height": caps.wMaxOutputHeight,
        }

    # -- capture ------------------------------------------------------------
    def start(self, width, height, frame_duration):
        """Start the SDK capture thread; BGR frames arrive via the callback."""

        def _on_frame(pbframe, cbframe, timestamp, param):
            # Runs on the SDK capture thread. Never let an exception cross
            # back into the C caller.
            try:
                holder = param if isinstance(param, FrameHolder) else self._holder
                if not pbframe or cbframe <= 0:
                    return
                raw = (c_ubyte * cbframe).from_address(pbframe)
                stride = cbframe // height
                arr = np.frombuffer(raw, dtype=np.uint8).reshape(height, stride)
                # Drop any row padding, shape to YUY2 (HxWx2), convert to BGR.
                yuy2 = arr[:, : width * 2].reshape(height, width, 2)
                bgr = cv2.cvtColor(yuy2, cv2.COLOR_YUV2BGR_YUYV)
                holder.set(bgr)
            except Exception as err:
                sys.stderr.write(f"[callback] {err}\n")

        # Keep a reference so the ctypes trampoline is not garbage-collected.
        self._callback_ref = mw.mw_video_capture_callback(_on_frame)

        self._hvideo = self._cap.mw_create_video_capture(
            self._channel,
            width,
            height,
            _CAPTURE_FOURCC,
            frame_duration,
            self._callback_ref,
            self._holder,
        )
        if not self._hvideo:
            self._callback_ref = None
            return False
        return True

    def stop(self):
        """Stop the SDK capture thread and release the callback reference."""
        if self._hvideo:
            self._cap.mw_destory_video_capture(self._hvideo)
            self._hvideo = 0
        self._callback_ref = None

    @property
    def holder(self):
        """The :class:`FrameHolder` receiving captured BGR frames."""
        return self._holder


# ============================================================================
# Configuration setters (call before initialize / open)
# ============================================================================

def set_sdk_path(path):
    """Set the SDK's bundled Python folder (contains ``mwcapture`` + the DLL).

    Must be called before :func:`initialize`. Returns 0 on success.
    """
    _config["sdk_path"] = str(path)
    return 0


def set_device_index(index):
    """Select which detected device to open (0 = first). Returns 0."""
    _config["device_index"] = int(index)
    return 0


def set_resolution(width, height):
    """Set desired capture resolution. Use 0,0 to follow the input signal.

    Returns 0 on success.
    """
    _config["width"] = int(width)
    _config["height"] = int(height)
    return 0


def set_fps(fps):
    """Set desired capture frame rate. Use 0 to follow the input signal.

    Returns 0 on success.
    """
    _config["fps"] = int(fps)
    return 0


def set_output_dir(path):
    """Set the folder for snapshots and recordings. Returns 0."""
    _config["output_dir"] = str(path)
    return 0


# ============================================================================
# Lifecycle
# ============================================================================

def initialize():
    """Load the Magewell SDK and create the capture instance.

    Lazily adds the configured SDK path to ``sys.path`` / working directory and
    imports the bundled ``mwcapture`` package, then creates the SDK instance and
    refreshes the device list.

    Returns 0 on success, -1 on failure (see :func:`get_last_error`).
    """
    global mw, _cap, _FAMILY_NAMES, _SIGNAL_STATE_NAMES, _CAPTURE_FOURCC
    try:
        if _cap is not None:
            return 0  # already initialised

        sdk_path = _config["sdk_path"]
        if sdk_path and os.path.isdir(sdk_path):
            if sdk_path not in sys.path:
                sys.path.insert(0, sdk_path)
            os.chdir(sdk_path)

        # Lazy import so set_sdk_path() can run first.
        from mwcapture import libmwcapture as _mw
        mw = _mw

        _FAMILY_NAMES = {
            mw.MW_FAMILY_ID_PRO_CAPTURE: "Pro Capture",
            mw.MW_FAMILY_ID_ECO_CAPTURE: "Eco Capture",
            mw.MW_FAMILY_ID_USB_CAPTURE: "USB Capture",
        }
        _SIGNAL_STATE_NAMES = {
            mw.MWCAP_VIDEO_SIGNAL_NONE: "NONE (no source connected)",
            mw.MWCAP_VIDEO_SIGNAL_UNSUPPORTED: "UNSUPPORTED",
            mw.MWCAP_VIDEO_SIGNAL_LOCKING: "LOCKING",
            mw.MWCAP_VIDEO_SIGNAL_LOCKED: "LOCKED",
        }
        # High-level USB capture delivers packed YUV (YUY2).
        _CAPTURE_FOURCC = mw.MWFOURCC_YUY2

        _cap = MagewellCapture()
        return 0
    except Exception as exc:
        _set_error(f"initialize() failed: {exc}")
        return -1


def open_device():
    """Open the configured device index. Returns 0 on success, -1 on failure."""
    try:
        if _cap is None:
            _set_error("open_device() called before initialize()")
            return -1
        _cap.open(_config["device_index"])
        return 0
    except Exception as exc:
        _set_error(f"open_device() failed: {exc}")
        return -1


def get_device_count():
    """Return the number of detected devices, or -1 on error."""
    try:
        if _cap is None:
            _set_error("get_device_count() called before initialize()")
            return -1
        return len(_cap.list_devices())
    except Exception as exc:
        _set_error(f"get_device_count() failed: {exc}")
        return -1


def get_device_info(index):
    """Return "product|serial|family" for a device index, or "" on error."""
    try:
        if _cap is None:
            _set_error("get_device_info() called before initialize()")
            return ""
        for d in _cap.list_devices():
            if d["index"] == int(index):
                return f"{d['product']}|{d['serial']}|{d['family']}"
        _set_error(f"get_device_info(): index {index} not found")
        return ""
    except Exception as exc:
        _set_error(f"get_device_info() failed: {exc}")
        return ""


def get_signal_status():
    """Return the input signal as a 1-D array of doubles.

    Layout: ``[state, width, height, fps, interlaced]`` where ``state`` matches
    the SDK signal-state enum (3 = LOCKED) and ``interlaced`` is 0/1. Returns an
    empty array on error.
    """
    try:
        if _cap is None:
            _set_error("get_signal_status() called before initialize()")
            return np.zeros(0, dtype=np.float64)
        sig = _cap.signal_status()
        return np.array(
            [
                float(sig["state"]),
                float(sig["width"]),
                float(sig["height"]),
                float(sig["fps"]),
                1.0 if sig["interlaced"] else 0.0,
            ],
            dtype=np.float64,
        )
    except Exception as exc:
        _set_error(f"get_signal_status() failed: {exc}")
        return np.zeros(0, dtype=np.float64)


# ============================================================================
# Capture control
# ============================================================================

def start_capture():
    """Start capture using the configured resolution / fps.

    Follows the input signal when width/height/fps are 0, and falls back to a
    supported standard resolution if the requested one is rejected by the
    hardware scaler. Returns 0 on success, -1 on failure. Query the actual size
    with :func:`get_frame_dims`.
    """
    global _active_width, _active_height, _active_fps
    try:
        if _cap is None:
            _set_error("start_capture() called before initialize()")
            return -1

        sig = _cap.signal_status()
        if sig["state"] != mw.MWCAP_VIDEO_SIGNAL_LOCKED:
            _set_error("start_capture(): no locked input signal")
            return -1

        req_width = _config["width"] or sig["width"]
        req_height = _config["height"] or sig["height"]
        if _config["fps"]:
            frame_duration = int(round(1e7 / _config["fps"]))
            out_fps = float(_config["fps"])
        else:
            frame_duration = sig["frame_duration"] or 166667
            out_fps = round(1e7 / frame_duration, 3)

        candidates = [(req_width, req_height)]
        for fb in _FALLBACK_RESOLUTIONS:
            if fb not in candidates:
                candidates.append(fb)

        for cw, ch in candidates:
            if _cap.start(cw, ch, frame_duration):
                _active_width, _active_height, _active_fps = cw, ch, out_fps
                return 0
            sys.stderr.write(f"[Capture_LV] device rejected {cw}x{ch}, trying next...\n")

        _set_error("start_capture(): could not start at any resolution")
        return -1
    except Exception as exc:
        _set_error(f"start_capture() failed: {exc}")
        return -1


def get_frame_dims():
    """Return ``[width, height, channels]`` for the active capture (ints).

    Channels is always 3 (RGB). Returns ``[0, 0, 0]`` if capture is not running.
    """
    return np.array([_active_width, _active_height, 3], dtype=np.int32)


def get_frame(as_rgb=1, timeout_ms=500):
    """Return the latest frame as a flat uint8 array for LabVIEW.

    The array length is ``width * height * 3``; LabVIEW reshapes it to
    ``height x width x 3`` for display. By default pixels are RGB
    (``as_rgb`` non-zero); pass ``as_rgb=0`` to keep the native BGR order.
    ``timeout_ms`` is how long to wait for a fresh frame. Returns an empty
    array if no frame is available.
    """
    try:
        if _cap is None:
            _set_error("get_frame() called before initialize()")
            return np.zeros(0, dtype=np.uint8)

        holder = _cap.holder
        holder.updated.wait(timeout=max(0.0, timeout_ms / 1000.0))
        holder.updated.clear()
        bgr = holder.get()
        if bgr is None:
            return np.zeros(0, dtype=np.uint8)

        frame = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if as_rgb else bgr
        return np.ascontiguousarray(frame, dtype=np.uint8).reshape(-1)
    except Exception as exc:
        _set_error(f"get_frame() failed: {exc}")
        return np.zeros(0, dtype=np.uint8)


def snapshot():
    """Save the latest frame as .npy (raw) + .png (image).

    Returns the saved .png path on success, or "" on failure.
    """
    try:
        if _cap is None:
            _set_error("snapshot() called before initialize()")
            return ""
        bgr = _cap.holder.get()
        if bgr is None:
            _set_error("snapshot(): no frame available yet")
            return ""
        os.makedirs(_config["output_dir"], exist_ok=True)
        base = os.path.join(_config["output_dir"], f"snapshot_{_timestamp()}")
        np.save(base + ".npy", bgr)          # raw data format
        cv2.imwrite(base + ".png", bgr)      # visual image
        return base + ".png"
    except Exception as exc:
        _set_error(f"snapshot() failed: {exc}")
        return ""


def start_recording():
    """Begin recording the live capture to a timestamped .mp4.

    Returns the recording path on success, or "" on failure.
    """
    global _writer
    try:
        if _cap is None:
            _set_error("start_recording() called before initialize()")
            return ""
        if _writer is not None:
            _set_error("start_recording(): already recording")
            return ""
        if not _active_width or not _active_height:
            _set_error("start_recording(): capture not started")
            return ""
        os.makedirs(_config["output_dir"], exist_ok=True)
        path = os.path.join(
            _config["output_dir"],
            f"recording_{_timestamp()}{_config['record_extension']}",
        )
        fourcc = cv2.VideoWriter_fourcc(*_config["record_codec"])
        writer = cv2.VideoWriter(
            path, fourcc, _active_fps or 30.0, (_active_width, _active_height)
        )
        if not writer.isOpened():
            _set_error(f"start_recording(): could not open writer for {path}")
            return ""
        _writer = writer
        return path
    except Exception as exc:
        _set_error(f"start_recording() failed: {exc}")
        return ""


def record_frame():
    """Write the current latest frame to the open recording.

    LabVIEW should call this repeatedly in its acquisition loop while recording.
    Returns 0 on success, -1 on failure.
    """
    try:
        if _writer is None:
            _set_error("record_frame(): not recording")
            return -1
        bgr = _cap.holder.get() if _cap is not None else None
        if bgr is None:
            return 0  # nothing new yet; not an error
        _writer.write(bgr)
        return 0
    except Exception as exc:
        _set_error(f"record_frame() failed: {exc}")
        return -1


def stop_recording():
    """Finish and close the current recording. Returns 0 on success, -1 on error."""
    global _writer
    try:
        if _writer is None:
            return 0
        _writer.release()
        _writer = None
        return 0
    except Exception as exc:
        _set_error(f"stop_recording() failed: {exc}")
        return -1


def stop_capture():
    """Stop the SDK capture thread (device stays open). Returns 0, or -1 on error."""
    global _active_width, _active_height, _active_fps
    try:
        stop_recording()
        if _cap is not None:
            _cap.stop()
        _active_width = _active_height = 0
        _active_fps = 0.0
        return 0
    except Exception as exc:
        _set_error(f"stop_capture() failed: {exc}")
        return -1


def close():
    """Stop capture, close the device and release the SDK. Returns 0, or -1 on error."""
    global _cap
    try:
        stop_recording()
        if _cap is not None:
            _cap.close()
            _cap = None
        return 0
    except Exception as exc:
        _set_error(f"close() failed: {exc}")
        return -1


def get_last_error():
    """Return the most recent error message (empty string if none)."""
    return _last_error


# ============================================================================
# Helpers
# ============================================================================

def _timestamp():
    """Return a millisecond-precision timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


# ============================================================================
# Standalone self-test (mimics the LabVIEW call sequence)
# ============================================================================

def _self_test():
    """Run the full sequence from plain Python to validate before LabVIEW.

    Requires a connected device with a locked input signal.
    """
    print("initialize     ->", initialize())
    if initialize() != 0:
        print("  last error:", get_last_error())
        return

    count = get_device_count()
    print("device count   ->", count)
    for i in range(max(count, 0)):
        print(f"  [{i}] {get_device_info(i)}")

    print("open_device    ->", open_device())
    print("signal status  ->", get_signal_status().tolist())

    if start_capture() != 0:
        print("start_capture  -> FAILED:", get_last_error())
        close()
        return
    print("start_capture  -> 0")
    print("frame dims     ->", get_frame_dims().tolist())

    frame = get_frame()
    print("get_frame len  ->", int(frame.size))

    print("snapshot       ->", snapshot())

    print("stop_capture   ->", stop_capture())
    print("close          ->", close())


if __name__ == "__main__":
    _self_test()
