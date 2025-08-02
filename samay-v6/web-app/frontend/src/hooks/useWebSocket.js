import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (sessionId) => {
  const [wsStatus, setWsStatus] = useState('disconnected'); // disconnected, connecting, connected, error
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!sessionId) {
      console.log('⚠️ No session ID provided for WebSocket connection');
      return;
    }

    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket already connected');
      return;
    }

    try {
      setWsStatus('connecting');
      console.log(`🔌 Connecting to WebSocket for session: ${sessionId}`);
      
      // Determine WebSocket URL based on current location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const port = process.env.NODE_ENV === 'development' ? '8000' : window.location.port;
      const wsUrl = `${protocol}//${host}:${port}/ws/${sessionId}`;
      
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setWsStatus('connected');
        setConnectionAttempts(0);
        
        // Send initial connection message
        sendMessage({
          type: 'connection_established',
          sessionId: sessionId,
          timestamp: new Date().toISOString()
        });
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', message);
          setLastMessage(message);
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setWsStatus('disconnected');
        
        // Attempt to reconnect if not intentionally closed
        if (event.code !== 1000 && connectionAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000); // Exponential backoff, max 30s
          console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${connectionAttempts + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeout.current = setTimeout(() => {
            setConnectionAttempts(prev => prev + 1);
            connect();
          }, delay);
        } else if (connectionAttempts >= maxReconnectAttempts) {
          console.error('❌ Max reconnection attempts reached');
          setWsStatus('error');
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setWsStatus('error');
      };

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      setWsStatus('error');
    }
  }, [sessionId, connectionAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (ws.current) {
      console.log('🔌 Disconnecting WebSocket');
      ws.current.close(1000, 'Intentional disconnect');
      ws.current = null;
    }
    
    setWsStatus('disconnected');
    setConnectionAttempts(0);
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        const messageString = JSON.stringify(message);
        ws.current.send(messageString);
        console.log('📤 WebSocket message sent:', message);
        return true;
      } catch (error) {
        console.error('❌ Failed to send WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message:', message);
      return false;
    }
  }, []);

  // Connect when sessionId is available
  useEffect(() => {
    if (sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Ping server periodically to keep connection alive
  useEffect(() => {
    if (wsStatus === 'connected') {
      const pingInterval = setInterval(() => {
        sendMessage({
          type: 'ping',
          timestamp: new Date().toISOString()
        });
      }, 30000); // Ping every 30 seconds

      return () => clearInterval(pingInterval);
    }
  }, [wsStatus, sendMessage]);

  // Clear last message after it's been processed
  const clearLastMessage = useCallback(() => {
    setLastMessage(null);
  }, []);

  return {
    wsStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    clearLastMessage,
    connectionAttempts,
    isConnected: wsStatus === 'connected'
  };
};