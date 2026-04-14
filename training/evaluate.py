"""
Evaluate the trained YOLO26 model on the test set.
Generates confusion matrix, per-class metrics, and visualizations.
"""

import argparse
import json
from pathlib import Path

from ultralytics import YOLO


CLASSES = [
    "bird", "boar", "dog", "dragon", "hare", "horse",
    "monkey", "ox", "ram", "rat", "snake", "tiger"
]


def _resolve_project_root(project_root: str | None = None) -> Path:
    if project_root:
        return Path(project_root).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def _load_latest_paths(project_root: Path) -> dict:
    latest_paths_file = project_root / "training" / "latest_paths.json"
    if latest_paths_file.exists():
        try:
            with latest_paths_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _find_latest_best_pt(project_root: Path) -> Path | None:
    candidates = list(project_root.glob("runs/**/weights/best.pt"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _resolve_model_path(model_path: str | None, project_root: Path, latest: dict) -> Path:
    if model_path:
        return Path(model_path).expanduser().resolve()

    latest_best = latest.get("best_pt") if isinstance(latest, dict) else None
    if latest_best:
        candidate = Path(latest_best).expanduser().resolve()
        if candidate.exists():
            return candidate

    discovered = _find_latest_best_pt(project_root)
    if discovered:
        return discovered.resolve()

    raise FileNotFoundError(
        "Could not resolve model path. Pass --model or run training first to create training/latest_paths.json."
    )


def _resolve_data_yaml(data_yaml: str | None, project_root: Path, latest: dict) -> Path:
    if data_yaml:
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

    latest_data = latest.get("data_yaml") if isinstance(latest, dict) else None
    if latest_data:
        candidate = Path(latest_data).expanduser().resolve()
        if candidate.exists():
            return candidate

    fallback_candidates = [
        project_root / "training" / "Naruto-hand-sign-1" / "data.yaml",
        project_root / "training" / "data.yaml",
        project_root / "data.yaml",
    ]
    for candidate in fallback_candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "Could not resolve data.yaml path. Pass --data explicitly."
    )


def evaluate(model_path: str, data_yaml: str, device: str = "0",
             output_dir: str = "./eval_results"):
    """
    Run evaluation on the test/validation set and generate reports.
    """
    print(f"Loading model: {model_path}")
    model = YOLO(model_path)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    print(f"\nRunning evaluation on: {data_yaml}")
    results = model.val(
        data=data_yaml,
        device=device,
        save_json=True,
        plots=True,
        project=output_dir,
        name="eval",
        exist_ok=True,
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    
    print(f"\nmAP@0.5:      {results.box.map50:.4f}")
    print(f"mAP@0.5:0.95: {results.box.map:.4f}")
    print(f"Precision:    {results.box.mp:.4f}")
    print(f"Recall:       {results.box.mr:.4f}")
    
    # Per-class metrics
    print(f"\n{'Class':<12} {'Precision':>10} {'Recall':>10} {'mAP@0.5':>10}")
    print("-" * 45)
    
    for i, cls_name in enumerate(CLASSES):
        if i < len(results.box.ap50):
            p = results.box.p[i] if i < len(results.box.p) else 0
            r = results.box.r[i] if i < len(results.box.r) else 0
            ap50 = results.box.ap50[i]
            print(f"{cls_name:<12} {p:>10.4f} {r:>10.4f} {ap50:>10.4f}")
    
    print("-" * 45)
    print(f"{'MEAN':<12} {results.box.mp:>10.4f} {results.box.mr:>10.4f} {results.box.map50:>10.4f}")
    
    # Check if target met
    target_map = 0.80
    if results.box.map50 >= target_map:
        print(f"\n✅ Target mAP@0.5 ≥ {target_map} ACHIEVED! ({results.box.map50:.4f})")
    else:
        print(f"\n⚠️ Target mAP@0.5 ≥ {target_map} NOT MET ({results.box.map50:.4f})")
        print("   Consider: more training epochs, more data, or larger model size")
    
    print(f"\nDetailed plots saved to: {output_path / 'eval'}")
    print("  - confusion_matrix.png")
    print("  - P_curve.png, R_curve.png, PR_curve.png")
    print("  - F1_curve.png")


def compare_inference_speed(pt_path: str, onnx_path: str, device: str = "0"):
    """Compare inference speed between PyTorch and ONNX models."""
    import time
    import numpy as np
    
    print("\n" + "=" * 60)
    print("INFERENCE SPEED COMPARISON")
    print("=" * 60)
    
    # Create a dummy image
    dummy = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    n_warmup = 10
    n_runs = 50
    
    # PyTorch model
    print(f"\nPyTorch model ({pt_path}):")
    model_pt = YOLO(pt_path)
    for _ in range(n_warmup):
        model_pt.predict(dummy, verbose=False, device=device)
    
    start = time.perf_counter()
    for _ in range(n_runs):
        model_pt.predict(dummy, verbose=False, device=device)
    pt_time = (time.perf_counter() - start) / n_runs * 1000
    print(f"  Average: {pt_time:.1f} ms/frame ({1000/pt_time:.0f} FPS)")
    
    # ONNX model (if available)
    if onnx_path and Path(onnx_path).exists():
        print(f"\nONNX model ({onnx_path}):")
        model_onnx = YOLO(onnx_path)
        for _ in range(n_warmup):
            model_onnx.predict(dummy, verbose=False, device=device)
        
        start = time.perf_counter()
        for _ in range(n_runs):
            model_onnx.predict(dummy, verbose=False, device=device)
        onnx_time = (time.perf_counter() - start) / n_runs * 1000
        print(f"  Average: {onnx_time:.1f} ms/frame ({1000/onnx_time:.0f} FPS)")
        
        speedup = pt_time / onnx_time
        print(f"\nONNX speedup: {speedup:.2f}x")


def main():
    parser = argparse.ArgumentParser(description="Evaluate YOLO26 hand seal model")
    parser.add_argument("--model", type=str, default=None,
                        help="Path to trained model (.pt). If omitted, auto-detects latest best.pt")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to data.yaml. If omitted, uses latest_paths.json or common defaults")
    parser.add_argument("--device", type=str, default="0",
                        help="Device: '0' for GPU, 'cpu' for CPU")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory for evaluation results")
    parser.add_argument("--compare-onnx", type=str, default=None,
                        help="Path to ONNX model for speed comparison")
    parser.add_argument("--project-root", type=str, default=None,
                        help="Project root path (auto-detected by default)")
    args = parser.parse_args()

    project_root = _resolve_project_root(args.project_root)
    latest = _load_latest_paths(project_root)
    model_path = _resolve_model_path(args.model, project_root, latest)
    data_yaml = _resolve_data_yaml(args.data, project_root, latest)
    output_dir = Path(args.output).expanduser().resolve() if args.output else (project_root / "eval_results")

    print(f"Project root: {project_root}")
    print(f"Model path: {model_path}")
    print(f"Data yaml: {data_yaml}")
    print(f"Eval output dir: {output_dir}")
    
    evaluate(str(model_path), str(data_yaml), args.device, str(output_dir))
    
    if args.compare_onnx:
        compare_inference_speed(str(model_path), args.compare_onnx, args.device)


if __name__ == "__main__":
    main()
