"""Benchmark ONNX model inference latency.

Examples:
  python models/benchmark_inference.py
  python models/benchmark_inference.py --runs 300 --warmup 30
  python models/benchmark_inference.py --provider cpu
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark ONNX inference latency")
    parser.add_argument("--model", type=str, default="models/best.onnx", help="Path to ONNX model")
    parser.add_argument("--runs", type=int, default=200, help="Timed runs")
    parser.add_argument("--warmup", type=int, default=20, help="Warmup runs")
    parser.add_argument("--batch", type=int, default=1, help="Batch size (used if input has dynamic batch)")
    parser.add_argument("--height", type=int, default=640, help="Input height (for dynamic shape)")
    parser.add_argument("--width", type=int, default=640, help="Input width (for dynamic shape)")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["auto", "cuda", "cpu"],
        default="auto",
        help="Execution provider",
    )
    parser.add_argument("--seed", type=int, default=123, help="Random seed")
    return parser.parse_args()


def choose_providers(provider: str) -> list[str]:
    available = ort.get_available_providers()
    if provider == "cuda":
        if "CUDAExecutionProvider" not in available:
            raise RuntimeError("CUDAExecutionProvider not available in this environment")
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if provider == "cpu":
        return ["CPUExecutionProvider"]
    if "CUDAExecutionProvider" in available:
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]


def resolve_input_shape(raw_shape: list[object], batch: int, height: int, width: int) -> list[int]:
    resolved: list[int] = []
    for i, dim in enumerate(raw_shape):
        if isinstance(dim, int) and dim > 0:
            resolved.append(dim)
            continue
        if i == 0:
            resolved.append(batch)
        elif i == 2:
            resolved.append(height)
        elif i == 3:
            resolved.append(width)
        else:
            resolved.append(3)
    return resolved


def dtype_from_onnx_type(onnx_type: str) -> np.dtype:
    mapping = {
        "tensor(float)": np.float32,
        "tensor(float16)": np.float16,
        "tensor(double)": np.float64,
        "tensor(int64)": np.int64,
        "tensor(int32)": np.int32,
    }
    if onnx_type not in mapping:
        raise RuntimeError(f"Unsupported input dtype: {onnx_type}")
    return mapping[onnx_type]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(round((p / 100.0) * (len(sorted_vals) - 1)))
    return sorted_vals[idx]


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    providers = choose_providers(args.provider)
    session = ort.InferenceSession(str(model_path), providers=providers)

    input_meta = session.get_inputs()[0]
    input_name = input_meta.name
    input_shape = resolve_input_shape(list(input_meta.shape), args.batch, args.height, args.width)
    input_dtype = dtype_from_onnx_type(input_meta.type)

    x = np.random.random(input_shape).astype(input_dtype)
    feed = {input_name: x}

    for _ in range(args.warmup):
        session.run(None, feed)

    times_ms: list[float] = []
    for _ in range(args.runs):
        t0 = time.perf_counter()
        session.run(None, feed)
        times_ms.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = statistics.fmean(times_ms)
    median_ms = statistics.median(times_ms)
    min_ms = min(times_ms)
    max_ms = max(times_ms)
    p95_ms = percentile(times_ms, 95)
    std_ms = statistics.pstdev(times_ms)
    fps = 1000.0 / mean_ms if mean_ms > 0 else 0.0

    active_provider = session.get_providers()[0]
    print("=== ONNX Inference Benchmark ===")
    print(f"Model      : {model_path}")
    print(f"Provider   : {active_provider}")
    print(f"Input name : {input_name}")
    print(f"Input type : {input_meta.type}")
    print(f"Input shape: {input_shape}")
    print(f"Warmup     : {args.warmup}")
    print(f"Runs       : {args.runs}")
    print(f"Mean (ms)  : {mean_ms:.3f}")
    print(f"Median (ms): {median_ms:.3f}")
    print(f"P95 (ms)   : {p95_ms:.3f}")
    print(f"Min (ms)   : {min_ms:.3f}")
    print(f"Max (ms)   : {max_ms:.3f}")
    print(f"Std (ms)   : {std_ms:.3f}")
    print(f"FPS        : {fps:.2f}")


if __name__ == "__main__":
    main()
