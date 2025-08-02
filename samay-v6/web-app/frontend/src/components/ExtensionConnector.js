import { useEffect, useRef, useCallback } from 'react';

const ExtensionConnector = ({ onConnectionChange, sessionId }) => {
  const reconnectInterval = useRef(null);

  const checkExtensionConnection = useCallback(() => {
    // Check if Samay extension bridge is available
    if (typeof window !== 'undefined' && window.SamayExtension && window.SamayExtension.isAvailable) {
      try {
        // Use the bridge to ping the extension
        window.SamayExtension.sendMessage('extension-ping', { sessionId }, (response) => {
          if (response && response.type === 'extension-pong') {
            console.log('✅ Extension connected via bridge:', response);
            onConnectionChange(true);
          } else {
            console.log('Extension ping failed via bridge');
            onConnectionChange(false);
          }
        });
      } catch (error) {
        console.log('Extension bridge communication error:', error);
        onConnectionChange(false);
      }
    } else {
      // No Samay extension bridge available
      console.log('Samay extension bridge not available');
      onConnectionChange(false);
    }
  }, [onConnectionChange, sessionId]);

  useEffect(() => {
    // Listen for extension ready event
    const handleExtensionReady = () => {
      console.log('🎉 Extension ready event received');
      setTimeout(checkExtensionConnection, 500); // Check connection after bridge is ready
    };

    window.addEventListener('samayExtensionReady', handleExtensionReady);
    
    // Initial check
    checkExtensionConnection();
    
    // Set up periodic connection checks
    reconnectInterval.current = setInterval(checkExtensionConnection, 30000); // Check every 30 seconds

    return () => {
      window.removeEventListener('samayExtensionReady', handleExtensionReady);
      if (reconnectInterval.current) {
        clearInterval(reconnectInterval.current);
      }
    };
  }, [checkExtensionConnection]);

  // This component doesn't render anything visible
  return null;
};

export default ExtensionConnector;