"""
Magewell USB Capture Plus - Configure, Display, Record and Snapshot
===================================================================

Uses the MWCapture SDK's bundled `mwcapture` Python (ctypes) package for full
hardware control, OpenCV for live display / recording, and NumPy for frame
buffers and raw snapshot export.

USB Capture devices belong to the SDK "USB Capture" family. The cross-family
high-level call `MWCreateVideoCapture()` is used here: it spins up the SDK's
own capture thread and delivers each decoded frame to a Python callback. The
callback copies the frame into a shared holder; the main thread then displays,
records and snapshots it.

Features
--------
* Device enumeration / selection (Pro / Eco / USB families)
* Input signal status detection (lock state, resolution, frame rate)
* Configurable capture settings (resolution, frame rate, color format)
* Live preview window
* Optional video recording to file
* Snapshot to .npy (raw data) + .png (visual) on demand

Controls (while the preview window is focused)
---------------------------------------------
    s  -> save a snapshot (.npy raw data + .png image)
    r  -> toggle recording on/off
    q  -> quit

Requirements
------------
    pip install opencv-python numpy
    MWCapture SDK installed (provides the bundled `mwcapture` Python package
    and LibMWCapture.dll).
"""

# ============================================================================
# CONFIGURATION  -  edit these values to suit your setup
# ============================================================================

# Folder that contains the `mwcapture` package AND the `mwcapture\bin\...` DLL.
# The SDK loads its DLL with a path relative to this folder, so the script
# changes its working directory here before loading the SDK. This is the SDK's
# bundled Python example directory.
SDK_PYTHON_PATH = r"C:\Program Files\MWCaptureSDK 3.3.1.1556\SDKv3\Examples\Python\AVCapturePY"

# Which detected device to open (0 = first device). Run the script once to
# print the list of detected devices and their indices.
DEVICE_INDEX = 0

# Desired capture resolution. Leave as None to follow the input signal exactly
# (recommended - capturing higher than the input only upscales, adding no
# real detail). Set explicit values to force a fixed capture size.
CAPTURE_WIDTH = None
CAPTURE_HEIGHT = None

# Desired frame rate (frames per second). Set to None to follow the input
# signal's native frame rate.
FPS = 60

# NOTE on color format: the SDK's high-level USB capture delivers packed YUV
# (YUY2 / YUV 4:2:2). This script captures YUY2 and converts to OpenCV-native
# BGR for display, recording and snapshots. No configuration is needed.

# Recording -------------------------------------------------------------------
RECORD = False            # start recording immediately on launch
RECORD_CODEC = "mp4v"     # FourCC for the output container (mp4v -> .mp4)
RECORD_EXTENSION = ".mp4"

# Where snapshots and recordings are written.
OUTPUT_DIR = r"d:\dev\Guy_Storage\Home\Magewell Capture\output"

# Preview window scaling (1.0 = native size).
PREVIEW_SCALE = 1.0

# ============================================================================
# IMPLEMENTATION
# ============================================================================

import os
import sys
import threading
from ctypes import c_ubyte, create_unicode_buffer
from datetime import datetime

import cv2
import numpy as np

# --- Make the bundled SDK package importable and its DLL loadable -------------
# The SDK loads LibMWCapture.dll using a path relative to the current working
# directory, so we must both add the folder to sys.path and chdir into it.
if SDK_PYTHON_PATH and os.path.isdir(SDK_PYTHON_PATH):
    sys.path.insert(0, SDK_PYTHON_PATH)
    os.chdir(SDK_PYTHON_PATH)

try:
    from mwcapture import libmwcapture as mw
except ImportError as exc:  # pragma: no cover - environment specific
    sys.stderr.write(
        "\nERROR: could not import the Magewell 'mwcapture' package.\n"
        "  * Make sure the MWCapture SDK is installed.\n"
        "  * Set SDK_PYTHON_PATH at the top of this file to the SDK's\n"
        "    '...\\Examples\\Python\\AVCapturePY' folder.\n"
        f"  * Underlying error: {exc}\n\n"
    )
    raise


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

# The high-level MWCreateVideoCapture path on USB Capture devices supports
# packed YUV (YUY2). Frames are converted to BGR with OpenCV.
_CAPTURE_FOURCC = mw.MWFOURCC_YUY2

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


class FrameHolder:
    """Thread-safe slot holding the most recent captured frame.

    The SDK capture thread writes frames via :meth:`set` while the main
    thread reads the latest one via :meth:`get`. Only the newest frame is
    kept (old frames are dropped) so display/recording never lag behind.
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

    def __enter__(self):
        """Context-manager entry; returns this instance."""
        return self

    def __exit__(self, *exc):
        """Context-manager exit; always releases SDK resources."""
        self.close()

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
        """Open the device at the given index and return its info dict.

        Resolves the device path for ``index`` and opens a capture channel
        on it. Raises if no devices exist or the index is invalid.
        """
        devices = self.list_devices()
        if not devices:
            raise RuntimeError("No Magewell capture devices detected.")
        match = next((d for d in devices if d["index"] == index), None)
        if match is None:
            raise IndexError(f"DEVICE_INDEX {index} not found among detected devices.")
        path = create_unicode_buffer(128)
        self._cap.mw_get_device_path(index, path)
        self._channel = self._cap.mw_open_channel_by_path(path)
        if not self._channel:
            raise RuntimeError(f"Failed to open device index {index}.")
        return match

    # -- signal -------------------------------------------------------------
    def signal_status(self):
        """Return a dict describing the current input signal.

        Includes lock state, resolution, frame rate, frame duration (in
        100 ns units) and whether the source is interlaced.
        """
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
        """Start the SDK capture thread; BGR frames arrive via the callback.

        Returns True on success. The device only accepts a fixed set of
        standard output resolutions, so this can fail for an unsupported
        (e.g. non-standard / portrait) size; callers should handle False.
        """

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


# --- Application -------------------------------------------------------------
def _ensure_output_dir():
    """Create the snapshot/recording output directory if it is missing."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _timestamp():
    """Return a millisecond-precision timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def _save_snapshot(frame):
    """Save a frame as both raw NumPy data (.npy) and a viewable image (.png)."""
    base = os.path.join(OUTPUT_DIR, f"snapshot_{_timestamp()}")
    np.save(base + ".npy", frame)          # raw data format
    cv2.imwrite(base + ".png", frame)      # visual image
    print(f"[snapshot] saved {base}.npy and {base}.png")


def _open_writer(width, height, fps):
    """Open and return an OpenCV VideoWriter for a new timestamped recording."""
    path = os.path.join(OUTPUT_DIR, f"recording_{_timestamp()}{RECORD_EXTENSION}")
    fourcc = cv2.VideoWriter_fourcc(*RECORD_CODEC)
    writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for {path}")
    print(f"[record] started -> {path}")
    return writer


def main():
    """Run the full capture workflow: enumerate, open, configure and display.

    Enumerates devices, opens ``DEVICE_INDEX``, prints its hardware caps and
    input signal, starts capture at the requested (or native) resolution with
    automatic fallback to a supported standard mode, then runs the live
    preview loop (s = snapshot, r = toggle record, q = quit).
    """
    _ensure_output_dir()

    with MagewellCapture() as cap:
        # 1) Enumerate.
        devices = cap.list_devices()
        print("Detected Magewell devices:")
        for d in devices:
            print(f"  [{d['index']}] {d['family']:<12} {d['product']}  (SN {d['serial']})")
        if not devices:
            print("No devices found. Check connections and SDK installation.")
            return

        # 2) Open the selected device.
        info = cap.open(DEVICE_INDEX)
        print(f"\nOpened device [{DEVICE_INDEX}]: {info['family']} - {info['product']}")

        # Report the device's hardware maximum resolution.
        caps = cap.video_caps()
        if caps:
            print(
                f"Device max: input {caps['max_input_width']}x{caps['max_input_height']}, "
                f"capture {caps['max_output_width']}x{caps['max_output_height']}"
            )

        # 3) Check input signal.
        sig = cap.signal_status()
        print(
            f"Signal: {sig['state_name']} "
            f"{sig['width']}x{sig['height']} @ {sig['fps']} fps "
            f"({'interlaced' if sig['interlaced'] else 'progressive'})"
        )
        if sig["state"] != mw.MWCAP_VIDEO_SIGNAL_LOCKED:
            print("No locked input signal - connect a source and retry.")
            return

        # 4) Resolve capture geometry / timing.
        req_width = CAPTURE_WIDTH or sig["width"]
        req_height = CAPTURE_HEIGHT or sig["height"]
        if FPS:
            frame_duration = int(round(1e7 / FPS))
            out_fps = FPS
        else:
            frame_duration = sig["frame_duration"] or 166667
            out_fps = round(1e7 / frame_duration, 3)

        # 5) Start capture. The device only accepts a fixed set of standard
        # output resolutions, so the requested (possibly native/portrait) size
        # may be rejected. Try it first, then fall back to standard modes.
        candidates = [(req_width, req_height)]
        for fb in _FALLBACK_RESOLUTIONS:
            if fb not in candidates:
                candidates.append(fb)

        width = height = None
        for cw, ch in candidates:
            if cap.start(cw, ch, frame_duration):
                width, height = cw, ch
                break
            print(f"  device rejected {cw}x{ch}, trying next...")

        if width is None:
            print("Could not start capture at any resolution.")
            return

        scaled = (width, height) != (sig["width"], sig["height"])
        note = " (rescaled from input)" if scaled else " (native)"
        print(f"Capturing {width}x{height}{note} (YUY2->BGR) @ ~{out_fps} fps.")

        recording = RECORD
        writer = _open_writer(width, height, out_fps) if recording else None

        window = "Magewell USB Capture Plus"
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        print("\nControls:  s=snapshot   r=toggle record   q=quit\n")

        holder = cap.holder
        try:
            while True:
                # Wait briefly for a new frame to keep the UI responsive.
                holder.updated.wait(timeout=0.5)
                holder.updated.clear()
                bgr = holder.get()

                if bgr is not None:
                    if writer is not None:
                        writer.write(bgr)

                    display = bgr
                    if PREVIEW_SCALE != 1.0:
                        display = cv2.resize(
                            bgr,
                            None,
                            fx=PREVIEW_SCALE,
                            fy=PREVIEW_SCALE,
                            interpolation=cv2.INTER_AREA,
                        )
                    if recording:
                        display = display.copy()
                        cv2.circle(display, (24, 24), 8, (0, 0, 255), -1)
                    cv2.imshow(window, display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("s") and bgr is not None:
                    _save_snapshot(bgr)
                elif key == ord("r"):
                    recording = not recording
                    if recording and writer is None:
                        writer = _open_writer(width, height, out_fps)
                    elif not recording and writer is not None:
                        writer.release()
                        writer = None
                        print("[record] stopped")
        finally:
            if writer is not None:
                writer.release()
            cv2.destroyAllWindows()
            print("Stopped.")


if __name__ == "__main__":
    main()
