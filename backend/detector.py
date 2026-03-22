"""
YOLO26 ONNX Runtime detector for Naruto hand signs.
Handles model loading, preprocessing, inference, and post-processing.
"""

import cv2
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    print("Please install onnxruntime-gpu: pip install onnxruntime-gpu")
    exit(1)


CLASSES = [
    "bird", "boar", "dog", "dragon", "hare", "horse",
    "monkey", "ox", "ram", "rat", "snake", "tiger"
]

CLASS_COLORS = {
    "bird":    (0, 200, 255),
    "boar":    (80, 127, 255),
    "dog":     (255, 165, 0),
    "dragon":  (0, 0, 255),
    "hare":    (200, 200, 200),
    "horse":   (0, 255, 128),
    "monkey":  (0, 215, 255),
    "ox":      (139, 69, 19),
    "ram":     (255, 0, 255),
    "rat":     (128, 128, 0),
    "snake":   (0, 128, 0),
    "tiger":   (0, 165, 255),
}


class HandSignDetector:
    """YOLO26 ONNX Runtime detector for Naruto hand signs."""

    def __init__(self, model_path: str = "models/best.onnx",
                 confidence_threshold: float = 0.5,
                 iou_threshold: float = 0.45):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.input_size = 640

        providers = []
        if "CUDAExecutionProvider" in ort.get_available_providers():
            providers.append("CUDAExecutionProvider")
            print("✅ Using CUDA GPU for inference")
        providers.append("CPUExecutionProvider")

        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_names = [o.name for o in self.session.get_outputs()]

        print(f"Model loaded: {model_path}")
        print(f"  Input: {self.input_name} {self.input_shape}")
        print(f"  Provider: {self.session.get_providers()[0]}")

    def preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, tuple]:
        orig_h, orig_w = frame.shape[:2]
        scale = min(self.input_size / orig_h, self.input_size / orig_w)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        padded = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        pad_x = (self.input_size - new_w) // 2
        pad_y = (self.input_size - new_h) // 2
        padded[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized

        blob = padded[:, :, ::-1].astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)
        blob = np.expand_dims(blob, axis=0)
        return blob, (orig_h, orig_w, scale, pad_x, pad_y)

    def postprocess(self, outputs: list, meta: tuple) -> list[dict]:
        orig_h, orig_w, scale, pad_x, pad_y = meta
        output = outputs[0]
        if output.ndim == 3:
            output = output[0]
        if output.shape[0] < output.shape[1]:
            output = output.T

        detections = []
        for det in output:
            if len(det) < 5:
                continue
            bbox, scores = det[:4], det[4:]
            class_id = np.argmax(scores)
            confidence = float(scores[class_id])
            if confidence < self.confidence_threshold:
                continue

            cx, cy, w, h = bbox
            x1 = max(0, min((cx - w/2 - pad_x) / scale, orig_w))
            y1 = max(0, min((cy - h/2 - pad_y) / scale, orig_h))
            x2 = max(0, min((cx + w/2 - pad_x) / scale, orig_w))
            y2 = max(0, min((cy + h/2 - pad_y) / scale, orig_h))

            class_name = CLASSES[class_id] if class_id < len(CLASSES) else f"class_{class_id}"
            detections.append({
                "class": class_name,
                "class_id": int(class_id),
                "confidence": confidence,
                "bbox": [float(x1), float(y1), float(x2), float(y2)]
            })

        return self._nms(detections) if len(detections) > 1 else detections

    def _nms(self, detections: list[dict]) -> list[dict]:
        if not detections:
            return []
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)
            detections = [d for d in detections
                          if self._compute_iou(best["bbox"], d["bbox"]) < self.iou_threshold]
        return keep

    @staticmethod
    def _compute_iou(box1: list, box2: list) -> float:
        x1, y1 = max(box1[0], box2[0]), max(box1[1], box2[1])
        x2, y2 = min(box1[2], box2[2]), min(box1[3], box2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        union = ((box1[2]-box1[0])*(box1[3]-box1[1]) +
                 (box2[2]-box2[0])*(box2[3]-box2[1]) - inter)
        return inter / union if union > 0 else 0

    def detect(self, frame: np.ndarray) -> list[dict]:
        blob, meta = self.preprocess(frame)
        outputs = self.session.run(self.output_names, {self.input_name: blob})
        return self.postprocess(outputs, meta)
