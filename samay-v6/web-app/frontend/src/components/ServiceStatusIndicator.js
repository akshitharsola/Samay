import React, { useState } from 'react';

const ServiceStatusIndicator = ({ 
  backendHealth = 'checking', 
  extensionConnected = false, 
  wsStatus = 'disconnected',
  onExtensionCheck 
}) => {
  const [showGuide, setShowGuide] = useState(false);

  const getStatusInfo = (status) => {
    switch (status) {
      case 'healthy':
        return { className: 'status-healthy', icon: 'fas fa-check-circle', text: 'Healthy' };
      case 'degraded':
        return { className: 'status-degraded', icon: 'fas fa-exclamation-triangle', text: 'Degraded' };
      case 'checking':
        return { className: 'status-degraded', icon: 'fas fa-spinner fa-spin', text: 'Checking...' };
      case 'error':
      default:
        return { className: 'status-offline', icon: 'fas fa-times-circle', text: 'Offline' };
    }
  };

  const backendStatus = getStatusInfo(backendHealth);
  const extensionStatus = getStatusInfo(extensionConnected ? 'healthy' : 'error');
  const wsStatusInfo = getStatusInfo(wsStatus === 'connected' ? 'healthy' : 'error');

  return (
    <div className="service-status-indicator">
      
      {/* Backend Status */}
      <div className={`status-item ${backendStatus.className}`}>
        <div className="status-icon-container">
          <i className={backendStatus.icon}></i>
        </div>
        <div className="status-text">
          <div className="status-label">Backend</div>
          <div className="status-value">{backendStatus.text}</div>
        </div>
      </div>

      {/* Extension Status */}
      <div className={`status-item ${extensionStatus.className}`}>
        <div className="status-icon-container">
          <i className={extensionStatus.icon}></i>
        </div>
        <div className="status-text">
          <div className="status-label">Extension</div>
          <div className="status-value">{extensionStatus.text}</div>
        </div>
        {!extensionConnected && (
          <button 
            className="status-action-btn"
            onClick={onExtensionCheck}
            title="Check Extension Connection"
          >
            <i className="fas fa-refresh"></i>
          </button>
        )}
      </div>

      {/* WebSocket Status */}
      <div className={`status-item ${wsStatusInfo.className}`}>
        <div className="status-icon-container">
          <i className={wsStatusInfo.icon}></i>
        </div>
        <div className="status-text">
          <div className="status-label">WebSocket</div>
          <div className="status-value">{wsStatusInfo.text}</div>
        </div>
      </div>

      {/* Extension Installation Guide */}
      {!extensionConnected && (
        <div className="extension-guide">
          <button className="guide-btn" onClick={() => setShowGuide(!showGuide)}>
            <i className="fas fa-question-circle"></i>
            Extension Help
          </button>
        </div>
      )}

      <ExtensionGuide show={showGuide} onClose={() => setShowGuide(false)} />

      <style jsx="true">{`
        .service-status-indicator {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }

        .status-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          transition: all 0.3s ease;
        }

        .status-item:hover {
          transform: translateY(-1px);
        }

        .status-healthy {
          background: #d1edff;
          color: #0066cc;
          border: 1px solid #b3d9ff;
        }

        .status-degraded {
          background: #fff3cd;
          color: #856404;
          border: 1px solid #ffeaa7;
        }

        .status-offline {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f1b6bb;
        }

        .status-icon-container {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 16px;
          height: 16px;
        }

        .status-text {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 1px;
        }

        .status-label {
          font-size: 10px;
          opacity: 0.8;
          font-weight: 400;
        }

        .status-value {
          font-size: 11px;
          font-weight: 600;
        }

        .status-action-btn {
          background: none;
          border: none;
          color: inherit;
          cursor: pointer;
          padding: 2px;
          margin-left: 4px;
          border-radius: 4px;
          transition: all 0.2s ease;
        }

        .status-action-btn:hover {
          background: rgba(0, 0, 0, 0.1);
        }

        .extension-guide {
          margin-left: 8px;
        }

        .guide-btn {
          background: #667eea;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 11px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .guide-btn:hover {
          background: #5a6fd8;
          transform: translateY(-1px);
        }

        @media (max-width: 768px) {
          .service-status-indicator {
            flex-direction: column;
            align-items: stretch;
            gap: 8px;
          }

          .status-item {
            justify-content: space-between;
          }
        }
      `}</style>
    </div>
  );
};

// Extension installation guide component
const ExtensionGuide = ({ show, onClose }) => {
  if (!show) return null;

  return (
    <div className="extension-guide-modal">
      <div className="guide-content">
        <div className="guide-header">
          <h3>Extension Installation Guide</h3>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>
        
        <div className="guide-steps">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>Open Chrome Extensions</h4>
              <p>Navigate to <code>chrome://extensions/</code></p>
            </div>
          </div>
          
          <div className="step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>Enable Developer Mode</h4>
              <p>Toggle "Developer mode" in the top-right corner</p>
            </div>
          </div>
          
          <div className="step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Load Extension</h4>
              <p>Click "Load unpacked" and select the <code>extension/</code> folder</p>
            </div>
          </div>
          
          <div className="step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h4>Verify Installation</h4>
              <p>Look for the Samay v6 extension in your extensions list</p>
            </div>
          </div>
        </div>
        
        <div className="guide-footer">
          <button className="btn btn-primary" onClick={onClose}>
            Got it!
          </button>
        </div>
      </div>
      
      <style jsx="true">{`
        .extension-guide-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .guide-content {
          background: white;
          border-radius: 12px;
          padding: 24px;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
        }

        .guide-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .guide-header h3 {
          margin: 0;
          color: #333;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #666;
        }

        .step {
          display: flex;
          gap: 16px;
          margin-bottom: 20px;
        }

        .step-number {
          background: #667eea;
          color: white;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 600;
          flex-shrink: 0;
        }

        .step-content h4 {
          margin: 0 0 4px 0;
          font-size: 14px;
          color: #333;
        }

        .step-content p {
          margin: 0;
          font-size: 13px;
          color: #666;
          line-height: 1.4;
        }

        .step-content code {
          background: #f1f3f4;
          padding: 2px 4px;
          border-radius: 4px;
          font-size: 12px;
        }

        .guide-footer {
          text-align: center;
          margin-top: 24px;
          padding-top: 20px;
          border-top: 1px solid #e9ecef;
        }
      `}</style>
    </div>
  );
};

export default ServiceStatusIndicator;