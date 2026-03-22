"""
Gradio frontend for Naruto Jutsu Hand Sign Recognition.
Connects to FastAPI backend via WebSocket for real-time detection.
"""

import os
import json
import base64
import asyncio
import time
from pathlib import Path

import cv2
import numpy as np
import gradio as gr
import requests
import websockets

from jutsu_data import (
    JUTSU_DATABASE, HAND_SIGNS, SIGN_SYMBOLS, ELEMENT_EMOJI,
    format_signs_display, get_difficulty_display, get_jutsu_by_id,
)
from sequence_detector import SequenceDetector


# ─── Configuration ────────────────────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL", "ws://localhost:8000")
BACKEND_REST = BACKEND_URL.replace("ws://", "http://").replace("wss://", "https://")
WS_URL = f"{BACKEND_URL}/ws/detect"

CSS_PATH = Path(__file__).parent / "custom.css"
EFFECTS_DIR = Path(__file__).parent / "effects"


# ─── Load assets ──────────────────────────────────────────────────
def load_css():
    if CSS_PATH.exists():
        return CSS_PATH.read_text()
    return ""


def load_effect_js(effect_type: str) -> str:
    """Load a JS effect file and return the full HTML+JS to inject."""
    effect_map = {
        "fireball": "fire_effect.js",
        "lightning": "lightning_effect.js",
        "clone": "clone_effect.js",
        "water": "water_effect.js",
        "wind": "wind_effect.js",
    }
    filename = effect_map.get(effect_type, "")
    filepath = EFFECTS_DIR / filename
    if filepath.exists():
        js_code = filepath.read_text()
        return f"""
        <canvas id="effects-canvas" width="800" height="600"
                style="position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:9999;">
        </canvas>
        <script>
        (function() {{
            {js_code}
            const canvas = document.getElementById('effects-canvas');
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            create{effect_type.capitalize()}Effect(canvas);
            setTimeout(() => {{ if(canvas) canvas.remove(); }}, 5000);
        }})();
        </script>
        """
    return ""


# ─── Sequence detector (client-side state) ────────────────────────
seq_detector = SequenceDetector(hold_duration=0.5, sequence_timeout=5.0)


# ─── WebSocket detection function ─────────────────────────────────
async def detect_frame_ws(frame_data: bytes) -> dict:
    """Send a frame to the backend via WebSocket and get detection results."""
    try:
        async with websockets.connect(WS_URL) as ws:
            b64 = base64.b64encode(frame_data).decode("utf-8")
            await ws.send(json.dumps({"frame": b64}))
            response = await ws.recv()
            return json.loads(response)
    except Exception as e:
        return {"detections": [], "error": str(e)}


def detect_sync(frame_data: bytes) -> dict:
    """Synchronous wrapper for WebSocket detection."""
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(detect_frame_ws(frame_data))
        loop.close()
        return result
    except Exception as e:
        return {"detections": [], "error": str(e)}


# ─── Detection + annotation pipeline ─────────────────────────────
def process_frame(frame):
    """Process a webcam frame: send to backend, annotate, update sequence."""
    if frame is None:
        return None, "Waiting for webcam...", "", ""

    # Encode frame as JPEG
    _, buffer = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), 
                              [cv2.IMWRITE_JPEG_QUALITY, 80])
    
    # Send to backend
    result = detect_sync(buffer.tobytes())
    detections = result.get("detections", [])
    inference_ms = result.get("inference_ms", 0)
    error = result.get("error", "")
    
    # Annotate frame
    annotated = frame.copy()
    detected_sign = ""
    detected_conf = 0.0
    
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        cls = det["class"]
        conf = det["confidence"]
        
        if conf > detected_conf:
            detected_sign = cls
            detected_conf = conf
        
        # Draw bbox (RGB colors for Gradio)
        color = (249, 115, 22)  # Naruto orange
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
        
        label = f"{cls.upper()} {conf:.0%}"
        (lw, lh), bl = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(annotated, (x1, y1 - lh - bl - 10), (x1 + lw + 10, y1), color, -1)
        cv2.putText(annotated, label, (x1 + 5, y1 - bl - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Update sequence detector
    seq_result = seq_detector.update(detected_sign, detected_conf)
    progress_text = seq_detector.get_progress_text(seq_result)
    
    # Build status text
    if error:
        status = f"⚠️ Backend: {error}"
    elif detected_sign:
        status = f"🔍 Detected: **{detected_sign.upper()}** ({detected_conf:.0%}) | {inference_ms:.0f}ms"
    else:
        status = f"👁️ Scanning... | {inference_ms:.0f}ms"
    
    # Check for jutsu activation
    effect_html = ""
    if seq_result["matched_jutsu"]:
        jutsu = get_jutsu_by_id(seq_result["matched_jutsu"])
        if jutsu:
            effect_html = load_effect_js(jutsu["effect_type"])
            seq_detector.reset()
    
    return annotated, status, progress_text, effect_html


# ─── Learn mode processing ───────────────────────────────────────
learn_detector = SequenceDetector(hold_duration=1.0, sequence_timeout=10.0)
current_learn_step = {"jutsu_id": "", "step": 0}


def process_learn_frame(frame, jutsu_id):
    """Process frame for Learn mode — checks if user performs the correct sign."""
    if frame is None or not jutsu_id:
        return frame, "Select a jutsu to start learning", ""
    
    jutsu = get_jutsu_by_id(jutsu_id)
    if not jutsu:
        return frame, "Invalid jutsu", ""
    
    # Reset if jutsu changed
    if current_learn_step["jutsu_id"] != jutsu_id:
        current_learn_step["jutsu_id"] = jutsu_id
        current_learn_step["step"] = 0
        learn_detector.reset()
    
    step = current_learn_step["step"]
    signs = jutsu["signs"]
    
    if step >= len(signs):
        return frame, f"🎉 You've mastered **{jutsu['name']}**! All signs complete!", ""
    
    target_sign = signs[step]
    
    # Detect current frame
    _, buffer = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
                              [cv2.IMWRITE_JPEG_QUALITY, 80])
    result = detect_sync(buffer.tobytes())
    detections = result.get("detections", [])
    
    best_det = max(detections, key=lambda d: d["confidence"]) if detections else None
    detected_sign = best_det["class"] if best_det else ""
    detected_conf = best_det["confidence"] if best_det else 0
    
    # Annotate
    annotated = frame.copy()
    if best_det:
        x1, y1, x2, y2 = [int(v) for v in best_det["bbox"]]
        is_correct = detected_sign == target_sign
        color = (34, 197, 94) if is_correct else (239, 68, 68)  # Green or red
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
        label = f"{'✓' if is_correct else '✗'} {detected_sign.upper()}"
        cv2.putText(annotated, label, (x1 + 5, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    # Update learn detector
    seq_result = learn_detector.update(
        detected_sign if detected_sign == target_sign else "", 
        detected_conf
    )
    
    if seq_result["sign_just_confirmed"] and detected_sign == target_sign:
        current_learn_step["step"] += 1
        learn_detector.reset()
        step += 1
    
    # Build progress display
    progress_parts = []
    for i, s in enumerate(signs):
        emoji = SIGN_SYMBOLS.get(s, "❓")
        if i < step:
            progress_parts.append(f"✅ {emoji} {s.capitalize()}")
        elif i == step:
            hold = seq_result.get("hold_progress", 0)
            bar = "▓" * int(hold * 5) + "░" * (5 - int(hold * 5))
            progress_parts.append(f"👉 {emoji} **{s.upper()}** [{bar}]")
        else:
            progress_parts.append(f"⬜ {emoji} {s.capitalize()}")
    
    progress = " → ".join(progress_parts)
    target_text = f"Step {step + 1}/{len(signs)}: Show **{target_sign.upper()}** {SIGN_SYMBOLS.get(target_sign, '')}"
    
    return annotated, target_text, progress


# ─── Build Gradio UI ──────────────────────────────────────────────
def create_app():
    custom_css = load_css()
    
    with gr.Blocks(
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.orange,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
        ),
        css=custom_css,
        title="Naruto Jutsu Hand Sign Recognition",
    ) as demo:
        
        # ── Header ──
        gr.HTML("""
        <div style="text-align: center; padding: 20px 0 10px 0;">
            <h1 class="app-title">🍥 Naruto Jutsu Recognition</h1>
            <p class="app-subtitle">Perform hand signs → Detect jutsu → Cast visual effects</p>
        </div>
        """)
        
        with gr.Tabs():
            # ══════════════════════════════════════════════════════
            # TAB 1: JUTSU LIBRARY
            # ══════════════════════════════════════════════════════
            with gr.Tab("📚 Jutsu Library"):
                gr.Markdown("### Browse all available jutsu and their hand sign sequences")
                
                for jutsu in JUTSU_DATABASE:
                    element = jutsu["element"]
                    emoji = ELEMENT_EMOJI.get(element, "")
                    sign_display = format_signs_display(jutsu["signs"])
                    difficulty = get_difficulty_display(jutsu["difficulty"])
                    sign_count = len(jutsu["signs"])
                    
                    with gr.Accordion(
                        f"{emoji} {jutsu['name']}  •  {difficulty}  •  {sign_count} signs",
                        open=False
                    ):
                        gr.Markdown(f"""
**{jutsu['japanese_name']}**

{jutsu['description']}

**Character:** {jutsu['character']}  
**Element:** {emoji} {element.capitalize()}  
**Difficulty:** {difficulty}

**Hand Signs ({sign_count}):**  
{sign_display}
""")
            
            # ══════════════════════════════════════════════════════
            # TAB 2: LEARN MODE
            # ══════════════════════════════════════════════════════
            with gr.Tab("🎓 Learn"):
                gr.Markdown("### Learn jutsu hand signs step by step")
                gr.Markdown("Select a jutsu, then perform each hand sign. Hold each sign for **1 second** to confirm.")
                
                with gr.Row():
                    jutsu_choices = [(f"{ELEMENT_EMOJI.get(j['element'],'')} {j['name']} ({len(j['signs'])} signs)", j["id"]) 
                                     for j in JUTSU_DATABASE]
                    learn_jutsu_select = gr.Dropdown(
                        choices=jutsu_choices,
                        label="Select Jutsu to Learn",
                        value=None,
                    )
                
                with gr.Row():
                    with gr.Column(scale=2):
                        learn_webcam = gr.Image(
                            sources=["webcam"],
                            streaming=True,
                            label="Your Camera",
                        )
                    with gr.Column(scale=1):
                        learn_target = gr.Markdown("Select a jutsu to begin")
                        learn_progress = gr.Markdown("")
                
                learn_webcam.stream(
                    fn=process_learn_frame,
                    inputs=[learn_webcam, learn_jutsu_select],
                    outputs=[learn_webcam, learn_target, learn_progress],
                    stream_every=0.1,
                )
            
            # ══════════════════════════════════════════════════════
            # TAB 3: DETECT MODE
            # ══════════════════════════════════════════════════════
            with gr.Tab("⚡ Detect"):
                gr.Markdown("### Free-form detection — perform any jutsu from memory!")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        detect_webcam = gr.Image(
                            sources=["webcam"],
                            streaming=True,
                            label="Live Detection",
                        )
                    with gr.Column(scale=1):
                        detect_status = gr.Markdown("👁️ Scanning...")
                        detect_progress = gr.Markdown("")
                        gr.Markdown("---")
                        reset_btn = gr.Button("🔄 Reset Sequence", variant="secondary")
                
                # Effects canvas (injected via HTML)
                effects_html = gr.HTML("")
                
                detect_webcam.stream(
                    fn=process_frame,
                    inputs=[detect_webcam],
                    outputs=[detect_webcam, detect_status, detect_progress, effects_html],
                    stream_every=0.066,  # ~15fps to backend (balances smoothness + load)
                )
                
                def reset_sequence():
                    seq_detector.reset()
                    return "👁️ Scanning...", "Sequence reset", ""
                
                reset_btn.click(
                    fn=reset_sequence,
                    outputs=[detect_status, detect_progress, effects_html],
                )
        
        # ── Footer ──
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #64748B; font-size: 12px;">
            Built with YOLO26 + ONNX Runtime + FastAPI + Gradio | 
            <a href="http://localhost:8000/docs" target="_blank" style="color: #F97316;">API Docs</a>
        </div>
        """)
    
    return demo


# ─── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
