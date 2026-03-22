"""
Train YOLO26 model on Naruto hand seal dataset.
Fine-tunes a pretrained YOLO26 nano model and exports to ONNX format.
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def train(data_yaml: str, model_size: str = "n", epochs: int = 100,
          batch: int = 16, imgsz: int = 640, device: str = "0",
          output_dir: str = "./runs"):
    """
    Train YOLO26 on the hand seal dataset.
    
    Args:
        data_yaml: Path to data.yaml
        model_size: Model size variant (n=nano, s=small, m=medium)
        epochs: Number of training epochs
        batch: Batch size
        imgsz: Input image size
        device: Device to train on ('0' for GPU, 'cpu' for CPU)
        output_dir: Directory to save training results
    """
    # Load pretrained YOLO26 model
    model_name = f"yolo26{model_size}.pt"
    print(f"Loading pretrained model: {model_name}")
    model = YOLO(model_name)
    
    # Train
    print(f"\nStarting training for {epochs} epochs...")
    print(f"  Dataset: {data_yaml}")
    print(f"  Image size: {imgsz}")
    print(f"  Batch size: {batch}")
    print(f"  Device: {device}")
    print()
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        augment=True,
        patience=20,           # Early stopping patience
        save=True,
        save_period=10,        # Save checkpoint every 10 epochs
        project=output_dir,
        name="naruto-handsign",
        exist_ok=True,
        # Augmentation settings
        hsv_h=0.015,           # HSV-Hue augmentation
        hsv_s=0.7,             # HSV-Saturation augmentation
        hsv_v=0.4,             # HSV-Value augmentation
        degrees=15.0,          # Rotation augmentation
        translate=0.1,         # Translation augmentation
        scale=0.5,             # Scale augmentation
        flipud=0.0,            # No vertical flip (hand signs are orientation-dependent)
        fliplr=0.5,            # Horizontal flip
        mosaic=1.0,            # Mosaic augmentation
        mixup=0.1,             # MixUp augmentation
    )
    
    # Get best model path
    best_model_path = Path(output_dir) / "naruto-handsign" / "weights" / "best.pt"
    print(f"\nTraining complete!")
    print(f"Best model: {best_model_path}")
    print(f"Results: {Path(output_dir) / 'naruto-handsign'}")
    
    return str(best_model_path)


def export_onnx(model_path: str, output_dir: str = "../models"):
    """
    Export trained model to ONNX format for production inference.
    
    Args:
        model_path: Path to trained .pt model
        output_dir: Directory to save ONNX model
    """
    print(f"\nExporting to ONNX: {model_path}")
    model = YOLO(model_path)
    
    # Export with dynamic batch size and simplified graph
    onnx_path = model.export(
        format="onnx",
        dynamic=True,      # Dynamic input size
        simplify=True,     # Simplify ONNX graph
        opset=17,          # ONNX opset version
        imgsz=640,
    )
    
    # Copy to output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    import shutil
    dest = output_path / "best.onnx"
    shutil.copy2(onnx_path, dest)
    
    print(f"ONNX model exported to: {dest}")
    print(f"ONNX model size: {dest.stat().st_size / 1024 / 1024:.1f} MB")
    
    return str(dest)


def main():
    parser = argparse.ArgumentParser(description="Train YOLO26 on Naruto hand seals")
    parser.add_argument("--data", type=str, required=True,
                        help="Path to data.yaml")
    parser.add_argument("--model-size", type=str, default="n",
                        choices=["n", "s", "m", "l", "x"],
                        help="YOLO26 model size (default: n=nano)")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Training epochs (default: 100)")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (default: 16)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Input image size (default: 640)")
    parser.add_argument("--device", type=str, default="0",
                        help="Device: '0' for GPU, 'cpu' for CPU")
    parser.add_argument("--output", type=str, default="./runs",
                        help="Output directory for training results")
    parser.add_argument("--export-only", type=str, default=None,
                        help="Skip training, only export existing .pt model to ONNX")
    args = parser.parse_args()

    if args.export_only:
        export_onnx(args.export_only)
    else:
        best_model = train(
            data_yaml=args.data,
            model_size=args.model_size,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            output_dir=args.output,
        )
        export_onnx(best_model)


if __name__ == "__main__":
    main()
