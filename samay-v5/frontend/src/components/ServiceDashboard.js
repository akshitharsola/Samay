import React, { useState, useEffect } from 'react';

const ServiceDashboard = ({ services: initialServices }) => {
  const [services, setServices] = useState(initialServices || {});
  const [isExpanded, setIsExpanded] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(Date.now());

  // Refresh service status
  const refreshServices = async () => {
    try {
      const response = await fetch('/api/services/status');
      const data = await response.json();
      setServices(data.services);
      setLastUpdated(Date.now());
    } catch (error) {
      console.error('Failed to refresh services:', error);
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(refreshServices, 30000);
    return () => clearInterval(interval);
  }, []);

  // Service configuration
  const serviceConfig = {
    'claude': {
      name: 'Claude',
      icon: '💎',
      description: 'Anthropic\'s AI assistant',
      url: 'https://claude.ai'
    },
    'gemini': {
      name: 'Gemini',
      icon: '🧠',
      description: 'Google\'s AI model',
      url: 'https://gemini.google.com'
    },
    'perplexity': {
      name: 'Perplexity',
      icon: '🔍',
      description: 'AI-powered search',
      url: 'https://www.perplexity.ai'
    },
    'chatgpt': {
      name: 'ChatGPT',
      icon: '💬',
      description: 'OpenAI\'s chatbot',
      url: 'https://chat.openai.com'
    },
    'openai': {
      name: 'ChatGPT',
      icon: '💬',
      description: 'OpenAI\'s chatbot',
      url: 'https://chat.openai.com'
    },
    'local': {
      name: 'Local Assistant',
      icon: '🏠',
      description: 'Phi-3-Mini local processing',
      url: null
    },
    'weather': {
      name: 'Weather API',
      icon: '🌤️',
      description: 'OpenWeatherMap API',
      url: 'https://openweathermap.org'
    },
    'news': {
      name: 'News API',
      icon: '📰',
      description: 'NewsAPI integration',
      url: 'https://newsapi.org'
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'available':
      case 'authenticated':
      case 'ready':
        return 'success';
      case 'unavailable':
      case 'error':
      case 'failed':
        return 'error';
      case 'authenticating':
      case 'connecting':
        return 'warning';
      default:
        return 'unknown';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'available':
      case 'authenticated':
      case 'ready':
        return '✅';
      case 'unavailable':
      case 'error':
      case 'failed':
        return '❌';
      case 'authenticating':
      case 'connecting':
        return '⏳';
      default:
        return '❓';
    }
  };

  const totalServices = Object.keys(services).length;
  const availableServices = Object.values(services).filter(
    status => ['available', 'authenticated', 'ready'].includes(status?.toLowerCase())
  ).length;

  return (
    <div className="service-dashboard">
      <div className="dashboard-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="dashboard-summary">
          <div className="service-count">
            <span className="count-text">
              {availableServices}/{totalServices} Services
            </span>
            <span className="count-icon">
              {availableServices === totalServices ? '🟢' : availableServices > 0 ? '🟡' : '🔴'}
            </span>
          </div>
          <div className="dashboard-actions">
            <button 
              className="refresh-btn"
              onClick={(e) => {
                e.stopPropagation();
                refreshServices();
              }}
              title="Refresh service status"
            >
              🔄
            </button>
            <button className="expand-btn">
              {isExpanded ? '▼' : '▶'}
            </button>
          </div>
        </div>
      </div>

      <div className={`dashboard-content ${isExpanded ? 'expanded' : ''}`}>
        <div className="services-grid">
          {Object.entries(services).map(([serviceName, status]) => {
            const config = serviceConfig[serviceName.toLowerCase()] || {
              name: serviceName,
              icon: '🤖',
              description: 'AI Service',
              url: null
            };

            return (
              <div 
                key={serviceName}
                className={`service-card ${getStatusColor(status)}`}
              >
                <div className="service-header">
                  <span className="service-icon">{config.icon}</span>
                  <div className="service-info">
                    <h5 className="service-name">{config.name}</h5>
                    <p className="service-description">{config.description}</p>
                  </div>
                  <div className="service-status">
                    <span className="status-icon">{getStatusIcon(status)}</span>
                    <span className="status-text">{status || 'Unknown'}</span>
                  </div>
                </div>

                {config.url && (
                  <div className="service-actions">
                    <a 
                      href={config.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="service-link"
                      title={`Open ${config.name}`}
                    >
                      🔗 Open
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="dashboard-footer">
          <div className="status-legend">
            <div className="legend-item">
              <span className="legend-icon">✅</span>
              <span>Available</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">⏳</span>
              <span>Connecting</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">❌</span>
              <span>Unavailable</span>
            </div>
          </div>
          
          <div className="last-updated">
            Last updated: {new Date(lastUpdated).toLocaleTimeString()}
          </div>
        </div>

        <div className="dashboard-stats">
          <div className="stat-item">
            <h6>🎯 System Status</h6>
            <div className="stat-value">
              {availableServices === totalServices ? 'All Systems Go' :
               availableServices > totalServices / 2 ? 'Partial Service' :
               availableServices > 0 ? 'Limited Service' : 'Service Degraded'}
            </div>
          </div>

          <div className="stat-item">
            <h6>🔄 Automation Status</h6>
            <div className="stat-value">
              {services.claude || services.gemini || services.perplexity ? 'AI Services Ready' : 'AI Services Unavailable'}
            </div>
          </div>

          <div className="stat-item">
            <h6>📡 Local Processing</h6>
            <div className="stat-value">
              {services.local === 'available' ? 'Phi-3-Mini Active' : 'Local LLM Unavailable'}
            </div>
          </div>
        </div>

        <div className="dashboard-tips">
          <h6>💡 Quick Tips:</h6>
          <ul>
            <li>Green (✅) services are ready for automation</li>
            <li>Red (❌) services may need re-authentication</li>
            <li>Yellow (⏳) services are currently connecting</li>
            <li>Local processing is always available for privacy</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ServiceDashboard;