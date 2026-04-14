import React, { useRef, useEffect, useState } from 'react';

const CameraFeed = ({ targetJutsu, onProgressUpdate, onJutsuCast }) => {
  const videoRef = useRef(null);
  const canvasOverlayRef = useRef(null);
  const hiddenCanvasRef = useRef(null);
  const wsRef = useRef(null);

  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  
  // Sequence Detection State
  const stateRef = useRef({
    currentSign: '',
    currentSignStartTime: 0,
    confirmedCount: 0,
    holdDurationMs: 800, // require holding a sign for 0.8s
  });

  useEffect(() => {
    // 1. Setup Camera Access
    async function setupCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' } 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Camera access denied or error:", err);
        setConnectionStatus("Camera Error");
      }
    }
    setupCamera();

    let reconnectInterval;

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/detect`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('Connected to AI');
        if (reconnectInterval) clearInterval(reconnectInterval);
      };

      ws.onclose = () => {
        setConnectionStatus('AI Disconnected (Retrying...)');
        // Try to reconnect every 3 seconds
        if (!reconnectInterval) {
          reconnectInterval = setInterval(connect, 3000);
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.detections) {
            handleDetections(data.detections);
          }
        } catch (err) {
          console.error("Error parsing WS message");
        }
      };
    }

    connect();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectInterval) clearInterval(reconnectInterval);
      if (videoRef.current && videoRef.current.srcObject) {
         videoRef.current.srcObject.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  // 3. Capture Frames and Send to WS continuously
  useEffect(() => {
    const FPS = 10; 
    let intervalId;

    const captureAndSend = () => {
      const video = videoRef.current;
      const hiddenCanvas = hiddenCanvasRef.current;
      const ws = wsRef.current;

      if (video && video.readyState >= 2 && hiddenCanvas && ws && ws.readyState === WebSocket.OPEN) {
        // Match canvas size to video internal size
        if (hiddenCanvas.width !== video.videoWidth) {
          hiddenCanvas.width = video.videoWidth;
          hiddenCanvas.height = video.videoHeight;
        }
        
        const ctx = hiddenCanvas.getContext('2d');
        // Un-mirror the video frame for YOLO to detect correctly, 
        // since our css mirrors the UI
        ctx.scale(-1, 1);
        ctx.translate(-hiddenCanvas.width, 0);
        ctx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
        
        // Reset transform
        ctx.translate(hiddenCanvas.width, 0);
        ctx.scale(-1, 1);

        // Convert to Base64 JPEG
        const dataUrl = hiddenCanvas.toDataURL('image/jpeg', 0.8);
        const b64 = dataUrl.split(',')[1];
        ws.send(JSON.stringify({ frame: b64 }));
      }
    };

    intervalId = setInterval(captureAndSend, 1000 / FPS);
    return () => clearInterval(intervalId);
  }, []);

  // 4. Handle Detections & Draw Bounding Boxes
  const handleDetections = (detections) => {
    const video = videoRef.current;
    const canvas = canvasOverlayRef.current;
    if (!video || !canvas) return;

    // Set canvas internal resolution to match video's display rect
    // This ensures bounding boxes align even if container resizes
    const rect = video.getBoundingClientRect();
    if (canvas.width !== video.videoWidth) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let bestDetection = null;

    detections.forEach(det => {
      const [x1, y1, x2, y2] = det.bbox;
      const conf = det.confidence;
      const label = det.class;

      if (!bestDetection || conf > bestDetection.confidence) {
        bestDetection = det;
      }

      // Draw Box (Orange Theme)
      ctx.strokeStyle = '#f97316';
      ctx.lineWidth = 4;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      // Draw Label
      ctx.fillStyle = '#f97316';
      ctx.font = '20px Arial';
      ctx.fillText(`${label.toUpperCase()} ${(conf * 100).toFixed(0)}%`, x1, y1 - 10);
    });

    processSequence(bestDetection ? bestDetection.class : '');
  };

  // 5. Sequence Logic Matching
  const processSequence = (detectedSign) => {
    if (!targetJutsu) return;
    
    const state = stateRef.current;
    const now = Date.now();
    const requiredSign = targetJutsu.signs[state.confirmedCount];

    if (!requiredSign) return; // already finished this jutsu

    if (detectedSign === requiredSign) {
      if (state.currentSign !== detectedSign) {
        // Just started holding the correct sign
        state.currentSign = detectedSign;
        state.currentSignStartTime = now;
      } else {
        // Continuing to hold the correct sign
        const holdTime = now - state.currentSignStartTime;
        if (holdTime > state.holdDurationMs) {
          // Confirmed! Match!
          state.confirmedCount += 1;
          onProgressUpdate(state.confirmedCount);
          
          state.currentSign = ''; // reset for next sign
          
          // Check if Jutsu is fully complete
          if (state.confirmedCount >= targetJutsu.signs.length) {
            onJutsuCast(targetJutsu.id);
            state.confirmedCount = 0; // reset sequence internally
          }
        }
      }
    } else if (detectedSign !== '') {
      // Detected wrong sign. In a real app we might reset, but let's be forgiving
      // state.currentSign = '';
    }
  };

  // Whenever Jutsu Target Changes from UI, reset tracking
  useEffect(() => {
    stateRef.current.confirmedCount = 0;
    stateRef.current.currentSign = '';
  }, [targetJutsu]);

  return (
    <div className="camera-container">
      {/* Invisible canvas for capturing frames without mirroring issues */}
      <canvas ref={hiddenCanvasRef} style={{ display: 'none' }} />
      
      <video 
        ref={videoRef} 
        autoPlay 
        playsInline 
        muted 
      />
      <canvas 
        ref={canvasOverlayRef} 
        className="overlay-canvas"
      />
      
      <div style={{ position: 'absolute', top: 20, right: 20, background: 'rgba(0,0,0,0.5)', padding: '5px 10px', borderRadius: '5px', color:'white', fontSize:'12px'}}>
        {connectionStatus}
      </div>
    </div>
  );
};

export default CameraFeed;
