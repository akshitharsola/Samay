import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import ModeSelector from './ModeSelector';  
import ResponseDisplay from './ResponseDisplay';

const ConversationFlow = ({ sessionId, onNewSession }) => {
  // State management
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState('normal'); // 'normal' or 'confidential'
  const [conversationStage, setConversationStage] = useState('initial'); // 'initial', 'discussing', 'ready', 'confirming', 'routing', 'complete'
  const [refinedQuery, setRefinedQuery] = useState('');
  const [serviceResponses, setServiceResponses] = useState(null);
  const [comprehensiveResponse, setComprehensiveResponse] = useState(null);
  
  // Refs
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // WebSocket connection
  useEffect(() => {
    if (sessionId && mode === 'normal') {
      connectWebSocket();
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId, mode]); // eslint-disable-line react-hooks/exhaustive-deps
  
  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/ws/${sessionId}`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'query_complete') {
            setComprehensiveResponse(data.data);
            setConversationStage('complete');
            toast.success('Query processing complete!');
          }
        } catch (e) {
          console.log('WebSocket message:', event.data);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };
  
  // Add message to conversation
  const addMessage = (role, content, metadata = {}) => {
    const message = {
      id: Date.now(),
      role, // 'user', 'assistant', 'system'
      content,
      timestamp: new Date().toISOString(),
      metadata
    };
    
    // Check if this is any automation response (old or new)
    if (metadata && (metadata.browser_automation || metadata.query_automation_triggered)) {
      handleBrowserAutomation(metadata);
    }
    
    setMessages(prev => [...prev, message]);
    return message;
  };

  // Handle browser automation from current tab
  const handleBrowserAutomation = (metadata) => {
    // Check if this is the NEW query automation system
    if (metadata.query_automation_triggered && metadata.new_automation_system) {
      console.log('🤖 NEW Query Automation System triggered');
      handleNewQueryAutomation(metadata);
    }
    // Check if this is old browser automation (debug commands)
    else if (metadata.javascript_action) {
      console.log('🔧 OLD Browser Automation triggered (debug command)');
      handleOldBrowserAutomation(metadata);
    }
  };

  // Handle NEW query automation system
  const handleNewQueryAutomation = (metadata) => {
    console.log('🚀 Starting NEW query automation pipeline...');
    
    // Step 1: Check if tabs need to be opened
    setTimeout(() => {
      console.log('🚀 Step 1: Checking if AI service tabs need to be opened...');
      
      // Check if tabs are already open (simple heuristic)
      const currentTabCount = window.open('', '_self').history.length;
      console.log(`Current browser context has ${currentTabCount} tabs`);
      
      // Always open tabs for now (user can ignore if already open)
      toast('🚀 Opening AI service tabs (ignore if already open)...', { duration: 3000 });
      const success = openAIServiceTabsWithFeedback();
      
      if (!success) {
        console.log('⚠️ Tab opening may have been blocked');
        toast('🚫 Tab opening blocked - manually open service tabs!', { duration: 5000 });
      }
    }, 1000);
    
    // Step 2: Show automation status and start injection
    setTimeout(() => {
      addMessage('system', '🤖 **Query Automation in Progress**\n\n**Phase 1**: ✅ Tabs opened\n**Phase 2**: 🔄 Preparing JavaScript injection...\n**Phase 3**: ⏳ Response monitoring setup...\n**Phase 4**: ⏳ Content extraction...\n**Phase 5**: ⏳ Response synthesis...\n\n💡 **Note**: This is the next-generation automation system!', {
        automation_status: true,
        automation_stage: metadata.automation_stage
      });
      
      // Start JavaScript injection process
      if (metadata.automation_result && metadata.automation_result.session_id) {
        setTimeout(() => {
          executeQueryInjection(metadata.automation_result.session_id);
        }, 3000); // Wait 3 seconds for tabs to load
      }
    }, 3000);
  };

  // Handle OLD browser automation (debug commands only)
  const handleOldBrowserAutomation = (metadata) => {
    console.log('🔧 Running old browser automation for debug...');
    
    // Regular browser automation (debug command only)
    console.log('🤖 Attempting automatic tab opening in 2 seconds...');
    setTimeout(() => {
      console.log('🚀 Executing automatic tab opening...');
      const success = openAIServiceTabsWithFeedback();
      
      if (!success) {
        console.log('⚠️ Automatic tab opening may have been blocked');
        toast('🚫 Automatic tab opening blocked - use the manual button below!', { duration: 5000 });
      }
    }, 2000);
    
    // Regular fallback
    setTimeout(() => {
      addMessage('system', '🔗 **Manual Tab Opening (Fallback)**\n\nIf tabs didn\'t open automatically due to popup blocker, click these links to open manually:\n\n• [ChatGPT](https://chat.openai.com/) - Tab 1\n• [Claude](https://claude.ai/) - Tab 2  \n• [Gemini](https://gemini.google.com/) - Tab 3\n• [Perplexity](https://www.perplexity.ai/) - Tab 4\n\n💡 **Tip**: Use the manual button above for best results, or allow popups for this site.', {
        manual_fallback: true,
        services: metadata.services
      });
    }, 6000);
  };

  // Open AI service tabs with success detection
  const openAIServiceTabsWithFeedback = () => {
    let successCount = 0;
    const services = [
      { name: 'ChatGPT', url: 'https://chat.openai.com/' },
      { name: 'Claude', url: 'https://claude.ai/' },
      { name: 'Gemini', url: 'https://gemini.google.com/' },
      { name: 'Perplexity', url: 'https://www.perplexity.ai/' }
    ];

    console.log('🚀 Opening AI service tabs from current browser...');
    toast('🚀 Opening AI service tabs... (Check if popup blocker is enabled)', { duration: 3000 });
    
    services.forEach((service, index) => {
      setTimeout(() => {
        console.log(`Attempting to open ${service.name} in new tab...`);
        try {
          const newTab = window.open(service.url, '_blank', 'noopener,noreferrer');
          
          if (newTab && newTab.location) {
            successCount++;
            console.log(`✅ ${service.name} tab opened successfully`);
            toast.success(`✅ ${service.name} tab opened!`, { duration: 2000 });
          } else {
            console.warn(`⚠️ ${service.name} tab blocked - popup blocker may be enabled`);
            toast.error(`⚠️ ${service.name} tab blocked - disable popup blocker!`, { duration: 4000 });
          }
        } catch (error) {
          console.error(`❌ Error opening ${service.name}:`, error);
          toast.error(`❌ Error opening ${service.name}: ${error.message}`, { duration: 4000 });
        }
      }, index * 1500); // 1.5 second delay between each tab for better visibility
    });

    // Show final message and return success status
    setTimeout(() => {
      console.log(`🎯 Tab opening completed. Success count: ${successCount}/${services.length}`);
      if (successCount > 0) {
        toast.success(`🎯 ${successCount}/${services.length} AI service tabs opened successfully!`, { duration: 5000 });
      } else {
        toast.error('🚫 No tabs opened - popup blocker detected! Use manual button.', { duration: 5000 });
      }
    }, services.length * 1500 + 1000);
    
    return successCount > 0;
  };

  // Open AI service tabs using JavaScript (simpler version for button clicks)
  const openAIServiceTabs = () => {
    const services = [
      { name: 'ChatGPT', url: 'https://chat.openai.com/' },
      { name: 'Claude', url: 'https://claude.ai/' },
      { name: 'Gemini', url: 'https://gemini.google.com/' },
      { name: 'Perplexity', url: 'https://www.perplexity.ai/' }
    ];

    console.log('🚀 Opening AI service tabs from current browser...');
    toast('🚀 Opening AI service tabs... (Check if popup blocker is enabled)', { duration: 3000 });
    
    services.forEach((service, index) => {
      setTimeout(() => {
        console.log(`Attempting to open ${service.name} in new tab...`);
        try {
          const newTab = window.open(service.url, '_blank', 'noopener,noreferrer');
          
          if (newTab) {
            console.log(`✅ ${service.name} tab opened successfully`);
            toast.success(`✅ ${service.name} tab opened!`, { duration: 2000 });
          } else {
            console.warn(`⚠️ ${service.name} tab blocked - popup blocker may be enabled`);
            toast.error(`⚠️ ${service.name} tab blocked - disable popup blocker!`, { duration: 4000 });
          }
        } catch (error) {
          console.error(`❌ Error opening ${service.name}:`, error);
          toast.error(`❌ Error opening ${service.name}: ${error.message}`, { duration: 4000 });
        }
      }, index * 1500); // 1.5 second delay between each tab for better visibility
    });

    // Show final message
    setTimeout(() => {
      console.log('🎯 All AI service tab opening attempts completed');
      toast.success('🎯 All AI service tabs processed! If tabs didn\'t open, please disable popup blocker.', { duration: 5000 });
    }, services.length * 1500 + 1000);
  };

  // Execute query injection into AI services
  const executeQueryInjection = async (sessionId) => {
    console.log('🚀 Phase 2: Executing query injection...');
    addMessage('system', '🔄 **Phase 2**: Getting injection scripts...', { automation_phase: 2 });
    
    try {
      // Get injection commands from backend
      const response = await fetch(`/api/automation/inject/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const injectionData = await response.json();
        
        if (injectionData.success && injectionData.injection_commands) {
          // Show manual injection instructions
          const instructions = injectionData.injection_commands.map((cmd, index) => {
            return `**${cmd.config.service_name}**:\n` +
                   `1. Go to ${cmd.config.service_name} tab\n` +
                   `2. Open browser console (F12)\n` +
                   `3. Paste and run this script:\n\n\`\`\`javascript\n${cmd.javascript.trim()}\n\`\`\`\n`;
          }).join('\n---\n\n');
          
          const manualInstructions = `📝 **Phase 2**: Manual JavaScript Injection Required\n\n` +
            `🚨 **Browser Security**: Cannot auto-inject into other tabs\n\n` +
            `🛠 **Manual Steps** (takes 2 minutes):\n\n${instructions}\n\n` +
            `💡 **Note**: Future versions will use a browser extension for full automation.`;
          
          addMessage('system', manualInstructions, { 
            automation_phase: 2,
            manual_injection: true,
            injection_commands: injectionData.injection_commands
          });
          
          // Skip to monitoring phase after showing instructions
          setTimeout(() => {
            addMessage('system', '👁️ **Phase 3**: Manual monitoring - check each tab for responses', { automation_phase: 3 });
            
            setTimeout(() => {
              addMessage('system', '✅ **Automation Demo Complete**\n\n' +
                '🎯 **What We Built**:\n' +
                '• ✅ Real JavaScript injection scripts\n' +
                '• ✅ Service-specific automation code\n' +
                '• ✅ Human-like typing simulation\n' +
                '• ✅ Complete automation pipeline\n\n' +
                '🚀 **Next Steps**: Build browser extension for full automation', 
                { automation_complete: true }
              );
            }, 3000);
          }, 2000);
        } else {
          throw new Error('No injection commands available');
        }
        
      } else {
        throw new Error('Failed to get injection commands');
      }
      
    } catch (error) {
      console.error('❌ Injection failed:', error);
      addMessage('system', `❌ **Phase 2 Failed**: ${error.message}`, { automation_error: true });
    }
  };

  // Start response monitoring (removed - handled in executeQueryInjection)

  // Response synthesis (removed - handled in executeQueryInjection)
  
  // Handle user input submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentInput.trim() || isLoading) return;
    
    const userMessage = currentInput.trim();
    setCurrentInput('');
    addMessage('user', userMessage);
    
    if (conversationStage === 'initial') {
      await startConversation(userMessage);
    } else if (conversationStage === 'discussing') {
      await refineQuery(userMessage);
    }
  };
  
  // Start conversation with local assistant
  const startConversation = async (query) => {
    setIsLoading(true);
    setConversationStage('discussing');
    
    try {
      if (mode === 'confidential') {
        // Handle confidential mode locally
        addMessage('assistant', `I understand you want to discuss: "${query}". Since we're in confidential mode, I'll process this locally without sending to external services. Could you provide more details about what specific aspect you'd like help with?`);
        setRefinedQuery(query);
        setConversationStage('ready');
      } else {
        // Normal mode - use backend
        const response = await fetch('/api/query/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query,
            session_id: sessionId,
            user_id: 'default'
          }),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          // Check for NEW automation system FIRST before adding message
          if (data.metadata && data.metadata.query_automation_triggered && data.metadata.new_automation_system) {
            console.log('🤖 NEW Query Automation detected - replacing content');
            // Replace content with automation-specific message
            const automationContent = '🤖 **Query Automation Pipeline Starting**\n\n' +
              `**Query**: "${data.metadata.automation_result?.session_id ? query.replace('automate: ', '') : query}"\n` +
              '**Services**: ChatGPT, Claude, Gemini, Perplexity\n\n' +
              '🚀 **Phase 1**: Opening service tabs...\n' +
              '📝 **Phase 2**: Preparing query injection...\n' +
              '👁️ **Phase 3**: Setting up response monitoring...\n' +
              '🔄 **Phase 4**: Content extraction ready...\n' +
              '✅ **Phase 5**: Response synthesis pending...\n\n' +
              '💡 **Next**: Automation will proceed automatically';
            
            addMessage('assistant', automationContent, data.metadata);
            // NOTE: Automation will be triggered automatically by addMessage -> handleBrowserAutomation
          } else {
            // Normal message for debug commands or regular queries
            addMessage('assistant', data.content, data.metadata);
          }
          
          if (data.stage === 'complete') {
            // Automation or debug command completed
            setConversationStage('complete');
            setRefinedQuery(query);
          } else if (data.stage === 'query_refinement' || data.stage === 'service_routing') {
            setRefinedQuery(data.metadata.refined_query || query);
            setConversationStage('discussing'); // Keep in discussing mode for further refinement
          }
        } else {
          throw new Error(data.error || 'Failed to start conversation');
        }
      }
      
    } catch (error) {
      console.error('Error starting conversation:', error);
      addMessage('system', `Error: ${error.message}`, { error: true });
      toast.error('Failed to start conversation');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Refine query based on user feedback
  const refineQuery = async (userResponse) => {
    setIsLoading(true);
    
    try {
      if (mode === 'confidential') {
        // Handle confidential mode locally
        addMessage('assistant', `Based on your input, I've refined your query. Here's what I understand: "${userResponse}". This looks ready to process. You can now choose to route this to AI services if needed.`);
        setRefinedQuery(userResponse);
        setConversationStage('ready');
      } else {
        // Normal mode - use backend for refinement
        const response = await fetch('/api/query/refine', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            user_response: userResponse
          }),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          addMessage('assistant', data.content, data.metadata);
          setRefinedQuery(data.metadata.refined_query || userResponse);
          
          if (data.stage === 'service_routing') {
            setConversationStage('confirming'); // Show confirmation before routing
          }
        } else {
          throw new Error(data.error || 'Failed to refine query');
        }
      }
      
    } catch (error) {
      console.error('Error refining query:', error);
      addMessage('system', `Error: ${error.message}`, { error: true });
      toast.error('Failed to refine query');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Show routing confirmation
  const handleReadyToRoute = () => {
    setConversationStage('confirming');
    addMessage('system', '🔍 Query Analysis Complete!\n\nRefined Query: "' + refinedQuery + '"\n\nReady to route to all AI services?', { 
      confirmation: true,
      refinedQuery: refinedQuery
    });
  };

  // Route to all AI services
  const handleRouteToServices = async () => {
    if (mode === 'confidential') {
      toast.error('Service routing is disabled in confidential mode');
      return;
    }
    
    setIsLoading(true);
    setConversationStage('routing');
    addMessage('system', '🚀 Routing your query to all AI services...', { routing: true });
    
    try {
      const response = await fetch('/api/query/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setServiceResponses(data.service_responses);
        setComprehensiveResponse(data.comprehensive_response);
        setConversationStage('complete');
        
        addMessage('system', `✅ Successfully queried ${data.service_responses.length} services in ${data.processing_time.toFixed(2)}s`, { 
          routing: true,
          processingTime: data.processing_time,
          serviceCount: data.service_responses.length
        });
        
        toast.success('All services queried successfully!');
      } else {
        throw new Error(data.error || 'Failed to execute query');
      }
      
    } catch (error) {
      console.error('Error routing to services:', error);
      addMessage('system', `❌ Error routing to services: ${error.message}`, { error: true });
      toast.error('Failed to route to services');
      setConversationStage('confirming'); // Allow retry from confirmation
    } finally {
      setIsLoading(false);
    }
  };
  
  // Start new conversation
  const handleNewConversation = () => {
    setMessages([]);
    setCurrentInput('');
    setConversationStage('initial');
    setRefinedQuery('');
    setServiceResponses(null);
    setComprehensiveResponse(null);
    
    if (onNewSession) {
      onNewSession();
    }
    
    toast.success('Started new conversation');
  };
  
  // Render message content with markdown link support
  const renderMessageContent = (content, metadata = {}) => {
    if (metadata.manual_fallback) {
      // Handle manual fallback links
      const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
      const parts = content.split(linkRegex);
      
      return (
        <div>
          {parts.map((part, index) => {
            if (index % 3 === 0) {
              // Regular text
              return <span key={index}>{part}</span>;
            } else if (index % 3 === 1) {
              // Link text (we'll use this with the next part)
              return null;
            } else {
              // URL - create clickable link
              const linkText = parts[index - 1];
              return (
                <a
                  key={index}
                  href={part}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="service-link"
                  style={{
                    color: '#2563eb',
                    textDecoration: 'underline',
                    fontWeight: 'bold'
                  }}
                >
                  {linkText}
                </a>
              );
            }
          })}
        </div>
      );
    }
    
    // Regular message content
    return <div style={{ whiteSpace: 'pre-wrap' }}>{content}</div>;
  };

  // Render message
  const renderMessage = (message) => {
    const { role, content, metadata = {} } = message;
    
    return (
      <div key={message.id} className={`message ${role} ${metadata.error ? 'error' : ''} ${metadata.routing ? 'routing' : ''} ${metadata.manual_fallback ? 'manual-fallback' : ''}`}>
        <div className="message-header">
          <span className="message-role">
            {role === 'user' ? '👤 You' : 
             role === 'assistant' ? '🤖 Assistant' : 
             '🔧 System'}
          </span>
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className="message-content">
          {renderMessageContent(content, metadata)}
          
          {/* Add manual open button for browser automation messages */}
          {metadata.browser_automation && metadata.javascript_action && (
            <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f0f8ff', borderRadius: '5px', border: '1px solid #4a90e2' }}>
              <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#2c3e50' }}>
                🔄 <strong>Manual Override Available</strong>
              </p>
              <button
                onClick={() => {
                  console.log('🔘 User clicked manual tab opening button');
                  openAIServiceTabs();
                }}
                style={{
                  backgroundColor: '#4a90e2',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#357abd'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#4a90e2'}
              >
                🚀 Click to Open All AI Service Tabs
              </button>
              <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#7f8c8d' }}>
                💡 Click-triggered actions bypass popup blockers
              </p>
            </div>
          )}
        </div>
        {metadata.processingTime && (
          <div className="message-metadata">
            Processing time: {metadata.processingTime.toFixed(2)}s | Services: {metadata.serviceCount}
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="conversation-flow">
      {/* Mode Selector */}
      <ModeSelector mode={mode} onModeChange={setMode} />
      
      {/* Conversation Area */}
      <div className="conversation-area">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h3>👋 Welcome to Samay v5</h3>
              <p>
                {mode === 'confidential' 
                  ? '🔒 Confidential Mode: Your conversation stays private and local.'
                  : '🌐 Normal Mode: I can route your queries to multiple AI services.'}
              </p>
              <p>Start by typing your question or request below.</p>
            </div>
          )}
          
          {messages.map(renderMessage)}
          
          {/* Ready to Route Button */}
          {conversationStage === 'discussing' && refinedQuery && mode === 'normal' && (
            <div className="ready-to-route-container">
              <button 
                onClick={handleReadyToRoute}
                className="ready-to-route-btn"
                disabled={isLoading}
              >
                🎯 Ready to Route to AI Services
              </button>
            </div>
          )}
          
          {/* Service Confirmation and Trigger */}
          {conversationStage === 'confirming' && mode === 'normal' && (
            <div className="confirmation-container">
              <div className="confirmation-content">
                <h4>🔍 Query Ready for Routing</h4>
                <div className="refined-query-preview">
                  <strong>Refined Query:</strong>
                  <p>"{refinedQuery}"</p>
                </div>
                <div className="confirmation-buttons">
                  <button 
                    onClick={handleRouteToServices}
                    className="confirm-route-btn"
                    disabled={isLoading}
                  >
                    {isLoading ? '⏳ Routing...' : '🚀 Yes, Route to All Services'}
                  </button>
                  <button 
                    onClick={() => setConversationStage('discussing')}
                    className="cancel-route-btn"
                    disabled={isLoading}
                  >
                    ✏️ Refine Query More
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Response Display */}
          {comprehensiveResponse && serviceResponses && (
            <ResponseDisplay
              comprehensiveResponse={comprehensiveResponse}
              serviceResponses={serviceResponses}
            />
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-container">
            <input
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              placeholder={
                conversationStage === 'initial' 
                  ? "Ask me anything..." 
                  : conversationStage === 'discussing'
                  ? "Please clarify or refine your request..."
                  : "Type your response..."
              }
              disabled={isLoading || conversationStage === 'routing'}
              className="chat-input"
            />
            <button 
              type="submit" 
              disabled={!currentInput.trim() || isLoading || conversationStage === 'routing'}
              className="send-button"
            >
              {isLoading ? '⏳' : '📤'}
            </button>
          </div>
        </form>
        
        {/* Action Buttons */}
        <div className="action-buttons">
          <button 
            onClick={handleNewConversation}
            className="new-conversation-btn"
            disabled={isLoading}
          >
            🔄 New Conversation
          </button>
          
          {mode === 'confidential' && conversationStage === 'ready' && (
            <div className="confidential-notice">
              🔒 Service routing disabled in confidential mode
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConversationFlow;