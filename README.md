# 🧰 Toolbox DXF Generator (Transparent PNG + Pro Mode)

This desktop application processes **transparent PNG images (with alpha channel)**, detects the contours of the tools, scales them according to a reference object, and exports a **DXF CAD file** ready for CNC / laser cutting.

The reference is automatically selected as the **contour closest to the bottom-right corner of the image** (usually a square marker placed in the scene).  
You can optionally enable **Pro Mode** to fine-tune curve smoothing, contour simplification, and scaling factors.

<p align="center">
  <em>Transparent PNG → Contour Detection → Scaling → DXF Export</em>
</p>

---

## ✨ Features

- ✅ Reads **transparent PNG** (alpha masking)
- ✅ If alpha is missing, falls back to grayscale thresholding for segmentation
- ✅ Automatically detects the reference square (closest object to image bottom-right)
- ✅ DXF output using polylines or splines
- ✅ Built-in GUI (Tkinter)
- ✅ **Pro Mode** for advanced users:
  - Enable/disable spline curve generation
  - Adjustable `approxPolyDP` epsilon value
  - Manual override of `SCALE_FIX_X / SCALE_FIX_Y`
  - Optional debug visual preview window

---

## 🧠 How It Works

1. Transparent PNG is loaded.
2. Alpha channel (or thresholded grayscale) is used to extract masks.
3. All contours are detected; the reference contour is chosen automatically.
4. Real dimensions (in millimeters) of that reference are entered by the user.
5. The contour points are scaled by `mm_per_pixel * scale_fix`.
6. Final DXF (`output/<filename>.dxf`) is generated.

---

## 🔧 Pro Mode Details

| Setting | Effect |
|---------|--------|
| **Spline Mode** | Generates smooth curves via `scipy.splprep`. If spline fails, fallback to polyline. |
| **Epsilon** | Controls contour simplification (`approxPolyDP`). Higher → fewer points, more angular. |
| **SCALE_FIX_X / SCALE_FIX_Y** | Additional scale factor to compensate lens/perspective distortion. |
| **Debug Preview** | Shows a temporary OpenCV window highlighting detected reference contour. |

**Default values (when Pro Mode is OFF):**

---

## 🔄 Optional Version: Background Removal via API (remove.bg)

There is an **alternative version** of this project that automatically removes the background using the `remove.bg` API.

### What this version does:
- Sends the input image to remove.bg
- Receives a transparent PNG with clean edges
- Passes that PNG to the same DXF generator pipeline

<p align="center">
  <em>JPEG → remove.bg API → Transparent PNG → DXF Generator</em>
</p>

### Benefits
- No need to manually remove background
- Works even if the image does not have transparency (PNG alpha)
- Ideal for quick scanning of tools

### Requirements
- remove.bg API key: https://www.remove.bg/api
- Internet connection

Place your API key in a `.env` file:


```python
DEFAULT_USE_SPLINE = True
DEFAULT_EPSILON = 0.0025
DEFAULT_SCALE_FIX_X = 1.10
DEFAULT_SCALE_FIX_Y = 1.10
