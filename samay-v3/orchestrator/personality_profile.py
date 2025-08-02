#!/usr/bin/env python3
"""
Samay v3 - Personality Profile System
====================================
Adaptive communication patterns for companion-style AI interactions
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import re


@dataclass
class CommunicationStyle:
    """User's preferred communication style"""
    formality_level: str  # casual, professional, mixed
    response_length: str  # brief, detailed, adaptive
    tone_preference: str  # friendly, analytical, supportive
    emoji_usage: bool
    explanation_depth: str  # surface, moderate, deep
    proactive_suggestions: bool


@dataclass
class InteractionPattern:
    """Patterns in user interactions"""
    preferred_times: List[str]  # morning, afternoon, evening
    session_duration: float  # average minutes per session
    topic_transitions: Dict[str, int]  # how user moves between topics
    question_types: Dict[str, int]  # frequency of different question types
    feedback_patterns: Dict[str, int]  # how user gives feedback


@dataclass
class PersonalityTraits:
    """AI companion personality traits"""
    warmth: float  # 0.0 to 1.0
    assertiveness: float
    curiosity: float
    patience: float
    humor: float
    empathy: float


class PersonalityProfile:
    """Adaptive personality system for companion AI"""
    
    def __init__(self, memory_dir: str = "memory", user_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.user_id = user_id
        
        # Initialize database
        self.db_path = self.memory_dir / "personality.db"
        self.init_database()
        
        # Load or create personality profile
        self.communication_style = self._load_communication_style()
        self.interaction_patterns = self._load_interaction_patterns()
        self.personality_traits = self._load_personality_traits()
        
        print(f"🎭 PersonalityProfile initialized for {user_id}")
        print(f"📁 Database: {self.db_path}")
        print(f"🎨 Style: {self.communication_style.tone_preference}")
    
    def init_database(self):
        """Initialize SQLite database for personality storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS communication_styles (
                    user_id TEXT PRIMARY KEY,
                    formality_level TEXT,
                    response_length TEXT,
                    tone_preference TEXT,
                    emoji_usage BOOLEAN,
                    explanation_depth TEXT,
                    proactive_suggestions BOOLEAN,
                    last_updated TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS interaction_patterns (
                    user_id TEXT PRIMARY KEY,
                    preferred_times TEXT,
                    session_duration REAL,
                    topic_transitions TEXT,
                    question_types TEXT,
                    feedback_patterns TEXT,
                    last_updated TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS personality_traits (
                    user_id TEXT PRIMARY KEY,
                    warmth REAL,
                    assertiveness REAL,
                    curiosity REAL,
                    patience REAL,
                    humor REAL,
                    empathy REAL,
                    last_updated TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS adaptation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    timestamp TEXT,
                    adaptation_type TEXT,
                    before_value TEXT,
                    after_value TEXT,
                    trigger_reason TEXT
                )
            ''')
    
    def adapt_to_interaction(self, user_input: str, user_feedback: Optional[str] = None, 
                           interaction_context: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None):
        """Adapt personality based on user interaction"""
        
        # Analyze communication style preferences
        style_changes = self._analyze_style_preferences(user_input, user_feedback)
        
        # Update interaction patterns
        pattern_updates = self._update_interaction_patterns(user_input, interaction_context)
        
        # Use context if provided, otherwise use interaction_context
        effective_context = context or interaction_context
        
        # Adjust personality traits based on feedback
        trait_adjustments = self._adjust_personality_traits(user_feedback, effective_context)
        
        # Apply changes and log adaptations
        if style_changes:
            self._apply_style_changes(style_changes)
        
        if pattern_updates:
            self._apply_pattern_updates(pattern_updates)
        
        if trait_adjustments:
            self._apply_trait_adjustments(trait_adjustments)
        
        print(f"🔄 Personality adapted based on interaction")
    
    def generate_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate adaptive system prompt based on current personality profile"""
        
        # Base companion identity
        prompt_parts = [
            "You are Samay, a personal AI companion.",
            f"Communication style: {self.communication_style.tone_preference} and {self.communication_style.formality_level}."
        ]
        
        # Personality traits
        traits_desc = self._generate_traits_description()
        if traits_desc:
            prompt_parts.append(traits_desc)
        
        # Response preferences
        if self.communication_style.response_length == "brief":
            prompt_parts.append("Keep responses concise and to the point.")
        elif self.communication_style.response_length == "detailed":
            prompt_parts.append("Provide thorough, detailed explanations.")
        
        # Emoji usage
        if self.communication_style.emoji_usage:
            prompt_parts.append("Use appropriate emojis to enhance communication.")
        else:
            prompt_parts.append("Avoid using emojis unless specifically requested.")
        
        # Proactive behavior
        if self.communication_style.proactive_suggestions:
            prompt_parts.append("Proactively offer suggestions and assistance.")
        
        # Context-specific adaptations
        if context:
            contextual_prompt = self._generate_contextual_prompt(context)
            if contextual_prompt:
                prompt_parts.append(contextual_prompt)
        
        return " ".join(prompt_parts)
    
    def get_response_template(self, message_type: str = "general") -> Dict[str, str]:
        """Get response template based on personality and message type"""
        
        templates = {
            "greeting": self._get_greeting_template(),
            "task_assistance": self._get_task_template(),
            "clarification": self._get_clarification_template(),
            "encouragement": self._get_encouragement_template(),
            "general": self._get_general_template()
        }
        
        return templates.get(message_type, templates["general"])
    
    def analyze_user_satisfaction(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze user satisfaction based on conversation patterns"""
        
        satisfaction_scores = {
            "response_relevance": 0.0,
            "communication_match": 0.0,
            "helpfulness": 0.0,
            "engagement": 0.0
        }
        
        if not conversation_history:
            return satisfaction_scores
        
        # Analyze response relevance
        satisfaction_scores["response_relevance"] = self._calculate_relevance_score(conversation_history)
        
        # Check communication style match
        satisfaction_scores["communication_match"] = self._calculate_style_match(conversation_history)
        
        # Evaluate helpfulness
        satisfaction_scores["helpfulness"] = self._calculate_helpfulness_score(conversation_history)
        
        # Measure engagement
        satisfaction_scores["engagement"] = self._calculate_engagement_score(conversation_history)
        
        return satisfaction_scores
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get comprehensive personality profile summary"""
        return {
            "communication_style": asdict(self.communication_style),
            "interaction_patterns": asdict(self.interaction_patterns),
            "personality_traits": asdict(self.personality_traits),
            "last_adaptation": self._get_last_adaptation_time(),
            "adaptation_count": self._get_adaptation_count()
        }
    
    # Private helper methods
    def _load_communication_style(self) -> CommunicationStyle:
        """Load communication style from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM communication_styles WHERE user_id = ?',
                (self.user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return CommunicationStyle(
                    formality_level=row[1],
                    response_length=row[2],
                    tone_preference=row[3],
                    emoji_usage=bool(row[4]),
                    explanation_depth=row[5],
                    proactive_suggestions=bool(row[6])
                )
            else:
                # Default style for new users
                default_style = CommunicationStyle(
                    formality_level="mixed",
                    response_length="adaptive",
                    tone_preference="friendly",
                    emoji_usage=False,
                    explanation_depth="moderate",
                    proactive_suggestions=True
                )
                self._save_communication_style(default_style)
                return default_style
    
    def _load_interaction_patterns(self) -> InteractionPattern:
        """Load interaction patterns from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM interaction_patterns WHERE user_id = ?',
                (self.user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return InteractionPattern(
                    preferred_times=json.loads(row[1]) if row[1] else [],
                    session_duration=row[2] or 0.0,
                    topic_transitions=json.loads(row[3]) if row[3] else {},
                    question_types=json.loads(row[4]) if row[4] else {},
                    feedback_patterns=json.loads(row[5]) if row[5] else {}
                )
            else:
                # Default patterns for new users
                default_patterns = InteractionPattern(
                    preferred_times=[],
                    session_duration=0.0,
                    topic_transitions={},
                    question_types={},
                    feedback_patterns={}
                )
                self._save_interaction_patterns(default_patterns)
                return default_patterns
    
    def _load_personality_traits(self) -> PersonalityTraits:
        """Load personality traits from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM personality_traits WHERE user_id = ?',
                (self.user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return PersonalityTraits(
                    warmth=row[1],
                    assertiveness=row[2],
                    curiosity=row[3],
                    patience=row[4],
                    humor=row[5],
                    empathy=row[6]
                )
            else:
                # Default balanced personality
                default_traits = PersonalityTraits(
                    warmth=0.7,
                    assertiveness=0.6,
                    curiosity=0.8,
                    patience=0.8,
                    humor=0.5,
                    empathy=0.7
                )
                self._save_personality_traits(default_traits)
                return default_traits
    
    def _analyze_style_preferences(self, user_input: str, feedback: Optional[str]) -> Dict[str, Any]:
        """Analyze user input for communication style preferences"""
        changes = {}
        
        # Analyze formality
        formal_indicators = ['please', 'could you', 'would you mind', 'thank you']
        casual_indicators = ['hey', 'yeah', 'ok', 'cool', 'thanks']
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in user_input.lower())
        casual_count = sum(1 for indicator in casual_indicators if indicator in user_input.lower())
        
        if formal_count > casual_count and self.communication_style.formality_level != "professional":
            changes['formality_level'] = "professional"
        elif casual_count > formal_count and self.communication_style.formality_level != "casual":
            changes['formality_level'] = "casual"
        
        # Analyze response length preference
        if len(user_input.split()) < 10 and self.communication_style.response_length != "brief":
            changes['response_length'] = "brief"
        elif len(user_input.split()) > 50 and self.communication_style.response_length != "detailed":
            changes['response_length'] = "detailed"
        
        # Analyze emoji usage from feedback
        if feedback and ('emoji' in feedback.lower() or '😊' in feedback):
            if 'no emoji' in feedback.lower() or 'without emoji' in feedback.lower():
                changes['emoji_usage'] = False
            elif 'emoji' in feedback.lower():
                changes['emoji_usage'] = True
        
        return changes
    
    def _update_interaction_patterns(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Update interaction patterns based on current interaction"""
        updates = {}
        
        # Update preferred times
        current_hour = datetime.now().hour
        time_period = "morning" if current_hour < 12 else "afternoon" if current_hour < 18 else "evening"
        
        if time_period not in self.interaction_patterns.preferred_times:
            updates['preferred_times'] = self.interaction_patterns.preferred_times + [time_period]
        
        # Analyze question types
        question_types = {
            'factual': ['what', 'when', 'where', 'who'],
            'procedural': ['how', 'steps', 'process'],
            'analytical': ['why', 'analyze', 'compare'],
            'creative': ['brainstorm', 'ideas', 'creative']
        }
        
        for q_type, keywords in question_types.items():
            if any(keyword in user_input.lower() for keyword in keywords):
                current_count = self.interaction_patterns.question_types.get(q_type, 0)
                updates[f'question_types_{q_type}'] = current_count + 1
        
        return updates
    
    def _adjust_personality_traits(self, feedback: Optional[str], context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Adjust personality traits based on feedback"""
        adjustments = {}
        
        if not feedback:
            return adjustments
        
        feedback_lower = feedback.lower()
        
        # Warmth adjustments
        if 'warm' in feedback_lower or 'friendly' in feedback_lower:
            adjustments['warmth'] = min(1.0, self.personality_traits.warmth + 0.1)
        elif 'cold' in feedback_lower or 'distant' in feedback_lower:
            adjustments['warmth'] = max(0.0, self.personality_traits.warmth - 0.1)
        
        # Assertiveness adjustments
        if 'more direct' in feedback_lower or 'assertive' in feedback_lower:
            adjustments['assertiveness'] = min(1.0, self.personality_traits.assertiveness + 0.1)
        elif 'less aggressive' in feedback_lower or 'gentler' in feedback_lower:
            adjustments['assertiveness'] = max(0.0, self.personality_traits.assertiveness - 0.1)
        
        # Humor adjustments
        if 'funny' in feedback_lower or 'humor' in feedback_lower:
            adjustments['humor'] = min(1.0, self.personality_traits.humor + 0.1)
        elif 'serious' in feedback_lower or 'no jokes' in feedback_lower:
            adjustments['humor'] = max(0.0, self.personality_traits.humor - 0.1)
        
        return adjustments
    
    def _generate_traits_description(self) -> str:
        """Generate personality traits description for system prompt"""
        traits = []
        
        if self.personality_traits.warmth > 0.7:
            traits.append("warm and approachable")
        if self.personality_traits.curiosity > 0.7:
            traits.append("curious and inquisitive")
        if self.personality_traits.patience > 0.7:
            traits.append("patient and understanding")
        if self.personality_traits.humor > 0.6:
            traits.append("with appropriate humor")
        if self.personality_traits.empathy > 0.7:
            traits.append("empathetic and supportive")
        
        if traits:
            return f"Be {', '.join(traits)}."
        return ""
    
    def _generate_contextual_prompt(self, context: Dict[str, Any]) -> str:
        """Generate contextual prompt additions"""
        additions = []
        
        if context.get('task_type') == 'brainstorming':
            additions.append("Focus on creative exploration and idea generation.")
        elif context.get('task_type') == 'analysis':
            additions.append("Provide structured, analytical thinking.")
        elif context.get('urgency') == 'high':
            additions.append("Prioritize efficiency and clear action items.")
        
        return " ".join(additions)
    
    def _get_greeting_template(self) -> Dict[str, str]:
        """Get greeting template based on personality"""
        if self.personality_traits.warmth > 0.7:
            return {
                "opening": "Hello! Great to see you again!",
                "follow_up": "How can I help you today?"
            }
        else:
            return {
                "opening": "Hello.",
                "follow_up": "What would you like to work on?"
            }
    
    def _get_task_template(self) -> Dict[str, str]:
        """Get task assistance template"""
        if self.communication_style.proactive_suggestions:
            return {
                "acknowledgment": "I'll help you with that.",
                "approach": "Here's how I suggest we approach it:",
                "follow_up": "Would you like me to elaborate on any of these steps?"
            }
        else:
            return {
                "acknowledgment": "I can help with that.",
                "approach": "Here's the information:",
                "follow_up": "Let me know if you need more details."
            }
    
    def _get_clarification_template(self) -> Dict[str, str]:
        """Get clarification template"""
        if self.personality_traits.patience > 0.7:
            return {
                "opening": "I want to make sure I understand correctly.",
                "question": "Could you help me clarify:",
                "closing": "This will help me give you the best response."
            }
        else:
            return {
                "opening": "I need clarification.",
                "question": "Please specify:",
                "closing": "Thanks."
            }
    
    def _get_encouragement_template(self) -> Dict[str, str]:
        """Get encouragement template"""
        if self.personality_traits.empathy > 0.7:
            return {
                "validation": "That sounds challenging, and it's completely understandable.",
                "support": "You're taking the right approach by thinking this through.",
                "motivation": "I'm here to support you through this process."
            }
        else:
            return {
                "validation": "I understand the situation.",
                "support": "Let's work through this systematically.",
                "motivation": "We can solve this together."
            }
    
    def _get_general_template(self) -> Dict[str, str]:
        """Get general response template"""
        return {
            "acknowledgment": "I understand.",
            "response": "Here's what I think:",
            "follow_up": "What would you like to explore next?"
        }
    
    def _calculate_relevance_score(self, history: List[Dict[str, Any]]) -> float:
        """Calculate response relevance score"""
        # Simplified relevance calculation
        return 0.8  # Placeholder
    
    def _calculate_style_match(self, history: List[Dict[str, Any]]) -> float:
        """Calculate communication style match score"""
        # Simplified style match calculation
        return 0.7  # Placeholder
    
    def _calculate_helpfulness_score(self, history: List[Dict[str, Any]]) -> float:
        """Calculate helpfulness score"""
        # Simplified helpfulness calculation
        return 0.9  # Placeholder
    
    def _calculate_engagement_score(self, history: List[Dict[str, Any]]) -> float:
        """Calculate engagement score"""
        # Simplified engagement calculation
        return 0.8  # Placeholder
    
    def _save_communication_style(self, style: CommunicationStyle):
        """Save communication style to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO communication_styles VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.user_id, style.formality_level, style.response_length,
                style.tone_preference, style.emoji_usage, style.explanation_depth,
                style.proactive_suggestions, datetime.now().isoformat()
            ))
    
    def _save_interaction_patterns(self, patterns: InteractionPattern):
        """Save interaction patterns to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO interaction_patterns VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.user_id, json.dumps(patterns.preferred_times),
                patterns.session_duration, json.dumps(patterns.topic_transitions),
                json.dumps(patterns.question_types), json.dumps(patterns.feedback_patterns),
                datetime.now().isoformat()
            ))
    
    def _save_personality_traits(self, traits: PersonalityTraits):
        """Save personality traits to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO personality_traits VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.user_id, traits.warmth, traits.assertiveness, traits.curiosity,
                traits.patience, traits.humor, traits.empathy, datetime.now().isoformat()
            ))
    
    def _apply_style_changes(self, changes: Dict[str, Any]):
        """Apply communication style changes"""
        for key, value in changes.items():
            setattr(self.communication_style, key, value)
        self._save_communication_style(self.communication_style)
        self._log_adaptation("style", changes)
    
    def _apply_pattern_updates(self, updates: Dict[str, Any]):
        """Apply interaction pattern updates"""
        for key, value in updates.items():
            if key.startswith('question_types_'):
                q_type = key.replace('question_types_', '')
                self.interaction_patterns.question_types[q_type] = value
            else:
                setattr(self.interaction_patterns, key, value)
        self._save_interaction_patterns(self.interaction_patterns)
        self._log_adaptation("patterns", updates)
    
    def _apply_trait_adjustments(self, adjustments: Dict[str, float]):
        """Apply personality trait adjustments"""
        for trait, value in adjustments.items():
            setattr(self.personality_traits, trait, value)
        self._save_personality_traits(self.personality_traits)
        self._log_adaptation("traits", adjustments)
    
    def _log_adaptation(self, adaptation_type: str, changes: Dict[str, Any]):
        """Log personality adaptation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO adaptation_history 
                (user_id, timestamp, adaptation_type, before_value, after_value, trigger_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.user_id, datetime.now().isoformat(), adaptation_type,
                "", json.dumps(changes), "user_interaction"
            ))
    
    def _get_last_adaptation_time(self) -> Optional[str]:
        """Get timestamp of last adaptation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT MAX(timestamp) FROM adaptation_history WHERE user_id = ?',
                (self.user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result[0] else None
    
    def _get_adaptation_count(self) -> int:
        """Get total number of adaptations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT COUNT(*) FROM adaptation_history WHERE user_id = ?',
                (self.user_id,)
            )
            return cursor.fetchone()[0]


def main():
    """Test the personality profile system"""
    print("🎭 Testing Personality Profile System")
    print("=" * 50)
    
    # Initialize personality profile
    profile = PersonalityProfile(user_id="test_user")
    
    # Test system prompt generation
    system_prompt = profile.generate_system_prompt()
    print(f"\n🤖 Generated System Prompt:")
    print(f"   {system_prompt}")
    
    # Test response templates
    greeting_template = profile.get_response_template("greeting")
    print(f"\n👋 Greeting Template:")
    for key, value in greeting_template.items():
        print(f"   {key}: {value}")
    
    # Test adaptation
    print(f"\n🔄 Testing Adaptation:")
    profile.adapt_to_interaction(
        "Hey, can you help me with something quick?",
        feedback="I prefer more casual responses",
        interaction_context={"task_type": "quick_help"}
    )
    
    # Generate updated system prompt
    updated_prompt = profile.generate_system_prompt()
    print(f"   Updated prompt: {updated_prompt}")
    
    # Test personality summary
    summary = profile.get_personality_summary()
    print(f"\n📊 Personality Summary:")
    print(f"   Communication Style: {summary['communication_style']['tone_preference']}")
    print(f"   Warmth: {summary['personality_traits']['warmth']:.1f}")
    print(f"   Adaptations: {summary['adaptation_count']}")
    
    print(f"\n✅ PersonalityProfile system test completed!")


if __name__ == "__main__":
    main()