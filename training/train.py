"""
Train YOLO26 model on Naruto hand seal dataset.
Fine-tunes a pretrained YOLO26 nano model and exports to ONNX format.
"""

import argparse
import json
from pathlib import Path
from ultralytics import YOLO


def _resolve_project_root(project_root: str | None = None) -> Path:
    if project_root:
        return Path(project_root).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def _resolve_data_yaml(data_yaml: str, project_root: Path) -> Path:
    candidate = Path(data_yaml).expanduser()
    if candidate.is_absolute():
        return candidate

    if candidate.exists():
        return candidate.resolve()

    root_candidate = (project_root / candidate)
    if root_candidate.exists():
        return root_candidate.resolve()

    training_candidate = (project_root / "training" / candidate)
    if training_candidate.exists():
        return training_candidate.resolve()

    return candidate.resolve()


def _save_latest_paths(metadata_path: Path, payload: dict) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


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
    
    # Add overall epoch progress bar using tqdm
    try:
        from tqdm import tqdm
        pbar = tqdm(total=epochs, desc="Overall Training Progress", unit="epoch")
        
        def on_train_epoch_end(trainer):
            pbar.update(1)
            # Update description with current metrics if desired
            if hasattr(trainer, 'metrics') and trainer.metrics:
                map50 = trainer.metrics.get('metrics/mAP50(B)', 0)
                pbar.set_description(f"Overall Progress (mAP50: {map50:.3f})")
                
        def on_train_end(trainer):
            pbar.close()
            
        model.add_callback("on_train_epoch_end", on_train_epoch_end)
        model.add_callback("on_train_end", on_train_end)
    except ImportError:
        pbar = None
        print("tqdm not installed. Skipping overall progress bar.")
    
    # Train
    print(f"\nStarting training for {epochs} epochs...")
    print(f"  Dataset: {data_yaml}")
    print(f"  Image size: {imgsz}")
    print(f"  Batch size: {batch}")
    print(f"  Device: {device}")
    print()

    
    model.train(
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


def export_onnx(model_path: str, output_dir: str):
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
    dest = output_path / "yolo26s.onnx"
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
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory for training results")
    parser.add_argument("--onnx-output", type=str, default=None,
                        help="Directory to store exported ONNX model")
    parser.add_argument("--export-only", type=str, default=None,
                        help="Skip training, only export existing .pt model to ONNX")
    parser.add_argument("--project-root", type=str, default=None,
                        help="Project root path (auto-detected by default)")
    parser.add_argument("--no-export", action="store_true",
                        help="Skip ONNX export after training")
    args = parser.parse_args()

    project_root = _resolve_project_root(args.project_root)
    default_runs_dir = project_root / "runs"
    default_onnx_dir = project_root / "models"
    output_dir = Path(args.output).expanduser().resolve() if args.output else default_runs_dir
    onnx_output_dir = Path(args.onnx_output).expanduser().resolve() if args.onnx_output else default_onnx_dir
    latest_paths_file = project_root / "training" / "latest_paths.json"

    print(f"Project root: {project_root}")
    print(f"Training output dir: {output_dir}")
    print(f"ONNX output dir: {onnx_output_dir}")

    if args.export_only:
        model_path = Path(args.export_only).expanduser().resolve()
        onnx_path = export_onnx(str(model_path), str(onnx_output_dir))
        _save_latest_paths(
            latest_paths_file,
            {
                "project_root": str(project_root),
                "data_yaml": None,
                "best_pt": str(model_path),
                "run_dir": str(model_path.parent.parent) if model_path.parent.name == "weights" else None,
                "onnx": str(Path(onnx_path).resolve()),
            },
        )
        print(f"Latest paths saved to: {latest_paths_file}")
    else:
        resolved_data_yaml = _resolve_data_yaml(args.data, project_root)
        best_model = train(
            data_yaml=str(resolved_data_yaml),
            model_size=args.model_size,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            output_dir=str(output_dir),
        )

        onnx_path = None
        if not args.no_export:
            onnx_path = export_onnx(best_model, str(onnx_output_dir))

        _save_latest_paths(
            latest_paths_file,
            {
                "project_root": str(project_root),
                "data_yaml": str(resolved_data_yaml),
                "best_pt": str(Path(best_model).resolve()),
                "run_dir": str((output_dir / "naruto-handsign").resolve()),
                "onnx": str(Path(onnx_path).resolve()) if onnx_path else None,
            },
        )
        print(f"Latest paths saved to: {latest_paths_file}")


if __name__ == "__main__":
    main()
