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

# Colors for each class (BGR for OpenCV)
CLASS_COLORS = {
    "bird":    (0, 200, 255),    # Orange
    "boar":    (80, 127, 255),   # Coral
    "dog":     (255, 165, 0),    # Blue
    "dragon":  (0, 0, 255),      # Red
    "hare":    (200, 200, 200),  # Light gray
    "horse":   (0, 255, 128),    # Green
    "monkey":  (0, 215, 255),    # Gold
    "ox":      (139, 69, 19),    # Dark blue
    "ram":     (255, 0, 255),    # Magenta
    "rat":     (128, 128, 0),    # Teal
    "snake":   (0, 128, 0),      # Dark green
    "tiger":   (0, 165, 255),    # Orange
}


class HandSignDetector:
    """YOLO26 ONNX Runtime detector for Naruto hand signs."""
    
    def __init__(self, model_path: str = "models/best.onnx", 
                 confidence_threshold: float = 0.5,
                 iou_threshold: float = 0.45):
        """
        Initialize the detector.
        
        Args:
            model_path: Path to the ONNX model file
            confidence_threshold: Minimum confidence to accept a detection
            iou_threshold: IoU threshold for NMS (YOLO26 is NMS-free, but kept as fallback)
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.input_size = 640
        
        # Create ONNX Runtime session with GPU priority
        providers = []
        if "CUDAExecutionProvider" in ort.get_available_providers():
            providers.append("CUDAExecutionProvider")
            print("Using CUDA GPU for inference")
        providers.append("CPUExecutionProvider")
        
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # Get model input/output info
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_names = [o.name for o in self.session.get_outputs()]
        
        print(f"Model loaded: {model_path}")
        print(f"  Input: {self.input_name} {self.input_shape}")
        print(f"  Outputs: {self.output_names}")
        print(f"  Provider: {self.session.get_providers()[0]}")
    
    def preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, tuple]:
        """
        Preprocess frame for YOLO inference.
        
        Args:
            frame: BGR image from OpenCV (H, W, 3)
            
        Returns:
            preprocessed: (1, 3, 640, 640) float32 tensor
            original_shape: (orig_h, orig_w) for scaling boxes back
        """
        orig_h, orig_w = frame.shape[:2]
        
        # Resize with letterboxing
        scale = min(self.input_size / orig_h, self.input_size / orig_w)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Create padded image
        padded = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        pad_x = (self.input_size - new_w) // 2
        pad_y = (self.input_size - new_h) // 2
        padded[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized
        
        # Convert BGR to RGB, normalize, transpose to CHW
        blob = padded[:, :, ::-1].astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)  # HWC -> CHW
        blob = np.expand_dims(blob, axis=0)  # Add batch dim
        
        return blob, (orig_h, orig_w, scale, pad_x, pad_y)
    
    def postprocess(self, outputs: list, meta: tuple) -> list[dict]:
        """
        Post-process YOLO outputs to get detections.
        
        Args:
            outputs: Raw model outputs
            meta: (orig_h, orig_w, scale, pad_x, pad_y)
            
        Returns:
            List of detection dicts: {class, confidence, bbox: [x1,y1,x2,y2]}
        """
        orig_h, orig_w, scale, pad_x, pad_y = meta
        
        # YOLO output shape: (1, num_classes + 4, num_detections)
        # Transpose to (num_detections, num_classes + 4)
        output = outputs[0]
        if output.ndim == 3:
            output = output[0]  # Remove batch dim
        
        # Handle different output formats
        if output.shape[0] < output.shape[1]:
            output = output.T  # Transpose if needed
        
        detections = []
        
        for det in output:
            # First 4 values are bbox (cx, cy, w, h), rest are class scores
            if len(det) < 5:
                continue
                
            bbox = det[:4]
            scores = det[4:]
            
            # Get best class
            class_id = np.argmax(scores)
            confidence = float(scores[class_id])
            
            if confidence < self.confidence_threshold:
                continue
            
            # Convert from center format to corner format
            cx, cy, w, h = bbox
            x1 = cx - w / 2
            y1 = cy - h / 2
            x2 = cx + w / 2
            y2 = cy + h / 2
            
            # Remove padding and scale to original image
            x1 = (x1 - pad_x) / scale
            y1 = (y1 - pad_y) / scale
            x2 = (x2 - pad_x) / scale
            y2 = (y2 - pad_y) / scale
            
            # Clip to image bounds
            x1 = max(0, min(x1, orig_w))
            y1 = max(0, min(y1, orig_h))
            x2 = max(0, min(x2, orig_w))
            y2 = max(0, min(y2, orig_h))
            
            class_name = CLASSES[class_id] if class_id < len(CLASSES) else f"class_{class_id}"
            
            detections.append({
                "class": class_name,
                "class_id": int(class_id),
                "confidence": confidence,
                "bbox": [float(x1), float(y1), float(x2), float(y2)]
            })
        
        # Apply NMS if multiple detections
        if len(detections) > 1:
            detections = self._nms(detections)
        
        return detections
    
    def _nms(self, detections: list[dict]) -> list[dict]:
        """Simple NMS implementation (fallback for non-NMS-free models)."""
        if not detections:
            return []
        
        # Sort by confidence
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        
        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)
            
            remaining = []
            for det in detections:
                iou = self._compute_iou(best["bbox"], det["bbox"])
                if iou < self.iou_threshold:
                    remaining.append(det)
            detections = remaining
        
        return keep
    
    @staticmethod
    def _compute_iou(box1: list, box2: list) -> float:
        """Compute IoU between two bboxes [x1, y1, x2, y2]."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Run detection on a frame.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            List of detections: [{class, confidence, bbox}, ...]
        """
        blob, meta = self.preprocess(frame)
        outputs = self.session.run(self.output_names, {self.input_name: blob})
        detections = self.postprocess(outputs, meta)
        return detections
    
    def detect_and_annotate(self, frame: np.ndarray) -> tuple[np.ndarray, list[dict]]:
        """
        Run detection and draw results on the frame.
        
        Args:
            frame: BGR image (or RGB from Gradio)
            
        Returns:
            annotated_frame: Frame with drawn bounding boxes and labels
            detections: List of detection dicts
        """
        detections = self.detect(frame)
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
            cls = det["class"]
            conf = det["confidence"]
            color = CLASS_COLORS.get(cls, (0, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label = f"{cls.upper()} {conf:.0%}"
            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            cv2.rectangle(
                annotated,
                (x1, y1 - label_h - baseline - 8),
                (x1 + label_w + 8, y1),
                color, -1
            )
            
            # Draw label text
            cv2.putText(
                annotated, label,
                (x1 + 4, y1 - baseline - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2
            )
        
        return annotated, detections
