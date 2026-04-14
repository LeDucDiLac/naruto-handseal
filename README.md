# 🍥 Naruto Jutsu Hand Sign Recognition

Real-time hand sign detection using **YOLO26 + ONNX Runtime**, with a **FastAPI** backend and **Gradio** frontend.

Perform Naruto hand signs → Detect the jutsu → Watch visual effects on screen!

## Architecture

```
┌────────────────┐     WebSocket      ┌──────────────────┐
│  Gradio UI     │ ◄──────────────► │  FastAPI Backend │
│  :7860         │   base64 frames   │  :8000           │
│                │   JSON results    │                  │
│  • Jutsu Lib   │                   │  • YOLO26 ONNX   │
│  • Learn Mode  │                   │  • /ws/detect     │
│  • Detect Mode │                   │  • /api/jutsu     │
│  • VFX Canvas  │                   │  • /api/health    │
└────────────────┘                   └──────────────────┘
```

## Quick Start

### Docker (Recommended)
```bash
# GPU inference
docker compose up --build

# Open http://localhost:7860
```

### Local Development
```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2 — Frontend
cd frontend
pip install -r requirements.txt
python main.py
```

## Training the Model

```bash
cd training
pip install -r requirements.txt

# 1. Download datasets (requires free Roboflow API key)
python download_dataset.py --api-key YOUR_KEY

# 2. Train YOLO26 + export to ONNX
python train.py --data datasets/naruto-hand-seals/merged/data.yaml

# 3. Evaluate
python evaluate.py --model runs/naruto-handsign/weights/best.pt \
                   --data datasets/naruto-hand-seals/merged/data.yaml

# Model is auto-exported to models/best.onnx
```

## Supported Jutsu

| Jutsu | Signs | Element |
|-------|-------|---------|
| 🔥 Great Fireball | Snake → Ram → Monkey → Boar → Horse → Tiger | Fire |
| ⚡ Chidori | Ox → Hare → Monkey | Lightning |
| 🟣 Shadow Clone | Ram | Special |
| 💧 Water Dragon | 42 signs | Water |
| 🌪️ Wind Scythe | Rat | Wind |

## Project Structure

```text
jutsu-handsign/
├── DEV_LOG.md
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── detector.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── custom.css
│   ├── jutsu_data.py
│   ├── main.py
│   ├── requirements.txt
│   ├── sequence_detector.py
│   └── effects/
│       ├── clone_effect.js
│       ├── fire_effect.js
│       ├── lightning_effect.js
│       ├── water_effect.js
│       └── wind_effect.js
├── models/
│   ├── benchmark_inference.py
│   ├── live_inference.py
│   ├── best.onnx
│   ├── yolo26s.onnx
│   └── yolo26s.pt
├── runs/
│   └── detect/
│       └── eval_results/
└── training/
    ├── analyze.py
    ├── best.onnx
    ├── best.pt
    ├── data.yaml
    ├── download_dataset.py
    ├── download_from_roboflow.py
    ├── evaluate.py
    ├── requirements.txt
    ├── train.py
    ├── eval_results/
    └── Naruto-hand-sign-1/
        ├── data.yaml
        ├── README.dataset.txt
        ├── README.roboflow.txt
        ├── test/
        ├── train/
        └── valid/
```

## Tech Stack

- **ML**: YOLO26 (Ultralytics) → ONNX Runtime (GPU)
- **Backend**: FastAPI + WebSocket
- **Frontend**: Gradio + Canvas JS effects
- **Deploy**: Docker + NVIDIA Container Toolkit
