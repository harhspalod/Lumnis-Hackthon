import React from 'react';

export default function Header({ apiStatus }) {
  return (
    <header className="header" id="app-header">
      <div className="header-left">
        <div className="header-logo">⚡</div>
        <div className="header-title">
          <h1>AutoPM</h1>
          <span>Autonomous Code Review & Product Intelligence</span>
        </div>
      </div>

      <div className="header-controls">
        <div className="api-status" id="api-status">
          <div className={`status-dot ${apiStatus?.gemini_configured ? '' : 'warning'}`} />
          {apiStatus?.gemini_configured ? 'AI Connected' : 'Demo Mode (Mock AI)'}
        </div>
      </div>
    </header>
  );
}
