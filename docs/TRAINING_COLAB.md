# Cloud Training Guide (Google Colab)

This guide walks you through setting up and running the Road Damage System training pipeline on a free Google Colab T4 GPU instance.

## 1. Setup the Environment

Open a new Colab Notebook and select **Runtime > Change runtime type**. Choose **T4 GPU**.

Run the following in a cell to clone the repository and install `uv` and dependencies:

```bash
# Clone the repository
!git clone https://github.com/your-org/road-damage-system.git
%cd road-damage-system

# Install uv (astral)
!curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
import os
os.environ['PATH'] += f":/root/.cargo/bin"

# Install project dependencies
!make setup
```

## 2. Fetch the Data

Assuming your raw data is stored in Google Cloud Storage (GCS) or AWS S3, download it into the `data/raw` folder.

```bash
# Example for GCS:
!gsutil -m cp -r gs://your-bucket/road-damage-data/* data/raw/

# Or if downloading a zip file:
!wget https://example.com/road-damage-data.zip
!unzip road-damage-data.zip -d data/raw
```

## 3. Run the Data Pipeline

Run the data pipeline to audit, split, and convert the dataset to YOLO format.

```bash
# 1. Audit the raw data
!uv run training/audit_dataset.py --dataset_root data/raw

# 2. Sequence-grouped split
!uv run training/make_split.py --dataset_root data/raw --group_strategy prefix

# 3. Leakage check
!uv run training/check_leakage.py --manifest data/processed/split_manifest.csv --dataset_root data/raw

# 4. Convert to 3-class YOLO format
!uv run training/convert_to_3class.py --dataset_root data/raw --manifest data/processed/split_manifest.csv

# 5. Extract orientation crops
!uv run training/make_orientation_crops.py --dataset_root data/raw --manifest data/processed/split_manifest.csv
```

## 4. Train the Models

Train the YOLOv8 object detector and the ResNet18 orientation classifier.

```bash
# Train YOLO detector
!uv run training/train.py --config training/configs/train_v1.yaml

# Evaluate YOLO detector
!uv run training/evaluate.py --weights runs/detect/train_v1/weights/best.pt

# Train Orientation Classifier
!uv run training/train_orientation.py
```

## 5. Export for Production

Export the best PyTorch model to ONNX format for deployment.

```bash
!uv run training/export_onnx.py --weights runs/detect/train_v1/weights/best.pt
```

Download the exported ONNX model and the orientation classifier from the Colab file browser to use in your local `ai-service` deployment!
