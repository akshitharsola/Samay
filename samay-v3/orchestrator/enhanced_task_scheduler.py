"""
Enhanced Task Scheduler for Samay v3 - Phase 4
Provides smart scheduling, calendar integration, and proactive task management
"""

import sqlite3
import json
import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

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
    OVERDUE = "overdue"

class RecurrenceType(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

@dataclass
class SmartTask:
    id: Optional[int]
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    due_date: Optional[datetime.datetime]
    estimated_duration: Optional[int]  # minutes
    category: str
    tags: List[str]
    dependencies: List[int]  # task IDs this depends on
    recurrence: RecurrenceType
    context: Dict[str, Any]  # additional context
    created_at: datetime.datetime
    updated_at: datetime.datetime

@dataclass
class CalendarEvent:
    id: Optional[int]
    title: str
    description: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    location: Optional[str]
    attendees: List[str]
    task_id: Optional[int]  # linked task
    event_type: str  # meeting, reminder, deadline, etc.

class EnhancedTaskScheduler:
    def __init__(self, db_path: str = "memory/enhanced_tasks.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize the enhanced task scheduling database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS smart_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    due_date TIMESTAMP,
                    estimated_duration INTEGER,
                    category TEXT,
                    tags TEXT,  -- JSON array
                    dependencies TEXT,  -- JSON array of task IDs
                    recurrence TEXT NOT NULL DEFAULT 'none',
                    context TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    location TEXT,
                    attendees TEXT,  -- JSON array
                    task_id INTEGER,
                    event_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES smart_tasks (id)
                );
                
                CREATE TABLE IF NOT EXISTS time_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    block_type TEXT NOT NULL,  -- focus, break, meeting, etc.
                    tasks TEXT,  -- JSON array of task IDs
                    productivity_score REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS productivity_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_overdue INTEGER DEFAULT 0,
                    focus_time_minutes INTEGER DEFAULT 0,
                    productivity_score REAL,
                    energy_level INTEGER,  -- 1-10 scale
                    mood TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS smart_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    schedule_data TEXT NOT NULL,  -- JSON representation
                    optimization_strategy TEXT,
                    effectiveness_score REAL,
                    user_feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    # Smart Task Management
    
    def create_smart_task(self, title: str, description: str = "", 
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         due_date: Optional[datetime.datetime] = None,
                         estimated_duration: Optional[int] = None,
                         category: str = "general",
                         tags: List[str] = None,
                         dependencies: List[int] = None,
                         recurrence: RecurrenceType = RecurrenceType.NONE,
                         context: Dict[str, Any] = None) -> int:
        """Create a new smart task with enhanced features"""
        if tags is None:
            tags = []
        if dependencies is None:
            dependencies = []
        if context is None:
            context = {}
        
        now = datetime.datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO smart_tasks 
                (title, description, priority, status, due_date, estimated_duration,
                 category, tags, dependencies, recurrence, context, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, priority.value, TaskStatus.PENDING.value, 
                  due_date, estimated_duration, category, json.dumps(tags),
                  json.dumps(dependencies), recurrence.value, json.dumps(context),
                  now, now))
            
            task_id = cursor.lastrowid
            
            # Auto-schedule if due date is provided
            if due_date:
                self._auto_schedule_task(task_id, due_date, estimated_duration or 60)
            
            return task_id
    
    def get_smart_schedule(self, date: datetime.date = None) -> Dict[str, Any]:
        """Generate an optimized daily schedule"""
        if date is None:
            date = datetime.date.today()
        
        # Get tasks for the day
        tasks = self._get_tasks_for_date(date)
        
        # Get calendar events
        events = self._get_calendar_events_for_date(date)
        
        # Get productivity patterns
        productivity_data = self._get_productivity_patterns()
        
        # Generate optimized schedule
        schedule = self._optimize_daily_schedule(tasks, events, productivity_data, date)
        
        # Store the schedule
        self._store_schedule(date, schedule)
        
        return schedule
    
    def _get_tasks_for_date(self, date: datetime.date) -> List[SmartTask]:
        """Get all tasks for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM smart_tasks 
                WHERE date(due_date) = ? OR status = 'pending'
                ORDER BY priority DESC, due_date ASC
            """, (date.isoformat(),))
            
            tasks = []
            for row in cursor.fetchall():
                task = self._row_to_smart_task(row)
                tasks.append(task)
            
            return tasks
    
    def _get_calendar_events_for_date(self, date: datetime.date) -> List[CalendarEvent]:
        """Get calendar events for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM calendar_events 
                WHERE date(start_time) = ?
                ORDER BY start_time ASC
            """, (date.isoformat(),))
            
            events = []
            for row in cursor.fetchall():
                event = self._row_to_calendar_event(row)
                events.append(event)
            
            return events
    
    def _optimize_daily_schedule(self, tasks: List[SmartTask], 
                                events: List[CalendarEvent],
                                productivity_data: Dict[str, Any],
                                date: datetime.date) -> Dict[str, Any]:
        """Generate an optimized daily schedule using AI techniques"""
        
        schedule = {
            "date": date.isoformat(),
            "optimization_strategy": "energy_priority_based",
            "time_blocks": [],
            "task_assignments": {},
            "recommendations": [],
            "estimated_productivity": 0.0
        }
        
        # Create time blocks based on energy patterns
        energy_pattern = productivity_data.get("energy_pattern", {})
        
        # Morning block (high energy for complex tasks)
        morning_block = {
            "start_time": "09:00",
            "end_time": "12:00",
            "type": "focus",
            "energy_level": "high",
            "recommended_tasks": []
        }
        
        # Afternoon block (medium energy for routine tasks)
        afternoon_block = {
            "start_time": "14:00",
            "end_time": "17:00",
            "type": "routine",
            "energy_level": "medium",
            "recommended_tasks": []
        }
        
        # Assign tasks to blocks based on priority and complexity
        high_priority_tasks = [t for t in tasks if t.priority in [TaskPriority.HIGH, TaskPriority.URGENT]]
        medium_priority_tasks = [t for t in tasks if t.priority == TaskPriority.MEDIUM]
        
        # Assign high priority to morning (high energy)
        for task in high_priority_tasks[:3]:  # Max 3 high priority tasks per day
            morning_block["recommended_tasks"].append({
                "task_id": task.id,
                "title": task.title,
                "estimated_duration": task.estimated_duration or 60,
                "priority": task.priority.name
            })
        
        # Assign medium priority to afternoon
        for task in medium_priority_tasks[:4]:  # Max 4 medium tasks
            afternoon_block["recommended_tasks"].append({
                "task_id": task.id,
                "title": task.title,
                "estimated_duration": task.estimated_duration or 45,
                "priority": task.priority.name
            })
        
        schedule["time_blocks"] = [morning_block, afternoon_block]
        
        # Add events to schedule
        schedule["calendar_events"] = [
            {
                "title": event.title,
                "start_time": event.start_time.strftime("%H:%M"),
                "end_time": event.end_time.strftime("%H:%M"),
                "type": event.event_type
            } for event in events
        ]
        
        # Generate recommendations
        schedule["recommendations"] = self._generate_schedule_recommendations(tasks, events, productivity_data)
        
        # Estimate productivity score
        schedule["estimated_productivity"] = self._calculate_productivity_estimate(schedule)
        
        return schedule
    
    def _generate_schedule_recommendations(self, tasks: List[SmartTask], 
                                         events: List[CalendarEvent],
                                         productivity_data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered scheduling recommendations"""
        recommendations = []
        
        # Task load analysis
        total_tasks = len(tasks)
        high_priority_count = len([t for t in tasks if t.priority in [TaskPriority.HIGH, TaskPriority.URGENT]])
        
        if total_tasks > 10:
            recommendations.append("Consider breaking down large tasks into smaller chunks for better focus")
        
        if high_priority_count > 3:
            recommendations.append("You have many high-priority tasks. Consider delegating or rescheduling some")
        
        # Time management suggestions
        total_estimated_time = sum(t.estimated_duration or 60 for t in tasks)
        if total_estimated_time > 480:  # 8 hours
            recommendations.append("Your task load exceeds a typical work day. Prioritize the most important items")
        
        # Energy optimization
        if productivity_data.get("best_focus_time") == "morning":
            recommendations.append("Schedule your most challenging tasks in the morning when your energy is highest")
        
        # Meeting optimization
        if len(events) > 3:
            recommendations.append("Consider batching meetings to preserve focus time blocks")
        
        return recommendations
    
    def create_calendar_event(self, title: str, start_time: datetime.datetime,
                            end_time: datetime.datetime, description: str = "",
                            location: str = None, attendees: List[str] = None,
                            task_id: int = None, event_type: str = "meeting") -> int:
        """Create a new calendar event"""
        if attendees is None:
            attendees = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO calendar_events 
                (title, description, start_time, end_time, location, attendees, task_id, event_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, start_time, end_time, location, 
                  json.dumps(attendees), task_id, event_type))
            
            return cursor.lastrowid
    
    def get_productivity_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get productivity insights and patterns"""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get productivity metrics
            cursor = conn.execute("""
                SELECT * FROM productivity_metrics 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            metrics = cursor.fetchall()
            
            # Calculate averages and trends
            insights = {
                "period": f"{days} days",
                "average_productivity": 0.0,
                "tasks_completed_avg": 0.0,
                "focus_time_avg": 0.0,
                "energy_pattern": {},
                "recommendations": [],
                "trends": {}
            }
            
            if metrics:
                avg_productivity = sum(m[4] or 0 for m in metrics) / len(metrics)
                avg_tasks = sum(m[2] for m in metrics) / len(metrics)
                avg_focus = sum(m[4] or 0 for m in metrics) / len(metrics)
                
                insights.update({
                    "average_productivity": round(avg_productivity, 2),
                    "tasks_completed_avg": round(avg_tasks, 1),
                    "focus_time_avg": round(avg_focus, 0)
                })
                
                # Generate recommendations based on patterns
                if avg_productivity < 0.6:
                    insights["recommendations"].append("Consider reducing task load or breaking tasks into smaller chunks")
                
                if avg_focus < 180:  # Less than 3 hours
                    insights["recommendations"].append("Try to increase focused work time with time-blocking techniques")
            
            return insights
    
    def update_task_status(self, task_id: int, status: TaskStatus) -> bool:
        """Update task status and track completion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE smart_tasks 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status.value, datetime.datetime.now(), task_id))
            
            # If task completed, update productivity metrics
            if status == TaskStatus.COMPLETED:
                self._record_task_completion(task_id)
            
            return cursor.rowcount > 0
    
    def _record_task_completion(self, task_id: int):
        """Record task completion for productivity tracking"""
        today = datetime.date.today()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if today's metrics exist
            cursor = conn.execute("""
                SELECT id, tasks_completed FROM productivity_metrics 
                WHERE date = ?
            """, (today.isoformat(),))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                conn.execute("""
                    UPDATE productivity_metrics 
                    SET tasks_completed = tasks_completed + 1
                    WHERE date = ?
                """, (today.isoformat(),))
            else:
                # Create new record
                conn.execute("""
                    INSERT INTO productivity_metrics (date, tasks_completed)
                    VALUES (?, 1)
                """, (today.isoformat(),))
    
    def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """Generate proactive suggestions based on current context"""
        suggestions = []
        
        # Check for overdue tasks
        overdue_tasks = self._get_overdue_tasks()
        if overdue_tasks:
            suggestions.append({
                "type": "urgent_action",
                "title": "Overdue Tasks Alert",
                "message": f"You have {len(overdue_tasks)} overdue tasks that need attention",
                "action": "reschedule_overdue_tasks",
                "priority": "high"
            })
        
        # Check for upcoming deadlines
        upcoming_deadlines = self._get_upcoming_deadlines(days=3)
        if upcoming_deadlines:
            suggestions.append({
                "type": "deadline_reminder",
                "title": "Upcoming Deadlines",
                "message": f"{len(upcoming_deadlines)} tasks due in the next 3 days",
                "action": "review_deadlines",
                "priority": "medium"
            })
        
        # Suggest schedule optimization
        today_tasks = self._get_tasks_for_date(datetime.date.today())
        if len(today_tasks) > 8:
            suggestions.append({
                "type": "optimization",
                "title": "Schedule Optimization",
                "message": "Your day looks busy. Would you like me to optimize your schedule?",
                "action": "optimize_schedule",
                "priority": "medium"
            })
        
        # Suggest breaks based on work patterns
        suggestions.append({
            "type": "wellness",
            "title": "Take a Break",
            "message": "Consider taking a 15-minute break to maintain productivity",
            "action": "schedule_break",
            "priority": "low"
        })
        
        return suggestions
    
    def _get_overdue_tasks(self) -> List[SmartTask]:
        """Get tasks that are overdue"""
        now = datetime.datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM smart_tasks 
                WHERE due_date < ? AND status NOT IN ('completed', 'cancelled')
            """, (now,))
            
            return [self._row_to_smart_task(row) for row in cursor.fetchall()]
    
    def _get_upcoming_deadlines(self, days: int = 3) -> List[SmartTask]:
        """Get tasks with upcoming deadlines"""
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM smart_tasks 
                WHERE due_date BETWEEN ? AND ? AND status NOT IN ('completed', 'cancelled')
                ORDER BY due_date ASC
            """, (now, future))
            
            return [self._row_to_smart_task(row) for row in cursor.fetchall()]
    
    def _auto_schedule_task(self, task_id: int, due_date: datetime.datetime, duration: int):
        """Automatically create a calendar event for a task"""
        # Find optimal time slot before due date
        start_time = due_date - datetime.timedelta(minutes=duration)
        
        event_title = f"Work on: {self._get_task_title(task_id)}"
        
        self.create_calendar_event(
            title=event_title,
            start_time=start_time,
            end_time=due_date,
            task_id=task_id,
            event_type="task_work"
        )
    
    def _get_task_title(self, task_id: int) -> str:
        """Get task title by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT title FROM smart_tasks WHERE id = ?", (task_id,))
            result = cursor.fetchone()
            return result[0] if result else "Unknown Task"
    
    def _get_productivity_patterns(self) -> Dict[str, Any]:
        """Analyze productivity patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT AVG(productivity_score), AVG(energy_level), AVG(focus_time_minutes)
                FROM productivity_metrics 
                WHERE date >= date('now', '-30 days')
            """)
            
            result = cursor.fetchone()
            
            return {
                "avg_productivity": result[0] or 0.7,
                "avg_energy": result[1] or 7,
                "avg_focus_time": result[2] or 240,
                "best_focus_time": "morning",  # Default based on research
                "energy_pattern": {
                    "morning": 9,
                    "afternoon": 7,
                    "evening": 5
                }
            }
    
    def _store_schedule(self, date: datetime.date, schedule: Dict[str, Any]):
        """Store generated schedule"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO smart_schedules 
                (date, schedule_data, optimization_strategy, effectiveness_score)
                VALUES (?, ?, ?, ?)
            """, (date.isoformat(), json.dumps(schedule), 
                  schedule.get("optimization_strategy"), 
                  schedule.get("estimated_productivity")))
    
    def _calculate_productivity_estimate(self, schedule: Dict[str, Any]) -> float:
        """Calculate estimated productivity score for a schedule"""
        base_score = 0.7
        
        # Factor in task distribution
        time_blocks = schedule.get("time_blocks", [])
        if len(time_blocks) >= 2:
            base_score += 0.1
        
        # Factor in realistic task load
        total_tasks = sum(len(block.get("recommended_tasks", [])) for block in time_blocks)
        if 3 <= total_tasks <= 7:  # Optimal range
            base_score += 0.1
        elif total_tasks > 10:
            base_score -= 0.2
        
        # Factor in break time
        if any("break" in block.get("type", "") for block in time_blocks):
            base_score += 0.1
        
        return min(1.0, max(0.0, base_score))
    
    # Utility methods
    
    def _row_to_smart_task(self, row) -> SmartTask:
        """Convert database row to SmartTask object"""
        return SmartTask(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            priority=TaskPriority(row[3]),
            status=TaskStatus(row[4]),
            due_date=datetime.datetime.fromisoformat(row[5]) if row[5] else None,
            estimated_duration=row[6],
            category=row[7] or "general",
            tags=json.loads(row[8]) if row[8] else [],
            dependencies=json.loads(row[9]) if row[9] else [],
            recurrence=RecurrenceType(row[10]),
            context=json.loads(row[11]) if row[11] else {},
            created_at=datetime.datetime.fromisoformat(row[12]),
            updated_at=datetime.datetime.fromisoformat(row[13])
        )
    
    def _row_to_calendar_event(self, row) -> CalendarEvent:
        """Convert database row to CalendarEvent object"""
        return CalendarEvent(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            start_time=datetime.datetime.fromisoformat(row[3]),
            end_time=datetime.datetime.fromisoformat(row[4]),
            location=row[5],
            attendees=json.loads(row[6]) if row[6] else [],
            task_id=row[7],
            event_type=row[8]
        )

# Example usage and testing
if __name__ == "__main__":
    scheduler = EnhancedTaskScheduler()
    
    # Create some test tasks
    task1_id = scheduler.create_smart_task(
        title="Complete project proposal",
        description="Draft the Q4 project proposal",
        priority=TaskPriority.HIGH,
        due_date=datetime.datetime.now() + datetime.timedelta(days=2),
        estimated_duration=120,
        category="work",
        tags=["project", "deadline"]
    )
    
    # Get today's schedule
    schedule = scheduler.get_smart_schedule()
    print("Today's optimized schedule:")
    print(json.dumps(schedule, indent=2, default=str))
    
    # Get proactive suggestions
    suggestions = scheduler.get_proactive_suggestions()
    print("\nProactive suggestions:")
    for suggestion in suggestions:
        print(f"- {suggestion['title']}: {suggestion['message']}")
    
    print("Enhanced Task Scheduler ready!")