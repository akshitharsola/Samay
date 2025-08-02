import React, { useState } from 'react';

const QueryInput = ({ onSubmit, disabled = false, currentQuery = '' }) => {
  const [query, setQuery] = useState(currentQuery);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !disabled) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit(e);
    }
  };

  // Example queries for demonstration
  const exampleQueries = [
    "Explain quantum computing for beginners",
    "How to optimize React application performance",
    "Latest developments in artificial intelligence",
    "Best practices for database design"
  ];

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  return (
    <div className="query-input-container">
      <div className="query-input-header">
        <h2>
          <i className="fas fa-comment-dots"></i>
          Ask Your Question
        </h2>
        <p>Enter your query below and watch as all 4 AI services respond automatically</p>
      </div>

      <form onSubmit={handleSubmit} className="query-form">
        <textarea
          className="query-textarea"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter your question here... (Ctrl+Enter to submit)"
          disabled={disabled}
          rows={4}
        />

        <div className="query-actions">
          <button
            type="submit"
            className="submit-btn"
            disabled={disabled || !query.trim()}
          >
            {disabled ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                Processing...
              </>
            ) : (
              <>
                <i className="fas fa-rocket"></i>
                Automate Query
              </>
            )}
          </button>
        </div>
      </form>

      {/* Example Queries */}
      {!disabled && !currentQuery && (
        <div className="example-queries">
          <p className="example-title">
            <i className="fas fa-lightbulb"></i>
            Try these examples:
          </p>
          <div className="example-buttons">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                className="example-btn"
                onClick={() => handleExampleClick(example)}
                type="button"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      <style jsx="true">{`
        .example-queries {
          margin-top: 24px;
          padding-top: 24px;
          border-top: 1px solid #e9ecef;
        }

        .example-title {
          font-size: 14px;
          font-weight: 500;
          color: #666;
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .example-buttons {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
        }

        .example-btn {
          padding: 12px 16px;
          border: 1px solid #e9ecef;
          border-radius: 8px;
          background: white;
          color: #333;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: left;
          line-height: 1.4;
        }

        .example-btn:hover {
          border-color: #667eea;
          background: #f8f9ff;
          transform: translateY(-1px);
        }

        @media (max-width: 768px) {
          .example-buttons {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default QueryInput;