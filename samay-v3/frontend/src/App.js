import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, 
  Bot, 
  User, 
  Shield, 
  Cloud, 
  Home,
  CheckCircle,
  XCircle,
  Download
} from 'lucide-react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => 'session-' + Math.random().toString(36).substr(2, 9));
  const [, setWebsocket] = useState(null);
  const [services, setServices] = useState({});
  const [selectedServices, setSelectedServices] = useState(['claude', 'gemini', 'perplexity']);
  const [confidentialMode, setConfidentialMode] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const messagesEndRef = useRef(null);

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'result':
        setIsLoading(false);
        addMessage('assistant', formatMultiAgentResponse(message.data), message.data);
        break;
      case 'error':
        setIsLoading(false);
        addMessage('error', `Error: ${message.data.message}`);
        break;
      case 'status':
        // Handle status updates (e.g., show progress)
        console.log('Status:', message.data.message);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWebsocket(ws);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWebsocket(null);
    };
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [sessionId, handleWebSocketMessage]);

  // Fetch initial data
  useEffect(() => {
    fetchServices();
    fetchSystemHealth();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'result':
        setIsLoading(false);
        addMessage('assistant', formatMultiAgentResponse(message.data), message.data);
        break;
      case 'error':
        setIsLoading(false);
        addMessage('error', `Error: ${message.data.message}`);
        break;
      case 'status':
        // Handle status updates (e.g., show progress)
        console.log('Status:', message.data.message);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await axios.get('/services');
      setServices(response.data.services);
    } catch (error) {
      console.error('Failed to fetch services:', error);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await axios.get('/health');
      setSystemHealth(response.data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };

  const addMessage = (sender, content, metadata = null) => {
    const newMessage = {
      id: Date.now(),
      sender,
      content,
      metadata,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const formatMultiAgentResponse = (data) => {
    const responses = data.responses || [];
    let formatted = `**Multi-Agent Response** (${data.total_time?.toFixed(1)}s)\n\n`;
    
    responses.forEach(response => {
      const status = response.success ? '✅' : '❌';
      const serviceName = response.service === 'local_phi3' ? '🏠 Local LLM' : `☁️ ${response.service.charAt(0).toUpperCase() + response.service.slice(1)}`;
      
      formatted += `${status} **${serviceName}** (${response.execution_time?.toFixed(1)}s)\n`;
      
      if (response.success) {
        formatted += `${response.response}\n\n`;
      } else {
        formatted += `*Error: ${response.error}*\n\n`;
      }
    });
    
    return formatted;
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message to chat
    addMessage('user', userMessage);

    try {
      await axios.post('/query', {
        prompt: userMessage,
        services: confidentialMode ? null : selectedServices,
        confidential: confidentialMode,
        session_id: sessionId
      });

      // Response will come via WebSocket, so we don't need to handle it here
    } catch (error) {
      setIsLoading(false);
      addMessage('error', `Failed to send message: ${error.message}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const ServiceStatus = ({ service, info }) => {
    const isReady = info.ready;
    return (
      <div className={`service-status ${isReady ? 'ready' : 'not-ready'}`}>
        {isReady ? <CheckCircle size={16} /> : <XCircle size={16} />}
        <span>{service.charAt(0).toUpperCase() + service.slice(1)}</span>
      </div>
    );
  };

  const MessageBubble = ({ message }) => {
    const isUser = message.sender === 'user';
    const isError = message.sender === 'error';
    
    return (
      <div className={`message ${isUser ? 'user' : isError ? 'error' : 'assistant'}`}>
        <div className="message-header">
          {isUser ? <User size={16} /> : isError ? <XCircle size={16} /> : <Bot size={16} />}
          <span className="message-time">{message.timestamp}</span>
        </div>
        <div className="message-content">
          {message.content.split('\n').map((line, i) => (
            <div key={i}>
              {line.startsWith('**') && line.endsWith('**') ? (
                <strong>{line.slice(2, -2)}</strong>
              ) : line.startsWith('*') && line.endsWith('*') ? (
                <em>{line.slice(1, -1)}</em>
              ) : (
                line
              )}
            </div>
          ))}
        </div>
        {message.metadata && (
          <div className="message-metadata">
            <button onClick={() => console.log(message.metadata)}>
              <Download size={14} />
              View Reports
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-title">
          <Bot size={24} />
          <h1>Samay v3</h1>
          <span className="subtitle">Multi-Agent AI Assistant</span>
        </div>
        
        <div className="header-controls">
          {systemHealth && (
            <div className="system-status">
              <div className={`status-indicator ${systemHealth.status}`} />
              <span>{systemHealth.status}</span>
            </div>
          )}
        </div>
      </header>

      <div className="app-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>🎯 Mode</h3>
            <div className="mode-toggle">
              <button 
                className={!confidentialMode ? 'active' : ''}
                onClick={() => setConfidentialMode(false)}
              >
                <Cloud size={16} />
                Multi-Agent
              </button>
              <button 
                className={confidentialMode ? 'active' : ''}
                onClick={() => setConfidentialMode(true)}
              >
                <Shield size={16} />
                Confidential
              </button>
            </div>
          </div>

          {!confidentialMode && (
            <div className="sidebar-section">
              <h3>☁️ Services</h3>
              <div className="service-list">
                {Object.entries(services).map(([service, info]) => (
                  <label key={service} className="service-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedServices.includes(service)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedServices([...selectedServices, service]);
                        } else {
                          setSelectedServices(selectedServices.filter(s => s !== service));
                        }
                      }}
                      disabled={!info.ready}
                    />
                    <ServiceStatus service={service} info={info} />
                  </label>
                ))}
              </div>
            </div>
          )}

          {confidentialMode && (
            <div className="sidebar-section">
              <h3>🏠 Local Processing</h3>
              <div className="local-info">
                <Home size={16} />
                <span>Phi-3-Mini Model</span>
                <div className="local-status ready">
                  <CheckCircle size={12} />
                  Ready
                </div>
              </div>
            </div>
          )}

          <div className="sidebar-section">
            <h3>📊 Session</h3>
            <div className="session-info">
              <div>ID: {sessionId.slice(-8)}</div>
              <div>Messages: {messages.length}</div>
              <button onClick={() => setMessages([])}>Clear History</button>
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="chat-area">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-message">
                <Bot size={48} />
                <h2>Welcome to Samay v3</h2>
                <p>Your multi-agent AI assistant with both cloud and local processing capabilities.</p>
                <div className="welcome-features">
                  <div>☁️ Multi-Agent: Query Claude, Gemini, and Perplexity in parallel</div>
                  <div>🔒 Confidential: Process sensitive data locally with Phi-3-Mini</div>
                  <div>📊 Comprehensive: Get detailed reports and comparisons</div>
                </div>
              </div>
            )}
            
            {messages.map(message => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {isLoading && (
              <div className="loading-message">
                <div className="loading-spinner"></div>
                <span>
                  {confidentialMode 
                    ? 'Processing locally with Phi-3-Mini...' 
                    : `Querying ${selectedServices.length} AI services...`
                  }
                </span>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="input-area">
            <div className="input-container">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  confidentialMode 
                    ? "Enter confidential prompt (processed locally)..." 
                    : "Ask me anything..."
                }
                disabled={isLoading}
                rows={1}
              />
              <button 
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="send-button"
              >
                <Send size={20} />
              </button>
            </div>
            
            <div className="input-info">
              {confidentialMode ? (
                <span className="confidential-notice">
                  <Shield size={12} />
                  Confidential mode: Data processed locally only
                </span>
              ) : (
                <span className="service-notice">
                  <Cloud size={12} />
                  Multi-agent mode: {selectedServices.length} services selected
                </span>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;