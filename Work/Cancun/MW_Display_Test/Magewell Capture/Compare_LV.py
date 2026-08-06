"""
RGB Frame Comparator - LabVIEW-callable interface
==================================================

Compares two RGB frames produced by :func:`Capture_LV.get_frame` and exposes
the results through simple getter functions that LabVIEW's **Python Node** can
call one at a time.

Why two metrics?
----------------
* **SSIM (Structural Similarity Index)** — a single score from 0.0 (completely
  different) to 1.0 (identical). Perceptually meaningful: it tolerates minor
  signal noise that would register as pixel differences but look identical to the
  eye. Use ``get_ssim_score()`` as a **pass/fail threshold** (e.g. score >= 0.99).

* **Pixel diff map / stats** — exact, per-pixel absolute difference. Tells you
  *where* the images differ and by *how much*. Use ``get_diff_stats()`` and
  ``get_diff_map()`` to **debug failures** found by the SSIM check.

Why this shape
--------------
* LabVIEW's Python Node calls a *single* function per node and can only pass /
  return numerics, strings, booleans and 1-D/2-D arrays. Every public function
  here returns one of those simple types.
* A Python exception makes the LabVIEW node error out. Every public function
  therefore catches its own exceptions, stores the message in ``_last_error``,
  and returns a safe sentinel value. Call :func:`get_last_error` to read it.
* Module-level state persists for the life of one LabVIEW *Python Session*, so
  the most recent comparison result is available via the getters without
  re-passing the frame data.

Typical LabVIEW call order
--------------------------
    set_output_dir(r"d:\\...\\output")              # optional
    ...
    frame_a = Capture_LV.get_frame(as_rgb=1)        # flat U8 array  (w*h*3)
    dims    = Capture_LV.get_frame_dims()           # [width, height, 3]
    frame_b = Capture_LV.get_frame(as_rgb=1)        # second frame
    ...
    compare_frames(frame_a, frame_b, dims[0], dims[1])  # -> 0 on success
    get_ssim_score()                                # -> float64  (0.0 – 1.0)
    get_diff_stats()                                # -> float64[4]
    get_diff_map()                                  # -> flat U8 array (w*h*3)
    save_diff_image()                               # -> saved .png path

Requirements
------------
    pip install opencv-python numpy scikit-image
"""

import os
import sys
from datetime import datetime

import cv2
import numpy as np

# ============================================================================
# Module state (persists across calls within one LabVIEW Python Session)
# ============================================================================

_config = {
    "output_dir": r"c:\Temp\capture_output",
}

_last_error: str = ""
_last_ssim_score: float = -1.0          # -1 = no comparison run yet
_last_diff_stats: np.ndarray = np.zeros(4, dtype=np.float64)
_last_diff_map: np.ndarray = np.zeros(0, dtype=np.uint8)   # flat, same size as input
_last_frame_shape: tuple = (0, 0, 3)    # (height, width, channels)


def _set_error(message: str) -> None:
    """Record the most recent error message and echo it to stderr."""
    global _last_error
    _last_error = str(message)
    sys.stderr.write(f"[Compare_LV] {_last_error}\n")


def _timestamp() -> str:
    """Return a millisecond-precision timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


# ============================================================================
# Configuration setter
# ============================================================================

def set_output_dir(path: str) -> int:
    """Set the folder where diff images are saved. Returns 0."""
    _config["output_dir"] = str(path)
    return 0


# ============================================================================
# Core comparison
# ============================================================================

def compare_frames(
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    width: int,
    height: int,
    channels: int = 3,
) -> int:
    """Compare two flat uint8 RGB arrays from :func:`Capture_LV.get_frame`.

    Reshapes both arrays to ``(height, width, channels)``, then computes:

    * **Absolute pixel diff map** — stored for :func:`get_diff_map`.
    * **Diff statistics** — stored for :func:`get_diff_stats`.
    * **SSIM score** — per-channel average, stored for :func:`get_ssim_score`.

    Parameters
    ----------
    frame_a, frame_b : flat uint8 numpy arrays (length = width * height * channels)
        The two frames to compare, as returned by ``Capture_LV.get_frame(as_rgb=1)``.
    width, height : int
        Frame dimensions from ``Capture_LV.get_frame_dims()``.
    channels : int, optional
        Number of colour channels (default 3 for RGB/BGR).

    Returns
    -------
    int
        0 on success, -1 on failure (see :func:`get_last_error`).
    """
    global _last_ssim_score, _last_diff_stats, _last_diff_map, _last_frame_shape

    try:
        from skimage.metrics import structural_similarity as ssim

        w, h, c = int(width), int(height), int(channels)
        expected = w * h * c

        frame_a = np.asarray(frame_a, dtype=np.uint8)
        frame_b = np.asarray(frame_b, dtype=np.uint8)

        if frame_a.size != expected or frame_b.size != expected:
            _set_error(
                f"compare_frames(): expected {expected} elements "
                f"({w}x{h}x{c}), got {frame_a.size} and {frame_b.size}"
            )
            return -1

        img_a = frame_a.reshape(h, w, c)
        img_b = frame_b.reshape(h, w, c)

        # --- Pixel diff map -----------------------------------------------
        diff = cv2.absdiff(img_a, img_b)              # (H, W, C) uint8

        # --- Diff statistics ----------------------------------------------
        diff_f = diff.astype(np.float64)
        mean_diff = float(diff_f.mean())
        max_diff = float(diff_f.max())
        rmse = float(np.sqrt((diff_f ** 2).mean()))
        # Pixels where ANY channel changed
        changed_mask = diff.max(axis=2) > 0
        pct_changed = float(changed_mask.sum()) / (w * h) * 100.0

        # --- SSIM per channel, then average --------------------------------
        win_size = min(7, h, w)
        if win_size % 2 == 0:
            win_size -= 1
        if win_size < 1:
            _set_error("compare_frames(): frame too small for SSIM (need >= 1x1)")
            return -1

        ssim_scores = []
        for ch in range(c):
            score, _ = ssim(
                img_a[:, :, ch],
                img_b[:, :, ch],
                win_size=win_size,
                data_range=255,
                full=True,
            )
            ssim_scores.append(score)

        # --- Commit results ------------------------------------------------
        _last_ssim_score = float(np.mean(ssim_scores))
        _last_diff_stats = np.array(
            [mean_diff, max_diff, rmse, pct_changed], dtype=np.float64
        )
        _last_diff_map = np.ascontiguousarray(diff.reshape(-1), dtype=np.uint8)
        _last_frame_shape = (h, w, c)

        return 0

    except ImportError:
        _set_error(
            "compare_frames(): scikit-image not installed. "
            "Run: pip install scikit-image"
        )
        return -1
    except Exception as exc:
        _set_error(f"compare_frames() failed: {exc}")
        return -1


# ============================================================================
# Result getters
# ============================================================================

def get_ssim_score() -> float:
    """Return the average SSIM score from the last :func:`compare_frames` call.

    Range: 0.0 (completely different) to 1.0 (identical). Returns -1.0 if no
    comparison has been run yet.

    Recommended threshold for "same image": >= 0.99 for high-quality capture.
    """
    return _last_ssim_score


def get_diff_stats() -> np.ndarray:
    """Return per-pixel difference statistics as a float64 array.

    Layout: ``[mean_diff, max_diff, rmse, pct_pixels_changed]``

    * ``mean_diff``          — average absolute pixel error across all channels (0-255).
    * ``max_diff``           — maximum absolute pixel error found (0-255).
    * ``rmse``               — root mean squared error across all channels.
    * ``pct_pixels_changed`` — percentage of pixels where any channel changed (0-100).

    Returns ``[0, 0, 0, 0]`` if no comparison has been run yet.
    """
    return _last_diff_stats.copy()


def get_diff_map() -> np.ndarray:
    """Return the absolute pixel difference image as a flat uint8 array.

    The array has the same length as the input frames (``width * height * channels``).
    LabVIEW reshapes it to ``height x width x 3`` for display.

    Returns an empty array if no comparison has been run yet.
    """
    return _last_diff_map.copy()


def save_diff_image(filename: str = "") -> str:
    """Save a false-colour heatmap of the last diff map to *output_dir*.

    The heatmap uses OpenCV's COLORMAP_JET (blue = no change, red = large
    change), making differences immediately visible. A second side-by-side
    PNG with the raw diff is also written.

    Parameters
    ----------
    filename : str, optional
        Base filename (without extension). If empty, a timestamped name is
        generated automatically.

    Returns
    -------
    str
        Path to the saved heatmap ``.png``, or ``""`` on failure.
    """
    try:
        if _last_diff_map.size == 0:
            _set_error("save_diff_image(): no comparison result available")
            return ""

        h, w, c = _last_frame_shape
        if h == 0 or w == 0:
            _set_error("save_diff_image(): invalid frame shape")
            return ""

        diff_img = _last_diff_map.reshape(h, w, c)          # (H, W, 3)

        # Collapse to single-channel intensity for the heatmap
        intensity = diff_img.max(axis=2)                     # (H, W) uint8

        # Apply jet colourmap for easy visual inspection
        heatmap = cv2.applyColorMap(intensity, cv2.COLORMAP_JET)  # BGR

        os.makedirs(_config["output_dir"], exist_ok=True)
        stem = filename if filename else f"diff_{_timestamp()}"
        path = os.path.join(_config["output_dir"], stem + ".png")
        cv2.imwrite(path, heatmap)
        return path

    except Exception as exc:
        _set_error(f"save_diff_image() failed: {exc}")
        return ""


def get_last_error() -> str:
    """Return the most recent error message (empty string if none)."""
    return _last_error


# ============================================================================
# Standalone self-test
# ============================================================================

def _self_test() -> None:
    """Quick validation without a Magewell device.

    Creates two synthetic 1920x1080 RGB frames:
    * Test 1: identical frames  → SSIM should be 1.0, all diff stats 0.
    * Test 2: frames differ by a 50x50 white square in the top-left
      → SSIM < 1.0, non-zero diff stats, diff image saved.
    """
    W, H = 1920, 1080

    print("=== Compare_LV self-test ===\n")

    # -- Test 1: identical frames ------------------------------------------
    rng = np.random.default_rng(42)
    base = rng.integers(0, 256, size=(H * W * 3,), dtype=np.uint8)
    status = compare_frames(base, base.copy(), W, H)
    print(f"Test 1 (identical) compare_frames -> {status}")
    print(f"  SSIM score      : {get_ssim_score():.6f}  (expected ~1.0)")
    stats = get_diff_stats()
    print(f"  mean_diff       : {stats[0]:.4f}  (expected 0)")
    print(f"  max_diff        : {stats[1]:.4f}  (expected 0)")
    print(f"  rmse            : {stats[2]:.4f}  (expected 0)")
    print(f"  pct_changed     : {stats[3]:.4f}%  (expected 0)")
    print()

    # -- Test 2: frames differ by a white 50x50 square ----------------------
    modified = base.copy().reshape(H, W, 3)
    modified[0:50, 0:50, :] = 255
    modified = modified.reshape(-1)

    set_output_dir(r"c:\Temp\capture_output")
    status = compare_frames(base, modified, W, H)
    print(f"Test 2 (50x50 square) compare_frames -> {status}")
    print(f"  SSIM score      : {get_ssim_score():.6f}  (expected < 1.0)")
    stats = get_diff_stats()
    print(f"  mean_diff       : {stats[0]:.4f}")
    print(f"  max_diff        : {stats[1]:.4f}  (expected ~255)")
    print(f"  rmse            : {stats[2]:.4f}")
    print(f"  pct_changed     : {stats[3]:.4f}%")

    saved = save_diff_image()
    print(f"  diff image      : {saved if saved else '(save failed)'}")
    if get_last_error():
        print(f"  last error      : {get_last_error()}")

    print("\nDone.")


if __name__ == "__main__":
    _self_test()
