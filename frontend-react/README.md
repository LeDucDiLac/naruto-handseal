# Naruto Jutsu React Frontend

A high-performance modern web interface built explicitly to solve latency and rendering limitations. It acts as the interactive visual layer for the FastAPI bounding-box server.

## 🚀 Getting Started
```bash
cd frontend-react
npm install
npm run dev
```
Access the application on `http://localhost:5173`. Make sure your FastAPI backend on `port 8000` is currently running or the UI will report AI Connection Errors.

## 📁 Project Structure
*   **`src/App.jsx`**: Global layout, sidebar handsign sequence progression logic, and trigger points for the Multi-Format VFX rendering.
*   **`src/components/CameraFeed.jsx`**: Highly optimized camera capture. Uses an invisible HTML5 canvas to serialize webcam streams into base64 JPEGs rapidly to push out via `WebSockets`. Renders YOLO responses onto a separate, transparent absolute-positioned `<canvas>`.
*   **`src/utils/jutsu_data.js`**: Client-side mirror of the Jutsu combos and metadata, completely bypassing API lag for checking combination statuses locally.

## 🔥 Adding Custom VFX
Because standard Web particles (`tsparticles`) aren't sufficient for detailed effects like the Sharingan or Water Dragons, `App.jsx` uses a compositing wrapper logic.

To add new custom effects, open `App.jsx`, locate the `<div className="effects-container">` block, and inject your downloaded media based on the `activeEffect` flag!
Example:
```jsx
{activeEffect === 'water_dragon' && (
   <video src="/effects/water_dragon.webm" autoPlay transparent className="..." />
)}
```

## 🖐️ Adding Handsign Images
The application is pre-configured to automatically cycle through reference images found in `/public/signs/` depending on the current required combination.
1. Download reference images from the internet (e.g. `rat`, `ox`, `tiger`).
2. Save them strictly as `[hand_sign].png` inside the `frontend-react/public/signs/` folder.
3. The UI handles the rest automatically.
