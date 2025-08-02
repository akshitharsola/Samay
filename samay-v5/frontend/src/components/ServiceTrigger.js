import React, { useState } from 'react';

const ServiceTrigger = ({ refinedQuery, onTrigger, isLoading }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleTrigger = () => {
    if (!isLoading && refinedQuery) {
      onTrigger();
    }
  };

  return (
    <div className="service-trigger">
      <div className="trigger-card">
        <div className="trigger-header">
          <div className="trigger-icon">🚀</div>
          <div className="trigger-title">
            <h4>Query Ready for AI Services</h4>
            <p>Your query has been refined and is ready to be sent to all AI services</p>
          </div>
        </div>

        <div className="refined-query-preview">
          <div 
            className="query-header"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <h5>📝 Refined Query:</h5>
            <button className="expand-btn">
              {isExpanded ? '▼' : '▶'}
            </button>
          </div>
          
          <div className={`query-content ${isExpanded ? 'expanded' : ''}`}>
            <div className="query-text">
              {refinedQuery || 'No query available'}
            </div>
          </div>
        </div>

        <div className="services-preview">
          <h5>🎯 Target Services:</h5>
          <div className="service-list">
            <div className="service-item">
              <span className="service-icon">💎</span>
              <span className="service-name">Claude</span>
              <span className="service-status ready">Ready</span>
            </div>
            <div className="service-item">
              <span className="service-icon">🧠</span>
              <span className="service-name">Gemini</span>
              <span className="service-status ready">Ready</span>
            </div>
            <div className="service-item">
              <span className="service-icon">🔍</span>
              <span className="service-name">Perplexity</span>
              <span className="service-status ready">Ready</span>
            </div>
            <div className="service-item">
              <span className="service-icon">💬</span>
              <span className="service-name">ChatGPT</span>
              <span className="service-status ready">Ready</span>
            </div>
          </div>
        </div>

        <div className="trigger-actions">
          <button 
            className={`trigger-btn ${isLoading ? 'loading' : ''}`}
            onClick={handleTrigger}
            disabled={isLoading || !refinedQuery}
          >
            {isLoading ? (
              <>
                <span className="loading-spinner">⏳</span>
                <span>Querying Services...</span>
              </>
            ) : (
              <>
                <span className="rocket-icon">🚀</span>
                <span>Route to All AI Services</span>
              </>
            )}
          </button>

          {isLoading && (
            <div className="loading-info">
              <div className="loading-text">
                Sending your query to all AI services simultaneously...
              </div>
              <div className="loading-progress">
                <div className="progress-bar">
                  <div className="progress-fill"></div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="trigger-footer">
          <div className="info-item">
            <span className="info-icon">⚡</span>
            <span>Parallel processing for faster results</span>
          </div>
          <div className="info-item">
            <span className="info-icon">🎯</span>
            <span>Comprehensive synthesis from all services</span>
          </div>
          <div className="info-item">
            <span className="info-icon">📊</span>
            <span>Response comparison and analysis</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServiceTrigger;