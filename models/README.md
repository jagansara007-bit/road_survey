# Pre-Trained & Fine-Tuned AI Models for Road Damage Detection

This directory contains the bundled computer vision models for detecting and classifying road defects from dashcam imagery and video streams.

## Included Models

| Model File | Format | Size | Architecture | Description / Use Case |
| :--- | :--- | :--- | :--- | :--- |
| `best.onnx` | ONNX | ~12.2 MB | YOLOv8 | **Default production model** used by `ai-service/app/detector.py`. Runs fast CPU/GPU inference via `onnxruntime` without requiring PyTorch. |
| `best.pt` | PyTorch | ~6.2 MB | YOLOv8 | Fine-tuned PyTorch checkpoint trained on road damage datasets. Used with Ultralytics YOLO for training, evaluation, and PyTorch runtime. |
| `yolov8n.pt` | PyTorch | ~6.5 MB | YOLOv8 Nano | Base pre-trained YOLOv8 nano model for transfer learning and baseline fine-tuning. |

## Defect Classes Detected

The models are trained to identify 4 municipal road defect categories:
1. **`D00`**: Longitudinal Crack
2. **`D10`**: Transverse Crack
3. **`D20`**: Alligator Crack
4. **`D40`**: Pothole

## How Models are Loaded

When the backend starts (`make run-ai` or `uvicorn app.main:app`), `ai-service/app/detector.py` automatically resolves the model in the following order:
1. `models/best.onnx` (relative to workspace root)
2. Fallback relative paths (`../../../models/best.onnx`, `../../models/best.onnx`)

If `models/best.onnx` is present, it uses `onnxruntime` for real-time defect bounding box prediction, class assignment, and confidence scoring.

## Quick Test After Cloning

To verify model inference immediately after cloning the repository:

```bash
# 1. Install dependencies
uv sync

# 2. Run backend test suite
uv run pytest ai-service/tests -v
```
