#!/usr/bin/env python3
"""
Samay v3 - Task Scheduler System
===============================
Local task management and scheduling for companion AI
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import re
from enum import Enum


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


@dataclass
class Task:
    """Individual task with scheduling information"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: str
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: Optional[int] = None  # minutes
    tags: List[str] = None
    dependencies: List[str] = None  # task IDs
    notes: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
        if self.notes is None:
            self.notes = []


@dataclass
class Reminder:
    """Reminder with timing and context"""
    id: str
    task_id: Optional[str]
    title: str
    message: str
    remind_at: str
    is_active: bool = True
    created_at: str = None
    reminder_type: str = "general"  # task, appointment, follow_up
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Schedule:
    """Daily schedule with time blocks"""
    date: str
    time_blocks: List[Dict[str, Any]]
    available_slots: List[Dict[str, str]]
    scheduled_tasks: List[str]  # task IDs


class TaskScheduler:
    """Intelligent task scheduling and management system"""
    
    def __init__(self, memory_dir: str = "memory", user_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.user_id = user_id
        
        # Initialize database
        self.db_path = self.memory_dir / "tasks.db"
        self.init_database()
        
        # Load current tasks and reminders
        self.active_tasks = self._load_active_tasks()
        self.pending_reminders = self._load_pending_reminders()
        
        print(f"📅 TaskScheduler initialized for {user_id}")
        print(f"📁 Database: {self.db_path}")
        print(f"📋 Active tasks: {len(self.active_tasks)}")
        print(f"⏰ Pending reminders: {len(self.pending_reminders)}")
    
    def init_database(self):
        """Initialize SQLite database for task storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    description TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_at TEXT,
                    due_date TEXT,
                    completed_at TEXT,
                    estimated_duration INTEGER,
                    tags TEXT,
                    dependencies TEXT,
                    notes TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    task_id TEXT,
                    title TEXT,
                    message TEXT,
                    remind_at TEXT,
                    is_active BOOLEAN,
                    created_at TEXT,
                    reminder_type TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    date TEXT PRIMARY KEY,
                    user_id TEXT,
                    time_blocks TEXT,
                    available_slots TEXT,
                    scheduled_tasks TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    task_id TEXT,
                    action TEXT,
                    timestamp TEXT,
                    details TEXT
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(remind_at)')
    
    def create_task(self, title: str, description: str = "", priority: TaskPriority = TaskPriority.MEDIUM,
                   due_date: Optional[str] = None, estimated_duration: Optional[int] = None,
                   tags: List[str] = None) -> str:
        """Create a new task"""
        
        # Generate unique task ID
        task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            due_date=due_date,
            estimated_duration=estimated_duration,
            tags=tags or []
        )
        
        # Save to database
        self._save_task(task)
        self.active_tasks[task_id] = task
        
        # Log task creation
        self._log_task_action(task_id, "created", {"priority": priority.name})
        
        print(f"✅ Created task: {title} (ID: {task_id})")
        
        # Auto-schedule if due date is provided
        if due_date:
            self._auto_schedule_task(task_id)
        
        return task_id
    
    def update_task_status(self, task_id: str, status: TaskStatus, notes: str = "") -> bool:
        """Update task status"""
        if task_id not in self.active_tasks:
            print(f"❌ Task {task_id} not found")
            return False
        
        task = self.active_tasks[task_id]
        old_status = task.status
        task.status = status
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now().isoformat()
        
        if notes:
            task.notes.append(f"{datetime.now().isoformat()}: {notes}")
        
        # Update in database
        self._save_task(task)
        
        # Log status change
        self._log_task_action(task_id, "status_updated", {
            "from": old_status.value,
            "to": status.value,
            "notes": notes
        })
        
        print(f"🔄 Updated task {task_id}: {old_status.value} → {status.value}")
        return True
    
    def add_reminder(self, title: str, message: str, remind_at: str, 
                    task_id: Optional[str] = None, reminder_type: str = "general") -> str:
        """Add a reminder"""
        
        reminder_id = f"reminder_{int(datetime.now().timestamp() * 1000)}"
        
        reminder = Reminder(
            id=reminder_id,
            task_id=task_id,
            title=title,
            message=message,
            remind_at=remind_at,
            reminder_type=reminder_type
        )
        
        # Save to database
        self._save_reminder(reminder)
        self.pending_reminders[reminder_id] = reminder
        
        print(f"⏰ Added reminder: {title} at {remind_at}")
        return reminder_id
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get reminders that are due now"""
        current_time = datetime.now()
        due_reminders = []
        
        for reminder in self.pending_reminders.values():
            if not reminder.is_active:
                continue
                
            remind_time = datetime.fromisoformat(reminder.remind_at)
            if remind_time <= current_time:
                due_reminders.append(reminder)
        
        return due_reminders
    
    def get_daily_schedule(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get schedule for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Get scheduled tasks for the date
        scheduled_tasks = self._get_scheduled_tasks(date)
        
        # Get due tasks
        due_tasks = self._get_due_tasks(date)
        
        # Get reminders for the date
        daily_reminders = self._get_daily_reminders(date)
        
        return {
            "date": date,
            "scheduled_tasks": scheduled_tasks,
            "due_tasks": due_tasks,
            "reminders": daily_reminders,
            "summary": self._generate_daily_summary(scheduled_tasks, due_tasks, daily_reminders)
        }
    
    def suggest_task_priorities(self) -> List[Dict[str, Any]]:
        """Suggest task prioritization based on due dates and dependencies"""
        suggestions = []
        
        for task in self.active_tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            urgency_score = self._calculate_urgency_score(task)
            importance_score = self._calculate_importance_score(task)
            
            suggestions.append({
                "task_id": task.id,
                "title": task.title,
                "current_priority": task.priority.name,
                "suggested_priority": self._suggest_priority_level(urgency_score, importance_score),
                "urgency_score": urgency_score,
                "importance_score": importance_score,
                "reasoning": self._generate_priority_reasoning(task, urgency_score, importance_score)
            })
        
        # Sort by combined score
        suggestions.sort(key=lambda x: x["urgency_score"] + x["importance_score"], reverse=True)
        return suggestions
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """Generate productivity insights and recommendations"""
        
        # Task completion stats
        completion_stats = self._calculate_completion_stats()
        
        # Time management analysis
        time_analysis = self._analyze_time_patterns()
        
        # Bottleneck identification
        bottlenecks = self._identify_bottlenecks()
        
        # Recommendations
        recommendations = self._generate_recommendations(completion_stats, time_analysis, bottlenecks)
        
        return {
            "completion_stats": completion_stats,
            "time_analysis": time_analysis,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "last_updated": datetime.now().isoformat()
        }
    
    def parse_natural_language_task(self, text: str) -> Dict[str, Any]:
        """Parse natural language input to extract task information"""
        
        # Extract task title (simple approach)
        task_info = {
            "title": text.strip(),
            "description": "",
            "priority": TaskPriority.MEDIUM,
            "due_date": None,
            "tags": []
        }
        
        # Look for priority indicators
        priority_patterns = {
            r'\b(urgent|asap|immediately)\b': TaskPriority.URGENT,
            r'\b(important|high priority)\b': TaskPriority.HIGH,
            r'\b(low priority|later|when possible)\b': TaskPriority.LOW
        }
        
        for pattern, priority in priority_patterns.items():
            if re.search(pattern, text.lower()):
                task_info["priority"] = priority
                break
        
        # Look for due date patterns
        date_patterns = [
            r'\b(today)\b',
            r'\b(tomorrow)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(\d{1,2}/\d{1,2})\b',
            r'\b(in \d+ days?)\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                task_info["due_date"] = self._parse_date_expression(match.group())
                break
        
        # Extract tags from hashtags or keywords
        hashtags = re.findall(r'#(\w+)', text)
        task_info["tags"] = hashtags
        
        # Clean title by removing parsed elements
        clean_title = re.sub(r'#\w+', '', text)
        clean_title = re.sub(r'\b(urgent|asap|important|low priority|today|tomorrow)\b', '', clean_title, flags=re.IGNORECASE)
        task_info["title"] = clean_title.strip()
        
        return task_info
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get comprehensive task statistics"""
        stats = {
            "total_tasks": len(self.active_tasks),
            "by_status": defaultdict(int),
            "by_priority": defaultdict(int),
            "overdue_tasks": 0,
            "completed_today": 0,
            "average_completion_time": 0
        }
        
        today = datetime.now().date()
        
        for task in self.active_tasks.values():
            stats["by_status"][task.status.value] += 1
            stats["by_priority"][task.priority.name] += 1
            
            # Check for overdue tasks
            if task.due_date and task.status == TaskStatus.PENDING:
                due_date = datetime.fromisoformat(task.due_date).date()
                if due_date < today:
                    stats["overdue_tasks"] += 1
            
            # Count completed today
            if task.completed_at:
                completed_date = datetime.fromisoformat(task.completed_at).date()
                if completed_date == today:
                    stats["completed_today"] += 1
        
        return dict(stats)
    
    # Private helper methods
    def _load_active_tasks(self) -> Dict[str, Task]:
        """Load active tasks from database"""
        tasks = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM tasks WHERE user_id = ? AND status != ?',
                (self.user_id, TaskStatus.COMPLETED.value)
            )
            
            for row in cursor.fetchall():
                task = Task(
                    id=row[0], title=row[2], description=row[3],
                    priority=TaskPriority(row[4]), status=TaskStatus(row[5]),
                    created_at=row[6], due_date=row[7], completed_at=row[8],
                    estimated_duration=row[9],
                    tags=json.loads(row[10]) if row[10] else [],
                    dependencies=json.loads(row[11]) if row[11] else [],
                    notes=json.loads(row[12]) if row[12] else []
                )
                tasks[task.id] = task
        
        return tasks
    
    def _load_pending_reminders(self) -> Dict[str, Reminder]:
        """Load pending reminders from database"""
        reminders = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM reminders WHERE user_id = ? AND is_active = 1',
                (self.user_id,)
            )
            
            for row in cursor.fetchall():
                reminder = Reminder(
                    id=row[0], task_id=row[2], title=row[3], message=row[4],
                    remind_at=row[5], is_active=bool(row[6]), created_at=row[7],
                    reminder_type=row[8]
                )
                reminders[reminder.id] = reminder
        
        return reminders
    
    def _save_task(self, task: Task):
        """Save task to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, self.user_id, task.title, task.description,
                task.priority.value, task.status.value, task.created_at,
                task.due_date, task.completed_at, task.estimated_duration,
                json.dumps(task.tags), json.dumps(task.dependencies),
                json.dumps(task.notes)
            ))
    
    def _save_reminder(self, reminder: Reminder):
        """Save reminder to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO reminders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reminder.id, self.user_id, reminder.task_id, reminder.title,
                reminder.message, reminder.remind_at, reminder.is_active,
                reminder.created_at, reminder.reminder_type
            ))
    
    def _log_task_action(self, task_id: str, action: str, details: Dict[str, Any]):
        """Log task action to history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO task_history (user_id, task_id, action, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.user_id, task_id, action, datetime.now().isoformat(),
                json.dumps(details)
            ))
    
    def _auto_schedule_task(self, task_id: str):
        """Automatically schedule a task based on due date and duration"""
        # Simplified auto-scheduling logic
        print(f"📅 Auto-scheduling task {task_id}")
    
    def _get_scheduled_tasks(self, date: str) -> List[Dict[str, Any]]:
        """Get tasks scheduled for a specific date"""
        scheduled = []
        
        for task in self.active_tasks.values():
            if task.due_date:
                task_date = datetime.fromisoformat(task.due_date).strftime("%Y-%m-%d")
                if task_date == date:
                    scheduled.append({
                        "id": task.id,
                        "title": task.title,
                        "priority": task.priority.name,
                        "status": task.status.value,
                        "estimated_duration": task.estimated_duration
                    })
        
        return scheduled
    
    def _get_due_tasks(self, date: str) -> List[Dict[str, Any]]:
        """Get tasks due on a specific date"""
        # For simplicity, same as scheduled tasks
        return self._get_scheduled_tasks(date)
    
    def _get_daily_reminders(self, date: str) -> List[Dict[str, Any]]:
        """Get reminders for a specific date"""
        daily_reminders = []
        
        for reminder in self.pending_reminders.values():
            reminder_date = datetime.fromisoformat(reminder.remind_at).strftime("%Y-%m-%d")
            if reminder_date == date and reminder.is_active:
                daily_reminders.append({
                    "id": reminder.id,
                    "title": reminder.title,
                    "message": reminder.message,
                    "time": datetime.fromisoformat(reminder.remind_at).strftime("%H:%M"),
                    "type": reminder.reminder_type
                })
        
        return daily_reminders
    
    def _generate_daily_summary(self, scheduled_tasks: List, due_tasks: List, reminders: List) -> str:
        """Generate a daily summary"""
        summary_parts = []
        
        if scheduled_tasks:
            summary_parts.append(f"{len(scheduled_tasks)} scheduled tasks")
        
        if due_tasks:
            summary_parts.append(f"{len(due_tasks)} due tasks")
        
        if reminders:
            summary_parts.append(f"{len(reminders)} reminders")
        
        if not summary_parts:
            return "No scheduled activities"
        
        return ", ".join(summary_parts)
    
    def _calculate_urgency_score(self, task: Task) -> float:
        """Calculate urgency score based on due date"""
        if not task.due_date:
            return 0.3  # Low urgency for tasks without due dates
        
        due_date = datetime.fromisoformat(task.due_date)
        days_until_due = (due_date - datetime.now()).days
        
        if days_until_due <= 0:
            return 1.0  # Overdue
        elif days_until_due == 1:
            return 0.9  # Due tomorrow
        elif days_until_due <= 3:
            return 0.7  # Due soon
        elif days_until_due <= 7:
            return 0.5  # Due this week
        else:
            return 0.3  # Due later
    
    def _calculate_importance_score(self, task: Task) -> float:
        """Calculate importance score based on priority and dependencies"""
        base_score = task.priority.value / 4.0  # Normalize to 0-1
        
        # Boost score if other tasks depend on this one
        dependent_count = sum(1 for t in self.active_tasks.values() 
                            if task.id in t.dependencies)
        dependency_boost = min(dependent_count * 0.1, 0.3)
        
        return min(base_score + dependency_boost, 1.0)
    
    def _suggest_priority_level(self, urgency: float, importance: float) -> str:
        """Suggest priority level based on urgency and importance"""
        combined_score = (urgency + importance) / 2
        
        if combined_score >= 0.8:
            return "URGENT"
        elif combined_score >= 0.6:
            return "HIGH"
        elif combined_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_priority_reasoning(self, task: Task, urgency: float, importance: float) -> str:
        """Generate reasoning for priority suggestion"""
        reasons = []
        
        if urgency > 0.7:
            reasons.append("approaching deadline")
        if importance > 0.7:
            reasons.append("high priority task")
        if task.dependencies:
            reasons.append("has dependencies")
        
        return "; ".join(reasons) if reasons else "standard priority"
    
    def _calculate_completion_stats(self) -> Dict[str, Any]:
        """Calculate task completion statistics"""
        return {
            "total_completed": len([t for t in self.active_tasks.values() 
                                  if t.status == TaskStatus.COMPLETED]),
            "completion_rate": 0.75,  # Placeholder
            "average_time_to_complete": 2.5  # days, placeholder
        }
    
    def _analyze_time_patterns(self) -> Dict[str, Any]:
        """Analyze time management patterns"""
        return {
            "most_productive_hours": ["9-11", "14-16"],
            "task_duration_accuracy": 0.8,  # placeholder
            "time_block_utilization": 0.7   # placeholder
        }
    
    def _identify_bottlenecks(self) -> List[str]:
        """Identify productivity bottlenecks"""
        return [
            "Too many concurrent tasks",
            "Unclear task priorities",
            "Missing time estimates"
        ]
    
    def _generate_recommendations(self, completion_stats: Dict, time_analysis: Dict, bottlenecks: List) -> List[str]:
        """Generate productivity recommendations"""
        return [
            "Focus on 3-5 high-priority tasks per day",
            "Break large tasks into smaller subtasks",
            "Schedule important work during peak hours (9-11 AM)",
            "Set realistic time estimates for tasks"
        ]
    
    def _parse_date_expression(self, expression: str) -> str:
        """Parse natural language date expressions"""
        today = datetime.now()
        
        if expression.lower() == "today":
            return today.isoformat()
        elif expression.lower() == "tomorrow":
            return (today + timedelta(days=1)).isoformat()
        
        # For more complex date parsing, would use a library like dateutil
        return today.isoformat()  # Fallback


def main():
    """Test the task scheduler system"""
    print("📅 Testing Task Scheduler System")
    print("=" * 50)
    
    # Initialize scheduler
    scheduler = TaskScheduler(user_id="test_user")
    
    # Test task creation
    task_id1 = scheduler.create_task(
        "Complete project proposal",
        "Write and review the Q2 project proposal",
        TaskPriority.HIGH,
        (datetime.now() + timedelta(days=2)).isoformat(),
        120  # 2 hours
    )
    
    task_id2 = scheduler.create_task(
        "Review budget reports",
        "Monthly budget analysis",
        TaskPriority.MEDIUM,
        tags=["finance", "monthly"]
    )
    
    # Test reminder
    reminder_id = scheduler.add_reminder(
        "Meeting prep",
        "Prepare slides for team meeting",
        (datetime.now() + timedelta(minutes=30)).isoformat(),
        task_id1,
        "task"
    )
    
    # Test natural language parsing
    nl_task = scheduler.parse_natural_language_task(
        "urgent: finish presentation for tomorrow #work #important"
    )
    print(f"\n🗣️  Parsed task: {nl_task}")
    
    # Test daily schedule
    schedule = scheduler.get_daily_schedule()
    print(f"\n📅 Today's Schedule:")
    print(f"   Summary: {schedule['summary']}")
    print(f"   Scheduled tasks: {len(schedule['scheduled_tasks'])}")
    print(f"   Reminders: {len(schedule['reminders'])}")
    
    # Test priority suggestions
    suggestions = scheduler.suggest_task_priorities()
    print(f"\n🎯 Priority Suggestions:")
    for suggestion in suggestions[:3]:  # Show top 3
        print(f"   {suggestion['title']}: {suggestion['suggested_priority']} ({suggestion['reasoning']})")
    
    # Test statistics
    stats = scheduler.get_task_statistics()
    print(f"\n📊 Task Statistics:")
    print(f"   Total tasks: {stats['total_tasks']}")
    print(f"   By status: {dict(stats['by_status'])}")
    print(f"   Overdue: {stats['overdue_tasks']}")
    
    # Test productivity insights
    insights = scheduler.get_productivity_insights()
    print(f"\n💡 Productivity Insights:")
    print(f"   Completion rate: {insights['completion_stats']['completion_rate']:.1%}")
    print(f"   Recommendations: {len(insights['recommendations'])}")
    
    print(f"\n✅ TaskScheduler system test completed!")


if __name__ == "__main__":
    main()