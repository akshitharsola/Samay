#!/usr/bin/env python3
"""
Samay v3 - Conversation Memory System
====================================
Persistent memory system for companion-style AI interactions
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import re


@dataclass
class ConversationEntry:
    """Individual conversation entry with metadata"""
    id: str
    session_id: str
    timestamp: str
    user_input: str
    assistant_response: str
    context_tags: List[str]
    sentiment: str
    importance_score: float
    related_topics: List[str]
    follow_up_reminders: List[str]


@dataclass
class UserContext:
    """Accumulated user context and preferences"""
    user_id: str
    name: Optional[str]
    preferences: Dict[str, Any]
    working_style: str
    active_projects: List[str]
    recurring_topics: Dict[str, int]
    relationship_context: Dict[str, str]
    schedule_patterns: Dict[str, Any]
    last_interaction: str
    interaction_count: int


@dataclass
class TopicCluster:
    """Clustered conversation topics for context retrieval"""
    topic_id: str
    topic_name: str
    keywords: List[str]
    conversation_ids: List[str]
    last_discussed: str
    frequency: int
    importance: float


class ConversationMemory:
    """Advanced conversation memory system for companion AI"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.session_id = session_id
        
        # Initialize database
        self.db_path = self.memory_dir / "conversations.db"
        self.init_database()
        
        # Context caches
        self.user_context_cache: Dict[str, UserContext] = {}
        self.topic_clusters_cache: Dict[str, TopicCluster] = {}
        
        print(f"🧠 ConversationMemory initialized")
        print(f"📁 Memory directory: {self.memory_dir.absolute()}")
        print(f"🗃️  Database: {self.db_path}")
    
    def init_database(self):
        """Initialize SQLite database for persistent memory"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    user_input TEXT,
                    assistant_response TEXT,
                    context_tags TEXT,
                    sentiment TEXT,
                    importance_score REAL,
                    related_topics TEXT,
                    follow_up_reminders TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_contexts (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    preferences TEXT,
                    working_style TEXT,
                    active_projects TEXT,
                    recurring_topics TEXT,
                    relationship_context TEXT,
                    schedule_patterns TEXT,
                    last_interaction TEXT,
                    interaction_count INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS topic_clusters (
                    topic_id TEXT PRIMARY KEY,
                    topic_name TEXT,
                    keywords TEXT,
                    conversation_ids TEXT,
                    last_discussed TEXT,
                    frequency INTEGER,
                    importance REAL
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_topics ON conversations(related_topics)')
    
    def store_conversation(self, user_input: str, assistant_response: str, 
                         context_data: Optional[Dict[str, Any]] = None) -> str:
        """Store a conversation with intelligent context extraction"""
        
        # Generate unique ID
        conversation_id = hashlib.md5(
            f"{self.session_id}_{datetime.now().isoformat()}_{user_input[:50]}".encode()
        ).hexdigest()[:12]
        
        # Extract context intelligently
        context_tags = self._extract_context_tags(user_input, assistant_response)
        sentiment = self._analyze_sentiment(user_input)
        importance_score = self._calculate_importance(user_input, assistant_response, context_tags)
        related_topics = self._extract_topics(user_input + " " + assistant_response)
        follow_up_reminders = self._extract_reminders(assistant_response)
        
        # Create conversation entry
        entry = ConversationEntry(
            id=conversation_id,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            assistant_response=assistant_response,
            context_tags=context_tags,
            sentiment=sentiment,
            importance_score=importance_score,
            related_topics=related_topics,
            follow_up_reminders=follow_up_reminders
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id, entry.session_id, entry.timestamp, entry.user_input,
                entry.assistant_response, json.dumps(entry.context_tags), entry.sentiment,
                entry.importance_score, json.dumps(entry.related_topics),
                json.dumps(entry.follow_up_reminders)
            ))
        
        # Update user context
        self._update_user_context(user_input, assistant_response, context_tags, related_topics)
        
        # Update topic clusters
        self._update_topic_clusters(related_topics, conversation_id)
        
        print(f"💾 Stored conversation: {conversation_id}")
        return conversation_id
    
    def get_relevant_context(self, current_input: str, context_window: int = 10) -> Dict[str, Any]:
        """Get relevant conversation context for current input"""
        
        # Extract topics from current input
        current_topics = self._extract_topics(current_input)
        
        # Get recent conversations
        recent_conversations = self._get_recent_conversations(limit=context_window)
        
        # Get topically related conversations
        related_conversations = self._get_related_conversations(current_topics, limit=5)
        
        # Get user context
        user_context = self._get_user_context()
        
        # Get important conversations
        important_conversations = self._get_important_conversations(limit=3)
        
        return {
            "current_topics": current_topics,
            "recent_conversations": recent_conversations,
            "related_conversations": related_conversations,
            "user_context": asdict(user_context) if user_context else {},
            "important_conversations": important_conversations,
            "conversation_summary": self._generate_context_summary(recent_conversations, related_conversations)
        }
    
    def get_conversation_history(self, limit: int = 50) -> List[ConversationEntry]:
        """Get conversation history for session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (self.session_id, limit))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append(ConversationEntry(
                    id=row[0], session_id=row[1], timestamp=row[2],
                    user_input=row[3], assistant_response=row[4],
                    context_tags=json.loads(row[5]), sentiment=row[6],
                    importance_score=row[7], related_topics=json.loads(row[8]),
                    follow_up_reminders=json.loads(row[9])
                ))
            
            return conversations
    
    def update_user_preference(self, category: str, preference: str, value: Any):
        """Update user preference"""
        user_context = self._get_user_context() or UserContext(
            user_id=self.session_id, name=None, preferences={},
            working_style="", active_projects=[], recurring_topics={},
            relationship_context={}, schedule_patterns={},
            last_interaction=datetime.now().isoformat(), interaction_count=0
        )
        
        if category not in user_context.preferences:
            user_context.preferences[category] = {}
        
        user_context.preferences[category][preference] = value
        self._save_user_context(user_context)
        
        print(f"👤 Updated user preference: {category}.{preference} = {value}")
    
    def get_follow_up_reminders(self) -> List[Dict[str, Any]]:
        """Get pending follow-up reminders"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, timestamp, follow_up_reminders FROM conversations 
                WHERE session_id = ? AND follow_up_reminders != '[]'
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', (self.session_id,))
            
            reminders = []
            for row in cursor.fetchall():
                follow_ups = json.loads(row[2])
                for reminder in follow_ups:
                    reminders.append({
                        "conversation_id": row[0],
                        "timestamp": row[1],
                        "reminder": reminder,
                        "days_ago": (datetime.now() - datetime.fromisoformat(row[1])).days
                    })
            
            return reminders
    
    def search_conversations(self, query: str, limit: int = 10) -> List[ConversationEntry]:
        """Search conversations by text content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM conversations 
                WHERE session_id = ? AND (
                    user_input LIKE ? OR 
                    assistant_response LIKE ? OR
                    related_topics LIKE ?
                )
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            ''', (self.session_id, f"%{query}%", f"%{query}%", f"%{query}%", limit))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append(ConversationEntry(
                    id=row[0], session_id=row[1], timestamp=row[2],
                    user_input=row[3], assistant_response=row[4],
                    context_tags=json.loads(row[5]), sentiment=row[6],
                    importance_score=row[7], related_topics=json.loads(row[8]),
                    follow_up_reminders=json.loads(row[9])
                ))
            
            return conversations
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total conversations
            total_conversations = conn.execute(
                'SELECT COUNT(*) FROM conversations WHERE session_id = ?', 
                (self.session_id,)
            ).fetchone()[0]
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_activity = conn.execute(
                'SELECT COUNT(*) FROM conversations WHERE session_id = ? AND timestamp > ?',
                (self.session_id, week_ago)
            ).fetchone()[0]
            
            # Top topics
            cursor = conn.execute(
                'SELECT related_topics FROM conversations WHERE session_id = ?',
                (self.session_id,)
            )
            
            topic_count = defaultdict(int)
            for row in cursor.fetchall():
                topics = json.loads(row[0])
                for topic in topics:
                    topic_count[topic] += 1
            
            top_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_conversations": total_conversations,
                "recent_activity": recent_activity,
                "top_topics": top_topics,
                "memory_size": self.db_path.stat().st_size if self.db_path.exists() else 0,
                "last_interaction": self._get_last_interaction_time()
            }
    
    # Private helper methods
    def _extract_context_tags(self, user_input: str, assistant_response: str) -> List[str]:
        """Extract context tags from conversation"""
        tags = []
        
        # Question types
        if any(word in user_input.lower() for word in ['how', 'what', 'why', 'when', 'where']):
            tags.append('question')
        
        # Request types
        if any(word in user_input.lower() for word in ['please', 'can you', 'could you', 'help']):
            tags.append('request')
        
        # Task-related
        if any(word in user_input.lower() for word in ['task', 'project', 'work', 'deadline']):
            tags.append('task')
        
        # Personal
        if any(word in user_input.lower() for word in ['i need', 'i want', 'my']):
            tags.append('personal')
        
        # Technical
        if any(word in user_input.lower() for word in ['code', 'api', 'database', 'script', 'programming']):
            tags.append('technical')
        
        # Planning
        if any(word in user_input.lower() for word in ['plan', 'schedule', 'organize', 'prepare']):
            tags.append('planning')
        
        return tags
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'perfect', 'love', 'like', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'frustrated', 'angry', 'problem']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_importance(self, user_input: str, assistant_response: str, context_tags: List[str]) -> float:
        """Calculate importance score for conversation"""
        score = 0.5  # Base score
        
        # Length factor
        total_length = len(user_input) + len(assistant_response)
        if total_length > 500:
            score += 0.2
        elif total_length > 200:
            score += 0.1
        
        # Context tags factor
        important_tags = ['task', 'planning', 'personal', 'technical']
        tag_score = sum(0.1 for tag in context_tags if tag in important_tags)
        score += min(tag_score, 0.3)
        
        # Question depth
        if user_input.count('?') > 1:
            score += 0.1
        
        # Task-related keywords
        task_keywords = ['deadline', 'important', 'urgent', 'project', 'remember']
        if any(keyword in user_input.lower() for keyword in task_keywords):
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text using simple keyword extraction"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter and count
        topic_words = [word for word in words if word not in stop_words]
        
        # Get unique topics with minimum frequency
        word_count = defaultdict(int)
        for word in topic_words:
            word_count[word] += 1
        
        # Return topics that appear at least once and are meaningful
        topics = [word for word, count in word_count.items() if count >= 1 and len(word) >= 4]
        return topics[:10]  # Limit to top 10 topics
    
    def _extract_reminders(self, assistant_response: str) -> List[str]:
        """Extract follow-up reminders from assistant response"""
        reminders = []
        
        # Look for reminder patterns
        reminder_patterns = [
            r"remember to (.+?)(?:\.|$)",
            r"don't forget to (.+?)(?:\.|$)",
            r"make sure to (.+?)(?:\.|$)",
            r"follow up (?:on|with) (.+?)(?:\.|$)",
            r"check back (?:on|in) (.+?)(?:\.|$)"
        ]
        
        for pattern in reminder_patterns:
            matches = re.findall(pattern, assistant_response.lower(), re.IGNORECASE)
            reminders.extend(matches)
        
        return reminders[:5]  # Limit to 5 reminders
    
    def _get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_input, assistant_response, timestamp, importance_score FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (self.session_id, limit))
            
            return [
                {
                    "user_input": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                    "assistant_response": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                    "timestamp": row[2],
                    "importance_score": row[3]
                }
                for row in cursor.fetchall()
            ]
    
    def _get_related_conversations(self, topics: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Get conversations related to current topics"""
        if not topics:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join(['?'] * len(topics))
            cursor = conn.execute(f'''
                SELECT user_input, assistant_response, timestamp, importance_score, related_topics 
                FROM conversations 
                WHERE session_id = ? AND (
                    {' OR '.join([f'related_topics LIKE ?' for _ in topics])}
                )
                ORDER BY importance_score DESC, timestamp DESC 
                LIMIT ?
            ''', [self.session_id] + [f'%{topic}%' for topic in topics] + [limit])
            
            return [
                {
                    "user_input": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                    "assistant_response": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                    "timestamp": row[2],
                    "importance_score": row[3],
                    "matching_topics": [topic for topic in topics if topic in row[4]]
                }
                for row in cursor.fetchall()
            ]
    
    def _get_important_conversations(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get most important conversations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_input, assistant_response, timestamp, importance_score FROM conversations 
                WHERE session_id = ? AND importance_score > 0.7
                ORDER BY importance_score DESC 
                LIMIT ?
            ''', (self.session_id, limit))
            
            return [
                {
                    "user_input": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                    "assistant_response": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                    "timestamp": row[2],
                    "importance_score": row[3]
                }
                for row in cursor.fetchall()
            ]
    
    def _generate_context_summary(self, recent: List[Dict], related: List[Dict]) -> str:
        """Generate a summary of conversation context"""
        if not recent and not related:
            return "No previous conversation context available."
        
        summary_parts = []
        
        if recent:
            summary_parts.append(f"Recent discussions include {len(recent)} conversations")
            
        if related:
            summary_parts.append(f"Found {len(related)} topically related conversations")
        
        return ". ".join(summary_parts) + "."
    
    def _update_user_context(self, user_input: str, assistant_response: str, 
                           context_tags: List[str], topics: List[str]):
        """Update user context based on conversation"""
        user_context = self._get_user_context() or UserContext(
            user_id=self.session_id, name=None, preferences={},
            working_style="", active_projects=[], recurring_topics={},
            relationship_context={}, schedule_patterns={},
            last_interaction=datetime.now().isoformat(), interaction_count=0
        )
        
        # Update recurring topics
        for topic in topics:
            if topic in user_context.recurring_topics:
                user_context.recurring_topics[topic] += 1
            else:
                user_context.recurring_topics[topic] = 1
        
        # Update interaction count and timestamp
        user_context.interaction_count += 1
        user_context.last_interaction = datetime.now().isoformat()
        
        # Detect working style patterns
        if 'planning' in context_tags:
            user_context.working_style = "organized_planner"
        elif 'technical' in context_tags:
            user_context.working_style = "technical_focused"
        
        self._save_user_context(user_context)
    
    def _get_user_context(self) -> Optional[UserContext]:
        """Get user context from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM user_contexts WHERE user_id = ?', 
                (self.session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return UserContext(
                    user_id=row[0], name=row[1], 
                    preferences=json.loads(row[2]) if row[2] else {},
                    working_style=row[3], 
                    active_projects=json.loads(row[4]) if row[4] else [],
                    recurring_topics=json.loads(row[5]) if row[5] else {},
                    relationship_context=json.loads(row[6]) if row[6] else {},
                    schedule_patterns=json.loads(row[7]) if row[7] else {},
                    last_interaction=row[8], interaction_count=row[9]
                )
        return None
    
    def _save_user_context(self, user_context: UserContext):
        """Save user context to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO user_contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_context.user_id, user_context.name,
                json.dumps(user_context.preferences), user_context.working_style,
                json.dumps(user_context.active_projects), json.dumps(user_context.recurring_topics),
                json.dumps(user_context.relationship_context), json.dumps(user_context.schedule_patterns),
                user_context.last_interaction, user_context.interaction_count
            ))
    
    def _update_topic_clusters(self, topics: List[str], conversation_id: str):
        """Update topic clusters with new conversation"""
        # This is a simplified implementation
        # In production, you might want more sophisticated clustering
        pass
    
    def _get_last_interaction_time(self) -> Optional[str]:
        """Get timestamp of last interaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT MAX(timestamp) FROM conversations WHERE session_id = ?',
                (self.session_id,)
            )
            result = cursor.fetchone()
            return result[0] if result[0] else None


def main():
    """Test the conversation memory system"""
    print("🧠 Testing Conversation Memory System")
    print("=" * 50)
    
    # Initialize memory
    memory = ConversationMemory(session_id="test_session")
    
    # Test storing conversations
    conv_id1 = memory.store_conversation(
        "Hi, I need help planning my project timeline for next week",
        "I'd be happy to help you plan your project timeline! Let's break this down into manageable steps. What's the main project you're working on, and what are the key deliverables you need to complete by next week?"
    )
    
    conv_id2 = memory.store_conversation(
        "The project is a web application using React and I need to finish the user authentication system",
        "Great! A React authentication system is a crucial component. Here's a suggested timeline: Day 1-2: Set up authentication backend (login/register APIs), Day 3-4: Create React login/register components, Day 5: Implement protected routes and session management, Day 6-7: Testing and bug fixes. Don't forget to test with different user scenarios and edge cases."
    )
    
    # Test context retrieval
    context = memory.get_relevant_context("How should I handle user sessions in React?")
    
    print(f"\n📊 Memory Stats:")
    stats = memory.get_memory_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n🎯 Context for 'React sessions':")
    print(f"   Current topics: {context['current_topics']}")
    print(f"   Recent conversations: {len(context['recent_conversations'])}")
    print(f"   Related conversations: {len(context['related_conversations'])}")
    print(f"   Summary: {context['conversation_summary']}")
    
    # Test search
    search_results = memory.search_conversations("React")
    print(f"\n🔍 Search results for 'React': {len(search_results)} found")
    
    # Test reminders
    reminders = memory.get_follow_up_reminders()
    print(f"\n⏰ Follow-up reminders: {len(reminders)} found")
    
    print(f"\n✅ Conversation Memory system test completed!")


if __name__ == "__main__":
    main()