import { useState, useEffect, useCallback } from 'react';

export const useExtensionCommunication = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [extensionMessage, setExtensionMessage] = useState(null);
  const [bridgeReady, setBridgeReady] = useState(false);

  // Check if Samay extension bridge is available
  const isBridgeAvailable = useCallback(() => {
    return typeof window !== 'undefined' && 
           window.SamayExtension && 
           window.SamayExtension.isAvailable === true;
  }, []);

  // Send message to extension via bridge or direct Chrome API
  const sendToExtension = useCallback((message) => {
    console.log('📤 Attempting to send message to extension:', message);
    console.log('🔍 Bridge availability check:', {
      windowExists: typeof window !== 'undefined',
      samayExtensionExists: typeof window !== 'undefined' && !!window.SamayExtension,
      isAvailableProperty: typeof window !== 'undefined' && window.SamayExtension && window.SamayExtension.isAvailable,
      bridgeAvailable: isBridgeAvailable()
    });
    
    return new Promise((resolve, reject) => {
      // Try bridge first
      if (isBridgeAvailable()) {
        console.log('🌉 Using extension bridge');
        try {
          // Map message format to bridge format
          let type, payload;
          
          if (message.action === 'startAutomation') {
            type = 'start-automation';
            payload = {
              query: message.query,
              sessionId: message.sessionId,
              options: message.options
            };
          } else if (message.action === 'ping') {
            type = 'extension-ping';
            payload = { timestamp: message.timestamp || Date.now() };
          } else {
            type = message.action;
            payload = message;
          }

          // Send via bridge with timeout
          const timeoutId = setTimeout(() => {
            reject(new Error('Bridge communication timeout'));
          }, 5000);

          window.SamayExtension.sendMessage(type, payload, (response) => {
            clearTimeout(timeoutId);
            console.log('📨 Extension response received via bridge:', response);
            
            if (response && response.type === 'extension-pong') {
              setIsConnected(true);
              resolve({ status: 'pong', ...response.payload });
            } else if (response && response.type === 'automation-started') {
              setIsConnected(true);
              resolve(response.payload);
            } else if (response) {
              setIsConnected(true);
              resolve(response);
            } else {
              reject(new Error('No response from extension'));
            }
          });
          return;
          
        } catch (error) {
          console.error('❌ Bridge communication failed, trying direct:', error);
        }
      }
      
      // Fallback to direct Chrome extension API
      if (typeof window !== 'undefined' && window.chrome && window.chrome.runtime) {
        console.log('🔄 Using direct Chrome extension API');
        console.log('🔍 Chrome API check:', {
          chromeExists: !!window.chrome,
          runtimeExists: !!window.chrome.runtime,
          runtimeId: window.chrome.runtime?.id,
          lastError: window.chrome.runtime?.lastError
        });
        
        try {
          window.chrome.runtime.sendMessage(message, (response) => {
            if (window.chrome.runtime.lastError) {
              console.error('❌ Direct extension communication failed:', {
                error: window.chrome.runtime.lastError,
                message: window.chrome.runtime.lastError.message,
                runtimeId: window.chrome.runtime?.id
              });
              setIsConnected(false);
              reject(new Error(window.chrome.runtime.lastError.message));
            } else {
              console.log('📨 Extension response received directly:', response);
              setIsConnected(true);
              resolve(response);
            }
          });
        } catch (error) {
          console.error('❌ Failed to send message directly:', error);
          setIsConnected(false);
          reject(error);
        }
      } else {
        console.warn('❌ No extension communication method available:', {
          windowExists: typeof window !== 'undefined',
          chromeExists: typeof window !== 'undefined' && !!window.chrome,
          runtimeExists: typeof window !== 'undefined' && !!window.chrome?.runtime
        });
        setIsConnected(false);
        reject(new Error('Extension bridge not available'));
      }
    });
  }, [isBridgeAvailable]);

  // Listen for extension ready event and messages
  useEffect(() => {
    console.log('🔧 Setting up extension communication listeners...');

    // Listen for extension ready event
    const handleExtensionReady = (event) => {
      console.log('✅ Samay extension bridge ready:', event.detail);
      setBridgeReady(true);
      
      // Wait a moment for bridge to be fully initialized
      setTimeout(() => {
        if (isBridgeAvailable()) {
          console.log('🌉 Bridge confirmed available after ready event');
          setIsConnected(true);
        }
      }, 100);
    };

    // Listen for extension messages
    const handleExtensionMessage = (event) => {
      // Only accept messages from same origin
      if (event.origin !== window.location.origin) {
        return;
      }
      
      // Check for Samay extension messages
      if (!event.data || event.data.source !== 'samay-extension') {
        return;
      }
      
      console.log('📨 Extension message received via bridge:', event.data);
      
      // Update connection status
      setIsConnected(true);
      
      // Convert bridge message format to component format
      let componentMessage = event.data.payload || {};
      
      if (event.data.type === 'extension-ready') {
        componentMessage = { action: 'extensionReady', ...event.data.payload };
      } else if (event.data.type === 'automation-progress') {
        componentMessage = { action: 'automationProgress', ...event.data.payload };
      } else if (event.data.type === 'automation-complete') {
        componentMessage = { action: 'automationComplete', ...event.data.payload };
      } else if (event.data.type === 'automation-error') {
        componentMessage = { action: 'automationError', ...event.data.payload };
      } else if (event.data.type === 'service-response') {
        componentMessage = { action: 'serviceResponseReceived', ...event.data.payload };
      }
      
      // Store the message for components to handle
      setExtensionMessage(componentMessage);
    };

    // Listen for direct Chrome extension messages (fallback)
    const handleChromeExtensionMessage = (message, sender, sendResponse) => {
      console.log('📨 Extension message received directly:', message);
      setIsConnected(true);
      setExtensionMessage(message);
      sendResponse({ status: 'received' });
      return true;
    };

    // Add event listeners
    window.addEventListener('samayExtensionReady', handleExtensionReady);
    window.addEventListener('message', handleExtensionMessage);
    
    // Add Chrome extension message listener (fallback)
    if (window.chrome && window.chrome.runtime && window.chrome.runtime.onMessage) {
      window.chrome.runtime.onMessage.addListener(handleChromeExtensionMessage);
    }

    // Check if bridge is already available
    const checkBridgeAvailability = () => {
      if (isBridgeAvailable()) {
        console.log('✅ Bridge already available on setup');
        setBridgeReady(true);
        setIsConnected(true);
        return true;
      }
      return false;
    };

    // Initial check
    if (!checkBridgeAvailability()) {
      // Retry bridge check multiple times with increasing delays
      const retryIntervals = [500, 1000, 2000, 3000];
      retryIntervals.forEach((delay, index) => {
        setTimeout(() => {
          if (!bridgeReady && checkBridgeAvailability()) {
            console.log(`✅ Bridge became available after ${delay}ms`);
          }
        }, delay);
      });

      // Try to detect extension directly if bridge is not available after delays
      setTimeout(() => {
        if (!bridgeReady && window.chrome && window.chrome.runtime) {
          console.log('🔍 Bridge still not available, trying direct detection...');
          try {
            window.chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
              if (!window.chrome.runtime.lastError && response) {
                console.log('✅ Extension detected directly');
                setIsConnected(true);
              }
            });
          } catch (error) {
            console.log('❌ Direct detection failed:', error.message);
          }
        }
      }, 5000);
    }

    return () => {
      // Cleanup: remove event listeners
      window.removeEventListener('samayExtensionReady', handleExtensionReady);
      window.removeEventListener('message', handleExtensionMessage);
      if (window.chrome && window.chrome.runtime && window.chrome.runtime.onMessage) {
        window.chrome.runtime.onMessage.removeListener(handleChromeExtensionMessage);
      }
    };
  }, [isBridgeAvailable, bridgeReady]);

  // Ping extension to check connection
  const pingExtension = useCallback(async () => {
    try {
      console.log('🏓 Pinging extension...');
      const response = await sendToExtension({ 
        action: 'ping', 
        timestamp: Date.now() 
      });
      
      console.log('🏓 Ping response:', response);
      
      if (response && response.status === 'pong') {
        setIsConnected(true);
        return true;
      } else {
        setIsConnected(false);
        return false;
      }
    } catch (error) {
      console.log('🏓 Extension ping failed:', error.message);
      setIsConnected(false);
      return false;
    }
  }, [sendToExtension]);

  // Auto-ping extension periodically after bridge is ready
  useEffect(() => {
    if (!bridgeReady) return;

    // Initial ping after a short delay
    const initialPing = setTimeout(() => {
      pingExtension();
    }, 1000);

    // Set up periodic ping
    const pingInterval = setInterval(pingExtension, 30000); // Every 30 seconds

    return () => {
      clearTimeout(initialPing);
      clearInterval(pingInterval);
    };
  }, [bridgeReady, pingExtension]);

  // Clear extension message after it's been processed
  const clearExtensionMessage = useCallback(() => {
    setExtensionMessage(null);
  }, []);

  return {
    isConnected,
    extensionMessage,
    sendToExtension,
    pingExtension,
    clearExtensionMessage,
    isExtensionAPIAvailable: isBridgeAvailable(),
    bridgeReady
  };
};