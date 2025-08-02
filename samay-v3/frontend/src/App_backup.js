import React, { useState } from 'react';
import SimplifiedApp from './SimplifiedApp';
import EnhancedApp from './EnhancedApp';
import { Settings } from 'lucide-react';

function App() {
  const [useSimplified, setUseSimplified] = useState(true);

  if (useSimplified) {
    return (
      <div style={{ position: 'relative' }}>
        <button 
          onClick={() => setUseSimplified(false)}
          style={{
            position: 'fixed',
            top: '10px',
            right: '10px',
            zIndex: 1000,
            background: '#007acc',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            padding: '8px 12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
          title="Switch to Enhanced Interface"
        >
          <Settings size={16} />
          Enhanced
        </button>
        <SimplifiedApp />
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <button 
        onClick={() => setUseSimplified(true)}
        style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          zIndex: 1000,
          background: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          padding: '8px 12px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '5px'
        }}
        title="Switch to Simplified Interface"
      >
        <Settings size={16} />
        Simplified
      </button>
      <EnhancedApp />
    </div>
  );
}

export default App;