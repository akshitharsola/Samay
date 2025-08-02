// Samay v6 Extension Content Script
// Handles communication between web app and extension
// Only runs on localhost (web app) pages

console.log('🔗 Samay v6 Content Script Loaded on:', window.location.href);

// Content script state
let contentState = {
  isConnected: false,
  sessionId: null,
  messageQueue: [],
  retryCount: 0,
  maxRetries: 5
};

// Configuration
const CONFIG = {
  RETRY_DELAY: 2000,
  HEARTBEAT_INTERVAL: 30000,
  MESSAGE_TIMEOUT: 10000
};

// Initialize content script
function initializeContentScript() {
  console.log('🚀 Initializing Samay v6 content script...');
  
  // Check if we're on the web app
  if (!isWebAppPage()) {
    console.log('⚠️ Not on web app page, content script will not initialize');
    return;
  }
  
  // Set up message passing bridge
  setupMessageBridge();
  
  // Set up DOM monitoring
  setupDOMMonitoring();
  
  // Start heartbeat
  startHeartbeat();
  
  console.log('✅ Content script initialized successfully');
}

// Check if current page is the web app
function isWebAppPage() {
  const { hostname, port } = window.location;
  return hostname === 'localhost' && (port === '3000' || port === '3001');
}

// Set up bidirectional message bridge between web app and extension
function setupMessageBridge() {
  console.log('🌉 Setting up message bridge...');
  
  // Listen for messages from the web app (page scripts)
  window.addEventListener('message', handleWebAppMessage, false);
  
  // Listen for messages from the extension background script
  chrome.runtime.onMessage.addListener(handleExtensionMessage);
  
  // Inject bridge script into page context
  injectBridgeScript();
  
  // Notify web app that extension is available
  notifyWebAppReady();
}

// Handle messages from the web app
function handleWebAppMessage(event) {
  // Only accept messages from same origin
  if (event.origin !== window.location.origin) {
    return;
  }
  
  // Check for Samay extension messages
  if (!event.data || event.data.source !== 'samay-web-app') {
    return;
  }
  
  console.log('📨 Message from web app:', event.data);
  
  const { type, payload, messageId } = event.data;
  
  switch (type) {
    case 'extension-ping':
      handleWebAppPing(messageId, payload);
      break;
      
    case 'start-automation':
      handleStartAutomation(payload, messageId);
      break;
      
    case 'stop-automation':
      handleStopAutomation(payload, messageId);
      break;
      
    case 'get-automation-status':
      handleGetAutomationStatus(messageId);
      break;
      
    case 'session-created':
      handleSessionCreated(payload);
      break;
      
    default:
      console.log('❓ Unknown message type from web app:', type);
  }
}

// Handle ping from web app
function handleWebAppPing(messageId, payload) {
  console.log('🏓 Ping from web app with payload:', payload);
  
  // Send pong back to web app
  sendToWebApp({
    type: 'extension-pong',
    payload: {
      connected: true,
      timestamp: Date.now(),
      extensionId: chrome.runtime.id,
      receivedTimestamp: payload?.timestamp
    },
    messageId: messageId
  });
}

// Handle automation start request from web app
function handleStartAutomation(payload, messageId) {
  console.log('🚀 Starting automation:', payload);
  
  const { query, sessionId, options } = payload;
  
  // Store session ID
  contentState.sessionId = sessionId;
  
  // Forward to extension background script
  chrome.runtime.sendMessage({
    action: 'startAutomation',
    query: query,
    sessionId: sessionId,
    options: options
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('❌ Error starting automation:', chrome.runtime.lastError);
      
      sendToWebApp({
        type: 'automation-error',
        payload: {
          error: chrome.runtime.lastError.message,
          sessionId: sessionId
        },
        messageId: messageId
      });
    } else {
      console.log('✅ Automation started:', response);
      
      sendToWebApp({
        type: 'automation-started',
        payload: response,
        messageId: messageId
      });
    }
  });
}

// Handle automation stop request
function handleStopAutomation(payload, messageId) {
  console.log('🛑 Stopping automation');
  
  chrome.runtime.sendMessage({
    action: 'stopAutomation',
    sessionId: contentState.sessionId
  }, (response) => {
    console.log('🛑 Automation stopped:', response);
    
    sendToWebApp({
      type: 'automation-stopped',
      payload: response,
      messageId: messageId
    });
  });
}

// Handle automation status request
function handleGetAutomationStatus(messageId) {
  chrome.runtime.sendMessage({
    action: 'getAutomationStatus'
  }, (response) => {
    sendToWebApp({
      type: 'automation-status',
      payload: response,
      messageId: messageId
    });
  });
}

// Handle session creation notification
function handleSessionCreated(payload) {
  console.log('📝 Session created:', payload.sessionId);
  contentState.sessionId = payload.sessionId;
}

// Handle messages from extension background script
function handleExtensionMessage(message, sender, sendResponse) {
  console.log('📨 Message from extension:', message);
  
  const { action } = message;
  
  // Forward extension messages to web app
  switch (action) {
    case 'automationProgress':
      sendToWebApp({
        type: 'automation-progress',
        payload: message
      });
      break;
      
    case 'automationError':
      sendToWebApp({
        type: 'automation-error',
        payload: message
      });
      break;
      
    case 'serviceResponseReceived':
      sendToWebApp({
        type: 'service-response',
        payload: message
      });
      break;
      
    case 'automationComplete':
      sendToWebApp({
        type: 'automation-complete',
        payload: message
      });
      break;
      
    default:
      console.log('❓ Unknown message from extension:', action);
  }
  
  // Send acknowledgment
  sendResponse({ status: 'received', timestamp: Date.now() });
  return true;
}

// Send message to web app
function sendToWebApp(message) {
  try {
    window.postMessage({
      source: 'samay-extension',
      ...message,
      timestamp: Date.now()
    }, window.location.origin);
    
    console.log('📤 Message sent to web app:', message);
  } catch (error) {
    console.error('❌ Failed to send message to web app:', error);
  }
}

// Inject bridge script into page context
function injectBridgeScript() {
  console.log('🔧 Attempting to inject bridge script...');
  
  try {
    // Create script element pointing to bridge file
    const script = document.createElement('script');
    const bridgeUrl = chrome.runtime.getURL('bridge.js');
    
    console.log('📁 Bridge script URL:', bridgeUrl);
    
    script.src = bridgeUrl;
    script.onload = function() {
      console.log('✅ Bridge script loaded successfully from file');
      
      // Verify bridge was created
      setTimeout(() => {
        const bridgeCheck = window.SamayExtension;
        console.log('🔍 Bridge verification after file load:', {
          bridgeExists: !!bridgeCheck,
          isAvailable: bridgeCheck?.isAvailable,
          bridgeType: 'file'
        });
      }, 100);
      
      this.remove();
    };
    script.onerror = function(error) {
      console.error('❌ Failed to load bridge script from file:', error);
      console.log('🔄 Falling back to inline bridge creation');
      // Fallback to direct bridge creation if file injection fails
      createBridgeDirectly();
      this.remove();
    };
    
    (document.head || document.documentElement).appendChild(script);
    
  } catch (error) {
    console.error('❌ Script injection failed:', error);
    // Fallback to direct bridge creation
    createBridgeDirectly();
  }
}

// Fallback: Create bridge directly in content script context
function createBridgeDirectly() {
  console.log('🔄 Creating bridge directly in content script context');
  
  // Since we can't inject into page context due to CSP, 
  // we'll create the bridge in the content script context
  // and use a different communication method
  
  // Create a more limited bridge that works within CSP constraints
  const bridgeCode = `
    window.SamayExtension = {
      isAvailable: true,
      sendMessage: function(type, payload, callback) {
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        if (callback && typeof callback === 'function') {
          this._callbacks = this._callbacks || {};
          this._callbacks[messageId] = callback;
        }
        
        window.postMessage({
          source: 'samay-web-app',
          type: type,
          payload: payload,
          messageId: messageId
        }, window.location.origin);
        
        return messageId;
      },
      _handleResponse: function(message) {
        if (this._callbacks && this._callbacks[message.messageId]) {
          this._callbacks[message.messageId](message);
          delete this._callbacks[message.messageId];
        }
      }
    };
    
    window.addEventListener('message', (event) => {
      if (event.origin === window.location.origin && 
          event.data && 
          event.data.source === 'samay-extension' &&
          event.data.messageId) {
        window.SamayExtension._handleResponse(event.data);
      }
    });
    
    window.dispatchEvent(new CustomEvent('samayExtensionReady', {
      detail: { timestamp: Date.now(), fallback: true }
    }));
  `;
  
  // Try to execute the bridge code
  try {
    const script = document.createElement('script');
    script.textContent = bridgeCode;
    (document.head || document.documentElement).appendChild(script);
    script.remove();
    console.log('✅ Fallback bridge created successfully');
    
    // Verify fallback bridge was created
    setTimeout(() => {
      const bridgeCheck = window.SamayExtension;
      console.log('🔍 Fallback bridge verification:', {
        bridgeExists: !!bridgeCheck,
        isAvailable: bridgeCheck?.isAvailable,
        bridgeType: 'fallback'
      });
      
      if (bridgeCheck && bridgeCheck.isAvailable) {
        // Dispatch ready event for fallback bridge
        window.dispatchEvent(new CustomEvent('samayExtensionReady', {
          detail: { timestamp: Date.now(), fallback: true }
        }));
      }
    }, 100);
    
  } catch (error) {
    console.error('❌ Even fallback bridge creation failed:', error);
  }
}

// Notify web app that extension is ready
function notifyWebAppReady() {
  // Wait a moment for the page to be ready
  setTimeout(() => {
    sendToWebApp({
      type: 'extension-ready',
      payload: {
        extensionId: chrome.runtime.id,
        version: chrome.runtime.getManifest().version,
        timestamp: Date.now()
      }
    });
    
    contentState.isConnected = true;
  }, 1000);
}

// Set up DOM monitoring for dynamic content
function setupDOMMonitoring() {
  // Monitor for changes that might indicate automation targets
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      // Could be used to detect automation-relevant changes in the web app
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        // Handle dynamic content if needed
      }
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: false
  });
}

// Start heartbeat to maintain connection
function startHeartbeat() {
  setInterval(() => {
    if (contentState.isConnected) {
      // Ping extension to ensure connection is alive
      chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('⚠️ Extension heartbeat failed:', chrome.runtime.lastError);
          contentState.isConnected = false;
          
          // Notify web app of disconnection
          sendToWebApp({
            type: 'extension-disconnected',
            payload: { reason: 'heartbeat_failed' }
          });
        }
      });
    }
  }, CONFIG.HEARTBEAT_INTERVAL);
}

// Error handler
function handleError(error, context) {
  console.error(`❌ Content script error (${context}):`, error);
  
  // Send error to web app
  sendToWebApp({
    type: 'extension-error',
    payload: {
      error: error.message,
      context: context,
      timestamp: Date.now()
    }
  });
}

// Cleanup function
function cleanup() {
  console.log('🧹 Cleaning up content script...');
  
  // Remove event listeners
  window.removeEventListener('message', handleWebAppMessage);
  
  // Reset state
  contentState.isConnected = false;
  contentState.sessionId = null;
  contentState.messageQueue = [];
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeContentScript);
} else {
  initializeContentScript();
}

// Handle page unload
window.addEventListener('beforeunload', cleanup);

console.log('✅ Samay v6 Content Script Setup Complete');