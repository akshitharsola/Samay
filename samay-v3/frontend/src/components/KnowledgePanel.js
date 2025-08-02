import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Plus, 
  BookOpen, 
  FileText,
  MessageSquare,
  Briefcase,
  User,
  Lightbulb,
  File,
  Link,
  Tag,
  Calendar,
  Brain,
  Filter
} from 'lucide-react';
import axios from 'axios';

const KnowledgePanel = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState('semantic');
  const [searchResults, setSearchResults] = useState([]);
  const [insights, setInsights] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [itemForm, setItemForm] = useState({
    title: '',
    content: '',
    knowledge_type: 'document',
    category: 'general',
    tags: []
  });
  const [newTag, setNewTag] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('all');

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const response = await axios.get('/knowledge/insights');
      setInsights(response.data.insights.slice(0, 5));
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    }
  };

  const performSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const response = await axios.get(`/knowledge/search?query=${encodeURIComponent(searchQuery)}&search_mode=${searchMode}`);
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const addKnowledgeItem = async () => {
    if (!itemForm.title.trim() || !itemForm.content.trim()) return;

    try {
      const response = await axios.post('/knowledge/add', itemForm);
      console.log('Knowledge item added:', response.data);
      resetForm();
      setShowAddForm(false);
      // Refresh insights
      fetchInsights();
    } catch (error) {
      console.error('Failed to add knowledge item:', error);
    }
  };

  const resetForm = () => {
    setItemForm({
      title: '',
      content: '',
      knowledge_type: 'document',
      category: 'general',
      tags: []
    });
    setNewTag('');
  };

  const addTag = () => {
    if (newTag.trim() && !itemForm.tags.includes(newTag.trim())) {
      setItemForm(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove) => {
    setItemForm(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      if (e.target.classList.contains('search-input')) {
        performSearch();
      } else if (e.target.classList.contains('tag-input')) {
        e.preventDefault();
        addTag();
      }
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'document': return <FileText size={16} />;
      case 'conversation': return <MessageSquare size={16} />;
      case 'project': return <Briefcase size={16} />;
      case 'contact': return <User size={16} />;
      case 'insight': return <Lightbulb size={16} />;
      case 'template': return <File size={16} />;
      case 'reference': return <Link size={16} />;
      default: return <BookOpen size={16} />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'document': return '#3b82f6';
      case 'conversation': return '#10b981';
      case 'project': return '#f59e0b';
      case 'contact': return '#8b5cf6';
      case 'insight': return '#ef4444';
      case 'template': return '#06b6d4';
      case 'reference': return '#84cc16';
      default: return '#6b7280';
    }
  };

  const truncateContent = (content, maxLength = 150) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const filteredResults = searchResults.filter(result => {
    if (selectedFilter === 'all') return true;
    return result.knowledge_type === selectedFilter;
  });

  return (
    <div className="knowledge-panel">
      <div className="panel-header">
        <div className="header-title">
          <Brain size={20} />
          <h3>Knowledge Management</h3>
        </div>
        <div className="header-actions">
          <button 
            onClick={() => setShowAddForm(true)}
            className="add-knowledge-btn"
          >
            <Plus size={16} />
            Add Knowledge
          </button>
        </div>
      </div>

      {showAddForm && (
        <div className="add-knowledge-form">
          <div className="form-header">
            <h4>Add Knowledge Item</h4>
            <button onClick={() => { setShowAddForm(false); resetForm(); }}>
              ✕
            </button>
          </div>

          <div className="form-content">
            <div className="form-row">
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={itemForm.title}
                  onChange={(e) => setItemForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter knowledge item title..."
                />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select
                  value={itemForm.knowledge_type}
                  onChange={(e) => setItemForm(prev => ({ ...prev, knowledge_type: e.target.value }))}
                >
                  <option value="document">Document</option>
                  <option value="conversation">Conversation</option>
                  <option value="project">Project</option>
                  <option value="contact">Contact</option>
                  <option value="insight">Insight</option>
                  <option value="template">Template</option>
                  <option value="reference">Reference</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Content</label>
              <textarea
                value={itemForm.content}
                onChange={(e) => setItemForm(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Enter the knowledge content..."
                rows={4}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Category</label>
                <input
                  type="text"
                  value={itemForm.category}
                  onChange={(e) => setItemForm(prev => ({ ...prev, category: e.target.value }))}
                  placeholder="e.g., development, research, personal..."
                />
              </div>
            </div>

            <div className="form-group">
              <label>Tags</label>
              <div className="tags-input">
                <div className="tags-list">
                  {itemForm.tags.map(tag => (
                    <span key={tag} className="tag">
                      {tag}
                      <button onClick={() => removeTag(tag)}>×</button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  className="tag-input"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Add tags..."
                />
                <button onClick={addTag} className="add-tag-btn">
                  <Plus size={14} />
                </button>
              </div>
            </div>

            <div className="form-actions">
              <button onClick={addKnowledgeItem} className="save-btn">
                Add Knowledge Item
              </button>
              <button onClick={() => { setShowAddForm(false); resetForm(); }} className="cancel-btn">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="knowledge-content">
        {/* Search Section */}
        <div className="search-section">
          <div className="search-header">
            <h4>🔍 Knowledge Search</h4>
          </div>
          
          <div className="search-controls">
            <div className="search-input-group">
              <input
                type="text"
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search your knowledge base..."
              />
              <button 
                onClick={performSearch}
                disabled={!searchQuery.trim() || isSearching}
                className="search-btn"
              >
                {isSearching ? (
                  <div className="loading-spinner small"></div>
                ) : (
                  <Search size={16} />
                )}
              </button>
            </div>

            <div className="search-options">
              <div className="search-mode">
                <label>Search Mode:</label>
                <select
                  value={searchMode}
                  onChange={(e) => setSearchMode(e.target.value)}
                >
                  <option value="semantic">Semantic</option>
                  <option value="exact">Exact Match</option>
                  <option value="fuzzy">Fuzzy</option>
                  <option value="context">Context-Aware</option>
                </select>
              </div>

              <div className="result-filter">
                <Filter size={14} />
                <select
                  value={selectedFilter}
                  onChange={(e) => setSelectedFilter(e.target.value)}
                >
                  <option value="all">All Types</option>
                  <option value="document">Documents</option>
                  <option value="conversation">Conversations</option>
                  <option value="project">Projects</option>
                  <option value="contact">Contacts</option>
                  <option value="insight">Insights</option>
                  <option value="template">Templates</option>
                  <option value="reference">References</option>
                </select>
              </div>
            </div>
          </div>

          {/* Search Results */}
          {filteredResults.length > 0 && (
            <div className="search-results">
              <div className="results-header">
                <span>Found {filteredResults.length} results</span>
              </div>
              <div className="results-list">
                {filteredResults.map((result, index) => (
                  <div key={result.item_id || index} className="result-item">
                    <div className="result-header">
                      <div className="result-type" style={{ color: getTypeColor(result.knowledge_type) }}>
                        {getTypeIcon(result.knowledge_type)}
                        <span>{result.knowledge_type}</span>
                      </div>
                      <div className="result-meta">
                        <Calendar size={12} />
                        <span>{new Date(result.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    <h5 className="result-title">{result.title}</h5>
                    <p className="result-content">{truncateContent(result.content)}</p>
                    
                    <div className="result-footer">
                      <div className="result-tags">
                        {result.tags && result.tags.map(tag => (
                          <span key={tag} className="result-tag">
                            <Tag size={10} />
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="result-category">
                        <span className="category-badge">{result.category}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Insights Section */}
        <div className="insights-section">
          <div className="insights-header">
            <h4>💡 AI-Generated Insights</h4>
            <button onClick={fetchInsights} className="refresh-insights">
              <Brain size={14} />
              Refresh
            </button>
          </div>

          {insights.length > 0 ? (
            <div className="insights-list">
              {insights.map((insight, index) => (
                <div key={insight.insight_id || index} className="insight-item">
                  <div className="insight-header">
                    <Lightbulb size={16} />
                    <span className="insight-type">{insight.type || 'General'}</span>
                  </div>
                  <p className="insight-content">{insight.content}</p>
                  <div className="insight-meta">
                    <span className="confidence">
                      Confidence: {(insight.confidence * 100 || 85).toFixed(0)}%
                    </span>
                    <span className="timestamp">
                      {new Date(insight.created_at || Date.now()).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-insights">
              <Brain size={24} />
              <p>No insights available yet</p>
              <small>Add more knowledge items to generate insights</small>
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="knowledge-stats">
          <h4>📊 Knowledge Stats</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <FileText size={16} />
              <span>Documents: {searchResults.filter(r => r.knowledge_type === 'document').length}</span>
            </div>
            <div className="stat-item">
              <MessageSquare size={16} />
              <span>Conversations: {searchResults.filter(r => r.knowledge_type === 'conversation').length}</span>
            </div>
            <div className="stat-item">
              <Briefcase size={16} />
              <span>Projects: {searchResults.filter(r => r.knowledge_type === 'project').length}</span>
            </div>
            <div className="stat-item">
              <Lightbulb size={16} />
              <span>Insights: {insights.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgePanel;