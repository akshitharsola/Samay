import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Plus, 
  Play, 
  Pause,
  Settings,
  Clock,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Copy,
  Trash2,
  Edit
} from 'lucide-react';
import axios from 'axios';

const WorkflowBuilder = () => {
  const [workflows, setWorkflows] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [showBuilder, setShowBuilder] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [workflowForm, setWorkflowForm] = useState({
    name: '',
    description: '',
    trigger_type: 'manual',
    trigger_data: {},
    steps: []
  });
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
    fetchWorkflows();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get('/workflows/templates');
      setTemplates(response.data.templates);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const fetchWorkflows = async () => {
    try {
      // Note: This endpoint doesn't exist yet, but would list user workflows
      // For now, we'll use templates as example workflows
      setWorkflows([]);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const createWorkflow = async () => {
    try {
      const response = await axios.post('/workflows/create', workflowForm);
      setWorkflows(prev => [...prev, { ...workflowForm, id: response.data.workflow_id }]);
      resetForm();
      setShowBuilder(false);
    } catch (error) {
      console.error('Failed to create workflow:', error);
    }
  };

  const executeWorkflow = async (workflowId, context = {}) => {
    try {
      const response = await axios.post(`/workflows/execute/${workflowId}`, context);
      setExecutions(prev => [response.data, ...prev]);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
    }
  };

  const resetForm = () => {
    setWorkflowForm({
      name: '',
      description: '',
      trigger_type: 'manual',
      trigger_data: {},
      steps: []
    });
  };

  const addStep = () => {
    setWorkflowForm(prev => ({
      ...prev,
      steps: [...prev.steps, { action: 'create_task', params: {} }]
    }));
  };

  const updateStep = (index, field, value) => {
    setWorkflowForm(prev => ({
      ...prev,
      steps: prev.steps.map((step, i) => 
        i === index ? { ...step, [field]: value } : step
      )
    }));
  };

  const removeStep = (index) => {
    setWorkflowForm(prev => ({
      ...prev,
      steps: prev.steps.filter((_, i) => i !== index)
    }));
  };

  const loadTemplate = (template) => {
    const templateSteps = getTemplateSteps(template.id);
    setWorkflowForm({
      name: template.name,
      description: template.description,
      trigger_type: template.id === 'daily_standup' ? 'time' : 'manual',
      trigger_data: template.id === 'daily_standup' ? { time: '09:00' } : {},
      steps: templateSteps
    });
    setShowBuilder(true);
  };

  const getTemplateSteps = (templateId) => {
    switch (templateId) {
      case 'daily_standup':
        return [
          { action: 'create_task', params: { title: 'Review yesterday\'s progress' } },
          { action: 'send_reminder', params: { message: 'Daily standup in 5 minutes' } },
          { action: 'generate_report', params: { type: 'daily_summary' } }
        ];
      case 'project_deadline':
        return [
          { action: 'check_deadlines', params: { days_ahead: 3 } },
          { action: 'send_reminder', params: { message: 'Upcoming deadline reminder' } },
          { action: 'create_task', params: { title: 'Prepare for deadline' } }
        ];
      case 'meeting_automation':
        return [
          { action: 'send_reminder', params: { message: 'Meeting starting in 15 minutes' } },
          { action: 'prepare_agenda', params: { template: 'standard' } },
          { action: 'create_task', params: { title: 'Follow up on action items' } }
        ];
      default:
        return [];
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'create_task': return <CheckCircle size={16} />;
      case 'send_reminder': return <AlertCircle size={16} />;
      case 'generate_report': return <BarChart3 size={16} />;
      case 'check_deadlines': return <Clock size={16} />;
      default: return <Zap size={16} />;
    }
  };

  const getTriggerIcon = (trigger) => {
    switch (trigger) {
      case 'time': return <Clock size={16} />;
      case 'event': return <Zap size={16} />;
      case 'manual': return <Play size={16} />;
      default: return <Settings size={16} />;
    }
  };

  if (loading) {
    return (
      <div className="workflow-builder loading">
        <div className="loading-spinner"></div>
        <p>Loading workflow builder...</p>
      </div>
    );
  }

  return (
    <div className="workflow-builder">
      <div className="builder-header">
        <div className="header-title">
          <Zap size={20} />
          <h3>Workflow Automation</h3>
        </div>
        <div className="header-actions">
          <button 
            onClick={() => setShowBuilder(true)}
            className="create-workflow-btn"
          >
            <Plus size={16} />
            Create Workflow
          </button>
        </div>
      </div>

      {showBuilder ? (
        <div className="workflow-builder-form">
          <div className="form-header">
            <h4>Create New Workflow</h4>
            <button onClick={() => { setShowBuilder(false); resetForm(); }}>
              ✕
            </button>
          </div>

          <div className="form-content">
            <div className="form-row">
              <div className="form-group">
                <label>Workflow Name</label>
                <input
                  type="text"
                  value={workflowForm.name}
                  onChange={(e) => setWorkflowForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter workflow name..."
                />
              </div>
              <div className="form-group">
                <label>Trigger Type</label>
                <select
                  value={workflowForm.trigger_type}
                  onChange={(e) => setWorkflowForm(prev => ({ ...prev, trigger_type: e.target.value }))}
                >
                  <option value="manual">Manual</option>
                  <option value="time">Time-based</option>
                  <option value="event">Event-based</option>
                  <option value="condition">Condition-based</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={workflowForm.description}
                onChange={(e) => setWorkflowForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe what this workflow does..."
                rows={2}
              />
            </div>

            {workflowForm.trigger_type === 'time' && (
              <div className="form-group">
                <label>Schedule Time</label>
                <input
                  type="time"
                  value={workflowForm.trigger_data.time || ''}
                  onChange={(e) => setWorkflowForm(prev => ({
                    ...prev,
                    trigger_data: { ...prev.trigger_data, time: e.target.value }
                  }))}
                />
              </div>
            )}

            <div className="workflow-steps">
              <div className="steps-header">
                <h5>Workflow Steps</h5>
                <button onClick={addStep} className="add-step-btn">
                  <Plus size={14} />
                  Add Step
                </button>
              </div>

              {workflowForm.steps.map((step, index) => (
                <div key={index} className="workflow-step">
                  <div className="step-header">
                    <span className="step-number">{index + 1}</span>
                    <select
                      value={step.action}
                      onChange={(e) => updateStep(index, 'action', e.target.value)}
                    >
                      <option value="create_task">Create Task</option>
                      <option value="send_reminder">Send Reminder</option>
                      <option value="generate_report">Generate Report</option>
                      <option value="check_deadlines">Check Deadlines</option>
                      <option value="update_status">Update Status</option>
                    </select>
                    <button onClick={() => removeStep(index)} className="remove-step">
                      <Trash2 size={14} />
                    </button>
                  </div>

                  <div className="step-params">
                    {step.action === 'create_task' && (
                      <input
                        type="text"
                        placeholder="Task title..."
                        value={step.params.title || ''}
                        onChange={(e) => updateStep(index, 'params', { ...step.params, title: e.target.value })}
                      />
                    )}
                    {step.action === 'send_reminder' && (
                      <input
                        type="text"
                        placeholder="Reminder message..."
                        value={step.params.message || ''}
                        onChange={(e) => updateStep(index, 'params', { ...step.params, message: e.target.value })}
                      />
                    )}
                    {step.action === 'generate_report' && (
                      <select
                        value={step.params.type || 'daily_summary'}
                        onChange={(e) => updateStep(index, 'params', { ...step.params, type: e.target.value })}
                      >
                        <option value="daily_summary">Daily Summary</option>
                        <option value="weekly_report">Weekly Report</option>
                        <option value="task_progress">Task Progress</option>
                      </select>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="form-actions">
              <button onClick={createWorkflow} className="create-btn">
                Create Workflow
              </button>
              <button onClick={() => { setShowBuilder(false); resetForm(); }} className="cancel-btn">
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="workflows-content">
          {/* Templates */}
          <div className="workflows-section">
            <h4>📋 Workflow Templates</h4>
            <div className="templates-grid">
              {templates.map(template => (
                <div key={template.id} className="template-card">
                  <div className="template-info">
                    <h5>{template.name}</h5>
                    <p>{template.description}</p>
                  </div>
                  <div className="template-actions">
                    <button onClick={() => loadTemplate(template)} className="use-template-btn">
                      <Copy size={14} />
                      Use Template
                    </button>
                    <button onClick={() => executeWorkflow(template.id)} className="execute-btn">
                      <Play size={14} />
                      Execute
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* User Workflows */}
          {workflows.length > 0 && (
            <div className="workflows-section">
              <h4>⚙️ Your Workflows</h4>
              <div className="workflows-grid">
                {workflows.map(workflow => (
                  <div key={workflow.id} className="workflow-card">
                    <div className="workflow-header">
                      <div className="workflow-info">
                        <h5>{workflow.name}</h5>
                        <p>{workflow.description}</p>
                      </div>
                      <div className="workflow-trigger">
                        {getTriggerIcon(workflow.trigger_type)}
                        <span>{workflow.trigger_type}</span>
                      </div>
                    </div>
                    
                    <div className="workflow-steps-preview">
                      {workflow.steps.slice(0, 3).map((step, index) => (
                        <div key={index} className="step-preview">
                          {getActionIcon(step.action)}
                          <span>{step.action.replace('_', ' ')}</span>
                        </div>
                      ))}
                      {workflow.steps.length > 3 && (
                        <span className="more-steps">+{workflow.steps.length - 3} more</span>
                      )}
                    </div>

                    <div className="workflow-actions">
                      <button onClick={() => executeWorkflow(workflow.id)} className="execute-btn">
                        <Play size={14} />
                        Execute
                      </button>
                      <button onClick={() => setSelectedWorkflow(workflow)} className="edit-btn">
                        <Edit size={14} />
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Executions */}
          {executions.length > 0 && (
            <div className="workflows-section">
              <h4>📈 Recent Executions</h4>
              <div className="executions-list">
                {executions.slice(0, 10).map((execution, index) => (
                  <div key={index} className="execution-item">
                    <div className="execution-info">
                      <span className="workflow-name">{execution.workflow_id}</span>
                      <span className="execution-time">
                        {new Date(execution.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="execution-status">
                      {execution.execution_result?.status === 'completed' ? (
                        <CheckCircle size={16} color="#22c55e" />
                      ) : (
                        <AlertCircle size={16} color="#ef4444" />
                      )}
                      <span>{execution.execution_result?.status || 'unknown'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkflowBuilder;