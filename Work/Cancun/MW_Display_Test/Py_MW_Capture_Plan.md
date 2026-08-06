# Plan: Magewell USB Capture Python Script

## Summary
A single `capture.py` script using the MWCapture SDK's bundled `mwcapture` ctypes
package for full hardware control, OpenCV for live display/recording, and NumPy
for frame buffers and raw snapshot export. Config block at the top; no GUI widgets.

**Output file**: `Home/Magewell Capture/capture.py`

## Environment
- MWCapture SDK installed; its bundled Python example folder
  (`...\Examples\Python\AVCapturePY`) provides the `mwcapture` package and
  `LibMWCapture.dll`. Point `SDK_PYTHON_PATH` at this folder.
- Python 3.x, 64-bit, in a virtual environment.

## Key technical findings
- The bundled `mwcapture.libmwcapture` requires **pywin32** (`from win32 import win32event`).
- The SDK loads `LibMWCapture.dll` via a path **relative to the CWD**, so the
  script does `os.chdir(SDK_PYTHON_PATH)` before importing.
- USB Capture is a distinct device **family (0x02)**; the SDK's PyQt sample
  skips it. The correct cross-family path is the high-level
  **`MWCreateVideoCapture(channel, w, h, fourcc, frameDuration, callback, param)`**
  which runs its own thread and pushes frames to a Python callback.
- The high-level USB capture path **only accepts YUY2** (packed YUV 4:2:2,
  `cbFrame = w*h*2`). BGR24/RGB24 return a NULL handle. The script captures YUY2
  and converts to BGR with `cv2.cvtColor(..., cv2.COLOR_YUV2BGR_YUYV)`.
- The USB hardware scaler **only outputs a fixed set of standard display modes**.
  `mw_create_video_capture` returns a NULL handle for non-standard or portrait
  sizes. The script therefore tries the requested/native size first, then falls
  back through `_FALLBACK_RESOLUTIONS` (largest standard mode first).
- `mw_get_video_caps` reports the device's max input / output resolution,
  surfaced at startup via `video_caps()`.
- Struct fields are camelCase (`cx`, `cy`, `dwFrameDuration`, `bInterlaced`).
- Device path buffer is `create_unicode_buffer(128)`.

## Architecture
- **Config block** — `SDK_PYTHON_PATH`, `DEVICE_INDEX`, `CAPTURE_WIDTH/HEIGHT`
  (default `None` = follow native signal), `FPS` (default `60`; `None` = follow
  native), `RECORD` / `RECORD_CODEC` (`mp4v`) / `RECORD_EXTENSION` (`.mp4`),
  `OUTPUT_DIR`, `PREVIEW_SCALE`, plus `_FALLBACK_RESOLUTIONS`
- **`MagewellCapture`** class — init/refresh, `list_devices()`,
  `open()`, `signal_status()`, `video_caps()` (hardware max in/out),
  `start()` (creates callback + `mw_create_video_capture`, returns `bool`),
  `stop()` (`mw_destory_video_capture`)
- **`FrameHolder`** — thread-safe latest-frame slot; callback (SDK thread)
  converts YUY2->BGR and stores; main thread displays/records/snapshots
- **`main()`** — enumerate -> open -> print caps -> check LOCKED signal ->
  start (native, then fallback) -> OpenCV loop

## Controls
- `s` -> snapshot: saves `.npy` (raw BGR array) + `.png` (image)
- `r` -> toggle recording (mp4v `.mp4`)
- `q` -> quit (clean teardown in `finally`)

## Dependencies
- `opencv-python`, `numpy`, `pywin32`
- `mwcapture` — bundled with the MWCapture SDK (via `SDK_PYTHON_PATH`)

## Notes / possible enhancements
- Latest-frame model means recording writes at ~display rate (drops frames).
  For frame-accurate recording, write inside the callback instead.
- `CAPTURE_WIDTH/HEIGHT = None` follows the native signal, but if that size is
  not a supported scaler mode the script auto-falls back to the largest standard
  mode. To capture true native pixels, raise the **source** output to a standard
  mode, or use a low-level (non-scaled) capture path.
