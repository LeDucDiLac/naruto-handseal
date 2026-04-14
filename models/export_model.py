import argparse
from pathlib import Path
from ultralytics import YOLO

def export_model(model_path: str, format: str = "onnx", imgsz: int = 640):
    """
    Standalone export script for YOLO models.
    """
    p = Path(model_path).resolve()
    if not p.exists():
        print(f"Error: Model file not found at {p}")
        return

    print(f"--- Export Process Started ---")
    print(f"Source Model: {p}")
    
    # Load the model
    model = YOLO(str(p))
    
    # Export parameters optimized for production
    output_path = model.export(
        format=format,
        imgsz=imgsz,
        dynamic=True,   # Required for varying input sizes/webcam
        simplify=True,  # Optimizes the ONNX graph for speed
        opset=17,       # Matches previous training configuration
    )
    
    print(f"\n--- Export Complete ---")
    print(f"Exported File: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean YOLO Export Tool")
    parser.add_argument("model", type=str, help="Path to the .pt model file")
    parser.add_argument("--format", type=str, default="onnx", help="Export format (default: onnx)")
    parser.add_argument("--imgsz", type=int, default=640, help="Resolution (default: 640)")
    
    args = parser.parse_args()
    export_model(args.model, args.format, args.imgsz)
