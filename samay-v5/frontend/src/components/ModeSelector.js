import React from 'react';

const ModeSelector = ({ mode, onModeChange }) => {
  return (
    <div className="mode-selector">
      <div className="mode-selector-header">
        <h4>Privacy Mode</h4>
        <div className="mode-indicator">
          {mode === 'confidential' ? '🔒 Private' : '🌐 Connected'}
        </div>
      </div>
      
      <div className="mode-buttons">
        <button 
          className={`mode-btn ${mode === 'normal' ? 'active' : ''}`}
          onClick={() => onModeChange('normal')}
          title="Connect to external AI services for comprehensive responses"
        >
          <div className="mode-icon">🌐</div>
          <div className="mode-info">
            <div className="mode-title">Normal Mode</div>
            <div className="mode-description">Route to AI services</div>
          </div>
        </button>
        
        <button 
          className={`mode-btn ${mode === 'confidential' ? 'active' : ''}`}
          onClick={() => onModeChange('confidential')}
          title="Local processing only - no external connections"
        >
          <div className="mode-icon">🔒</div>
          <div className="mode-info">
            <div className="mode-title">Confidential Mode</div>
            <div className="mode-description">Local processing only</div>
          </div>
        </button>
      </div>
      
      <div className="mode-details">
        {mode === 'normal' ? (
          <div className="mode-explanation normal">
            <h5>🌐 Normal Mode Features:</h5>
            <ul>
              <li>✅ Route queries to multiple AI services</li>
              <li>✅ Get comprehensive responses from Claude, Gemini, Perplexity</li>
              <li>✅ Conversation logging and analytics</li>
              <li>✅ WebSocket real-time updates</li>
              <li>✅ Response synthesis from all services</li>
            </ul>
          </div>
        ) : (
          <div className="mode-explanation confidential">
            <h5>🔒 Confidential Mode Features:</h5>
            <ul>
              <li>✅ Local AI processing only (Phi-3-Mini)</li>
              <li>✅ No external service connections</li>
              <li>✅ No conversation logging</li>
              <li>✅ No analytics tracking</li>
              <li>✅ Complete privacy protection</li>
            </ul>
            <div className="privacy-notice">
              <strong>⚠️ Privacy Notice:</strong> In confidential mode, your conversations 
              are processed locally and not shared with any external services.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModeSelector;