import React, { useState, useEffect, useMemo } from 'react';

const AutomationStatus = ({ status, currentQuery, sessionId, responses = {} }) => {
  const [serviceStates, setServiceStates] = useState({
    chatgpt: 'pending',
    claude: 'pending', 
    gemini: 'pending',
    perplexity: 'pending'
  });

  const [progress, setProgress] = useState(0);

  // Service configuration
  const serviceConfig = useMemo(() => ({
    chatgpt: {
      name: 'ChatGPT',
      icon: 'fas fa-robot',
      color: '#10a37f'
    },
    claude: {
      name: 'Claude',
      icon: 'fas fa-brain',
      color: '#ff6b35'
    },
    gemini: {
      name: 'Gemini',
      icon: 'fas fa-star',
      color: '#4285f4'
    },
    perplexity: {
      name: 'Perplexity',
      icon: 'fas fa-search',
      color: '#20b2aa'
    }
  }), []);

  // Update service states based on responses
  useEffect(() => {
    const newStates = {
      chatgpt: 'pending',
      claude: 'pending', 
      gemini: 'pending',
      perplexity: 'pending'
    };
    let completedCount = 0;

    Object.keys(serviceConfig).forEach(service => {
      if (responses[service]) {
        newStates[service] = 'complete';
        completedCount++;
      } else if (status === 'running') {
        newStates[service] = 'running';
      }
    });

    setServiceStates(newStates);
    setProgress((completedCount / 4) * 100);
  }, [responses, status, serviceConfig]);

  const getStatusInfo = () => {
    switch (status) {
      case 'starting':
        return {
          title: 'Starting Automation',
          message: 'Opening AI service tabs and preparing scripts...',
          icon: 'fas fa-play-circle',
          className: 'status-starting'
        };
      case 'running':
        return {
          title: 'Automation Running',
          message: 'Querying all AI services simultaneously...',
          icon: 'fas fa-cogs',
          className: 'status-running'
        };
      case 'complete':
        return {
          title: 'Automation Complete',
          message: 'All responses received successfully!',
          icon: 'fas fa-check-circle',
          className: 'status-complete'
        };
      case 'error':
        return {
          title: 'Automation Error',
          message: 'Something went wrong during automation.',
          icon: 'fas fa-exclamation-triangle',
          className: 'status-error'
        };
      default:
        return {
          title: 'Ready',
          message: 'Ready to start automation',
          icon: 'fas fa-circle',
          className: 'status-idle'
        };
    }
  };

  const statusInfo = getStatusInfo();

  const getServiceStateText = (state) => {
    switch (state) {
      case 'pending':
        return 'Waiting...';
      case 'running':
        return 'Processing...';
      case 'complete':
        return 'Complete!';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const getEstimatedTime = () => {
    if (status === 'complete') return 'Completed';
    if (status === 'error') return 'Failed';
    
    const completedServices = Object.values(serviceStates).filter(state => state === 'complete').length;
    const remainingTime = Math.max(0, 60 - (completedServices * 15)); // Rough estimate
    
    if (remainingTime === 0) return 'Almost done...';
    return `~${remainingTime}s remaining`;
  };

  return (
    <div className="automation-status">
      <div className="status-header">
        <h3 className="status-title">
          <i className={statusInfo.icon}></i>
          {statusInfo.title}
        </h3>
        <div className={`status-badge ${statusInfo.className}`}>
          {status === 'running' && <i className="fas fa-spinner fa-spin"></i>}
          {statusInfo.message}
        </div>
      </div>

      {/* Query Display */}
      <div className="current-query">
        <p className="query-label">
          <i className="fas fa-quote-left"></i>
          Current Query:
        </p>
        <div className="query-text">
          {currentQuery}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="status-progress">
        <div className="progress-header">
          <span className="progress-text">
            Progress: {Object.values(serviceStates).filter(state => state === 'complete').length}/4 services
          </span>
          <span className="estimated-time">
            {getEstimatedTime()}
          </span>
        </div>
        <div className="progress">
          <div 
            className="progress-bar" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* Service Status Grid */}
      <div className="service-status-grid">
        {Object.entries(serviceConfig).map(([serviceKey, config]) => {
          const state = serviceStates[serviceKey];
          return (
            <div key={serviceKey} className={`service-status-item ${state}`}>
              <div className="service-icon" style={{ color: config.color }}>
                <i className={config.icon}></i>
              </div>
              <div className="service-name">{config.name}</div>
              <div className="service-progress">
                {getServiceStateText(state)}
              </div>
              {state === 'complete' && responses[serviceKey] && (
                <div className="response-preview">
                  <i className="fas fa-check text-success"></i>
                  {(responses[serviceKey].content || responses[serviceKey]).substring(0, 50)}...
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Session Info */}
      <div className="session-info">
        <small className="text-muted">
          <i className="fas fa-id-card"></i>
          Session: {sessionId}
        </small>
      </div>

      <style jsx="true">{`
        .current-query {
          margin: 20px 0;
          padding: 16px;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 4px solid #667eea;
        }

        .query-label {
          font-size: 12px;
          font-weight: 500;
          color: #666;
          margin: 0 0 8px 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .query-text {
          font-size: 14px;
          color: #333;
          line-height: 1.5;
          font-style: italic;
        }

        .progress-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .estimated-time {
          font-size: 12px;
          color: #666;
          font-weight: 500;
        }

        .response-preview {
          margin-top: 8px;
          font-size: 11px;
          color: #666;
          display: flex;
          align-items: flex-start;
          gap: 6px;
          line-height: 1.3;
        }

        .session-info {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #e9ecef;
          text-align: center;
        }

        .text-success {
          color: #28a745;
        }

        .text-muted {
          color: #6c757d;
        }
      `}</style>
    </div>
  );
};

export default AutomationStatus;