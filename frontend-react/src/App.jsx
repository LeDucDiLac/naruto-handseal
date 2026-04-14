import React, { useState, useEffect } from 'react';
import CameraFeed from './components/CameraFeed';
import { JUTSU_DATABASE } from './utils/jutsu_data';

function App() {
  const [selectedJutsu, setSelectedJutsu] = useState(JUTSU_DATABASE[1]); // Default Chidori
  const [sequenceProgress, setSequenceProgress] = useState(0); // number of signs completed
  const [activeEffect, setActiveEffect] = useState(null);

  // Fallback images array since API failed. 
  // User can drop real images here later: public/signs/rat.png
  const getSignImage = (sign) => `/signs/${sign}.png`;

  const onJutsuCast = (jutsuId) => {
    setActiveEffect(jutsuId);
    // Clear effect after 4 seconds
    setTimeout(() => {
      setActiveEffect(null);
      setSequenceProgress(0);
    }, 4000);
  };

  return (
    <div className="app-container">
      {/* Sidebar UI */}
      <aside className="sidebar">
        <div>
          <h1>🍥 Jutsu Handsign</h1>
          <p className="subtitle">Realtime YOLOv11 + React</p>
        </div>

        <div className="jutsu-selector">
          <p className="subtitle" style={{marginBottom: "4px"}}>Select Jutsu to Learn:</p>
          {JUTSU_DATABASE.map(jutsu => (
            <button 
              key={jutsu.id}
              className={`jutsu-btn ${selectedJutsu.id === jutsu.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedJutsu(jutsu);
                setSequenceProgress(0);
                setActiveEffect(null);
              }}
            >
              {jutsu.name}
            </button>
          ))}
        </div>

        {selectedJutsu && (
          <div>
            <p className="subtitle" style={{marginTop: "8px"}}>Required Signs:</p>
            <div className="signs-container">
              {selectedJutsu.signs.map((sign, index) => {
                const isActive = index === sequenceProgress;
                const isCompleted = index < sequenceProgress;
                return (
                  <div 
                    key={`${sign}-${index}`} 
                    className={`sign-box ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                  >
                    <img 
                      src={getSignImage(sign)} 
                      alt={sign} 
                      className="sign-img"
                      onError={(e) => {
                        // Fallback to empty div if image doesn't exist yet
                        e.target.style.display = 'none'; 
                      }}
                    />
                    <span className="sign-label">{sign}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </aside>

      {/* Main Camera View */}
      <main className="main-view">
        <CameraFeed 
          targetJutsu={selectedJutsu}
          onProgressUpdate={setSequenceProgress}
          onJutsuCast={onJutsuCast}
        />
        
        {/* Multi-Format Effects Compositor Placeholder */}
        {activeEffect && (
          <div className="effects-container">
            <div className="jutsu-cast-announcement">
              <h2>{JUTSU_DATABASE.find(j => j.id === activeEffect)?.name || activeEffect}</h2>
              <p>JUTSU ACTIVATED</p>
            </div>
            
            {/* 
              Here we will conditionally render:
              - tsparticles for basic elements
              - <video autoPlay transparent> for Water Dragons
              - CSS animations for Sharingan
            */}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
