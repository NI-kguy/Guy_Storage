# Capture_LV.py — Session Summary

LabVIEW-callable Python interface for the Magewell USB Capture Plus, derived from
`capture.py`. This document compacts the work done in this session.

## Goal

Reuse the `capture.py` capture feature but drive it from **LabVIEW** instead of an
interactive OpenCV window. LabVIEW calls Python functions via its **Python Node**
(LabVIEW 2020+) and handles all display itself.

## Decisions

- **New file only:** `Capture_LV.py`; `capture.py` is left completely unchanged.
- **Self-contained:** `FrameHolder` + `MagewellCapture` engine copied in (not imported)
  for single-file LabVIEW deployment.
- **Frame delivery:** live frames returned as a flat `uint8` **RGB** array
  (`width*height*3`) for LabVIEW to reshape/display, plus snapshot-to-file.
- **No OpenCV window** — display is LabVIEW's job.
- **Config setters** exposed so LabVIEW sets SDK path / device / resolution / fps / output.
- Recording functions included as a bonus.

## Design constraints (why the API looks like this)

- LabVIEW's Python Node calls **one function per node** and passes/returns only
  numerics, strings, booleans and 1-D/2-D arrays → every public function uses those types.
- A Python exception makes the LabVIEW node error out → every public function catches
  its own exceptions, stores the message, and returns a status code
  (`0` = success, negative/empty = error). Read the message with `get_last_error()`.
- Module-level globals persist for one LabVIEW **Python Session** → open device and
  running capture are held in globals between calls.
- The Magewell SDK is imported **lazily inside `initialize()`** so `set_sdk_path()`
  can run first.

## Function API

**Config (call before initialize/open):**
`set_sdk_path`, `set_device_index`, `set_resolution(w,h)` (0,0 = follow signal),
`set_fps` (0 = follow signal), `set_output_dir` — each returns `0`.

**Lifecycle / info:**
- `initialize()` → `0` / `-1` (lazy SDK import + create instance)
- `open_device()` → `0` / `-1`
- `get_device_count()` → int
- `get_device_info(i)` → `"product|serial|family"`
- `get_signal_status()` → `[state, width, height, fps, interlaced]` (3 = LOCKED)

**Capture:**
- `start_capture()` → `0` / `-1` (auto-fallback to a supported resolution)
- `get_frame_dims()` → `[width, height, 3]`
- `get_frame(as_rgb=1, timeout_ms=500)` → flat `uint8` array (`w*h*3`)
- `snapshot()` → saved `.png` path (also writes `.npy`)

**Recording (optional):**
- `start_recording()` → `.mp4` path
- `record_frame()` → `0` / `-1` (call each loop iteration while recording)
- `stop_recording()` → `0` / `-1`

**Teardown / errors:**
- `stop_capture()` → `0`
- `close()` → `0`
- `get_last_error()` → message string

## Typical LabVIEW call order

```text
set_sdk_path(...) / set_output_dir(...) / set_device_index(0)
set_resolution(0, 0)        # follow signal
set_fps(60)
initialize()  -> 0
open_device() -> 0
get_signal_status()
start_capture() -> 0
loop:
    get_frame_dims()
    get_frame()             # reshape to height x width x 3 for display
    snapshot()              # on demand
stop_capture()
close()
```

## Issue found & fixed

- **`initialize() failed: No module named 'win32'`** → the SDK's `mwcapture` package
  needs **pywin32**. Installed `pywin32` into the workspace venv (`d:\dev\Guy_Storage\.venv`).

## Validation

- Syntax / byte-compile: clean.
- Static analysis / lint: no errors.
- No-hardware paths: all functions return documented error values gracefully (no crash).
- **Full hardware run passed** via `python Capture_LV.py`:
  - Device: **USB Capture HDMI+** (SN C204230314763)
  - Signal LOCKED 1280×1440 @ 59.95 fps
  - Native 1280×1440 rejected → auto fell back to 1920×1080
  - `get_frame` returned 6,220,800 bytes (= 1920×1080×3) ✓
  - Snapshot saved; clean `stop_capture` / `close`

## How to run in the venv

Venv location: `d:\dev\Guy_Storage\.venv`

**Direct (no activation):**
```powershell
cd "d:\dev\Guy_Storage\Work\Cancun\MW_Display_Test\Magewell Capture"
d:\dev\Guy_Storage\.venv\Scripts\python.exe Capture_LV.py
```

**Activate then run:**
```powershell
d:\dev\Guy_Storage\.venv\Scripts\Activate.ps1
cd "d:\dev\Guy_Storage\Work\Cancun\MW_Display_Test\Magewell Capture"
python Capture_LV.py
```

**Verify dependencies:**
```powershell
d:\dev\Guy_Storage\.venv\Scripts\python.exe -c "import cv2, numpy, win32api; print('deps OK')"
```

## LabVIEW setup notes

- **Open Python Session** → Python Path: `d:\dev\Guy_Storage\.venv\Scripts\python.exe`,
  Python Version: `3.11`.
- LabVIEW must be **64-bit** to match the venv and the Magewell 64-bit DLL.
- Confirm LabVIEW's supported Python version covers 3.11 (LabVIEW 2023 Q3+); otherwise
  recreate the venv with a matching Python version.
- Using a different interpreter re-triggers `No module named ...` errors.

## Requirements

```text
pip install opencv-python numpy pywin32
MWCapture SDK installed (provides the bundled `mwcapture` package + LibMWCapture.dll)
```
