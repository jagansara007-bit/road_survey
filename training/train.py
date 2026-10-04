import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml
from ultralytics import YOLO


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:  # noqa: BLE001
        return "unknown"

def hash_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="training/configs/train_v1.yaml")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # 1. Capture git commit and manifest hash
    commit_hash = get_git_commit()
    manifest_path = Path("data/processed/split_manifest.csv")
    manifest_hash = hash_file(manifest_path)

    print(f"Git commit: {commit_hash}")
    print(f"Manifest hash: {manifest_hash}")

    # 2. Load model
    model = YOLO(config.get("model", "yolov8n.pt"))

    # 3. Train
    model.train(
        data=config.get("data", "data/processed/yolo3/dataset.yaml"),
        epochs=config.get("epochs", 10),
        imgsz=config.get("imgsz", 640),
        batch=config.get("batch", 16),
        seed=config.get("seed", 42),
        project=config.get("project", "runs/detect"),
        name=config.get("name", "train_v1"),
        exist_ok=True,
    )
    
    # 4. Save metadata
    save_dir = Path(model.trainer.save_dir) if getattr(model, "trainer", None) else Path(config.get("project", "runs/detect")) / config.get("name", "train_v1")
    save_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "git_commit": commit_hash,
        "manifest_hash": manifest_hash,
        "config": config
    }
    with open(save_dir / "run_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

if __name__ == "__main__":
    main()
