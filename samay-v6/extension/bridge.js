// Samay v6 Web App Bridge Script
// This script runs in the page context to create communication bridge

console.log('🌉 Samay v6 bridge script loaded');

// Create global Samay object for web app to use
window.SamayExtension = {
  isAvailable: true,
  
  // Send message to extension
  sendMessage: function(type, payload, callback) {
    const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Store callback if provided
    if (callback && typeof callback === 'function') {
      this._callbacks = this._callbacks || {};
      this._callbacks[messageId] = callback;
      
      // Set timeout for callback cleanup
      setTimeout(() => {
        if (this._callbacks && this._callbacks[messageId]) {
          console.warn('⏰ Bridge message timeout for:', messageId);
          delete this._callbacks[messageId];
        }
      }, 10000);
    }
    
    // Send message to content script
    window.postMessage({
      source: 'samay-web-app',
      type: type,
      payload: payload,
      messageId: messageId
    }, window.location.origin);
    
    return messageId;
  },
  
  // Listen for extension messages
  onMessage: function(callback) {
    window.addEventListener('message', (event) => {
      if (event.origin === window.location.origin && 
          event.data && 
          event.data.source === 'samay-extension') {
        callback(event.data);
      }
    });
  },
  
  // Handle response callbacks
  _handleResponse: function(message) {
    if (this._callbacks && this._callbacks[message.messageId]) {
      try {
        this._callbacks[message.messageId](message);
      } catch (error) {
        console.error('❌ Bridge callback error:', error);
      }
      delete this._callbacks[message.messageId];
    }
  }
};

// Listen for responses to handle callbacks
window.addEventListener('message', (event) => {
  if (event.origin === window.location.origin && 
      event.data && 
      event.data.source === 'samay-extension' &&
      event.data.messageId) {
    window.SamayExtension._handleResponse(event.data);
  }
});

// Dispatch extension ready event
window.dispatchEvent(new CustomEvent('samayExtensionReady', {
  detail: { 
    timestamp: Date.now(),
    bridgeVersion: '1.0.0'
  }
}));

console.log('✅ Samay v6 bridge initialized successfully');