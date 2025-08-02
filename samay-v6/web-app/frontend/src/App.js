import React, { useState, useEffect, useCallback } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import QueryInput from './components/QueryInput';
import AutomationStatus from './components/AutomationStatus';
import ResponseViewer from './components/ResponseViewer';
import ExtensionConnector from './components/ExtensionConnector';
import ServiceStatusIndicator from './components/ServiceStatusIndicator';

import { useExtensionCommunication } from './hooks/useExtensionCommunication';
import { useWebSocket } from './hooks/useWebSocket';

import './App.css';

function App() {
  // State management
  const [currentQuery, setCurrentQuery] = useState('');
  const [automationStatus, setAutomationStatus] = useState('idle'); // idle, starting, running, complete, error
  const [sessionId, setSessionId] = useState(null);
  const [responses, setResponses] = useState({});
  const [synthesis, setSynthesis] = useState('');
  const [isExtensionConnected, setIsExtensionConnected] = useState(false);
  const [backendHealth, setBackendHealth] = useState('checking');

  // Custom hooks
  const { sendToExtension, extensionMessage } = useExtensionCommunication();
  const { wsStatus } = useWebSocket(sessionId);

  // Define functions first
  const checkBackendHealth = async () => {
    try {
      const response = await fetch('/health');
      const data = await response.json();
      setBackendHealth(data.status === 'healthy' ? 'healthy' : 'degraded');
    } catch (error) {
      console.error('Backend health check failed:', error);
      setBackendHealth('error');
      toast.error('Backend connection failed');
    }
  };

  const createFallbackSynthesis = useCallback((responses) => {
    let fallback = '# Multi-AI Response Summary\n\n';
    Object.entries(responses).forEach(([service, data]) => {
      const content = typeof data === 'string' ? data : data.content;
      fallback += `## ${service.toUpperCase()}\n${content}\n\n`;
    });
    return fallback;
  }, []);

  const generateSynthesis = useCallback(async (responses) => {
    try {
      console.log('🎯 Generating synthesis...');
      
      // Convert responses to required format
      const serviceResponses = Object.entries(responses).map(([service, data]) => ({
        service: service,
        content: typeof data === 'string' ? data : data.content,
        timestamp: new Date().toISOString(),
        word_count: (typeof data === 'string' ? data : data.content).split(' ').length,
        success: true
      }));

      const synthesisResponse = await fetch('/api/synthesis/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          responses: serviceResponses
        }),
      });

      if (!synthesisResponse.ok) {
        throw new Error(`Synthesis failed: ${synthesisResponse.status}`);
      }

      const synthesisData = await synthesisResponse.json();
      setSynthesis(synthesisData.synthesis);
      toast.success('Synthesis generated successfully!');

    } catch (error) {
      console.error('❌ Synthesis generation failed:', error);
      toast.error(`Synthesis failed: ${error.message}`);
      // Create fallback synthesis
      const fallback = createFallbackSynthesis(responses);
      setSynthesis(fallback);
    }
  }, [sessionId, createFallbackSynthesis]);

  const handleExtensionMessage = useCallback((message) => {
    console.log('📨 Extension message received:', message);
    
    switch (message.action) {
      case 'automationProgress':
        setAutomationStatus('running');
        toast.info(`Progress: ${Object.keys(message.progress).length} services processing`);
        break;
        
      case 'automationComplete':
        setAutomationStatus('complete');
        setResponses(message.responses);
        toast.success('Automation completed successfully!');
        
        // Trigger synthesis
        if (message.responses) {
          generateSynthesis(message.responses);
        }
        break;
        
      case 'automationError':
        setAutomationStatus('error');
        toast.error(`Automation failed: ${message.error}`);
        break;
        
      case 'extensionReady':
        setIsExtensionConnected(true);
        toast.success('Extension connected successfully!');
        break;
        
      default:
        console.log('Unknown extension message:', message);
    }
  }, [generateSynthesis]);

  // Generate session ID on mount
  useEffect(() => {
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    setSessionId(newSessionId);
  }, []);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  // Handle extension messages
  useEffect(() => {
    if (extensionMessage) {
      handleExtensionMessage(extensionMessage);
    }
  }, [extensionMessage, handleExtensionMessage]);

  const handleQuerySubmit = async (query) => {
    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    try {
      setCurrentQuery(query);
      setAutomationStatus('starting');
      setResponses({});
      setSynthesis('');

      // Send to backend first
      const response = await fetch('/api/automation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          session_id: sessionId,
          options: {
            followUps: true,
            synthesize: true,
            services: ['chatgpt', 'claude', 'gemini', 'perplexity']
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Backend response:', data);

      // Send to extension with fallback handling
      const extensionMessage = {
        action: 'startAutomation',
        query: query,
        sessionId: sessionId,
        options: {
          followUps: true,
          services: ['chatgpt', 'claude', 'gemini', 'perplexity']
        }
      };

      try {
        await sendToExtension(extensionMessage);
        toast.success('Automation started - opening AI service tabs...');
        console.log('✅ Extension message sent successfully');
      } catch (extensionError) {
        console.warn('⚠️ Extension communication failed, but backend is ready:', extensionError.message);
        toast.warning('Extension communication issue, but automation may still work. Check console for details.');
        // Don't stop the process, the extension might still work
      }

    } catch (error) {
      console.error('❌ Query submission failed:', error);
      setAutomationStatus('error');
      toast.error(`Failed to start automation: ${error.message}`);
    }
  };


  const handleReset = () => {
    setCurrentQuery('');
    setAutomationStatus('idle');
    setResponses({});
    setSynthesis('');
    toast.info('Session reset');
  };

  const checkExtensionStatus = () => {
    console.log('🔍 Manually checking extension status...');
    
    // Detailed bridge and Chrome API debugging
    console.log('🔍 Complete extension environment check:', {
      // Window and bridge checks
      windowExists: typeof window !== 'undefined',
      samayExtensionExists: typeof window !== 'undefined' && !!window.SamayExtension,
      isAvailableProperty: typeof window !== 'undefined' && window.SamayExtension && window.SamayExtension.isAvailable,
      
      // Chrome API checks
      chromeExists: typeof window !== 'undefined' && !!window.chrome,
      runtimeExists: typeof window !== 'undefined' && !!window.chrome?.runtime,
      runtimeId: typeof window !== 'undefined' && window.chrome?.runtime?.id,
      
      // Bridge functions check
      sendMessageExists: typeof window !== 'undefined' && window.SamayExtension && typeof window.SamayExtension.sendMessage === 'function'
    });
    
    // Check if Samay extension bridge is available
    if (typeof window !== 'undefined' && window.SamayExtension && window.SamayExtension.isAvailable) {
      console.log('✅ Bridge detected, sending ping...');
      try {
        window.SamayExtension.sendMessage('extension-ping', { timestamp: Date.now() }, (response) => {
          console.log('🏓 Manual ping response:', response);
          if (response && response.type === 'extension-pong') {
            setIsExtensionConnected(true);
            toast.success('Extension connection verified via bridge!');
          } else {
            setIsExtensionConnected(false);
            toast.warning('Extension ping failed - no pong received');
          }
        });
      } catch (error) {
        console.error('❌ Manual bridge ping error:', error);
        setIsExtensionConnected(false);
        toast.error(`Bridge communication error: ${error.message}`);
      }
    } else if (typeof window !== 'undefined' && window.chrome && window.chrome.runtime) {
      console.log('🔄 Bridge not available, trying direct Chrome API...');
      try {
        window.chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
          if (window.chrome.runtime.lastError) {
            console.error('❌ Direct Chrome API failed:', window.chrome.runtime.lastError);
            setIsExtensionConnected(false);
            toast.error(`Extension not responding: ${window.chrome.runtime.lastError.message}`);
          } else {
            console.log('✅ Direct Chrome API response:', response);
            setIsExtensionConnected(true);
            toast.success('Extension connection verified via Chrome API!');
          }
        });
      } catch (error) {
        console.error('❌ Direct Chrome API error:', error);
        setIsExtensionConnected(false);
        toast.error(`Chrome API error: ${error.message}`);
      }
    } else {
      console.log('❌ No extension communication method available');
      setIsExtensionConnected(false);
      toast.error('Extension bridge and Chrome API both unavailable - please reload extension');
    }
  };

  return (
    <div className="app">
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />

      {/* Header */}
      <header className="app-header">
        <div className="container">
          <div className="header-content">
            <div className="header-title">
              <h1>
                <i className="fas fa-robot"></i>
                Samay v6
              </h1>
              <p>Browser Extension Multi-AI Automation</p>
            </div>
            
            <div className="header-status">
              <ServiceStatusIndicator 
                backendHealth={backendHealth}
                extensionConnected={isExtensionConnected}
                wsStatus={wsStatus}
                onExtensionCheck={checkExtensionStatus}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          
          {/* Query Input Section */}
          <section className="query-section">
            <QueryInput
              onSubmit={handleQuerySubmit}
              disabled={automationStatus === 'running' || automationStatus === 'starting'}
              currentQuery={currentQuery}
            />
          </section>

          {/* Automation Status */}
          {automationStatus !== 'idle' && (
            <section className="status-section">
              <AutomationStatus
                status={automationStatus}
                currentQuery={currentQuery}
                sessionId={sessionId}
                responses={responses}
              />
            </section>
          )}

          {/* Results Section */}
          {(Object.keys(responses).length > 0 || synthesis) && (
            <section className="results-section">
              <ResponseViewer
                responses={responses}
                synthesis={synthesis}
                onReset={handleReset}
              />
            </section>
          )}

          {/* Extension Communication Component */}
          <ExtensionConnector
            onConnectionChange={setIsExtensionConnected}
            sessionId={sessionId}
          />

        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <p>
            <i className="fas fa-cog"></i>
            Samay v6 - Zero API Cost Multi-AI Automation
            <span className="version">v1.0.0</span>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;