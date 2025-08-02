// Samay v6 Extension Popup Script
console.log('🚀 Samay v6 Popup Loaded');

// Popup state
let popupState = {
  isConnected: false,
  webAppConnected: false,
  automationActive: false,
  currentSession: null,
  activeServices: [],
  progress: {}
};

// DOM elements
const elements = {
  extensionStatus: document.getElementById('extension-status'),
  extensionStatusText: document.getElementById('extension-status-text'),
  webappStatus: document.getElementById('webapp-status'),
  webappStatusText: document.getElementById('webapp-status-text'),
  automationStatus: document.getElementById('automation-status'),
  automationStatusText: document.getElementById('automation-status-text'),
  
  openWebappBtn: document.getElementById('open-webapp-btn'),
  checkConnectionBtn: document.getElementById('check-connection-btn'),
  stopAutomationBtn: document.getElementById('stop-automation-btn'),
  
  sessionSection: document.getElementById('session-section'),
  sessionId: document.getElementById('session-id'),
  activeServicesEl: document.getElementById('active-services'),
  progressFill: document.getElementById('progress-fill'),
  progressText: document.getElementById('progress-text'),
  
  servicesSection: document.getElementById('services-section'),
  serviceChatGPT: document.getElementById('service-chatgpt'),
  serviceClaude: document.getElementById('service-claude'),
  serviceGemini: document.getElementById('service-gemini'),
  servicePerplexity: document.getElementById('service-perplexity'),
  
  helpLink: document.getElementById('help-link'),
  settingsLink: document.getElementById('settings-link')
};

// Initialize popup
function initializePopup() {
  console.log('🎯 Initializing popup...');
  
  // Set up event listeners
  setupEventListeners();
  
  // Check initial status
  checkExtensionStatus();
  
  // Set up periodic updates
  setInterval(updateStatus, 5000);
  
  console.log('✅ Popup initialized');
}

// Set up event listeners
function setupEventListeners() {
  // Button event listeners
  elements.openWebappBtn.addEventListener('click', openWebApp);
  elements.checkConnectionBtn.addEventListener('click', checkConnection);
  elements.stopAutomationBtn.addEventListener('click', stopAutomation);
  
  // Footer links
  elements.helpLink.addEventListener('click', showHelp);
  elements.settingsLink.addEventListener('click', showSettings);
  
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener(handleBackgroundMessage);
}

// Check extension status
async function checkExtensionStatus() {
  try {
    // Check if background script is responsive
    const response = await sendToBackground({ action: 'ping' });
    
    if (response && response.status === 'pong') {
      updateExtensionStatus('online', 'Active');
      popupState.isConnected = true;
      
      // Check automation status
      checkAutomationStatus();
      
      // Check web app connection
      checkWebAppConnection();
      
    } else {
      updateExtensionStatus('offline', 'Not Responding');
    }
  } catch (error) {
    console.error('❌ Extension status check failed:', error);
    updateExtensionStatus('offline', 'Error');
  }
}

// Check automation status
async function checkAutomationStatus() {
  try {
    const response = await sendToBackground({ action: 'getAutomationStatus' });
    
    if (response) {
      popupState.automationActive = response.isActive;
      popupState.currentSession = response.currentSession;
      popupState.activeServices = Object.keys(response.activeTabs || {});
      popupState.progress = response.progress || {};
      
      updateAutomationStatus();
      updateSessionInfo();
      updateServicesStatus();
    }
  } catch (error) {
    console.error('❌ Automation status check failed:', error);
  }
}

// Check web app connection
function checkWebAppConnection() {
  // Query for web app tabs
  chrome.tabs.query({ url: 'http://localhost:3000/*' }, (tabs) => {
    if (tabs && tabs.length > 0) {
      updateWebAppStatus('online', 'Connected');
      popupState.webAppConnected = true;
    } else {
      updateWebAppStatus('offline', 'Not Open');
      popupState.webAppConnected = false;
    }
  });
}

// Update extension status
function updateExtensionStatus(status, text) {
  const statusDot = elements.extensionStatus.querySelector('.status-dot');
  statusDot.className = `status-dot ${status}`;
  elements.extensionStatusText.textContent = text;
}

// Update web app status
function updateWebAppStatus(status, text) {
  const statusDot = elements.webappStatus.querySelector('.status-dot');
  statusDot.className = `status-dot ${status}`;
  elements.webappStatusText.textContent = text;
}

// Update automation status
function updateAutomationStatus() {
  if (popupState.automationActive) {
    const statusDot = elements.automationStatus.querySelector('.status-dot');
    statusDot.className = 'status-dot loading';
    elements.automationStatusText.textContent = 'Running';
    
    elements.stopAutomationBtn.disabled = false;
    elements.sessionSection.style.display = 'block';
    elements.servicesSection.style.display = 'block';
  } else {
    const statusDot = elements.automationStatus.querySelector('.status-dot');
    statusDot.className = 'status-dot offline';
    elements.automationStatusText.textContent = 'Idle';
    
    elements.stopAutomationBtn.disabled = true;
    elements.sessionSection.style.display = 'none';
    elements.servicesSection.style.display = 'none';
  }
}

// Update session information
function updateSessionInfo() {
  if (popupState.currentSession) {
    elements.sessionId.textContent = popupState.currentSession.substring(0, 8) + '...';
    elements.activeServicesEl.textContent = popupState.activeServices.join(', ') || 'None';
    
    // Calculate progress
    const totalServices = popupState.activeServices.length;
    const completedServices = Object.values(popupState.progress).filter(status => status === 'complete').length;
    const progressPercent = totalServices > 0 ? Math.round((completedServices / totalServices) * 100) : 0;
    
    elements.progressFill.style.width = `${progressPercent}%`;
    elements.progressText.textContent = `${progressPercent}%`;
  }
}

// Update services status
function updateServicesStatus() {
  const serviceElements = {
    chatgpt: elements.serviceChatGPT,
    claude: elements.serviceClaude,
    gemini: elements.serviceGemini,
    perplexity: elements.servicePerplexity
  };
  
  Object.keys(serviceElements).forEach(service => {
    const element = serviceElements[service];
    const status = popupState.progress[service] || 'idle';
    const statusText = element.querySelector('.service-status');
    
    // Remove all status classes
    element.className = 'service-card';
    
    // Update based on status
    switch (status) {
      case 'tab_opened':
        element.classList.add('active');
        statusText.textContent = 'Ready';
        break;
      case 'injecting':
      case 'monitoring':
        element.classList.add('working');
        statusText.textContent = 'Working';
        break;
      case 'complete':
        element.classList.add('complete');
        statusText.textContent = 'Complete';
        break;
      case 'error':
        element.classList.add('error');
        statusText.textContent = 'Error';
        break;
      default:
        statusText.textContent = 'Idle';
    }
  });
}

// Send message to background script
function sendToBackground(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// Handle messages from background script
function handleBackgroundMessage(message, sender, sendResponse) {
  console.log('📨 Message from background:', message);
  
  const { action } = message;
  
  switch (action) {
    case 'automationProgress':
      popupState.progress = message.progress || {};
      updateServicesStatus();
      updateSessionInfo();
      break;
      
    case 'automationComplete':
      popupState.automationActive = false;
      updateAutomationStatus();
      break;
      
    case 'automationError':
      // Handle automation errors
      console.error('Automation error:', message.error);
      break;
  }
  
  sendResponse({ status: 'received' });
}

// Button handlers
async function openWebApp() {
  try {
    // Check if web app is already open
    const tabs = await new Promise(resolve => {
      chrome.tabs.query({ url: 'http://localhost:3000/*' }, resolve);
    });
    
    if (tabs && tabs.length > 0) {
      // Switch to existing tab
      chrome.tabs.update(tabs[0].id, { active: true });
      chrome.windows.update(tabs[0].windowId, { focused: true });
    } else {
      // Open new tab
      chrome.tabs.create({ url: 'http://localhost:3000' });
    }
    
    // Close popup
    window.close();
    
  } catch (error) {
    console.error('❌ Failed to open web app:', error);
  }
}

async function checkConnection() {
  elements.checkConnectionBtn.disabled = true;
  elements.checkConnectionBtn.innerHTML = '<span class="btn-icon">⏳</span> Checking...';
  
  try {
    await checkExtensionStatus();
    
    setTimeout(() => {
      elements.checkConnectionBtn.disabled = false;
      elements.checkConnectionBtn.innerHTML = '<span class="btn-icon">🔄</span> Check Connection';
    }, 1000);
    
  } catch (error) {
    console.error('❌ Connection check failed:', error);
    
    elements.checkConnectionBtn.disabled = false;
    elements.checkConnectionBtn.innerHTML = '<span class="btn-icon">🔄</span> Check Connection';
  }
}

async function stopAutomation() {
  try {
    elements.stopAutomationBtn.disabled = true;
    elements.stopAutomationBtn.innerHTML = '<span class="btn-icon">⏳</span> Stopping...';
    
    const response = await sendToBackground({ action: 'stopAutomation' });
    
    if (response && response.status === 'stopped') {
      popupState.automationActive = false;
      popupState.currentSession = null;
      popupState.activeServices = [];
      popupState.progress = {};
      
      updateAutomationStatus();
    }
    
  } catch (error) {
    console.error('❌ Failed to stop automation:', error);
    elements.stopAutomationBtn.disabled = false;
    elements.stopAutomationBtn.innerHTML = '<span class="btn-icon">🛑</span> Stop Automation';
  }
}

function showHelp() {
  chrome.tabs.create({ 
    url: 'https://github.com/your-repo/samay-v6#installation-guide' 
  });
}

function showSettings() {
  // Could open a settings page or modal
  console.log('Settings not implemented yet');
}

// Update status periodically
function updateStatus() {
  if (popupState.isConnected) {
    checkAutomationStatus();
    checkWebAppConnection();
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializePopup);

console.log('✅ Popup script loaded');