# Magewell Capture - Setup & Installation

Step-by-step guide to get `Magewell Capture/capture.py` running on Windows.

## 1. Prerequisites

- **Windows** (the script uses `pywin32` and the Magewell Windows DLL).
- **Python 3.x, 64-bit** — must match the SDK's 64-bit DLL. Check with:
  ```powershell
  python --version
  python -c "import struct; print(struct.calcsize('P') * 8, 'bit')"
  ```
  The second command must print `64 bit`.
- A **Magewell USB Capture** device connected, with a live HDMI source.

## 2. Install the MWCapture SDK

The code depends on Magewell's `mwcapture` package and `LibMWCapture.dll`, which
ship **only** with the MWCapture SDK (not on PyPI).

1. Download the **MWCapture SDK** from Magewell's site (Support -> Downloads).
2. Run the installer (default path is fine), e.g.
   `C:\Program Files\MWCaptureSDK <version>\`.
3. Locate the bundled Python example folder, typically:
   `C:\Program Files\MWCaptureSDK <version>\SDKv3\Examples\Python\AVCapturePY`
   (contains the `mwcapture` package and the DLL).
4. Open `capture.py` and set `SDK_PYTHON_PATH` near the top to that folder's path.

## 3. Create a Python virtual environment

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 4. Install the Python packages

With the virtual environment active:

```powershell
python -m pip install --upgrade pip
python -m pip install opencv-python numpy pywin32
```

| Package         | Why it is needed                                  |
| --------------- | ------------------------------------------------- |
| `opencv-python` | Live preview window, recording, image snapshots   |
| `numpy`         | Frame buffers and raw `.npy` snapshot export      |
| `pywin32`       | Required by the bundled `mwcapture` SDK package   |
| `mwcapture`     | Bundled with the SDK (step 2), not installed here |

## 5. Run the script

```powershell
cd "Work\Cancun\MW_Display_Test\Magewell Capture"
python capture.py
```

Controls (preview window focused): `s` = snapshot (`.npy` + `.png`),
`r` = toggle recording (`.mp4`), `q` = quit.

## 6. Troubleshooting

- **`could not import mwcapture`** — `SDK_PYTHON_PATH` wrong or SDK not installed (step 2).
- **`ImportError: ... win32event`** — `pywin32` missing; re-run step 4.
- **`No devices found`** — confirm device in Device Manager; reconnect and retry.
- **Wrong Python bitness** — reinstall 64-bit Python to match the SDK DLL.
