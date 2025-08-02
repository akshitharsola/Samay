import React, { useState } from 'react';

const ResponseDisplay = ({ comprehensiveResponse, serviceResponses }) => {
  const [activeTab, setActiveTab] = useState('synthesis');
  const [expandedServices, setExpandedServices] = useState({});

  const toggleServiceExpansion = (serviceName) => {
    setExpandedServices(prev => ({
      ...prev,
      [serviceName]: !prev[serviceName]
    }));
  };

  const getServiceIcon = (serviceName) => {
    const icons = {
      'claude': '💎',
      'gemini': '🧠', 
      'perplexity': '🔍',
      'chatgpt': '💬',
      'openai': '💬',
      'local': '🏠'
    };
    return icons[serviceName.toLowerCase()] || '🤖';
  };

  const getServiceDisplayName = (serviceName) => {
    const names = {
      'claude': 'Claude',
      'gemini': 'Gemini',
      'perplexity': 'Perplexity', 
      'chatgpt': 'ChatGPT',
      'openai': 'ChatGPT',
      'local': 'Local Assistant'
    };
    return names[serviceName.toLowerCase()] || serviceName;
  };

  const formatResponseTime = (responseTime) => {
    if (typeof responseTime === 'number') {
      return `${responseTime.toFixed(2)}s`;
    }
    return 'N/A';
  };

  return (
    <div className="response-display">
      <div className="response-header">
        <h3>🎯 Comprehensive AI Response</h3>
        <div className="response-stats">
          <span className="stat">
            📊 {serviceResponses?.length || 0} Services
          </span>
          <span className="stat">
            ⚡ {comprehensiveResponse?.total_response_time ? 
                formatResponseTime(comprehensiveResponse.total_response_time) : 'N/A'}
          </span>
          <span className="stat">
            🎯 {comprehensiveResponse?.confidence_score ? 
                Math.round(comprehensiveResponse.confidence_score * 100) + '%' : 'N/A'} Confidence
          </span>
        </div>
      </div>

      <div className="response-tabs">
        <button 
          className={`tab ${activeTab === 'synthesis' ? 'active' : ''}`}
          onClick={() => setActiveTab('synthesis')}
        >
          📈 Synthesized Response
        </button>
        <button 
          className={`tab ${activeTab === 'services' ? 'active' : ''}`}
          onClick={() => setActiveTab('services')}
        >
          🤖 Individual Services
        </button>
        <button 
          className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          🔍 Analysis & Sources
        </button>
      </div>

      <div className="response-content">
        {activeTab === 'synthesis' && (
          <div className="synthesis-tab">
            <div className="synthesis-section">
              <h4>🎯 Original Query</h4>
              <div className="query-display">
                {comprehensiveResponse?.original_query || 'No original query available'}
              </div>
            </div>

            {comprehensiveResponse?.refined_query && 
             comprehensiveResponse.refined_query !== comprehensiveResponse.original_query && (
              <div className="synthesis-section">
                <h4>🔄 Refined Query</h4>
                <div className="query-display refined">
                  {comprehensiveResponse.refined_query}
                </div>
              </div>
            )}

            <div className="synthesis-section main">
              <h4>📈 Synthesized Response</h4>
              <div className="synthesized-content">
                {comprehensiveResponse?.synthesized_content || 'No synthesized response available'}
              </div>
            </div>

            {comprehensiveResponse?.follow_up_suggestions?.length > 0 && (
              <div className="synthesis-section">
                <h4>💡 Follow-up Suggestions</h4>
                <div className="suggestions-list">
                  {comprehensiveResponse.follow_up_suggestions.map((suggestion, index) => (
                    <div key={index} className="suggestion-item">
                      <span className="suggestion-icon">💡</span>
                      <span className="suggestion-text">{suggestion}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'services' && (
          <div className="services-tab">
            {serviceResponses?.map((response, index) => {
              const serviceName = response.service || `Service ${index + 1}`;
              const isExpanded = expandedServices[serviceName];
              const hasError = response.error || response.status_code >= 400;

              return (
                <div key={index} className={`service-response ${hasError ? 'error' : 'success'}`}>
                  <div 
                    className="service-header"
                    onClick={() => toggleServiceExpansion(serviceName)}
                  >
                    <div className="service-info">
                      <span className="service-icon">
                        {getServiceIcon(serviceName)}
                      </span>
                      <div className="service-details">
                        <h5>{getServiceDisplayName(serviceName)}</h5>
                        <div className="service-meta">
                          <span className={`status ${hasError ? 'error' : 'success'}`}>
                            {hasError ? '❌ Error' : '✅ Success'}
                          </span>
                          <span className="response-time">
                            ⏱️ {formatResponseTime(response.response_time)}
                          </span>
                          {response.status_code && (
                            <span className="status-code">
                              Status: {response.status_code}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <button className="expand-btn">
                      {isExpanded ? '▼' : '▶'}
                    </button>
                  </div>

                  <div className={`service-content ${isExpanded ? 'expanded' : ''}`}>
                    {hasError ? (
                      <div className="error-content">
                        <h6>❌ Error Details:</h6>
                        <pre>{response.error || `HTTP ${response.status_code} Error`}</pre>
                      </div>
                    ) : (
                      <div className="success-content">
                        <div className="response-text">
                          {response.content || 'No content available'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="analysis-tab">
            <div className="analysis-section">
              <h4>📊 Response Analysis</h4>
              <div className="analysis-grid">
                <div className="analysis-item">
                  <h5>🎯 Confidence Score</h5>
                  <div className="confidence-display">
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill"
                        style={{ 
                          width: `${(comprehensiveResponse?.confidence_score || 0) * 100}%` 
                        }}
                      ></div>
                    </div>
                    <span className="confidence-text">
                      {comprehensiveResponse?.confidence_score ? 
                        Math.round(comprehensiveResponse.confidence_score * 100) + '%' : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="analysis-item">
                  <h5>⚡ Performance Metrics</h5>
                  <div className="metrics-list">
                    <div className="metric">
                      <span>Total Response Time:</span>
                      <span>{formatResponseTime(comprehensiveResponse?.total_response_time)}</span>
                    </div>
                    <div className="metric">
                      <span>Services Queried:</span>
                      <span>{serviceResponses?.length || 0}</span>
                    </div>
                    <div className="metric">
                      <span>Successful Responses:</span>
                      <span>
                        {serviceResponses?.filter(r => !r.error && r.status_code < 400).length || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {comprehensiveResponse?.sources?.length > 0 && (
              <div className="analysis-section">
                <h4>📚 Sources & References</h4>
                <div className="sources-list">
                  {comprehensiveResponse.sources.map((source, index) => (
                    <div key={index} className="source-item">
                      <span className="source-icon">📖</span>
                      <div className="source-info">
                        <div className="source-title">{source.title || `Source ${index + 1}`}</div>
                        {source.url && (
                          <a 
                            href={source.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="source-link"
                          >
                            {source.url}
                          </a>
                        )}
                        {source.description && (
                          <div className="source-description">{source.description}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="analysis-section">
              <h4>🔍 Service Comparison</h4>
              <div className="comparison-table">
                <div className="comparison-header">
                  <div>Service</div>
                  <div>Status</div>
                  <div>Response Time</div>
                  <div>Content Length</div>
                </div>
                {serviceResponses?.map((response, index) => (
                  <div key={index} className="comparison-row">
                    <div className="service-name">
                      {getServiceIcon(response.service)} {getServiceDisplayName(response.service)}
                    </div>
                    <div className={`status ${response.error ? 'error' : 'success'}`}>
                      {response.error ? '❌' : '✅'}
                    </div>
                    <div>{formatResponseTime(response.response_time)}</div>
                    <div>{response.content?.length || 0} chars</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResponseDisplay;