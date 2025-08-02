"""
Workflow Automation Engine for Samay v3 - Phase 4
Provides intelligent workflow automation, task chaining, and process optimization
"""

import sqlite3
import json
import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

class WorkflowStatus(Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TriggerType(Enum):
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    CONDITION_BASED = "condition_based"
    MANUAL = "manual"
    COMPLETION_BASED = "completion_based"

class ActionType(Enum):
    CREATE_TASK = "create_task"
    SEND_REMINDER = "send_reminder"
    UPDATE_STATUS = "update_status"
    GENERATE_REPORT = "generate_report"
    SCHEDULE_MEETING = "schedule_meeting"
    SEND_NOTIFICATION = "send_notification"
    EXECUTE_SCRIPT = "execute_script"
    CHAIN_WORKFLOW = "chain_workflow"

@dataclass
class WorkflowTrigger:
    id: Optional[int]
    type: TriggerType
    condition: str
    parameters: Dict[str, Any]
    is_active: bool

@dataclass
class WorkflowAction:
    id: Optional[int]
    type: ActionType
    parameters: Dict[str, Any]
    delay_minutes: int
    retry_count: int
    success_condition: str

@dataclass
class WorkflowStep:
    id: Optional[int]
    step_number: int
    name: str
    description: str
    triggers: List[WorkflowTrigger]
    actions: List[WorkflowAction]
    dependencies: List[int]  # step IDs this depends on
    parallel_execution: bool
    timeout_minutes: Optional[int]

@dataclass
class Workflow:
    id: Optional[int]
    name: str
    description: str
    category: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    created_at: datetime.datetime
    last_executed: Optional[datetime.datetime]
    execution_count: int
    success_rate: float

class WorkflowAutomation:
    def __init__(self, db_path: str = "memory/workflow_automation.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Workflow execution engine
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.active_workflows = {}
        
        # Built-in action handlers
        self.action_handlers = {
            ActionType.CREATE_TASK: self._handle_create_task,
            ActionType.SEND_REMINDER: self._handle_send_reminder,
            ActionType.UPDATE_STATUS: self._handle_update_status,
            ActionType.GENERATE_REPORT: self._handle_generate_report,
            ActionType.SCHEDULE_MEETING: self._handle_schedule_meeting,
            ActionType.SEND_NOTIFICATION: self._handle_send_notification,
            ActionType.CHAIN_WORKFLOW: self._handle_chain_workflow
        }
    
    def _init_database(self):
        """Initialize the workflow automation database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    status TEXT NOT NULL,
                    workflow_data TEXT NOT NULL,  -- JSON representation
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_executed TIMESTAMP,
                    execution_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0
                );
                
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    execution_status TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    execution_data TEXT,  -- JSON
                    error_message TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id)
                );
                
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    step_number INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    step_data TEXT NOT NULL,  -- JSON
                    status TEXT DEFAULT 'pending',
                    executed_at TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id)
                );
                
                CREATE TABLE IF NOT EXISTS automation_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    template_data TEXT NOT NULL,  -- JSON
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS workflow_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    trigger_type TEXT NOT NULL,
                    condition_data TEXT NOT NULL,  -- JSON
                    is_active BOOLEAN DEFAULT TRUE,
                    last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id)
                );
                
                CREATE TABLE IF NOT EXISTS automation_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    workflows_executed INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    failed_executions INTEGER DEFAULT 0,
                    time_saved_minutes INTEGER DEFAULT 0,
                    efficiency_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    # Workflow Creation and Management
    
    def create_workflow(self, name: str, description: str, category: str = "general") -> int:
        """Create a new workflow"""
        workflow = Workflow(
            id=None,
            name=name,
            description=description,
            category=category,
            status=WorkflowStatus.CREATED,
            steps=[],
            created_at=datetime.datetime.now(),
            last_executed=None,
            execution_count=0,
            success_rate=0.0
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflows (name, description, category, status, workflow_data)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, category, WorkflowStatus.CREATED.value,
                  json.dumps(self._workflow_to_dict(workflow))))
            
            return cursor.lastrowid
    
    def add_workflow_step(self, workflow_id: int, step: WorkflowStep) -> int:
        """Add a step to a workflow"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflow_steps 
                (workflow_id, step_number, name, description, step_data)
                VALUES (?, ?, ?, ?, ?)
            """, (workflow_id, step.step_number, step.name, step.description,
                  json.dumps(self._step_to_dict(step))))
            
            return cursor.lastrowid
    
    def create_daily_standup_workflow(self) -> int:
        """Create a predefined daily standup workflow"""
        workflow_id = self.create_workflow(
            name="Daily Standup Automation",
            description="Automates daily standup preparation and follow-up",
            category="productivity"
        )
        
        # Step 1: Morning preparation
        prep_step = WorkflowStep(
            id=None,
            step_number=1,
            name="Standup Preparation",
            description="Gather yesterday's accomplishments and today's priorities",
            triggers=[WorkflowTrigger(
                id=None,
                type=TriggerType.TIME_BASED,
                condition="daily_at_08:30",
                parameters={"time": "08:30", "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
                is_active=True
            )],
            actions=[
                WorkflowAction(
                    id=None,
                    type=ActionType.GENERATE_REPORT,
                    parameters={"report_type": "daily_summary", "include": ["completed_tasks", "priorities"]},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="report_generated"
                ),
                WorkflowAction(
                    id=None,
                    type=ActionType.SEND_REMINDER,
                    parameters={"message": "Daily standup in 30 minutes. Review your summary."},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="reminder_sent"
                )
            ],
            dependencies=[],
            parallel_execution=False,
            timeout_minutes=10
        )
        
        # Step 2: Post-standup follow-up
        followup_step = WorkflowStep(
            id=None,
            step_number=2,
            name="Post-Standup Actions",
            description="Create tasks based on standup commitments",
            triggers=[WorkflowTrigger(
                id=None,
                type=TriggerType.TIME_BASED,
                condition="daily_at_10:00",
                parameters={"time": "10:00", "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
                is_active=True
            )],
            actions=[
                WorkflowAction(
                    id=None,
                    type=ActionType.CREATE_TASK,
                    parameters={"template": "standup_followup", "priority": "medium"},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="task_created"
                )
            ],
            dependencies=[1],
            parallel_execution=False,
            timeout_minutes=5
        )
        
        self.add_workflow_step(workflow_id, prep_step)
        self.add_workflow_step(workflow_id, followup_step)
        
        return workflow_id
    
    def create_project_deadline_workflow(self) -> int:
        """Create a project deadline management workflow"""
        workflow_id = self.create_workflow(
            name="Project Deadline Management",
            description="Automated project deadline tracking and preparation",
            category="project_management"
        )
        
        # Step 1: Weekly deadline review
        review_step = WorkflowStep(
            id=None,
            step_number=1,
            name="Weekly Deadline Review",
            description="Review upcoming deadlines and progress",
            triggers=[WorkflowTrigger(
                id=None,
                type=TriggerType.TIME_BASED,
                condition="weekly_monday_09:00",
                parameters={"time": "09:00", "day": "monday"},
                is_active=True
            )],
            actions=[
                WorkflowAction(
                    id=None,
                    type=ActionType.GENERATE_REPORT,
                    parameters={"report_type": "deadline_overview", "period": "next_2_weeks"},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="report_generated"
                ),
                WorkflowAction(
                    id=None,
                    type=ActionType.SEND_NOTIFICATION,
                    parameters={"message": "Weekly deadline review completed. Check your priorities."},
                    delay_minutes=5,
                    retry_count=1,
                    success_condition="notification_sent"
                )
            ],
            dependencies=[],
            parallel_execution=False,
            timeout_minutes=15
        )
        
        # Step 2: Pre-deadline preparation (3 days before)
        prep_step = WorkflowStep(
            id=None,
            step_number=2,
            name="Pre-Deadline Preparation",
            description="Prepare for upcoming deadlines",
            triggers=[WorkflowTrigger(
                id=None,
                type=TriggerType.CONDITION_BASED,
                condition="deadline_in_3_days",
                parameters={"days_before": 3},
                is_active=True
            )],
            actions=[
                WorkflowAction(
                    id=None,
                    type=ActionType.CREATE_TASK,
                    parameters={"title": "Final review for {deadline_name}", "priority": "high"},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="task_created"
                ),
                WorkflowAction(
                    id=None,
                    type=ActionType.SCHEDULE_MEETING,
                    parameters={"title": "Pre-deadline check", "duration": 30},
                    delay_minutes=60,
                    retry_count=1,
                    success_condition="meeting_scheduled"
                )
            ],
            dependencies=[],
            parallel_execution=True,
            timeout_minutes=10
        )
        
        self.add_workflow_step(workflow_id, review_step)
        self.add_workflow_step(workflow_id, prep_step)
        
        return workflow_id
    
    def create_meeting_automation_workflow(self) -> int:
        """Create meeting preparation and follow-up workflow"""
        workflow_id = self.create_workflow(
            name="Meeting Automation",
            description="Automates meeting preparation and follow-up actions",
            category="meetings"
        )
        
        # Step 1: Pre-meeting preparation
        prep_step = WorkflowStep(
            id=None,
            step_number=1,
            name="Meeting Preparation",
            description="Prepare agenda and gather relevant information",
            triggers=[WorkflowTrigger(
                id=None,
                type=TriggerType.EVENT_BASED,
                condition="meeting_scheduled",
                parameters={"advance_notice_minutes": 60},
                is_active=True
            )],
            actions=[
                WorkflowAction(
                    id=None,
                    type=ActionType.GENERATE_REPORT,
                    parameters={"report_type": "meeting_prep", "include": ["agenda", "action_items"]},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="prep_completed"
                ),
                WorkflowAction(
                    id=None,
                    type=ActionType.SEND_REMINDER,
                    parameters={"message": "Meeting in 1 hour. Review your preparation."},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="reminder_sent"
                )
            ],
            dependencies=[],
            parallel_execution=False,
            timeout_minutes=15
        )
        
        # Step 2: Post-meeting follow-up
        followup_step = WorkflowStep(
            id=None,
            step_number=2,
            name="Post-Meeting Follow-up",
            description="Create action items and send summary",
            triggers=[WorkflowTrigger(
                id=None,
                type=TriggerType.EVENT_BASED,
                condition="meeting_ended",
                parameters={"delay_minutes": 30},
                is_active=True
            )],
            actions=[
                WorkflowAction(
                    id=None,
                    type=ActionType.CREATE_TASK,
                    parameters={"title": "Meeting follow-up: {meeting_name}", "category": "follow_up"},
                    delay_minutes=0,
                    retry_count=1,
                    success_condition="task_created"
                ),
                WorkflowAction(
                    id=None,
                    type=ActionType.SEND_NOTIFICATION,
                    parameters={"message": "Meeting action items created. Review and schedule."},
                    delay_minutes=5,
                    retry_count=1,
                    success_condition="notification_sent"
                )
            ],
            dependencies=[1],
            parallel_execution=False,
            timeout_minutes=10
        )
        
        self.add_workflow_step(workflow_id, prep_step)
        self.add_workflow_step(workflow_id, followup_step)
        
        return workflow_id
    
    # Workflow Execution Engine
    
    async def execute_workflow(self, workflow_id: int, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow with given context"""
        if context is None:
            context = {}
        
        execution_id = self._start_execution_tracking(workflow_id)
        
        try:
            workflow = self._get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            execution_result = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "running",
                "steps_completed": 0,
                "steps_failed": 0,
                "start_time": datetime.datetime.now().isoformat(),
                "context": context,
                "step_results": []
            }
            
            # Execute steps in order, respecting dependencies
            for step in sorted(workflow.steps, key=lambda x: x.step_number):
                step_result = await self._execute_step(step, context)
                execution_result["step_results"].append(step_result)
                
                if step_result["status"] == "completed":
                    execution_result["steps_completed"] += 1
                else:
                    execution_result["steps_failed"] += 1
                    if not step_result.get("continue_on_failure", False):
                        break
            
            # Determine final status
            if execution_result["steps_failed"] == 0:
                execution_result["status"] = "completed"
            elif execution_result["steps_completed"] > 0:
                execution_result["status"] = "partial"
            else:
                execution_result["status"] = "failed"
            
            end_time = datetime.datetime.now()
            execution_result["end_time"] = end_time.isoformat()
            start_time = datetime.datetime.fromisoformat(execution_result["start_time"])
            execution_result["duration_minutes"] = (
                end_time - start_time
            ).total_seconds() / 60
            
            # Update execution tracking
            self._update_execution_tracking(execution_id, execution_result)
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            self._update_execution_tracking(execution_id, {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.datetime.now()
            })
            raise
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_result = {
            "step_id": step.id,
            "step_name": step.name,
            "status": "running",
            "start_time": datetime.datetime.now().isoformat(),
            "actions_completed": 0,
            "actions_failed": 0,
            "action_results": []
        }
        
        try:
            # Check dependencies
            if not self._check_step_dependencies(step, context):
                step_result["status"] = "skipped"
                step_result["reason"] = "dependencies_not_met"
                return step_result
            
            # Execute actions
            if step.parallel_execution:
                # Execute actions in parallel
                tasks = [self._execute_action(action, context) for action in step.actions]
                action_results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Execute actions sequentially
                action_results = []
                for action in step.actions:
                    result = await self._execute_action(action, context)
                    action_results.append(result)
                    
                    # Stop on failure if not configured to continue
                    if result["status"] == "failed" and not action.parameters.get("continue_on_failure", False):
                        break
            
            # Process results
            for result in action_results:
                if isinstance(result, Exception):
                    step_result["action_results"].append({
                        "status": "failed",
                        "error": str(result)
                    })
                    step_result["actions_failed"] += 1
                else:
                    step_result["action_results"].append(result)
                    if result["status"] == "completed":
                        step_result["actions_completed"] += 1
                    else:
                        step_result["actions_failed"] += 1
            
            # Determine step status
            if step_result["actions_failed"] == 0:
                step_result["status"] = "completed"
            elif step_result["actions_completed"] > 0:
                step_result["status"] = "partial"
            else:
                step_result["status"] = "failed"
            
            step_result["end_time"] = datetime.datetime.now().isoformat()
            
            return step_result
            
        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            step_result["end_time"] = datetime.datetime.now().isoformat()
            return step_result
    
    async def _execute_action(self, action: WorkflowAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow action"""
        action_result = {
            "action_type": action.type.value,
            "status": "running",
            "start_time": datetime.datetime.now().isoformat(),
            "attempts": 0,
            "max_attempts": action.retry_count + 1
        }
        
        # Add delay if specified
        if action.delay_minutes > 0:
            await asyncio.sleep(action.delay_minutes * 60)
        
        # Execute with retries
        for attempt in range(action.retry_count + 1):
            action_result["attempts"] = attempt + 1
            
            try:
                # Get action handler
                handler = self.action_handlers.get(action.type)
                if not handler:
                    raise ValueError(f"No handler for action type: {action.type}")
                
                # Execute action
                result = await handler(action.parameters, context)
                
                # Check success condition
                if self._check_success_condition(action.success_condition, result, context):
                    action_result["status"] = "completed"
                    action_result["result"] = result
                    break
                else:
                    action_result["status"] = "failed"
                    action_result["reason"] = "success_condition_not_met"
                    
            except Exception as e:
                self.logger.error(f"Action execution attempt {attempt + 1} failed: {e}")
                action_result["error"] = str(e)
                
                if attempt == action.retry_count:  # Last attempt
                    action_result["status"] = "failed"
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        action_result["end_time"] = datetime.datetime.now().isoformat()
        return action_result
    
    # Action Handlers
    
    async def _handle_create_task(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task creation action"""
        # Mock implementation - would integrate with task scheduler
        task_data = {
            "title": parameters.get("title", "Automated Task"),
            "description": parameters.get("description", "Created by workflow automation"),
            "priority": parameters.get("priority", "medium"),
            "category": parameters.get("category", "automated")
        }
        
        # Simulate task creation
        task_id = hash(json.dumps(task_data)) % 10000
        
        return {
            "action": "create_task",
            "task_id": task_id,
            "task_data": task_data,
            "success": True
        }
    
    async def _handle_send_reminder(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reminder sending action"""
        message = parameters.get("message", "Automated reminder")
        recipient = parameters.get("recipient", "user")
        
        # Mock implementation - would integrate with notification system
        return {
            "action": "send_reminder",
            "message": message,
            "recipient": recipient,
            "sent_at": datetime.datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_update_status(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status update action"""
        entity_type = parameters.get("entity_type", "task")
        entity_id = parameters.get("entity_id")
        new_status = parameters.get("status")
        
        return {
            "action": "update_status",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_status": "unknown",
            "new_status": new_status,
            "success": True
        }
    
    async def _handle_generate_report(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation action"""
        report_type = parameters.get("report_type", "general")
        
        # Mock report generation
        report_data = {
            "type": report_type,
            "generated_at": datetime.datetime.now().isoformat(),
            "data": {"summary": "Report generated successfully"}
        }
        
        return {
            "action": "generate_report",
            "report_type": report_type,
            "report_data": report_data,
            "success": True
        }
    
    async def _handle_schedule_meeting(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle meeting scheduling action"""
        title = parameters.get("title", "Automated Meeting")
        duration = parameters.get("duration", 30)
        
        # Mock meeting scheduling
        meeting_id = f"meeting_{hash(title) % 10000}"
        
        return {
            "action": "schedule_meeting",
            "meeting_id": meeting_id,
            "title": title,
            "duration": duration,
            "scheduled_at": datetime.datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_send_notification(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification sending action"""
        message = parameters.get("message", "Automated notification")
        
        return {
            "action": "send_notification",
            "message": message,
            "sent_at": datetime.datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_chain_workflow(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow chaining action"""
        workflow_id = parameters.get("workflow_id")
        
        if workflow_id:
            # Execute chained workflow
            result = await self.execute_workflow(workflow_id, context)
            return {
                "action": "chain_workflow",
                "chained_workflow_id": workflow_id,
                "execution_result": result,
                "success": result["status"] == "completed"
            }
        
        return {
            "action": "chain_workflow",
            "error": "No workflow_id specified",
            "success": False
        }
    
    # Helper Methods
    
    def _check_step_dependencies(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Check if step dependencies are met"""
        # For now, assume dependencies are met
        # In real implementation, would check context for completed steps
        return True
    
    def _check_success_condition(self, condition: str, result: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if success condition is met"""
        if not condition:
            return True
        
        # Simple condition checking
        if condition == "success":
            return result.get("success", False)
        elif condition in result:
            return bool(result[condition])
        
        return True
    
    def _start_execution_tracking(self, workflow_id: int) -> int:
        """Start tracking workflow execution"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflow_executions (workflow_id, execution_status)
                VALUES (?, ?)
            """, (workflow_id, "running"))
            
            return cursor.lastrowid
    
    def _update_execution_tracking(self, execution_id: int, result: Dict[str, Any]):
        """Update execution tracking with results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE workflow_executions 
                SET execution_status = ?, end_time = ?, execution_data = ?
                WHERE id = ?
            """, (result.get("status"), result.get("end_time"), 
                  json.dumps(result), execution_id))
    
    def _get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM workflows WHERE id = ?
            """, (workflow_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Get workflow steps
            cursor = conn.execute("""
                SELECT * FROM workflow_steps WHERE workflow_id = ?
                ORDER BY step_number
            """, (workflow_id,))
            
            steps_data = cursor.fetchall()
            steps = [self._dict_to_step(json.loads(step[5])) for step in steps_data]
            
            workflow_data = json.loads(row[5])
            workflow_data["steps"] = steps
            
            return self._dict_to_workflow(workflow_data)
    
    def _workflow_to_dict(self, workflow: Workflow) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "category": workflow.category,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "last_executed": workflow.last_executed.isoformat() if workflow.last_executed else None,
            "execution_count": workflow.execution_count,
            "success_rate": workflow.success_rate
        }
    
    def _step_to_dict(self, step: WorkflowStep) -> Dict[str, Any]:
        """Convert workflow step to dictionary"""
        return {
            "id": step.id,
            "step_number": step.step_number,
            "name": step.name,
            "description": step.description,
            "triggers": [self._trigger_to_dict(t) for t in step.triggers],
            "actions": [self._action_to_dict(a) for a in step.actions],
            "dependencies": step.dependencies,
            "parallel_execution": step.parallel_execution,
            "timeout_minutes": step.timeout_minutes
        }
    
    def _trigger_to_dict(self, trigger: WorkflowTrigger) -> Dict[str, Any]:
        """Convert trigger to dictionary"""
        return {
            "id": trigger.id,
            "type": trigger.type.value,
            "condition": trigger.condition,
            "parameters": trigger.parameters,
            "is_active": trigger.is_active
        }
    
    def _action_to_dict(self, action: WorkflowAction) -> Dict[str, Any]:
        """Convert action to dictionary"""
        return {
            "id": action.id,
            "type": action.type.value,
            "parameters": action.parameters,
            "delay_minutes": action.delay_minutes,
            "retry_count": action.retry_count,
            "success_condition": action.success_condition
        }
    
    def _dict_to_workflow(self, data: Dict[str, Any]) -> Workflow:
        """Convert dictionary to workflow"""
        return Workflow(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "general"),
            status=WorkflowStatus(data["status"]),
            steps=data.get("steps", []),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            last_executed=datetime.datetime.fromisoformat(data["last_executed"]) if data.get("last_executed") else None,
            execution_count=data.get("execution_count", 0),
            success_rate=data.get("success_rate", 0.0)
        )
    
    def _dict_to_step(self, data: Dict[str, Any]) -> WorkflowStep:
        """Convert dictionary to workflow step"""
        return WorkflowStep(
            id=data.get("id"),
            step_number=data["step_number"],
            name=data["name"],
            description=data.get("description", ""),
            triggers=[self._dict_to_trigger(t) for t in data.get("triggers", [])],
            actions=[self._dict_to_action(a) for a in data.get("actions", [])],
            dependencies=data.get("dependencies", []),
            parallel_execution=data.get("parallel_execution", False),
            timeout_minutes=data.get("timeout_minutes")
        )
    
    def _dict_to_trigger(self, data: Dict[str, Any]) -> WorkflowTrigger:
        """Convert dictionary to trigger"""
        return WorkflowTrigger(
            id=data.get("id"),
            type=TriggerType(data["type"]),
            condition=data["condition"],
            parameters=data.get("parameters", {}),
            is_active=data.get("is_active", True)
        )
    
    def _dict_to_action(self, data: Dict[str, Any]) -> WorkflowAction:
        """Convert dictionary to action"""
        return WorkflowAction(
            id=data.get("id"),
            type=ActionType(data["type"]),
            parameters=data.get("parameters", {}),
            delay_minutes=data.get("delay_minutes", 0),
            retry_count=data.get("retry_count", 0),
            success_condition=data.get("success_condition", "success")
        )
    
    def get_workflow_analytics(self) -> Dict[str, Any]:
        """Get workflow automation analytics"""
        with sqlite3.connect(self.db_path) as conn:
            # Get execution statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN execution_status = 'completed' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN execution_status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(CASE WHEN end_time IS NOT NULL THEN 
                        (julianday(end_time) - julianday(start_time)) * 24 * 60
                    END) as avg_duration_minutes
                FROM workflow_executions 
                WHERE start_time >= datetime('now', '-30 days')
            """)
            
            stats = cursor.fetchone()
            
            # Get workflow usage
            cursor = conn.execute("""
                SELECT name, execution_count, success_rate
                FROM workflows 
                ORDER BY execution_count DESC
                LIMIT 5
            """)
            
            top_workflows = cursor.fetchall()
            
            return {
                "total_executions": stats[0] or 0,
                "success_rate": (stats[1] / max(stats[0], 1)) * 100,
                "failure_rate": (stats[2] / max(stats[0], 1)) * 100,
                "avg_duration_minutes": stats[3] or 0,
                "top_workflows": [
                    {"name": row[0], "executions": row[1], "success_rate": row[2]}
                    for row in top_workflows
                ]
            }

# Example usage and testing
if __name__ == "__main__":
    automation = WorkflowAutomation()
    
    # Create predefined workflows
    standup_id = automation.create_daily_standup_workflow()
    deadline_id = automation.create_project_deadline_workflow()
    meeting_id = automation.create_meeting_automation_workflow()
    
    print(f"Created workflows:")
    print(f"- Daily Standup: {standup_id}")
    print(f"- Project Deadlines: {deadline_id}")
    print(f"- Meeting Automation: {meeting_id}")
    
    # Test workflow execution
    async def test_execution():
        context = {"user_id": 1, "current_project": "Samay v3"}
        result = await automation.execute_workflow(standup_id, context)
        print(f"\nWorkflow execution result:")
        print(json.dumps(result, indent=2, default=str))
    
    # Run test
    import asyncio
    asyncio.run(test_execution())
    
    print("Workflow Automation ready!")