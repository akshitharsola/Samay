import React, { useState, useEffect } from 'react';
import './App.css';
import ConversationFlow from './components/ConversationFlow';
import ServiceDashboard from './components/ServiceDashboard';
import { Toaster } from 'react-hot-toast';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [serviceStatus, setServiceStatus] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initialize the application
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check service status
      const response = await fetch('/api/services/status');
      const data = await response.json();
      setServiceStatus(data.services);
      
      // Create a new session
      const sessionResponse = await fetch('/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: 'default' }),
      });
      const sessionData = await sessionResponse.json();
      setSessionId(sessionData.session_id);
      
    } catch (error) {
      console.error('Failed to initialize app:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <h2>Initializing Samay v5...</h2>
        <p>Setting up your AI assistant session</p>
      </div>
    );
  }

  return (
    <div className="App">
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
      
      <header className="app-header">
        <div className="header-content">
          <h1>🚀 Samay v5</h1>
          <p>Next-Generation API-First AI Assistant</p>
        </div>
        <ServiceDashboard services={serviceStatus} />
      </header>

      <main className="app-main">
        <ConversationFlow 
          sessionId={sessionId}
          onNewSession={initializeApp}
        />
      </main>

      <footer className="app-footer">
        <p>Samay v5 - Built with ❤️ for seamless AI automation</p>
      </footer>
    </div>
  );
}

export default App;