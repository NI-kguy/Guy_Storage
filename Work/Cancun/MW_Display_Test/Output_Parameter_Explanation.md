# Image Comparison Metrics: Technical Reference Manual

When comparing a baseline (reference) image against a test image, mathematical
metrics are essential to quantify differences objectively.

This document explains the outputs exposed by Compare_LV: the SSIM score from
get_ssim_score(), plus the four diff-stat fields returned by get_diff_stats().

---

## Metric Breakdown & Analytical Comparison

### 0. Structural Similarity Score (get_ssim_score)
Structural Similarity Index Measure (SSIM) is a highly advanced,
perception-based metric used to measure the similarity between two images.
Unlike traditional pixel-by-pixel metrics like mean_diff, max_diff, or rmse
(which only look at absolute numerical color differences), SSIM was
specifically engineered to model how the human visual system perceives image
quality. Developed by Zhou Wang et al. in 2004, SSIM recognizes that humans are
deeply attuned to structural information and patterns in a scene, rather than
the exact raw intensity of individual pixels.

The Core Philosophy: The Three Components

SSIM evaluates the difference between a reference image $x$ and a distorted
image $y$ by breaking down the comparison into three distinct, mathematically
independent categories: Luminance, Contrast, and Structure.

1. Luminance ($l(x, y)$)
What it measures: Differences in the average brightness or intensity between
the two images.
How it works: It calculates the mean pixel intensity ($\mu_x$ and $\mu_y$) of
both images. If one image is uniformly brighter than the other, the luminance
component decreases.
Formula:
$$l(x, y) = \frac{2\mu_x\mu_y + C_1}{\mu_x^2 + \mu_y^2 + C_1}$$
(Where $C_1$ is a small constant used to prevent division-by-zero errors when
denominators approach zero).

2. Contrast ($c(x, y)$)
What it measures: Differences in the sharpness or dynamic range of the images.
How it works: It compares the standard deviations ($\sigma_x$ and $\sigma_y$)
of the pixel intensities. Standard deviation dictates the variance in an image;
a blurred image loses its sharp contrast transitions, resulting in a lower
standard deviation.
Formula:
$$c(x, y) = \frac{2\sigma_x\sigma_y + C_2}{\sigma_x^2 + \sigma_y^2 + C_2}$$
(Where $C_2$ is a stabilization constant).

3. Structure ($s(x, y)$)
What it measures: Spatial patterns, pixel correlations, and shapes, completely
independent of local brightness or contrast variations.
How it works: It evaluates the cross-covariance ($\sigma_{xy}$) between the two
images. If structures, edges, or textures align perfectly across both images,
the structural correlation is high.
Formula:
$$s(x, y) = \frac{\sigma_{xy} + C_3}{\sigma_x\sigma_y + C_3}$$
(Where $C_3$ is a stabilization constant).

The Complete SSIM Formula

When these three independent terms are multiplied together (assuming standard
equal weighting exponents $\alpha = \beta = \gamma = 1$), they simplify into
the complete, classic SSIM equation:
$$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}$$

Interpreting the Score:
Range: -1 to +1 (though in practical image quality assessment, it almost always
falls between 0 and 1).
A score of 1.0: Means the two images are structurally identical.
A score of 0.0: Indicates absolutely zero structural relationship between the
images.

### 1. Mean Absolute Difference (`mean_diff`)
* **Mathematical Definition:** $$\text{mean\_diff} = \frac{1}{M \times N \times C} \sum_{x=1}^{M} \sum_{y=1}^{N} \sum_{c=1}^{C} |I_{\text{base}}(x,y,c) - I_{\text{test}}(x,y,c)|$$
  *Where $M \times N$ is the image dimensions, and $C$ is the number of color channels (e.g., 3 for RGB, 1 for Grayscale).*
* **Value Range:** `0` (Identical) to `255` (Maximum theoretical divergence).
* **Behavior Profile:** Measures the *global average shift*. It accumulates all absolute channel differences and averages them evenly across the entire pixel-channel space.
* **Primary Use Cases:**
  * Detecting global exposure shifts or ambient lighting variations in automated optical inspection (AOI).
  * Validating uniform color correction, white balance adjustments, or display brightness adjustments.
* **Limitations:** Prone to dilution. A severe localized defect (e.g., a completely corrupted $5\times5$ pixel block) will be mathematically averaged out across a high-resolution image, leading to a misleadingly low `mean_diff`.

### 2. Maximum Absolute Difference (`max_diff`)
* **Mathematical Definition:**
  $$\text{max\_diff} = \max_{x,y,c} |I_{\text{base}}(x,y,c) - I_{\text{test}}(x,y,c)|$$
* **Value Range:** `0` (Identical) to `255` (Absolute inversion, e.g., pure black `#000000` vs. pure white `#FFFFFF`).
* **Behavior Profile:** Strict, single-point peak detector. It scans the entire matrix and returns only the single largest delta found anywhere in the image array.
* **Primary Use Cases:**
  * **Zero-tolerance validation:** Testing high-precision UI elements, text anti-aliasing rendering engines, or safety-critical displays where even a single incorrect pixel indicates a failure.
  * Detecting single-pixel dropouts, dead pixels on camera sensors, or isolated hardware rendering artifacts.
* **Limitations:** Highly volatile and susceptible to high-frequency noise. A single random spark of sensor noise or single-pixel jitter will trigger a massive spike in `max_diff`, potentially causing false positives in noisy test environments.

### 3. Root Mean Square Error (`rmse`)
* **Mathematical Definition:**
  $$\text{RMSE} = \sqrt{\frac{1}{M \times N \times C} \sum_{x=1}^{M} \sum_{y=1}^{N} \sum_{c=1}^{C} (I_{\text{base}}(x,y,c) - I_{\text{test}}(x,y,c))^2}$$
* **Value Range:** `0` to `255`.
* **Behavior Profile:** Variance-sensitive. Because the error term is squared before averaging, **larger errors are penalized significantly more heavily than smaller errors.**
* **Primary Use Cases:**
  * Modeling human visual perception. Humans notice sharp, localized defects (like a distinct smudge, compression artifact block, or blotch) much more readily than faint, uniformly distributed noise.
  * Evaluating lossy compression algorithms (e.g., JPEG optimization levels) or blending/blurring filters.
* **Comparative Example:** Consider two error profiles:
  * **Profile A:** 1,000 pixels are slightly off by a value of `2`.
  * **Profile B:** Only 10 pixels are severely off by a value of `100`.
  * Both yield similar total linear error, but Profile B will result in a much higher `rmse` than Profile A, successfully flagging the sharp defect.

### 4. Percentage of Pixels Changed (`pct_pixels_changed`)
* **Mathematical Definition:**
  $$\text{pct\_pixels\_changed} = \frac{\sum_{x=1}^{M} \sum_{y=1}^{N} \text{Condition}(x,y)}{M \times N} \times 100$$
  *Where $\text{Condition}(x,y) = 1$ if $\exists c \text{ such that } |I_{\text{base}}(x,y,c) - I_{\text{test}}(x,y,c)| > 0$, else $0$.*
  *(Implementation note: current Compare_LV does not expose a configurable threshold for this check.)*
* **Value Range:** `0.0%` to `100.0%`.
* **Behavior Profile:** Spatial frequency/coverage counter. It maps the structural spread of a change rather than its color intensity.
* **Primary Use Cases:**
  * **Layout and Alignment Verification:** If a text box or button shifts out of position by even 2 pixels, `mean_diff` might remain low if the background matches, but `pct_pixels_changed` will spike dramatically because a massive cluster of pixels now covers different structural content.
  * Detecting missing UI components, structural overlaps, or unexpected element injections.
* **Limitations:** Insensitive to magnitude. If an image undergoes a subtle 1-unit brightness bump across all pixels, `pct_pixels_changed` will hit `100.0%` under the current `> 0` rule, even though the images are visually almost indistinguishable.

---

## Matrix Selection Guide

| Metric | Target Defect | Blind Spots | Test Environment Suitability |
| :--- | :--- | :--- | :--- |
| **`mean_diff`** | Global brightness/tint drift, camera exposure anomalies. | Concentrated local artifacts, text shifts. | Highly stable in noisy analog capture loops. |
| **`max_diff`** | Dead pixels, isolated rendering glitches, micro-artifacts. | Highly prone to sensor noise false alerts. | Best for pure digital-to-digital bitwise checks. |
| **`rmse`** | Localized smudges, blurring, compression blocks. | Uniform background hiss vs. single spike. | Standard for visual QA and compression evaluation. |
| **`pct_pixels_changed`** | Layout misalignments, structural shifts, component absence. | Absolute color error severity or intensity changes. | Excellent for automated web/mobile app UI regression testing. |

---

## Practical Application Strategies

In automated testing pipelines, relying on a single metric often introduces blind spots. A robust image validation framework typically utilizes a **combined threshold gate**:

1. **Digital UI & Render Testing:** Use SSIM as the first gate (for example,
  SSIM $\ge 0.99$) and then bound `max_diff` and `pct_pixels_changed` to catch
  hard pixel faults and small shifts.
2. **Camera / Hardware Vision Testing:** Use SSIM and `mean_diff` to monitor
  overall visual stability, plus an `rmse` gate to detect localized artifacts
  such as smudges, obstruction, or blur.

All thresholds above are starting points only and should be tuned per capture
pipeline.

---

## API Mapping (LabVIEW Python Node)

| Function | Return Type | Meaning | Pre-Run Sentinel |
| :--- | :--- | :--- | :--- |
| **`get_ssim_score()`** | float64 | Channel-mean SSIM similarity score. | `-1.0` |
| **`get_diff_stats()`** | float64[4] | `[mean_diff, max_diff, rmse, pct_pixels_changed]` | `[0,0,0,0]` |
| **`get_diff_map()`** | uint8[] (flat) | Absolute per-channel diff image (`w*h*c` length). | empty array |
| **`get_last_error()`** | string | Last captured error message. | empty string |

---

## Worked Example (Localized Defect)

Assume a 1920x1080 RGB frame where only a small 50x50 patch changes strongly.

1. **Expected SSIM behavior:** get_ssim_score() drops below `1.0`, often still
  relatively high because most of the image is unchanged.
2. **Expected diff stats behavior:**
  * `mean_diff` increases slightly (localized region diluted by full frame).
  * `max_diff` may approach `255` if the patch contains extreme deltas.
  * `rmse` rises more than mean_diff when the defect is strong.
  * `pct_pixels_changed` approximates changed-area percentage.
3. **Expected diff map behavior:** get_diff_map() highlights the changed patch
  location directly after reshaping to height x width x channels.