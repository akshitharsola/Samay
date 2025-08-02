import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  TrendingUp, 
  CheckSquare, 
  AlertCircle,
  Target,
  Activity,
  BarChart3
} from 'lucide-react';
import axios from 'axios';

const SmartDashboard = ({ sessionId }) => {
  const [schedule, setSchedule] = useState(null);
  const [productivity, setProductivity] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch all dashboard data in parallel
      const [scheduleRes, productivityRes, suggestionsRes] = await Promise.all([
        axios.get('/tasks/schedule'),
        axios.get('/analytics/productivity'),
        axios.post('/assistant/suggestions', {
          current_activity: 'working',
          focus_state: 'focused',
          energy_level: 8,
          mood: 'productive',
          location: 'office',
          time_of_day: getCurrentTimeOfDay(),
          workload_status: 'moderate'
        })
      ]);

      setSchedule(scheduleRes.data.schedule);
      setProductivity(productivityRes.data.insights);
      setSuggestions(suggestionsRes.data.suggestions.slice(0, 5)); // Top 5 suggestions
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    return 'evening';
  };

  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="smart-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading smart dashboard...</p>
      </div>
    );
  }

  return (
    <div className="smart-dashboard">
      <div className="dashboard-header">
        <h2>🎯 Smart Dashboard</h2>
        <div className="dashboard-actions">
          <button onClick={fetchDashboardData} className="refresh-btn">
            <Activity size={16} />
            Refresh
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Today's Schedule */}
        <div className="dashboard-card schedule-card">
          <div className="card-header">
            <Calendar size={20} />
            <h3>Today's Smart Schedule</h3>
          </div>
          <div className="card-content">
            {schedule?.time_blocks && schedule.time_blocks.length > 0 ? (
              <div className="time-blocks">
                {schedule.time_blocks.slice(0, 6).map((block, index) => (
                  <div key={index} className="time-block">
                    <div className="time-info">
                      <Clock size={14} />
                      <span>{block.start_time} - {block.end_time}</span>
                    </div>
                    <div className="block-details">
                      <span className="task-title">{block.task_title || block.activity}</span>
                      <div 
                        className="priority-indicator"
                        style={{ backgroundColor: getPriorityColor(block.priority) }}
                      />
                    </div>
                    {block.estimated_duration && (
                      <div className="duration">
                        {formatDuration(block.estimated_duration)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <Calendar size={24} />
                <p>No scheduled tasks for today</p>
                <button className="create-task-btn">Create First Task</button>
              </div>
            )}
          </div>
        </div>

        {/* Productivity Insights */}
        <div className="dashboard-card productivity-card">
          <div className="card-header">
            <TrendingUp size={20} />
            <h3>Productivity Insights</h3>
          </div>
          <div className="card-content">
            {productivity ? (
              <div className="productivity-metrics">
                <div className="metric">
                  <div className="metric-value">
                    {(productivity.task_completion_rate * 100 || 75).toFixed(0)}%
                  </div>
                  <div className="metric-label">Task Completion</div>
                </div>
                <div className="metric">
                  <div className="metric-value">
                    {productivity.focus_score || 8.2}
                  </div>
                  <div className="metric-label">Focus Score</div>
                </div>
                <div className="metric">
                  <div className="metric-value">
                    {productivity.productivity_trend || '+12%'}
                  </div>
                  <div className="metric-label">Weekly Trend</div>
                </div>
                
                {productivity.productivity_trends && (
                  <div className="trend-chart">
                    <BarChart3 size={16} />
                    <span>7-day productivity trend</span>
                    <div className="mini-chart">
                      {productivity.productivity_trends.slice(-7).map((point, index) => (
                        <div 
                          key={index} 
                          className="chart-bar"
                          style={{ height: `${point * 100}%` }}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <BarChart3 size={24} />
                <p>Building productivity insights...</p>
              </div>
            )}
          </div>
        </div>

        {/* Proactive Suggestions */}
        <div className="dashboard-card suggestions-card">
          <div className="card-header">
            <Target size={20} />
            <h3>Smart Suggestions</h3>
          </div>
          <div className="card-content">
            {suggestions.length > 0 ? (
              <div className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                  <div key={suggestion.suggestion_id || index} className="suggestion-item">
                    <div className="suggestion-content">
                      <div className="suggestion-category">
                        {suggestion.category === 'task' && <CheckSquare size={14} />}
                        {suggestion.category === 'productivity' && <TrendingUp size={14} />}
                        {suggestion.category === 'break' && <Clock size={14} />}
                        {suggestion.category === 'deadline' && <AlertCircle size={14} />}
                        <span>{suggestion.category}</span>
                      </div>
                      <p className="suggestion-text">{suggestion.content}</p>
                      <div className="suggestion-meta">
                        <span className={`priority ${suggestion.priority}`}>
                          {suggestion.priority}
                        </span>
                        <span className="confidence">
                          {(suggestion.relevance_score * 100).toFixed(0)}% relevant
                        </span>
                      </div>
                    </div>
                    <div className="suggestion-actions">
                      <button 
                        className="action-btn accept"
                        onClick={() => acknowledgeSuggestion(suggestion.suggestion_id, true)}
                      >
                        ✓
                      </button>
                      <button 
                        className="action-btn dismiss"
                        onClick={() => acknowledgeSuggestion(suggestion.suggestion_id, false)}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <Target size={24} />
                <p>No suggestions available</p>
                <small>Suggestions will appear based on your activity</small>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card actions-card">
          <div className="card-header">
            <CheckSquare size={20} />
            <h3>Quick Actions</h3>
          </div>
          <div className="card-content">
            <div className="quick-actions">
              <button className="action-button task">
                <CheckSquare size={16} />
                <span>Create Task</span>
              </button>
              <button className="action-button schedule">
                <Calendar size={16} />
                <span>View Schedule</span>
              </button>
              <button className="action-button workflow">
                <Activity size={16} />
                <span>Run Workflow</span>
              </button>
              <button className="action-button analytics">
                <BarChart3 size={16} />
                <span>View Analytics</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  async function acknowledgeSuggestion(suggestionId, helpful) {
    try {
      await axios.post(`/assistant/acknowledge/${suggestionId}?helpful=${helpful}`);
      // Remove the acknowledged suggestion from the list
      setSuggestions(prev => prev.filter(s => s.suggestion_id !== suggestionId));
    } catch (error) {
      console.error('Failed to acknowledge suggestion:', error);
    }
  }
};

export default SmartDashboard;