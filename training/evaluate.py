import argparse
import json
import shutil
from pathlib import Path

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, help="Path to weights file (e.g., best.pt)")
    parser.add_argument("--data", default="data/processed/yolo3/dataset.yaml")
    parser.add_argument("--run_name", default="eval_v1")
    args = parser.parse_args()

    model = YOLO(args.weights)
    
    # Evaluate on the test split
    metrics = model.val(data=args.data, split="test", project="runs/detect", name=args.run_name, exist_ok=True)
    
    # metrics.box has map50, map, mp, mr, etc.
    res_dict = {
        "mAP50": float(metrics.box.map50),
        "mAP50-95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
    }

    # Write JSON report
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"{args.run_name}.json"
    with open(json_path, "w") as f:
        json.dump(res_dict, f, indent=2)

    # Markdown report
    md_path = reports_dir / f"{args.run_name}.md"
    
    # Copy confusion matrix to reports dir for easier reference, if it exists
    cm_src = Path("runs/detect") / args.run_name / "confusion_matrix.png"
    cm_dst_str = ""
    if cm_src.exists():
        cm_dst = reports_dir / f"cm_{args.run_name}.png"
        shutil.copy(cm_src, cm_dst)
        cm_dst_str = f"![Confusion Matrix](cm_{args.run_name}.png)"
    
    # Check baseline
    baseline_path = reports_dir / "baseline_v0.json"
    baseline_md = "NOT AVAILABLE"
    if baseline_path.exists():
        try:
            with open(baseline_path, "r") as f:
                baseline_data = json.load(f)
            baseline_md = "```json\n" + json.dumps(baseline_data, indent=2) + "\n```"
        except Exception:  # noqa: BLE001
            baseline_md = "NOT AVAILABLE"

    md_content = f"""# Evaluation Report: {args.run_name}

## Metrics
- **mAP50:** {res_dict['mAP50']:.4f}
- **mAP50-95:** {res_dict['mAP50-95']:.4f}
- **Precision:** {res_dict['precision']:.4f}
- **Recall:** {res_dict['recall']:.4f}

## Confusion Matrix
{cm_dst_str}

## Comparison to baseline v0
{baseline_md}
"""
    with open(md_path, "w") as f:
        f.write(md_content)

    print(f"Evaluation complete. Reports saved to {reports_dir}")

if __name__ == "__main__":
    main()
