"""
FastAPI backend for Naruto Hand Sign Detection.
Serves YOLO26 ONNX model via WebSocket for real-time inference
and REST endpoints for jutsu data.
"""

import os
import sys
import json
import base64
import time
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from detector import HandSignDetector


# ─── Lifespan: load model on startup ───────────────────────────────
detector: HandSignDetector | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global detector
    model_path = os.environ.get("MODEL_PATH", "models/best.onnx")
    
    # Check if model exists, provide helpful error if not
    if not Path(model_path).exists():
        print(f"⚠️  Model not found at: {model_path}")
        print("   Run training first: cd training && python train.py --data data.yaml")
        print("   Or set MODEL_PATH environment variable to your .onnx model path")
        print("   Starting in demo mode (no detection)...")
        detector = None
    else:
        detector = HandSignDetector(
            model_path=model_path,
            confidence_threshold=float(os.environ.get("CONFIDENCE_THRESHOLD", "0.5")),
        )
    
    yield  # App runs here
    
    # Cleanup
    detector = None


# ─── App setup ─────────────────────────────────────────────────────
app = FastAPI(
    title="Naruto Jutsu Hand Sign API",
    description="Real-time hand sign detection via YOLO26 + ONNX Runtime",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Jutsu data ───────────────────────────────────────────────────
HAND_SIGNS = [
    "bird", "boar", "dog", "dragon", "hare", "horse",
    "monkey", "ox", "ram", "rat", "snake", "tiger"
]

SIGN_SYMBOLS = {
    "rat": "🐀", "ox": "🐂", "tiger": "🐅", "hare": "🐇",
    "dragon": "🐉", "snake": "🐍", "horse": "🐴", "ram": "🐏",
    "monkey": "🐒", "bird": "🐦", "dog": "🐕", "boar": "🐗",
}

JUTSU_DATABASE = [
    {
        "id": "fireball",
        "name": "Fire Release: Great Fireball Jutsu",
        "japanese_name": "火遁・豪火球の術 (Katon: Gōkakyū no Jutsu)",
        "element": "fire",
        "signs": ["snake", "ram", "monkey", "boar", "horse", "tiger"],
        "description": (
            "A signature technique of the Uchiha clan. The user kneads chakra "
            "in their body and converts it into fire, expelling it from the mouth "
            "as a massive orb of roaring flame."
        ),
        "character": "Sasuke Uchiha",
        "difficulty": "intermediate",
        "effect_type": "fireball",
    },
    {
        "id": "chidori",
        "name": "Chidori (One Thousand Birds)",
        "japanese_name": "千鳥 (Chidori)",
        "element": "lightning",
        "signs": ["ox", "hare", "monkey"],
        "description": (
            "A high concentration of lightning chakra channeled into the user's hand. "
            "The amount of chakra is so great that it becomes visible, emitting a sound "
            "like a thousand birds chirping."
        ),
        "character": "Kakashi Hatake / Sasuke Uchiha",
        "difficulty": "advanced",
        "effect_type": "lightning",
    },
    {
        "id": "shadow_clone",
        "name": "Shadow Clone Jutsu",
        "japanese_name": "影分身の術 (Kage Bunshin no Jutsu)",
        "element": "special",
        "signs": ["ram"],
        "description": (
            "Creates solid clones of the user. Unlike regular clones, shadow clones "
            "are actual copies with their own chakra. Naruto's signature technique."
        ),
        "character": "Naruto Uzumaki",
        "difficulty": "beginner",
        "effect_type": "clone",
    },
    {
        "id": "water_dragon",
        "name": "Water Release: Water Dragon Jutsu",
        "japanese_name": "水遁・水龍弾の術 (Suiton: Suiryūdan no Jutsu)",
        "element": "water",
        "signs": [
            "ox", "monkey", "hare", "rat", "boar", "bird", "ox", "horse",
            "bird", "rat", "tiger", "dog", "tiger", "snake", "ox", "ram",
            "snake", "boar", "ram", "rat", "monkey", "bird", "dragon",
            "bird", "ox", "horse", "ram", "tiger", "snake", "rat",
            "monkey", "hare", "boar", "dragon", "ram", "rat", "ox",
            "monkey", "bird", "rat", "boar", "bird",
        ],
        "description": (
            "A powerful water technique requiring 42 hand seals. "
            "Creates a giant water dragon that crashes into the opponent."
        ),
        "character": "Zabuza Momochi / Kakashi Hatake",
        "difficulty": "legendary",
        "effect_type": "water",
    },
    {
        "id": "wind_scythe",
        "name": "Wind Release: Wind Scythe Jutsu",
        "japanese_name": "風遁・鎌鼬の術 (Fūton: Kamaitachi no Jutsu)",
        "element": "wind",
        "signs": ["rat"],
        "description": (
            "The user creates powerful gusts of cutting wind that can slice "
            "through obstacles and opponents."
        ),
        "character": "Temari",
        "difficulty": "beginner",
        "effect_type": "wind",
    },
]


# ─── REST Endpoints ───────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": detector is not None,
        "provider": detector.session.get_providers()[0] if detector else None,
    }


@app.get("/api/jutsu")
async def get_jutsu_list():
    """Get all jutsu with their hand sign sequences."""
    return JSONResponse(content=JUTSU_DATABASE)


@app.get("/api/jutsu/{jutsu_id}")
async def get_jutsu(jutsu_id: str):
    """Get a specific jutsu by ID."""
    jutsu = next((j for j in JUTSU_DATABASE if j["id"] == jutsu_id), None)
    if not jutsu:
        return JSONResponse(content={"error": "Jutsu not found"}, status_code=404)
    return JSONResponse(content=jutsu)


@app.get("/api/signs")
async def get_hand_signs():
    """Get list of all hand signs with symbols."""
    return JSONResponse(content={
        "signs": HAND_SIGNS,
        "symbols": SIGN_SYMBOLS,
    })


# ─── WebSocket Endpoint ──────────────────────────────────────────

@app.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket):
    """
    Real-time hand sign detection via WebSocket.
    
    Client sends: base64-encoded JPEG frames
    Server responds: JSON with detection results
    
    Message format (client → server):
        { "frame": "<base64 JPEG data>" }
    
    Message format (server → client):
        {
            "detections": [
                { "class": "tiger", "confidence": 0.92, "bbox": [x1,y1,x2,y2] }
            ],
            "inference_ms": 3.2,
            "timestamp": 1234567890.123
        }
    """
    await websocket.accept()
    print("WebSocket client connected")
    
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if "frame" not in msg:
                await websocket.send_json({"error": "Missing 'frame' field"})
                continue
            
            # Decode base64 frame
            try:
                frame_bytes = base64.b64decode(msg["frame"])
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    await websocket.send_json({"error": "Failed to decode frame"})
                    continue
            except Exception as e:
                await websocket.send_json({"error": f"Frame decode error: {str(e)}"})
                continue
            
            # Run detection
            if detector is None:
                await websocket.send_json({
                    "detections": [],
                    "inference_ms": 0,
                    "timestamp": time.time(),
                    "warning": "Model not loaded",
                })
                continue
            
            start = time.perf_counter()
            detections = detector.detect(frame)
            inference_ms = (time.perf_counter() - start) * 1000
            
            # Send results
            await websocket.send_json({
                "detections": detections,
                "inference_ms": round(inference_ms, 1),
                "timestamp": time.time(),
            })
    
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
