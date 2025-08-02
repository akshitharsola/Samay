// Samay v6 Extension Background Script (Service Worker)
// Main automation orchestrator and communication hub

console.log('🚀 Samay v6 Extension Background Script Loaded');

// Extension state management
let extensionState = {
  isActive: false,
  currentSession: null,
  activeTabs: {},
  automationProgress: {}
};

// Service configurations for AI platforms
const serviceConfigs = {
  chatgpt: {
    name: 'ChatGPT',
    url: 'https://chatgpt.com/',
    selectors: {
      input: 'textarea[data-id="root"], #prompt-textarea, div[contenteditable="true"]',
      send_button: 'button[data-testid="send-button"], button[aria-label*="Send"], button[data-testid="frictionless-send-button"]',
      response_area: 'div[data-message-author-role="assistant"], .markdown, div[data-message-id]',
      loading_indicator: '.result-thinking, .text-token-text-secondary, .text-2xl'
    },
    timing: {
      injection_delay: 2000,
      typing_speed: 15, // chars per second
      response_timeout: 60000
    }
  },
  claude: {
    name: 'Claude',
    url: 'https://claude.ai/',
    selectors: {
      input: 'div[contenteditable="true"], .ProseMirror',
      send_button: 'button[aria-label*="Send"], button[type="submit"]',
      response_area: 'div[data-testid*="message"], .font-claude-message',
      loading_indicator: '.thinking, .loading-dots'
    },
    timing: {
      injection_delay: 2500,
      typing_speed: 12,
      response_timeout: 60000
    }
  },
  gemini: {
    name: 'Gemini',
    url: 'https://gemini.google.com/',
    selectors: {
      input: 'rich-textarea > div > p, .ql-editor p',
      send_button: 'button[aria-label*="Send"], button[data-testid="send-button"]',
      response_area: 'div[data-testid*="response"], .response-content',
      loading_indicator: '.loading, .spinner'
    },
    timing: {
      injection_delay: 2000,
      typing_speed: 14,
      response_timeout: 60000
    }
  },
  perplexity: {
    name: 'Perplexity',
    url: 'https://www.perplexity.ai/',
    selectors: {
      input: 'input[placeholder*="Ask"], textarea[placeholder*="Ask"], div[contenteditable="true"], .query-input',
      send_button: 'button[aria-label*="Submit"], .submit-button, button[type="submit"], button:has(svg[data-icon="arrow"])',
      response_area: '#main, .answer-content, .response-container, .prose, .result-content',
      loading_indicator: '.loading, .searching, .spinner, .thinking'
    },
    timing: {
      injection_delay: 2500,
      typing_speed: 28,
      response_timeout: 120000
    }
  }
};

// Listen for installation and startup
chrome.runtime.onInstalled.addListener((details) => {
  console.log('✅ Samay v6 Extension Installed:', details.reason);
  
  if (details.reason === 'install') {
    // Set up initial storage
    chrome.storage.local.set({
      extensionState: extensionState,
      serviceConfigs: serviceConfigs,
      settings: {
        autoOpenTabs: true,
        enableNotifications: true,
        debugMode: false
      }
    });
  }
});

// Message handler for communication with web app and content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('📨 Background received message:', message);
  
  const { action, sessionId } = message;
  
  switch (action) {
    case 'ping':
      handlePing(message, sender, sendResponse);
      break;
      
    case 'startAutomation':
      handleStartAutomation(message, sender, sendResponse);
      break;
      
    case 'getAutomationStatus':
      handleGetAutomationStatus(message, sender, sendResponse);
      break;
      
    case 'stopAutomation':
      handleStopAutomation(message, sender, sendResponse);
      break;
      
    case 'tabReady':
      handleTabReady(message, sender, sendResponse);
      break;
      
    case 'responseReceived':
      handleResponseReceived(message, sender, sendResponse);
      break;
      
    default:
      console.log('❓ Unknown message action:', action);
      sendResponse({ status: 'unknown_action', action });
  }
  
  return true; // Keep message channel open for async responses
});

// Handle ping requests (connection check)
function handlePing(message, sender, sendResponse) {
  console.log('🏓 Ping received from:', sender.tab ? 'tab' : 'extension');
  
  sendResponse({
    status: 'pong',
    timestamp: Date.now(),
    extensionId: chrome.runtime.id,
    version: chrome.runtime.getManifest().version
  });
}

// Handle automation start request
async function handleStartAutomation(message, sender, sendResponse) {
  const { query, sessionId, options = {} } = message;
  
  console.log('🚀 Starting automation for session:', sessionId);
  console.log('📝 Query:', query);
  console.log('⚙️ Options:', options);
  
  try {
    // Update extension state
    extensionState.isActive = true;
    extensionState.currentSession = sessionId;
    extensionState.automationProgress = {};
    
    // Services to automate (default to all if not specified)
    const servicesToAutomate = options.services || Object.keys(serviceConfigs);
    
    console.log('🎯 Services to automate:', servicesToAutomate);
    
    // Open tabs for all services
    const tabPromises = servicesToAutomate.map(service => openServiceTab(service));
    const tabs = await Promise.all(tabPromises);
    
    // Store tab information
    servicesToAutomate.forEach((service, index) => {
      if (tabs[index]) {
        extensionState.activeTabs[service] = tabs[index].id;
        extensionState.automationProgress[service] = 'tab_opened';
      }
    });
    
    console.log('📂 Tabs opened:', extensionState.activeTabs);
    
    // Send progress update to web app
    sendMessageToWebApp({
      action: 'automationProgress',
      sessionId: sessionId,
      status: 'tabs_opened',
      progress: extensionState.automationProgress
    });
    
    // Wait a moment for tabs to load, then start injection
    setTimeout(() => {
      startQueryInjection(query, sessionId, servicesToAutomate);
    }, 3000);
    
    sendResponse({
      status: 'automation_started',
      sessionId: sessionId,
      tabs: extensionState.activeTabs,
      services: servicesToAutomate
    });
    
  } catch (error) {
    console.error('❌ Automation start failed:', error);
    
    sendResponse({
      status: 'error',
      error: error.message
    });
    
    // Send error to web app
    sendMessageToWebApp({
      action: 'automationError',
      sessionId: sessionId,
      error: error.message
    });
  }
}

// Open a tab for a specific service
async function openServiceTab(service) {
  const config = serviceConfigs[service];
  
  if (!config) {
    throw new Error(`Unknown service: ${service}`);
  }
  
  console.log(`📂 Opening tab for ${config.name}...`);
  
  try {
    const tab = await chrome.tabs.create({
      url: config.url,
      active: false // Open in background
    });
    
    console.log(`✅ Tab opened for ${config.name}:`, tab.id);
    return tab;
    
  } catch (error) {
    console.error(`❌ Failed to open tab for ${config.name}:`, error);
    throw error;
  }
}

// Start query injection across all service tabs
async function startQueryInjection(query, sessionId, services) {
  console.log('💉 Starting query injection for services:', services);
  
  const injectionPromises = services.map(service => 
    injectQueryIntoService(service, query, sessionId)
  );
  
  try {
    await Promise.allSettled(injectionPromises);
    console.log('✅ Query injection completed for all services');
    
    // Update progress
    sendMessageToWebApp({
      action: 'automationProgress',
      sessionId: sessionId,
      status: 'injection_complete',
      progress: extensionState.automationProgress
    });
    
  } catch (error) {
    console.error('❌ Query injection failed:', error);
    
    sendMessageToWebApp({
      action: 'automationError',
      sessionId: sessionId,
      error: 'Query injection failed: ' + error.message
    });
  }
}

// Inject query into specific service tab using new automation system
async function injectQueryIntoService(service, query, sessionId) {
  const config = serviceConfigs[service];
  const tabId = extensionState.activeTabs[service];
  
  if (!tabId) {
    throw new Error(`No tab found for service: ${service}`);
  }
  
  console.log(`💉 Starting advanced automation for ${config.name} (tab: ${tabId})`);
  
  try {
    // Update progress
    extensionState.automationProgress[service] = 'initializing';
    
    // Inject the automation orchestrator and service-specific script
    await chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: [
        'automation/automation_orchestrator.js',
        `automation/${service}_automation.js`
      ]
    });
    
    // Initialize and run automation
    const result = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: runAdvancedAutomation,
      args: [service, query, sessionId]
    });
    
    console.log(`✅ Advanced automation result for ${config.name}:`, result);
    
    // Update progress based on result
    if (result && result[0] && result[0].result && result[0].result.success) {
      extensionState.automationProgress[service] = 'completed';
      
      // Store the response
      const response = result[0].result.response;
      
      // Send response to web app
      sendMessageToWebApp({
        action: 'serviceResponseReceived',
        sessionId: sessionId,
        service: service,
        response: response
      });
      
    } else {
      extensionState.automationProgress[service] = 'error';
      throw new Error(result[0]?.result?.error || 'Automation failed');
    }
    
  } catch (error) {
    console.error(`❌ Failed to run automation for ${config.name}:`, error);
    extensionState.automationProgress[service] = 'error';
    throw error;
  }
}

// Advanced automation function that runs in the page context
async function runAdvancedAutomation(serviceName, query, sessionId) {
  console.log(`🎯 Running advanced automation for ${serviceName}`);
  
  try {
    // Get the appropriate automator class
    let AutomatorClass;
    switch (serviceName) {
      case 'chatgpt':
        AutomatorClass = window.ChatGPTAutomator;
        break;
      case 'claude':
        AutomatorClass = window.ClaudeAutomator;
        break;
      case 'gemini':
        AutomatorClass = window.GeminiAutomator;
        break;
      case 'perplexity':
        AutomatorClass = window.PerplexityAutomator;
        break;
      default:
        throw new Error(`Unknown service: ${serviceName}`);
    }
    
    if (!AutomatorClass) {
      throw new Error(`Automator class not found for ${serviceName}`);
    }
    
    // Create and initialize automator
    const automator = new AutomatorClass();
    const initResult = await automator.initialize();
    
    if (!initResult.success) {
      throw new Error(initResult.error);
    }
    
    // Submit query and get response
    const result = await automator.submitQuery(query);
    
    console.log(`✅ Advanced automation completed for ${serviceName}`);
    return result;
    
  } catch (error) {
    console.error(`❌ Advanced automation failed for ${serviceName}:`, error);
    return {
      success: false,
      service: serviceName,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

// Legacy script injection function (fallback)
function injectQueryScript(query, selectors, timing, serviceName) {
  console.log(`🎯 Samay v6: Injecting query into ${serviceName}`);
  
  try {
    // Find input element
    const input = document.querySelector(selectors.input);
    if (!input) {
      console.error(`❌ Input element not found for ${serviceName}`);
      return { success: false, error: 'Input element not found' };
    }
    
    console.log(`✅ Found input element for ${serviceName}`);
    
    // Focus the input
    input.focus();
    
    // Clear existing content
    if (input.tagName === 'TEXTAREA' || input.type === 'text') {
      input.value = '';
    } else {
      input.textContent = '';
    }
    
    // Simulate human-like typing
    let index = 0;
    function typeCharacter() {
      if (index < query.length) {
        const char = query[index];
        
        if (input.tagName === 'TEXTAREA' || input.type === 'text') {
          input.value += char;
        } else {
          input.textContent += char;
        }
        
        // Trigger input events
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        
        index++;
        
        // Schedule next character with human-like delay
        const delay = 1000 / timing.typing_speed + (Math.random() * 20 - 10); // Add some randomness
        setTimeout(typeCharacter, delay);
        
      } else {
        // Typing complete, submit the query
        setTimeout(() => {
          const sendButton = document.querySelector(selectors.send_button);
          if (sendButton && !sendButton.disabled) {
            console.log(`📤 Submitting query to ${serviceName}`);
            sendButton.click();
          } else {
            console.error(`❌ Send button not found or disabled for ${serviceName}`);
          }
        }, 500);
      }
    }
    
    // Start typing after initial delay
    setTimeout(typeCharacter, timing.injection_delay);
    
    return { success: true, message: 'Query injection started' };
    
  } catch (error) {
    console.error(`❌ Injection script error for ${serviceName}:`, error);
    return { success: false, error: error.message };
  }
}

// Monitor service response
async function monitorServiceResponse(service, sessionId) {
  const config = serviceConfigs[service];
  const tabId = extensionState.activeTabs[service];
  
  console.log(`👁️ Monitoring response for ${config.name}`);
  
  try {
    // Execute monitoring script
    const result = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: monitorResponseScript,
      args: [config.selectors, config.timing, service]
    });
    
    console.log(`📊 Monitoring result for ${config.name}:`, result);
    
  } catch (error) {
    console.error(`❌ Failed to monitor ${config.name}:`, error);
    extensionState.automationProgress[service] = 'error';
  }
}

// Script to monitor responses in service tabs
function monitorResponseScript(selectors, timing, serviceName) {
  console.log(`👁️ Starting response monitoring for ${serviceName}`);
  
  return new Promise((resolve) => {
    const startTime = Date.now();
    
    function checkForResponse() {
      const responseArea = document.querySelector(selectors.response_area);
      const loadingIndicator = document.querySelector(selectors.loading_indicator);
      
      // Check if we have a response and no loading indicator
      if (responseArea && !loadingIndicator) {
        const content = responseArea.innerText || responseArea.textContent;
        
        if (content && content.length > 20) { // Minimum content length
          console.log(`✅ Response detected for ${serviceName}`);
          
          resolve({
            success: true,
            service: serviceName,
            content: content,
            timestamp: new Date().toISOString(),
            wordCount: content.split(' ').length
          });
          return;
        }
      }
      
      // Check timeout
      if (Date.now() - startTime > timing.response_timeout) {
        console.log(`⏰ Response monitoring timeout for ${serviceName}`);
        resolve({
          success: false,
          service: serviceName,
          error: 'Response timeout',
          timestamp: new Date().toISOString()
        });
        return;
      }
      
      // Continue monitoring
      setTimeout(checkForResponse, 2000);
    }
    
    // Start monitoring
    checkForResponse();
  });
}

// Handle automation status requests
function handleGetAutomationStatus(message, sender, sendResponse) {
  sendResponse({
    status: 'active',
    isActive: extensionState.isActive,
    currentSession: extensionState.currentSession,
    progress: extensionState.automationProgress,
    activeTabs: extensionState.activeTabs
  });
}

// Handle automation stop requests
function handleStopAutomation(message, sender, sendResponse) {
  console.log('🛑 Stopping automation');
  
  // Close all active tabs
  Object.values(extensionState.activeTabs).forEach(tabId => {
    chrome.tabs.remove(tabId).catch(error => {
      console.log('Tab already closed:', tabId);
    });
  });
  
  // Reset state
  extensionState.isActive = false;
  extensionState.currentSession = null;
  extensionState.activeTabs = {};
  extensionState.automationProgress = {};
  
  sendResponse({ status: 'stopped' });
}

// Send message to web app
function sendMessageToWebApp(message) {
  // Find tabs running the web app
  chrome.tabs.query({ url: 'http://localhost:3000/*' }, (tabs) => {
    tabs.forEach(tab => {
      chrome.tabs.sendMessage(tab.id, message).catch(error => {
        console.log('Failed to send message to web app tab:', error);
      });
    });
  });
}

// Handle tab ready notifications
function handleTabReady(message, sender, sendResponse) {
  const { service } = message;
  console.log(`📂 Tab ready for ${service}`);
  
  sendResponse({ status: 'acknowledged' });
}

// Handle response received notifications
function handleResponseReceived(message, sender, sendResponse) {
  const { service, response } = message;
  console.log(`📨 Response received from ${service}`);
  
  // Update progress
  extensionState.automationProgress[service] = 'complete';
  
  // Send to web app
  sendMessageToWebApp({
    action: 'serviceResponseReceived',
    sessionId: extensionState.currentSession,
    service: service,
    response: response
  });
  
  // Check if all services are complete
  const allServices = Object.keys(extensionState.activeTabs);
  const completedServices = Object.entries(extensionState.automationProgress)
    .filter(([service, status]) => status === 'complete')
    .map(([service]) => service);
  
  if (completedServices.length === allServices.length) {
    console.log('🎉 All services completed!');
    
    // Collect all responses
    const allResponses = {}; // This would be collected from each service
    
    sendMessageToWebApp({
      action: 'automationComplete',
      sessionId: extensionState.currentSession,
      responses: allResponses
    });
  }
  
  sendResponse({ status: 'acknowledged' });
}

console.log('✅ Samay v6 Extension Background Script Ready');