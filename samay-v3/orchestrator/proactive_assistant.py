"""
Proactive Assistant Engine for Samay v3 - Phase 4
Provides context-aware suggestions, proactive assistance, and intelligent monitoring
"""

import sqlite3
import json
import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib

class SuggestionType(Enum):
    TASK_REMINDER = "task_reminder"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    PRODUCTIVITY_TIP = "productivity_tip"
    BREAK_REMINDER = "break_reminder"
    DEADLINE_ALERT = "deadline_alert"
    WORKFLOW_SUGGESTION = "workflow_suggestion"
    CONTEXT_INSIGHT = "context_insight"
    HEALTH_WELLNESS = "health_wellness"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class ProactiveSuggestion:
    id: Optional[int]
    type: SuggestionType
    title: str
    message: str
    priority: Priority
    action_required: bool
    action_type: str
    action_data: Dict[str, Any]
    context: Dict[str, Any]
    relevance_score: float
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    acknowledged: bool

@dataclass
class UserContext:
    current_activity: str
    focus_state: str  # focused, distracted, break
    energy_level: int  # 1-10
    mood: str
    location: str
    time_of_day: str
    workload_status: str  # light, moderate, heavy, overloaded
    upcoming_deadlines: List[Dict[str, Any]]
    recent_productivity: float

class ProactiveAssistant:
    def __init__(self, db_path: str = "memory/proactive_assistant.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Initialize monitoring patterns
        self.monitoring_patterns = {
            "break_interval": 45,  # minutes
            "focus_session_target": 90,  # minutes
            "daily_task_limit": 8,
            "energy_threshold": 4,  # below this, suggest break
            "productivity_threshold": 0.6
        }
    
    def _init_database(self):
        """Initialize the proactive assistant database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS proactive_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    action_required BOOLEAN NOT NULL,
                    action_type TEXT,
                    action_data TEXT,  -- JSON
                    context TEXT,  -- JSON
                    relevance_score REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS user_context_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    current_activity TEXT,
                    focus_state TEXT,
                    energy_level INTEGER,
                    mood TEXT,
                    location TEXT,
                    time_of_day TEXT,
                    workload_status TEXT,
                    productivity_score REAL,
                    context_data TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS behavior_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,  -- JSON
                    frequency REAL,
                    last_occurrence TIMESTAMP,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS suggestion_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_id INTEGER,
                    feedback_type TEXT,  -- helpful, not_helpful, ignored
                    user_rating INTEGER,  -- 1-5
                    comments TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (suggestion_id) REFERENCES proactive_suggestions (id)
                );
                
                CREATE TABLE IF NOT EXISTS proactive_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    action_data TEXT NOT NULL,  -- JSON
                    trigger_context TEXT,  -- JSON
                    execution_status TEXT,  -- pending, completed, failed
                    result_data TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS wellness_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    focus_sessions INTEGER DEFAULT 0,
                    break_taken INTEGER DEFAULT 0,
                    stress_level INTEGER,  -- 1-10
                    satisfaction_level INTEGER,  -- 1-10
                    work_life_balance INTEGER,  -- 1-10
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    # Core Proactive Functions
    
    def update_user_context(self, context: UserContext) -> None:
        """Update current user context for proactive monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO user_context_history 
                (current_activity, focus_state, energy_level, mood, location,
                 time_of_day, workload_status, productivity_score, context_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (context.current_activity, context.focus_state, context.energy_level,
                  context.mood, context.location, context.time_of_day,
                  context.workload_status, context.recent_productivity,
                  json.dumps({"upcoming_deadlines": context.upcoming_deadlines})))
    
    def generate_proactive_suggestions(self, current_context: UserContext) -> List[ProactiveSuggestion]:
        """Generate contextual proactive suggestions"""
        suggestions = []
        
        # Update context first
        self.update_user_context(current_context)
        
        # Generate different types of suggestions based on context
        suggestions.extend(self._generate_wellness_suggestions(current_context))
        suggestions.extend(self._generate_productivity_suggestions(current_context))
        suggestions.extend(self._generate_schedule_suggestions(current_context))
        suggestions.extend(self._generate_workflow_suggestions(current_context))
        suggestions.extend(self._generate_deadline_suggestions(current_context))
        
        # Sort by relevance and priority
        suggestions.sort(key=lambda x: (x.priority.value, -x.relevance_score), reverse=True)
        
        # Store suggestions in database
        for suggestion in suggestions:
            self._store_suggestion(suggestion)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _generate_wellness_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """Generate wellness and health-related suggestions"""
        suggestions = []
        now = datetime.datetime.now()
        
        # Energy level monitoring
        if context.energy_level < self.monitoring_patterns["energy_threshold"]:
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.HEALTH_WELLNESS,
                title="Energy Level Alert",
                message=f"Your energy level is low ({context.energy_level}/10). Consider taking a break or having a healthy snack.",
                priority=Priority.MEDIUM,
                action_required=True,
                action_type="schedule_break",
                action_data={"duration": 15, "type": "energy_break"},
                context={"energy_level": context.energy_level},
                relevance_score=0.8,
                created_at=now,
                expires_at=now + datetime.timedelta(minutes=30),
                acknowledged=False
            ))
        
        # Break reminder based on focus state
        if context.focus_state == "focused":
            last_break = self._get_last_break_time()
            if last_break and (now - last_break).total_seconds() / 60 > self.monitoring_patterns["break_interval"]:
                suggestions.append(ProactiveSuggestion(
                    id=None,
                    type=SuggestionType.BREAK_REMINDER,
                    title="Break Time",
                    message=f"You've been focused for {self.monitoring_patterns['break_interval']} minutes. Time for a quick break!",
                    priority=Priority.MEDIUM,
                    action_required=False,
                    action_type="suggest_break",
                    action_data={"break_type": "focus_break", "duration": 10},
                    context={"focus_duration": self.monitoring_patterns["break_interval"]},
                    relevance_score=0.7,
                    created_at=now,
                    expires_at=now + datetime.timedelta(minutes=15),
                    acknowledged=False
                ))
        
        # Stress level monitoring based on workload
        if context.workload_status in ["heavy", "overloaded"]:
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.HEALTH_WELLNESS,
                title="Workload Management",
                message="Your workload seems heavy. Consider prioritizing tasks or delegating some items.",
                priority=Priority.HIGH,
                action_required=True,
                action_type="optimize_workload",
                action_data={"strategy": "prioritization"},
                context={"workload": context.workload_status},
                relevance_score=0.9,
                created_at=now,
                expires_at=now + datetime.timedelta(hours=2),
                acknowledged=False
            ))
        
        return suggestions
    
    def _generate_productivity_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """Generate productivity-focused suggestions"""
        suggestions = []
        now = datetime.datetime.now()
        
        # Low productivity alert
        if context.recent_productivity < self.monitoring_patterns["productivity_threshold"]:
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.PRODUCTIVITY_TIP,
                title="Productivity Boost",
                message=f"Your recent productivity is at {context.recent_productivity:.0%}. Try the Pomodoro technique or breaking tasks into smaller chunks.",
                priority=Priority.MEDIUM,
                action_required=False,
                action_type="productivity_tip",
                action_data={"technique": "pomodoro", "focus_duration": 25},
                context={"current_productivity": context.recent_productivity},
                relevance_score=0.8,
                created_at=now,
                expires_at=now + datetime.timedelta(hours=1),
                acknowledged=False
            ))
        
        # Focus state optimization
        if context.focus_state == "distracted":
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.PRODUCTIVITY_TIP,
                title="Focus Enhancement",
                message="You seem distracted. Try eliminating distractions or switching to a simpler task.",
                priority=Priority.MEDIUM,
                action_required=True,
                action_type="improve_focus",
                action_data={"strategies": ["remove_distractions", "change_environment", "switch_task"]},
                context={"focus_state": context.focus_state},
                relevance_score=0.7,
                created_at=now,
                expires_at=now + datetime.timedelta(minutes=45),
                acknowledged=False
            ))
        
        # Time-based productivity suggestions
        hour = now.hour
        if 9 <= hour <= 11:  # Morning high-energy period
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.PRODUCTIVITY_TIP,
                title="Peak Performance Time",
                message="This is typically a high-energy time. Consider tackling your most challenging tasks now.",
                priority=Priority.LOW,
                action_required=False,
                action_type="optimize_timing",
                action_data={"suggestion": "tackle_difficult_tasks"},
                context={"time_of_day": "morning_peak"},
                relevance_score=0.6,
                created_at=now,
                expires_at=now + datetime.timedelta(hours=2),
                acknowledged=False
            ))
        
        return suggestions
    
    def _generate_schedule_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """Generate schedule optimization suggestions"""
        suggestions = []
        now = datetime.datetime.now()
        
        # Workload optimization
        if context.workload_status == "overloaded":
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.SCHEDULE_OPTIMIZATION,
                title="Schedule Optimization",
                message="Your schedule looks packed. Would you like me to help reschedule or prioritize tasks?",
                priority=Priority.HIGH,
                action_required=True,
                action_type="optimize_schedule",
                action_data={"strategy": "reschedule_non_urgent"},
                context={"workload": context.workload_status},
                relevance_score=0.9,
                created_at=now,
                expires_at=now + datetime.timedelta(hours=3),
                acknowledged=False
            ))
        
        # Time block suggestion
        if context.focus_state == "focused" and context.energy_level >= 7:
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.SCHEDULE_OPTIMIZATION,
                title="Focus Time Block",
                message="You're in a great flow state. Consider blocking the next 90 minutes for deep work.",
                priority=Priority.MEDIUM,
                action_required=False,
                action_type="create_focus_block",
                action_data={"duration": 90, "type": "deep_work"},
                context={"energy_level": context.energy_level, "focus_state": context.focus_state},
                relevance_score=0.8,
                created_at=now,
                expires_at=now + datetime.timedelta(minutes=20),
                acknowledged=False
            ))
        
        return suggestions
    
    def _generate_workflow_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """Generate workflow improvement suggestions"""
        suggestions = []
        now = datetime.datetime.now()
        
        # Task batching suggestion
        similar_tasks = self._identify_similar_tasks()
        if len(similar_tasks) >= 3:
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.WORKFLOW_SUGGESTION,
                title="Task Batching Opportunity",
                message=f"I found {len(similar_tasks)} similar tasks. Consider batching them together for efficiency.",
                priority=Priority.MEDIUM,
                action_required=False,
                action_type="batch_tasks",
                action_data={"tasks": similar_tasks},
                context={"task_count": len(similar_tasks)},
                relevance_score=0.7,
                created_at=now,
                expires_at=now + datetime.timedelta(hours=4),
                acknowledged=False
            ))
        
        # Automation suggestion
        repetitive_patterns = self._detect_repetitive_patterns()
        if repetitive_patterns:
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.WORKFLOW_SUGGESTION,
                title="Automation Opportunity",
                message="I've detected repetitive patterns in your workflow. Consider automating these tasks.",
                priority=Priority.LOW,
                action_required=False,
                action_type="suggest_automation",
                action_data={"patterns": repetitive_patterns},
                context={"pattern_count": len(repetitive_patterns)},
                relevance_score=0.6,
                created_at=now,
                expires_at=now + datetime.timedelta(days=1),
                acknowledged=False
            ))
        
        return suggestions
    
    def _generate_deadline_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """Generate deadline-related suggestions"""
        suggestions = []
        now = datetime.datetime.now()
        
        # Upcoming deadline alerts
        for deadline in context.upcoming_deadlines:
            deadline_date = datetime.datetime.fromisoformat(deadline["due_date"])
            days_until = (deadline_date - now).days
            
            if days_until <= 1:
                priority = Priority.URGENT
                relevance = 1.0
            elif days_until <= 3:
                priority = Priority.HIGH
                relevance = 0.9
            elif days_until <= 7:
                priority = Priority.MEDIUM
                relevance = 0.7
            else:
                continue  # Skip far deadlines
            
            suggestions.append(ProactiveSuggestion(
                id=None,
                type=SuggestionType.DEADLINE_ALERT,
                title=f"Deadline Alert: {deadline['title']}",
                message=f"'{deadline['title']}' is due in {days_until} day(s). Ensure you have enough time allocated.",
                priority=priority,
                action_required=True,
                action_type="prepare_for_deadline",
                action_data={"task_id": deadline["id"], "days_until": days_until},
                context={"deadline": deadline},
                relevance_score=relevance,
                created_at=now,
                expires_at=deadline_date,
                acknowledged=False
            ))
        
        return suggestions
    
    # Monitoring and Analysis Functions
    
    def monitor_user_behavior(self) -> Dict[str, Any]:
        """Monitor and analyze user behavior patterns"""
        patterns = {
            "focus_patterns": self._analyze_focus_patterns(),
            "productivity_trends": self._analyze_productivity_trends(),
            "energy_patterns": self._analyze_energy_patterns(),
            "workload_patterns": self._analyze_workload_patterns()
        }
        
        # Store patterns for future reference
        self._store_behavior_patterns(patterns)
        
        return patterns
    
    def _analyze_focus_patterns(self) -> Dict[str, Any]:
        """Analyze user's focus patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT focus_state, COUNT(*), 
                       AVG(energy_level), 
                       strftime('%H', timestamp) as hour
                FROM user_context_history 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY focus_state, hour
                ORDER BY hour
            """)
            
            focus_data = cursor.fetchall()
            
            patterns = {
                "best_focus_hours": [],
                "focus_duration_avg": 0,
                "distraction_triggers": []
            }
            
            # Find best focus hours
            focused_hours = {}
            for row in focus_data:
                if row[0] == "focused":
                    hour = int(row[3])
                    focused_hours[hour] = row[1]  # count
            
            # Get top 3 focus hours
            patterns["best_focus_hours"] = sorted(focused_hours.keys(), 
                                                key=lambda x: focused_hours[x], 
                                                reverse=True)[:3]
            
            return patterns
    
    def _analyze_productivity_trends(self) -> Dict[str, Any]:
        """Analyze productivity trends"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date(timestamp) as day, 
                       AVG(productivity_score),
                       COUNT(*) as entries
                FROM user_context_history 
                WHERE timestamp >= datetime('now', '-14 days')
                GROUP BY day
                ORDER BY day DESC
            """)
            
            trends = cursor.fetchall()
            
            if trends:
                recent_avg = sum(t[1] for t in trends[:7]) / min(7, len(trends))
                previous_avg = sum(t[1] for t in trends[7:14]) / max(1, len(trends[7:14]))
                
                return {
                    "recent_average": recent_avg,
                    "trend": "improving" if recent_avg > previous_avg else "declining",
                    "change_rate": (recent_avg - previous_avg) / max(previous_avg, 0.01)
                }
            
            return {"recent_average": 0.7, "trend": "stable", "change_rate": 0.0}
    
    def _analyze_energy_patterns(self) -> Dict[str, Any]:
        """Analyze energy level patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT strftime('%H', timestamp) as hour,
                       AVG(energy_level) as avg_energy
                FROM user_context_history 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY hour
                ORDER BY avg_energy DESC
            """)
            
            energy_data = cursor.fetchall()
            
            return {
                "peak_energy_hours": [int(row[0]) for row in energy_data[:3]],
                "low_energy_hours": [int(row[0]) for row in energy_data[-3:]],
                "average_energy": sum(row[1] for row in energy_data) / max(1, len(energy_data))
            }
    
    def _analyze_workload_patterns(self) -> Dict[str, Any]:
        """Analyze workload patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT workload_status, COUNT(*) as frequency,
                       date(timestamp) as day
                FROM user_context_history 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY workload_status, day
            """)
            
            workload_data = cursor.fetchall()
            
            # Calculate workload distribution
            total_entries = sum(row[1] for row in workload_data)
            distribution = {}
            
            for row in workload_data:
                status = row[0]
                frequency = row[1]
                if status not in distribution:
                    distribution[status] = 0
                distribution[status] += frequency
            
            # Convert to percentages
            for status in distribution:
                distribution[status] = (distribution[status] / max(total_entries, 1)) * 100
            
            return {
                "distribution": distribution,
                "most_common": max(distribution.keys(), key=lambda x: distribution[x]) if distribution else "moderate"
            }
    
    # Helper Functions
    
    def _get_last_break_time(self) -> Optional[datetime.datetime]:
        """Get the time of last recorded break"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(timestamp) FROM user_context_history 
                WHERE current_activity LIKE '%break%'
            """)
            result = cursor.fetchone()
            return datetime.datetime.fromisoformat(result[0]) if result[0] else None
    
    def _identify_similar_tasks(self) -> List[Dict[str, Any]]:
        """Identify similar tasks that could be batched"""
        # Mock implementation - in real system would integrate with task scheduler
        return [
            {"id": 1, "title": "Review email", "category": "communication"},
            {"id": 2, "title": "Send follow-up emails", "category": "communication"},
            {"id": 3, "title": "Update team on progress", "category": "communication"}
        ]
    
    def _detect_repetitive_patterns(self) -> List[Dict[str, Any]]:
        """Detect repetitive patterns that could be automated"""
        # Mock implementation - would analyze user behavior patterns
        return [
            {"pattern": "daily_standup_notes", "frequency": 0.9, "suggestion": "template_creation"},
            {"pattern": "weekly_report_generation", "frequency": 0.8, "suggestion": "automation_script"}
        ]
    
    def _store_suggestion(self, suggestion: ProactiveSuggestion) -> int:
        """Store suggestion in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO proactive_suggestions 
                (type, title, message, priority, action_required, action_type,
                 action_data, context, relevance_score, created_at, expires_at, acknowledged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (suggestion.type.value, suggestion.title, suggestion.message,
                  suggestion.priority.value, suggestion.action_required, suggestion.action_type,
                  json.dumps(suggestion.action_data), json.dumps(suggestion.context),
                  suggestion.relevance_score, suggestion.created_at, suggestion.expires_at,
                  suggestion.acknowledged))
            
            return cursor.lastrowid
    
    def _store_behavior_patterns(self, patterns: Dict[str, Any]):
        """Store analyzed behavior patterns"""
        with sqlite3.connect(self.db_path) as conn:
            for pattern_type, pattern_data in patterns.items():
                conn.execute("""
                    INSERT INTO behavior_patterns 
                    (pattern_type, pattern_data, confidence_score)
                    VALUES (?, ?, ?)
                """, (pattern_type, json.dumps(pattern_data), 0.8))
    
    def get_suggestion_analytics(self) -> Dict[str, Any]:
        """Get analytics on suggestion effectiveness"""
        with sqlite3.connect(self.db_path) as conn:
            # Get suggestion statistics
            cursor = conn.execute("""
                SELECT type, COUNT(*) as total,
                       SUM(CASE WHEN acknowledged = 1 THEN 1 ELSE 0 END) as acknowledged,
                       AVG(relevance_score) as avg_relevance
                FROM proactive_suggestions 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY type
            """)
            
            stats = cursor.fetchall()
            
            analytics = {
                "total_suggestions": 0,
                "acknowledgment_rate": 0.0,
                "type_breakdown": {},
                "avg_relevance": 0.0
            }
            
            total_suggestions = sum(s[1] for s in stats)
            total_acknowledged = sum(s[2] for s in stats)
            
            analytics["total_suggestions"] = total_suggestions
            analytics["acknowledgment_rate"] = (total_acknowledged / max(total_suggestions, 1)) * 100
            
            for stat in stats:
                suggestion_type = stat[0]
                count = stat[1]
                acknowledged = stat[2]
                avg_relevance = stat[3]
                
                analytics["type_breakdown"][suggestion_type] = {
                    "count": count,
                    "acknowledgment_rate": (acknowledged / max(count, 1)) * 100,
                    "avg_relevance": avg_relevance
                }
            
            return analytics
    
    def acknowledge_suggestion(self, suggestion_id: int, feedback: str = "helpful") -> bool:
        """Mark suggestion as acknowledged with feedback"""
        with sqlite3.connect(self.db_path) as conn:
            # Update suggestion
            cursor = conn.execute("""
                UPDATE proactive_suggestions 
                SET acknowledged = TRUE 
                WHERE id = ?
            """, (suggestion_id,))
            
            # Store feedback
            conn.execute("""
                INSERT INTO suggestion_feedback 
                (suggestion_id, feedback_type, timestamp)
                VALUES (?, ?, ?)
            """, (suggestion_id, feedback, datetime.datetime.now()))
            
            return cursor.rowcount > 0

# Example usage and testing
if __name__ == "__main__":
    assistant = ProactiveAssistant()
    
    # Create sample context
    context = UserContext(
        current_activity="coding",
        focus_state="focused",
        energy_level=6,
        mood="productive",
        location="office",
        time_of_day="morning",
        workload_status="moderate",
        upcoming_deadlines=[
            {"id": 1, "title": "Project deadline", "due_date": "2025-07-27T17:00:00"}
        ],
        recent_productivity=0.75
    )
    
    # Generate suggestions
    suggestions = assistant.generate_proactive_suggestions(context)
    print("Proactive suggestions generated:")
    for suggestion in suggestions:
        print(f"- {suggestion.title}: {suggestion.message}")
    
    # Monitor behavior
    patterns = assistant.monitor_user_behavior()
    print("\nBehavior patterns:")
    print(json.dumps(patterns, indent=2, default=str))
    
    print("Proactive Assistant ready!")