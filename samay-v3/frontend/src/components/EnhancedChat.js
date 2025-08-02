import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Lightbulb,
  CheckSquare,
  Clock,
  TrendingUp,
  AlertCircle,
  Zap,
  Brain
} from 'lucide-react';
import axios from 'axios';

const EnhancedChat = ({ sessionId }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load conversation history
    loadConversationHistory();
    // Get initial suggestions
    fetchProactiveSuggestions();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversationHistory = async () => {
    try {
      const response = await axios.get(`/conversation/${sessionId}`);
      if (response.data.history) {
        const formattedMessages = response.data.history.map(entry => ({
          id: Date.now() + Math.random(),
          sender: entry.type === 'query' ? 'user' : 'assistant',
          content: entry.type === 'query' ? entry.content : formatCompanionResponse(entry.content),
          timestamp: new Date(entry.timestamp).toLocaleTimeString(),
          metadata: entry.type === 'response' ? entry.content : null
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  const fetchProactiveSuggestions = async () => {
    try {
      const response = await axios.post('/assistant/suggestions', {
        current_activity: 'chatting',
        focus_state: 'focused',
        energy_level: 8,
        mood: 'curious',
        location: 'office',
        time_of_day: getCurrentTimeOfDay(),
        workload_status: 'moderate'
      });
      setSuggestions(response.data.suggestions.slice(0, 3));
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const getCurrentTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    return 'evening';
  };

  const formatCompanionResponse = (responseData) => {
    if (typeof responseData === 'string') return responseData;
    
    if (responseData.content) {
      return responseData.content;
    }
    
    return JSON.stringify(responseData, null, 2);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message to chat
    addMessage('user', userMessage);

    try {
      const response = await axios.post('/companion/chat', {
        message: userMessage,
        include_suggestions: true,
        session_id: sessionId
      });

      // Add companion response
      addMessage('assistant', response.data.response.content, response.data);
      
      // Update suggestions if provided
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setSuggestions(response.data.suggestions.slice(0, 3));
      }

    } catch (error) {
      addMessage('error', `Failed to send message: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (sender, content, metadata = null) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      sender,
      content,
      metadata,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const applySuggestion = (suggestion) => {
    setInputMessage(suggestion.content);
    setShowSuggestions(false);
  };

  const acknowledgeSuggestion = async (suggestionId, helpful) => {
    try {
      await axios.post(`/assistant/acknowledge/${suggestionId}?helpful=${helpful}`);
      setSuggestions(prev => prev.filter(s => s.suggestion_id !== suggestionId));
    } catch (error) {
      console.error('Failed to acknowledge suggestion:', error);
    }
  };

  const getSuggestionIcon = (category) => {
    switch (category) {
      case 'task': return <CheckSquare size={14} />;
      case 'productivity': return <TrendingUp size={14} />;
      case 'break': return <Clock size={14} />;
      case 'deadline': return <AlertCircle size={14} />;
      case 'workflow': return <Zap size={14} />;
      default: return <Lightbulb size={14} />;
    }
  };

  const MessageBubble = ({ message }) => {
    const isUser = message.sender === 'user';
    const isError = message.sender === 'error';
    
    return (
      <div className={`message ${isUser ? 'user' : isError ? 'error' : 'assistant'}`}>
        <div className="message-header">
          {isUser ? <User size={16} /> : isError ? <AlertCircle size={16} /> : <Brain size={16} />}
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
        {message.metadata?.suggestions && (
          <div className="message-suggestions">
            <div className="suggestions-header">
              <Lightbulb size={14} />
              <span>Proactive Suggestions</span>
            </div>
            {message.metadata.suggestions.slice(0, 2).map((suggestion, index) => (
              <div key={index} className="inline-suggestion">
                {getSuggestionIcon(suggestion.category)}
                <span>{suggestion.content}</span>
                <button onClick={() => applySuggestion(suggestion)}>Apply</button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="enhanced-chat">
      <div className="chat-header">
        <div className="header-title">
          <Brain size={20} />
          <h3>Enhanced Companion Chat</h3>
        </div>
        <div className="chat-controls">
          <button 
            className={`suggestions-toggle ${showSuggestions ? 'active' : ''}`}
            onClick={() => setShowSuggestions(!showSuggestions)}
          >
            <Lightbulb size={16} />
            Suggestions
          </button>
          <button onClick={() => setMessages([])} className="clear-btn">
            Clear
          </button>
        </div>
      </div>

      <div className="chat-container">
        {/* Proactive Suggestions Panel */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="suggestions-panel">
            <div className="suggestions-header">
              <Lightbulb size={16} />
              <span>Smart Suggestions</span>
            </div>
            <div className="suggestions-list">
              {suggestions.map((suggestion, index) => (
                <div key={suggestion.suggestion_id || index} className="suggestion-card">
                  <div className="suggestion-content">
                    <div className="suggestion-meta">
                      {getSuggestionIcon(suggestion.category)}
                      <span className="category">{suggestion.category}</span>
                      <span className={`priority ${suggestion.priority}`}>
                        {suggestion.priority}
                      </span>
                    </div>
                    <p>{suggestion.content}</p>
                    <div className="suggestion-confidence">
                      {(suggestion.relevance_score * 100).toFixed(0)}% relevant
                    </div>
                  </div>
                  <div className="suggestion-actions">
                    <button 
                      className="apply-btn"
                      onClick={() => applySuggestion(suggestion)}
                    >
                      Apply
                    </button>
                    <button 
                      className="helpful-btn"
                      onClick={() => acknowledgeSuggestion(suggestion.suggestion_id, true)}
                    >
                      👍
                    </button>
                    <button 
                      className="dismiss-btn"
                      onClick={() => acknowledgeSuggestion(suggestion.suggestion_id, false)}
                    >
                      👎
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <Brain size={48} />
              <h2>Enhanced Companion Chat</h2>
              <p>Your intelligent companion with memory, personality, and proactive assistance.</p>
              <div className="welcome-features">
                <div>🧠 Persistent memory across conversations</div>
                <div>🎭 Adaptive personality that learns your preferences</div>
                <div>💡 Proactive suggestions based on context</div>
                <div>📅 Integrated with task scheduling and automation</div>
              </div>
            </div>
          )}
          
          {messages.map(message => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <div className="loading-message">
              <div className="loading-spinner"></div>
              <span>Companion is thinking...</span>
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
              placeholder="Chat with your intelligent companion..."
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
            <span className="companion-notice">
              <Brain size={12} />
              Enhanced mode: Memory, personality, and proactive assistance active
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedChat;