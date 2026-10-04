import argparse

import numpy as np
import onnxruntime as ort
import torch
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, help="Path to PyTorch weights (.pt)")
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    # 1. Load PyTorch model and export
    print(f"Exporting {args.weights} to ONNX...")
    model = YOLO(args.weights)
    export_path = model.export(format="onnx", imgsz=args.imgsz, simplify=True)
    print(f"Exported to {export_path}")

    # 2. Parity Check
    print("Running PyTorch vs ONNX parity check on 10 synthetic inputs...")
    
    # Load ONNX session
    session = ort.InferenceSession(export_path)
    input_name = session.get_inputs()[0].name
    
    # PyTorch model directly for inference
    # YOLO ultralytics automatically handles tensors if we pass them?
    # Actually, ultralytics model.predict works on images. To get raw tensor output, we can use the underlying PyTorch model.
    pt_model = model.model
    pt_model.eval()
    
    max_diffs = []
    
    for i in range(10):
        # Generate random input: [1, 3, imgsz, imgsz] normalized 0-1
        dummy_input = torch.rand(1, 3, args.imgsz, args.imgsz, dtype=torch.float32)
        
        # PyTorch inference
        with torch.no_grad():
            pt_out = pt_model(dummy_input)
            if isinstance(pt_out, (tuple, list)):
                pt_out = pt_out[0]  # Take main inference output
            pt_out_np = pt_out.cpu().numpy()
            
        # ONNX inference
        onnx_out = session.run(None, {input_name: dummy_input.numpy()})[0]
        
        diff = np.abs(pt_out_np - onnx_out).max()
        max_diffs.append(diff)
        
    overall_max_diff = max(max_diffs)
    print(f"Parity Check Complete. Max absolute difference: {overall_max_diff:.8f}")
    if overall_max_diff > 1e-3:
        print("WARNING: Max difference is larger than 1e-3. Please verify the export.")
    else:
        print("Parity Check Passed!")

if __name__ == "__main__":
    main()
