"""Live inference app for hand-sign detection.

Run with:
    streamlit run models/live_inference.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO


def _is_running_in_streamlit() -> bool:
    """Return True when this script is executed by `streamlit run`."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


@st.cache_resource
def _load_model(model_path: str) -> YOLO:
    return YOLO(model_path, task="detect")


def main() -> None:
    if not _is_running_in_streamlit():
        print("This file is a Streamlit app and must be run with:")
        print("  streamlit run models/live_inference.py")
        print("Tip: running `python models/live_inference.py` will not open the live UI.")
        sys.exit(1)

    st.set_page_config(page_title="Hand Sign Live Inference", layout="wide")
    st.title("Naruto Hand Sign Live Inference")
    st.caption("Browser webcam + ONNX detection")

    try:
        import av
        from streamlit_webrtc import WebRtcMode, webrtc_streamer
    except Exception:
        st.error("Missing package: streamlit-webrtc (and/or av).")
        st.code("pip install streamlit-webrtc av")
        st.stop()

    model_path = str(Path("models") / "best.onnx")
    model = _load_model(model_path)
    model.overrides["task"] = "detect"

    col1, col2 = st.columns([2, 1])
    with col2:
        conf = st.slider("Confidence", min_value=0.01, max_value=0.90, value=0.15, step=0.01)
        imgsz = st.selectbox("Image size", options=[256, 320, 416, 480, 640], index=1)
        frame_skip = st.selectbox("Process every Nth frame", options=[1, 2, 3, 4], index=1)
        infer_scale = st.selectbox("Inference scale", options=[1.0, 0.75, 0.5], index=1)
        st.info("Allow camera access in the browser prompt.")

    test_image = st.file_uploader("Quick test image (optional)", type=["jpg", "jpeg", "png"])
    if test_image is not None:
        file_bytes = test_image.read()
        if file_bytes:
            arr = np.frombuffer(file_bytes, dtype=np.uint8)
            bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if bgr is not None:
                test_result = model.predict(bgr, conf=conf, imgsz=imgsz, verbose=False)
                st.image(test_result[0].plot()[:, :, ::-1], caption="Test image detection", use_container_width=True)
                st.write(f"Detections: {len(test_result[0].boxes)}")
            else:
                st.warning("Could not decode test image.")

    runtime = {"frame_index": 0}

    def _video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        runtime["frame_index"] += 1
        image = frame.to_ndarray(format="bgr24")

        if runtime["frame_index"] % frame_skip != 0:
            return av.VideoFrame.from_ndarray(image, format="bgr24")

        if infer_scale < 1.0:
            resized = cv2.resize(image, dsize=None, fx=infer_scale, fy=infer_scale, interpolation=cv2.INTER_LINEAR)
            result = model.predict(resized, conf=conf, imgsz=imgsz, verbose=False)
            annotated_small = result[0].plot()
            annotated = cv2.resize(
                annotated_small,
                dsize=(image.shape[1], image.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
        else:
            result = model.predict(image, conf=conf, imgsz=imgsz, verbose=False)
            annotated = result[0].plot()

        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

    with col1:
        webrtc_streamer(
            key="handsign-live",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": True, "audio": False},
            video_frame_callback=_video_frame_callback,
            async_processing=True,
        )


if __name__ == "__main__":
    main()