import React, { useState } from 'react';

const ResponseViewer = ({ responses = {}, synthesis = '', onReset }) => {
  const [activeTab, setActiveTab] = useState('synthesis');

  // Service configuration for display
  const serviceConfig = {
    chatgpt: {
      name: 'ChatGPT',
      icon: 'fas fa-robot',
      color: '#10a37f',
      description: 'General AI Assistant'
    },
    claude: {
      name: 'Claude',
      icon: 'fas fa-brain', 
      color: '#ff6b35',
      description: 'Advanced Reasoning'
    },
    gemini: {
      name: 'Gemini',
      icon: 'fas fa-star',
      color: '#4285f4',
      description: 'Technical Analysis'
    },
    perplexity: {
      name: 'Perplexity',
      icon: 'fas fa-search',
      color: '#20b2aa',
      description: 'Research & Sources'
    }
  };

  const getResponseContent = (response) => {
    if (typeof response === 'string') {
      return response;
    }
    return response?.content || 'No content available';
  };

  const getResponseStats = (content) => {
    const words = content.split(' ').length;
    const chars = content.length;
    const readingTime = Math.ceil(words / 200); // Assuming 200 words per minute
    
    return {
      words,
      chars,
      readingTime
    };
  };

  const formatSynthesis = (text) => {
    // Convert markdown-like formatting to HTML
    return text
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^(.*)/, '<p>$1</p>');
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      responses: Object.entries(responses).map(([service, response]) => ({
        service,
        content: getResponseContent(response),
        stats: getResponseStats(getResponseContent(response))
      })),
      synthesis,
      metadata: {
        totalServices: Object.keys(responses).length,
        totalWords: Object.values(responses).reduce((total, response) => {
          return total + getResponseStats(getResponseContent(response)).words;
        }, 0)
      }
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `samay-v6-results-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Samay v6 Multi-AI Results',
          text: synthesis.substring(0, 200) + '...',
          url: window.location.href
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      // Fallback: copy to clipboard
      const shareText = `Samay v6 Multi-AI Results:\n\n${synthesis}`;
      await navigator.clipboard.writeText(shareText);
      alert('Results copied to clipboard!');
    }
  };

  const tabItems = [
    { id: 'synthesis', label: 'Synthesis', icon: 'fas fa-magic' },
    { id: 'individual', label: 'Individual Responses', icon: 'fas fa-list' },
    { id: 'comparison', label: 'Comparison', icon: 'fas fa-balance-scale' }
  ];

  return (
    <div className="response-viewer">
      <div className="response-header">
        <h3 className="response-title">
          <i className="fas fa-chart-line"></i>
          Multi-AI Results
        </h3>
        <div className="response-actions">
          <button className="btn btn-secondary" onClick={handleExport}>
            <i className="fas fa-download"></i>
            Export
          </button>
          <button className="btn btn-secondary" onClick={handleShare}>
            <i className="fas fa-share"></i>
            Share
          </button>
          <button className="btn btn-danger" onClick={onReset}>
            <i className="fas fa-redo"></i>
            New Query
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="response-tabs">
        {tabItems.map(tab => (
          <button
            key={tab.id}
            className={`response-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <i className={tab.icon}></i>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="response-content">
        
        {/* Synthesis Tab */}
        {activeTab === 'synthesis' && (
          <div className="synthesis-view">
            {synthesis ? (
              <div 
                className="synthesis-content"
                dangerouslySetInnerHTML={{ __html: formatSynthesis(synthesis) }}
              />
            ) : (
              <div className="synthesis-placeholder">
                <i className="fas fa-cog fa-spin"></i>
                <p>Generating comprehensive synthesis...</p>
              </div>
            )}
          </div>
        )}

        {/* Individual Responses Tab */}
        {activeTab === 'individual' && (
          <div className="individual-responses">
            {Object.entries(responses).map(([service, response]) => {
              const config = serviceConfig[service];
              const content = getResponseContent(response);
              const stats = getResponseStats(content);

              return (
                <div key={service} className="service-response">
                  <div className="service-response-header">
                    <div className="service-info">
                      <div className="service-name-badge" style={{ color: config.color }}>
                        <i className={config.icon}></i>
                        {config.name}
                      </div>
                      <div className="service-description">
                        {config.description}
                      </div>
                    </div>
                    <div className="response-meta">
                      <span className="word-count">{stats.words} words</span>
                      <span className="reading-time">{stats.readingTime} min read</span>
                    </div>
                  </div>
                  <div className="service-response-content">
                    {content}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === 'comparison' && (
          <div className="comparison-view">
            <div className="comparison-stats">
              <h4>Response Statistics</h4>
              <div className="stats-grid">
                {Object.entries(responses).map(([service, response]) => {
                  const config = serviceConfig[service];
                  const content = getResponseContent(response);
                  const stats = getResponseStats(content);

                  return (
                    <div key={service} className="stat-item">
                      <div className="stat-header" style={{ color: config.color }}>
                        <i className={config.icon}></i>
                        {config.name}
                      </div>
                      <div className="stat-details">
                        <div className="stat-row">
                          <span>Words:</span>
                          <strong>{stats.words}</strong>
                        </div>
                        <div className="stat-row">
                          <span>Characters:</span>
                          <strong>{stats.chars}</strong>
                        </div>
                        <div className="stat-row">
                          <span>Reading Time:</span>
                          <strong>{stats.readingTime} min</strong>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="comparison-insights">
              <h4>Key Insights</h4>
              <div className="insights-grid">
                <div className="insight-item">
                  <div className="insight-title">Most Comprehensive</div>
                  <div className="insight-value">
                    {Object.entries(responses).reduce((longest, [service, response]) => {
                      const currentLength = getResponseContent(response).length;
                      const longestLength = getResponseContent(responses[longest]).length;
                      return currentLength > longestLength ? service : longest;
                    }, Object.keys(responses)[0])}
                  </div>
                </div>
                <div className="insight-item">
                  <div className="insight-title">Total Words</div>
                  <div className="insight-value">
                    {Object.values(responses).reduce((total, response) => {
                      return total + getResponseStats(getResponseContent(response)).words;
                    }, 0)}
                  </div>
                </div>
                <div className="insight-item">
                  <div className="insight-title">Average Response</div>
                  <div className="insight-value">
                    {Math.round(Object.values(responses).reduce((total, response) => {
                      return total + getResponseStats(getResponseContent(response)).words;
                    }, 0) / Object.keys(responses).length)} words
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx="true">{`
        .synthesis-placeholder {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .synthesis-placeholder i {
          font-size: 24px;
          margin-bottom: 16px;
          color: #667eea;
        }

        .service-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .service-description {
          font-size: 12px;
          color: #666;
        }

        .response-meta {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #666;
        }

        .comparison-stats,
        .comparison-insights {
          margin-bottom: 32px;
        }

        .comparison-stats h4,
        .comparison-insights h4 {
          margin-bottom: 16px;
          color: #333;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .stat-item {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 16px;
        }

        .stat-header {
          font-weight: 600;
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .stat-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
          font-size: 14px;
        }

        .insights-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
        }

        .insight-item {
          text-align: center;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 12px;
        }

        .insight-title {
          font-size: 12px;
          opacity: 0.9;
          margin-bottom: 8px;
        }

        .insight-value {
          font-size: 18px;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .response-actions {
            flex-wrap: wrap;
          }
          
          .response-tabs {
            overflow-x: auto;
          }
          
          .stats-grid,
          .insights-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default ResponseViewer;