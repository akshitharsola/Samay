import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  Chrome, 
  CheckCircle, 
  XCircle, 
  Activity,
  Send,
  BarChart3,
  Settings,
  RefreshCw,
  Zap
} from 'lucide-react';
import axios from 'axios';

const WebServicesPanel = () => {
  const [services, setServices] = useState({});
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [queryForm, setQueryForm] = useState({
    prompt: '',
    services: ['claude'],
    expected_output: 'General response',
    output_format: 'json',
    max_refinements: 2
  });
  const [queryResult, setQueryResult] = useState(null);
  const [isQuerying, setIsQuerying] = useState(false);

  useEffect(() => {
    fetchServicesStatus();
    const interval = setInterval(fetchServicesStatus, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const fetchServicesStatus = async () => {
    try {
      const response = await axios.get('/webservices/status');
      setServices(response.data.service_status);
      setStats(response.data.communication_stats);
    } catch (error) {
      console.error('Failed to fetch services status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleServiceToggle = (serviceName, enabled) => {
    if (enabled) {
      setQueryForm(prev => ({
        ...prev,
        services: [...prev.services, serviceName]
      }));
    } else {
      setQueryForm(prev => ({
        ...prev,
        services: prev.services.filter(s => s !== serviceName)
      }));
    }
  };

  const executeQuery = async () => {
    if (!queryForm.prompt.trim() || queryForm.services.length === 0) return;

    setIsQuerying(true);
    try {
      const response = await axios.post('/webservices/query', queryForm);
      setQueryResult(response.data);
    } catch (error) {
      console.error('Query failed:', error);
      setQueryResult({
        error: error.response?.data?.detail || error.message
      });
    } finally {
      setIsQuerying(false);
    }
  };

  const getServiceIcon = (serviceName) => {
    switch (serviceName) {
      case 'claude': return '🤖';
      case 'gemini': return '✨';
      case 'perplexity': return '🔍';
      default: return '🌐';
    }
  };

  const getServiceStatus = (service) => {
    if (!service) return { status: 'unknown', color: '#6b7280' };
    
    if (service.logged_in && service.session_ready) {
      return { status: 'ready', color: '#22c55e' };
    } else if (service.logged_in) {
      return { status: 'logged_in', color: '#eab308' };
    } else {
      return { status: 'offline', color: '#ef4444' };
    }
  };

  const formatResponse = (response) => {
    if (typeof response === 'string') {
      try {
        return JSON.stringify(JSON.parse(response), null, 2);
      } catch {
        return response;
      }
    }
    return JSON.stringify(response, null, 2);
  };

  if (loading) {
    return (
      <div className="web-services-panel loading">
        <div className="loading-spinner"></div>
        <p>Loading web services...</p>
      </div>
    );
  }

  return (
    <div className="web-services-panel">
      <div className="panel-header">
        <div className="header-title">
          <Globe size={20} />
          <h3>Web Services Automation</h3>
        </div>
        <div className="header-actions">
          <button onClick={fetchServicesStatus} className="refresh-btn">
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      <div className="services-grid">
        {/* Service Status */}
        <div className="panel-card services-status">
          <div className="card-header">
            <Chrome size={18} />
            <h4>Service Status</h4>
          </div>
          <div className="card-content">
            <div className="services-list">
              {Object.entries(services).map(([serviceName, serviceData]) => {
                const status = getServiceStatus(serviceData);
                return (
                  <div key={serviceName} className="service-item">
                    <div className="service-info">
                      <span className="service-icon">{getServiceIcon(serviceName)}</span>
                      <div className="service-details">
                        <span className="service-name">
                          {serviceName.charAt(0).toUpperCase() + serviceName.slice(1)}
                        </span>
                        <span className="service-status" style={{ color: status.color }}>
                          {status.status === 'ready' && <CheckCircle size={14} />}
                          {status.status === 'logged_in' && <Activity size={14} />}
                          {status.status === 'offline' && <XCircle size={14} />}
                          {status.status}
                        </span>
                      </div>
                    </div>
                    {serviceData?.last_activity && (
                      <div className="last-activity">
                        Last: {new Date(serviceData.last_activity).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Communication Stats */}
        <div className="panel-card stats-card">
          <div className="card-header">
            <BarChart3 size={18} />
            <h4>Communication Stats</h4>
          </div>
          <div className="card-content">
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{stats.total_requests || 0}</div>
                <div className="stat-label">Total Requests</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.successful_requests || 0}</div>
                <div className="stat-label">Successful</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {stats.success_rate ? `${(stats.success_rate * 100).toFixed(0)}%` : '0%'}
                </div>
                <div className="stat-label">Success Rate</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.average_refinements || 0}</div>
                <div className="stat-label">Avg Refinements</div>
              </div>
            </div>
            
            {stats.service_usage && (
              <div className="service-usage">
                <h5>Service Usage</h5>
                {Object.entries(stats.service_usage).map(([service, count]) => (
                  <div key={service} className="usage-item">
                    <span>{service}</span>
                    <span>{count} requests</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Query Interface */}
        <div className="panel-card query-card">
          <div className="card-header">
            <Zap size={18} />
            <h4>Multi-Service Query</h4>
          </div>
          <div className="card-content">
            <div className="query-form">
              <div className="form-group">
                <label>Prompt</label>
                <textarea
                  value={queryForm.prompt}
                  onChange={(e) => setQueryForm(prev => ({ ...prev, prompt: e.target.value }))}
                  placeholder="Enter your query for the AI services..."
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Services</label>
                  <div className="services-checkboxes">
                    {Object.keys(services).map(serviceName => {
                      const serviceStatus = getServiceStatus(services[serviceName]);
                      const isReady = serviceStatus.status === 'ready';
                      return (
                        <label key={serviceName} className={`service-checkbox ${!isReady ? 'disabled' : ''}`}>
                          <input
                            type="checkbox"
                            checked={queryForm.services.includes(serviceName)}
                            onChange={(e) => handleServiceToggle(serviceName, e.target.checked)}
                            disabled={!isReady}
                          />
                          <span>{getServiceIcon(serviceName)} {serviceName}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                <div className="form-group">
                  <label>Output Format</label>
                  <select
                    value={queryForm.output_format}
                    onChange={(e) => setQueryForm(prev => ({ ...prev, output_format: e.target.value }))}
                  >
                    <option value="json">JSON</option>
                    <option value="text">Structured Text</option>
                    <option value="markdown">Markdown</option>
                    <option value="xml">XML</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Expected Output</label>
                  <input
                    type="text"
                    value={queryForm.expected_output}
                    onChange={(e) => setQueryForm(prev => ({ ...prev, expected_output: e.target.value }))}
                    placeholder="Describe the expected response structure..."
                  />
                </div>

                <div className="form-group">
                  <label>Max Refinements</label>
                  <input
                    type="number"
                    min="0"
                    max="5"
                    value={queryForm.max_refinements}
                    onChange={(e) => setQueryForm(prev => ({ ...prev, max_refinements: parseInt(e.target.value) }))}
                  />
                </div>
              </div>

              <button
                onClick={executeQuery}
                disabled={!queryForm.prompt.trim() || queryForm.services.length === 0 || isQuerying}
                className="execute-btn"
              >
                {isQuerying ? (
                  <>
                    <div className="loading-spinner small"></div>
                    Querying Services...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Execute Query
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Query Results */}
        {queryResult && (
          <div className="panel-card results-card">
            <div className="card-header">
              <BarChart3 size={18} />
              <h4>Query Results</h4>
            </div>
            <div className="card-content">
              {queryResult.error ? (
                <div className="error-result">
                  <XCircle size={16} />
                  <span>Error: {queryResult.error}</span>
                </div>
              ) : (
                <div className="results-container">
                  <div className="results-summary">
                    <div className="summary-item">
                      <span>Services Queried:</span>
                      <span>{queryResult.services_queried?.join(', ')}</span>
                    </div>
                    <div className="summary-item">
                      <span>Timestamp:</span>
                      <span>{new Date(queryResult.timestamp).toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="service-responses">
                    {Object.entries(queryResult.responses || {}).map(([service, response]) => (
                      <div key={service} className="service-response">
                        <div className="response-header">
                          <span className="service-name">
                            {getServiceIcon(service)} {service}
                          </span>
                          <div className="response-meta">
                            <span className={`status ${response.status}`}>{response.status}</span>
                            <span className="quality">Quality: {(response.quality_score * 100).toFixed(0)}%</span>
                            <span className="refinements">Refinements: {response.refinement_count}</span>
                          </div>
                        </div>
                        <div className="response-content">
                          <pre>{formatResponse(response.parsed_output || response.content)}</pre>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WebServicesPanel;