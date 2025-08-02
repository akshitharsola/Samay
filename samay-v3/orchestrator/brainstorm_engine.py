#!/usr/bin/env python3
"""
Samay v3 - Brainstorming Engine System
=====================================
Phase 2: Iterative Refinement with multi-round prompt optimization
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum

from .local_llm import LocalLLMClient


class RefinementStage(Enum):
    INITIAL = "initial"
    EXPLORATION = "exploration"
    FOCUSED = "focused"
    OPTIMIZATION = "optimization"
    FINALIZATION = "finalization"


class BranchType(Enum):
    ALTERNATIVE = "alternative"
    REFINEMENT = "refinement"
    EXPLORATION = "exploration"
    OPTIMIZATION = "optimization"


@dataclass
class PromptVersion:
    """Represents a version of a prompt in the refinement process"""
    version_id: str
    content: str
    stage: RefinementStage
    quality_score: float
    metadata: Dict[str, Any]
    created_at: str
    parent_version: Optional[str] = None


@dataclass
class ConversationBranch:
    """Represents a branching conversation path"""
    branch_id: str
    branch_type: BranchType
    parent_branch: Optional[str]
    prompt_versions: List[str]
    quality_metrics: Dict[str, float]
    exploration_focus: str
    created_at: str


@dataclass
class RefinementFeedback:
    """User feedback for refinement"""
    feedback_id: str
    version_id: str
    feedback_type: str  # positive, negative, suggestion, direction
    content: str
    priority: int  # 1-5
    timestamp: str


class BrainstormEngine:
    """Iterative prompt refinement and conversation branching system"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "brainstorming.db"
        self.session_id = session_id
        self.llm_client = LocalLLMClient()
        
        # Current session state
        self.current_prompt_id = None
        self.current_branch_id = None
        self.refinement_history = []
        self.active_branches = {}
        
        self.init_database()
        print(f"🧠 BrainstormEngine initialized for session {session_id}")
    
    def init_database(self):
        """Initialize brainstorming database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prompt versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_versions (
                version_id TEXT PRIMARY KEY,
                session_id TEXT,
                content TEXT,
                stage TEXT,
                quality_score REAL,
                metadata TEXT,
                parent_version TEXT,
                created_at TEXT,
                FOREIGN KEY (parent_version) REFERENCES prompt_versions (version_id)
            )
        ''')
        
        # Conversation branches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_branches (
                branch_id TEXT PRIMARY KEY,
                session_id TEXT,
                branch_type TEXT,
                parent_branch TEXT,
                prompt_versions TEXT,
                quality_metrics TEXT,
                exploration_focus TEXT,
                created_at TEXT,
                FOREIGN KEY (parent_branch) REFERENCES conversation_branches (branch_id)
            )
        ''')
        
        # Refinement feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refinement_feedback (
                feedback_id TEXT PRIMARY KEY,
                version_id TEXT,
                feedback_type TEXT,
                content TEXT,
                priority INTEGER,
                timestamp TEXT,
                FOREIGN KEY (version_id) REFERENCES prompt_versions (version_id)
            )
        ''')
        
        # Quality assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_assessments (
                assessment_id TEXT PRIMARY KEY,
                version_id TEXT,
                clarity_score REAL,
                specificity_score REAL,
                completeness_score REAL,
                coherence_score REAL,
                overall_score REAL,
                assessment_notes TEXT,
                timestamp TEXT,
                FOREIGN KEY (version_id) REFERENCES prompt_versions (version_id)
            )
        ''')
        
        # Refinement sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refinement_sessions (
                session_id TEXT PRIMARY KEY,
                initial_prompt TEXT,
                final_prompt TEXT,
                total_iterations INTEGER,
                refinement_goal TEXT,
                success_criteria TEXT,
                completion_status TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_brainstorming_session(
        self, 
        initial_prompt: str, 
        refinement_goal: str = "general_improvement",
        success_criteria: List[str] = None
    ) -> str:
        """Start a new brainstorming session"""
        
        # Create initial prompt version
        initial_version = PromptVersion(
            version_id=str(uuid.uuid4()),
            content=initial_prompt,
            stage=RefinementStage.INITIAL,
            quality_score=0.5,  # Baseline score
            metadata={
                "word_count": len(initial_prompt.split()),
                "refinement_goal": refinement_goal,
                "success_criteria": success_criteria or []
            },
            created_at=datetime.now().isoformat()
        )
        
        # Store initial version
        self._store_prompt_version(initial_version)
        self.current_prompt_id = initial_version.version_id
        
        # Create initial branch
        initial_branch = ConversationBranch(
            branch_id=str(uuid.uuid4()),
            branch_type=BranchType.REFINEMENT,
            parent_branch=None,
            prompt_versions=[initial_version.version_id],
            quality_metrics={"initial_score": 0.5},
            exploration_focus=refinement_goal,
            created_at=datetime.now().isoformat()
        )
        
        self._store_conversation_branch(initial_branch)
        self.current_branch_id = initial_branch.branch_id
        
        # Create refinement session record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO refinement_sessions 
            (session_id, initial_prompt, refinement_goal, success_criteria, completion_status, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            initial_prompt,
            refinement_goal,
            json.dumps(success_criteria or []),
            "active",
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        print(f"🚀 Started brainstorming session: {self.session_id}")
        print(f"📝 Initial prompt: {initial_prompt[:100]}...")
        print(f"🎯 Goal: {refinement_goal}")
        
        return self.session_id
    
    def refine_prompt(
        self, 
        feedback: str, 
        refinement_type: str = "improvement"
    ) -> PromptVersion:
        """Refine the current prompt based on feedback"""
        
        if not self.current_prompt_id:
            raise ValueError("No active brainstorming session. Start one first.")
        
        # Get current prompt
        current_version = self._get_prompt_version(self.current_prompt_id)
        
        # Generate refinement using LLM
        refinement_prompt = self._build_refinement_prompt(
            current_version.content, 
            feedback, 
            refinement_type
        )
        
        # Get refinement suggestions from LLM
        system_prompt = self._generate_refinement_system_prompt(current_version.stage)
        llm_response = self.llm_client.generate_response(refinement_prompt, system_prompt)
        
        if not llm_response.success:
            raise RuntimeError(f"LLM refinement failed: {llm_response.error_message}")
        
        # Determine next stage
        next_stage = self._determine_next_stage(current_version.stage, feedback)
        
        # Create refined version
        refined_version = PromptVersion(
            version_id=str(uuid.uuid4()),
            content=llm_response.response.strip(),
            stage=next_stage,
            quality_score=self._assess_prompt_quality(llm_response.response),
            metadata={
                "refinement_type": refinement_type,
                "feedback_incorporated": feedback[:200],
                "word_count": len(llm_response.response.split()),
                "improvement_over_parent": True
            },
            created_at=datetime.now().isoformat(),
            parent_version=current_version.version_id
        )
        
        # Store refined version
        self._store_prompt_version(refined_version)
        
        # Store feedback
        feedback_record = RefinementFeedback(
            feedback_id=str(uuid.uuid4()),
            version_id=current_version.version_id,
            feedback_type=refinement_type,
            content=feedback,
            priority=3,  # Default priority
            timestamp=datetime.now().isoformat()
        )
        self._store_feedback(feedback_record)
        
        # Update current prompt
        self.current_prompt_id = refined_version.version_id
        self.refinement_history.append(refined_version.version_id)
        
        # Update branch with new version
        self._update_branch_with_version(self.current_branch_id, refined_version.version_id)
        
        print(f"✅ Refined prompt (stage: {next_stage.value})")
        print(f"📊 Quality score: {refined_version.quality_score:.2f}")
        
        return refined_version
    
    def create_conversation_branch(
        self, 
        branch_type: BranchType, 
        exploration_focus: str,
        alternative_prompt: Optional[str] = None
    ) -> str:
        """Create a new conversation branch for exploring alternatives"""
        
        if not self.current_prompt_id:
            raise ValueError("No active session to branch from")
        
        # Create new branch
        new_branch = ConversationBranch(
            branch_id=str(uuid.uuid4()),
            branch_type=branch_type,
            parent_branch=self.current_branch_id,
            prompt_versions=[],
            quality_metrics={},
            exploration_focus=exploration_focus,
            created_at=datetime.now().isoformat()
        )
        
        # If alternative prompt provided, create new version
        if alternative_prompt:
            alt_version = PromptVersion(
                version_id=str(uuid.uuid4()),
                content=alternative_prompt,
                stage=RefinementStage.EXPLORATION,
                quality_score=self._assess_prompt_quality(alternative_prompt),
                metadata={
                    "branch_type": branch_type.value,
                    "exploration_focus": exploration_focus
                },
                created_at=datetime.now().isoformat(),
                parent_version=self.current_prompt_id
            )
            
            self._store_prompt_version(alt_version)
            new_branch.prompt_versions = [alt_version.version_id]
        else:
            # Branch starts from current prompt
            new_branch.prompt_versions = [self.current_prompt_id]
        
        # Store branch
        self._store_conversation_branch(new_branch)
        self.active_branches[new_branch.branch_id] = new_branch
        
        print(f"🌟 Created {branch_type.value} branch: {exploration_focus}")
        print(f"🆔 Branch ID: {new_branch.branch_id}")
        
        return new_branch.branch_id
    
    def switch_to_branch(self, branch_id: str) -> bool:
        """Switch active context to a different branch"""
        
        branch = self._get_conversation_branch(branch_id)
        if not branch:
            return False
        
        # Switch to the latest prompt version in this branch
        if branch.prompt_versions:
            self.current_prompt_id = branch.prompt_versions[-1]
            self.current_branch_id = branch_id
            
            print(f"🔄 Switched to branch: {branch.exploration_focus}")
            return True
        
        return False
    
    def compare_versions(self, version_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple prompt versions"""
        
        versions = [self._get_prompt_version(vid) for vid in version_ids]
        
        comparison = {
            "versions": [],
            "quality_comparison": {},
            "content_analysis": {},
            "recommendations": []
        }
        
        for version in versions:
            if version:
                comparison["versions"].append({
                    "version_id": version.version_id,
                    "stage": version.stage.value,
                    "quality_score": version.quality_score,
                    "word_count": version.metadata.get("word_count", 0),
                    "created_at": version.created_at
                })
        
        # Quality comparison
        scores = [v.quality_score for v in versions if v]
        if scores:
            comparison["quality_comparison"] = {
                "highest_score": max(scores),
                "lowest_score": min(scores),
                "average_score": sum(scores) / len(scores),
                "score_range": max(scores) - min(scores)
            }
        
        # Generate recommendations
        if len(versions) >= 2:
            best_version = max(versions, key=lambda v: v.quality_score if v else 0)
            if best_version:
                comparison["recommendations"].append(
                    f"Version {best_version.version_id} has the highest quality score ({best_version.quality_score:.2f})"
                )
        
        return comparison
    
    def get_refinement_suggestions(self, current_prompt: str) -> List[str]:
        """Get AI-generated suggestions for prompt refinement"""
        
        analysis_prompt = f"""
        Analyze this prompt and suggest 3-5 specific improvements:
        
        PROMPT TO ANALYZE:
        {current_prompt}
        
        Provide suggestions in these categories:
        1. Clarity improvements
        2. Specificity enhancements  
        3. Structure optimization
        4. Context additions
        5. Goal alignment
        
        Format as numbered list with brief explanations.
        """
        
        system_prompt = "You are an expert prompt engineer. Analyze prompts and suggest specific, actionable improvements."
        
        response = self.llm_client.generate_response(analysis_prompt, system_prompt)
        
        if response.success:
            # Parse suggestions from response
            suggestions = []
            lines = response.response.split('\n')
            for line in lines:
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                    suggestions.append(line.strip())
            return suggestions[:5]  # Limit to 5 suggestions
        
        return ["Unable to generate suggestions at this time"]
    
    def finalize_session(self, final_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Finalize the brainstorming session"""
        
        if not final_prompt and self.current_prompt_id:
            final_version = self._get_prompt_version(self.current_prompt_id)
            final_prompt = final_version.content if final_version else ""
        
        # Update session record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE refinement_sessions 
            SET final_prompt = ?, total_iterations = ?, completion_status = ?, completed_at = ?
            WHERE session_id = ?
        ''', (
            final_prompt,
            len(self.refinement_history),
            "completed",
            datetime.now().isoformat(),
            self.session_id
        ))
        conn.commit()
        conn.close()
        
        # Generate session summary
        summary = {
            "session_id": self.session_id,
            "total_iterations": len(self.refinement_history),
            "final_prompt": final_prompt,
            "final_quality_score": self._assess_prompt_quality(final_prompt) if final_prompt else 0,
            "branches_explored": len(self.active_branches),
            "completion_time": datetime.now().isoformat()
        }
        
        print(f"🎉 Brainstorming session completed!")
        print(f"📊 Total iterations: {summary['total_iterations']}")
        print(f"🏆 Final quality score: {summary['final_quality_score']:.2f}")
        
        return summary
    
    # Private helper methods
    def _store_prompt_version(self, version: PromptVersion):
        """Store prompt version in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prompt_versions 
            (version_id, session_id, content, stage, quality_score, metadata, parent_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version.version_id,
            self.session_id,
            version.content,
            version.stage.value,
            version.quality_score,
            json.dumps(version.metadata),
            version.parent_version,
            version.created_at
        ))
        conn.commit()
        conn.close()
    
    def _store_conversation_branch(self, branch: ConversationBranch):
        """Store conversation branch in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_branches 
            (branch_id, session_id, branch_type, parent_branch, prompt_versions, quality_metrics, exploration_focus, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            branch.branch_id,
            self.session_id,
            branch.branch_type.value,
            branch.parent_branch,
            json.dumps(branch.prompt_versions),
            json.dumps(branch.quality_metrics),
            branch.exploration_focus,
            branch.created_at
        ))
        conn.commit()
        conn.close()
    
    def _store_feedback(self, feedback: RefinementFeedback):
        """Store feedback in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO refinement_feedback 
            (feedback_id, version_id, feedback_type, content, priority, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            feedback.feedback_id,
            feedback.version_id,
            feedback.feedback_type,
            feedback.content,
            feedback.priority,
            feedback.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _get_prompt_version(self, version_id: str) -> Optional[PromptVersion]:
        """Retrieve prompt version from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT version_id, content, stage, quality_score, metadata, parent_version, created_at
            FROM prompt_versions WHERE version_id = ?
        ''', (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return PromptVersion(
                version_id=row[0],
                content=row[1],
                stage=RefinementStage(row[2]),
                quality_score=row[3],
                metadata=json.loads(row[4]) if row[4] else {},
                parent_version=row[5],
                created_at=row[6]
            )
        return None
    
    def _get_conversation_branch(self, branch_id: str) -> Optional[ConversationBranch]:
        """Retrieve conversation branch from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT branch_id, branch_type, parent_branch, prompt_versions, quality_metrics, exploration_focus, created_at
            FROM conversation_branches WHERE branch_id = ?
        ''', (branch_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ConversationBranch(
                branch_id=row[0],
                branch_type=BranchType(row[1]),
                parent_branch=row[2],
                prompt_versions=json.loads(row[3]) if row[3] else [],
                quality_metrics=json.loads(row[4]) if row[4] else {},
                exploration_focus=row[5],
                created_at=row[6]
            )
        return None
    
    def _build_refinement_prompt(self, current_prompt: str, feedback: str, refinement_type: str) -> str:
        """Build prompt for LLM refinement"""
        return f"""
        CURRENT PROMPT:
        {current_prompt}
        
        USER FEEDBACK:
        {feedback}
        
        REFINEMENT TYPE: {refinement_type}
        
        Please provide an improved version of the prompt that addresses the feedback.
        Focus on clarity, specificity, and effectiveness.
        
        REFINED PROMPT:
        """
    
    def _generate_refinement_system_prompt(self, stage: RefinementStage) -> str:
        """Generate system prompt based on refinement stage"""
        
        stage_prompts = {
            RefinementStage.INITIAL: "You are a prompt refinement expert. Help improve clarity and structure.",
            RefinementStage.EXPLORATION: "You are exploring creative alternatives. Focus on diverse approaches.",
            RefinementStage.FOCUSED: "You are focusing refinements. Enhance specificity and precision.",
            RefinementStage.OPTIMIZATION: "You are optimizing for performance. Maximize effectiveness.",
            RefinementStage.FINALIZATION: "You are finalizing the prompt. Ensure polish and completeness."
        }
        
        return stage_prompts.get(stage, "You are a helpful prompt refinement assistant.")
    
    def _determine_next_stage(self, current_stage: RefinementStage, feedback: str) -> RefinementStage:
        """Determine next refinement stage based on current stage and feedback"""
        
        feedback_lower = feedback.lower()
        
        # Stage progression logic
        stage_progression = {
            RefinementStage.INITIAL: RefinementStage.EXPLORATION,
            RefinementStage.EXPLORATION: RefinementStage.FOCUSED,
            RefinementStage.FOCUSED: RefinementStage.OPTIMIZATION,
            RefinementStage.OPTIMIZATION: RefinementStage.FINALIZATION,
            RefinementStage.FINALIZATION: RefinementStage.FINALIZATION
        }
        
        # Override based on feedback keywords
        if "explore" in feedback_lower or "alternative" in feedback_lower:
            return RefinementStage.EXPLORATION
        elif "focus" in feedback_lower or "specific" in feedback_lower:
            return RefinementStage.FOCUSED
        elif "optimize" in feedback_lower or "improve" in feedback_lower:
            return RefinementStage.OPTIMIZATION
        elif "final" in feedback_lower or "complete" in feedback_lower:
            return RefinementStage.FINALIZATION
        
        return stage_progression.get(current_stage, RefinementStage.FOCUSED)
    
    def _assess_prompt_quality(self, prompt: str) -> float:
        """Assess prompt quality using heuristics"""
        
        if not prompt:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length assessment (sweet spot around 50-200 words)
        word_count = len(prompt.split())
        if 50 <= word_count <= 200:
            score += 0.1
        elif 20 <= word_count <= 300:
            score += 0.05
        
        # Clarity indicators
        if any(word in prompt.lower() for word in ['specific', 'detailed', 'example', 'format']):
            score += 0.1
        
        # Structure indicators
        if any(char in prompt for char in [':', '-', '1.', '2.']):
            score += 0.1
        
        # Question or instruction clarity
        if prompt.strip().endswith('?') or any(word in prompt.lower() for word in ['please', 'provide', 'generate']):
            score += 0.1
        
        # Context indicators
        if any(word in prompt.lower() for word in ['context', 'background', 'goal', 'purpose']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _update_branch_with_version(self, branch_id: str, version_id: str):
        """Update branch with new version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current prompt versions
        cursor.execute('SELECT prompt_versions FROM conversation_branches WHERE branch_id = ?', (branch_id,))
        row = cursor.fetchone()
        
        if row:
            current_versions = json.loads(row[0]) if row[0] else []
            current_versions.append(version_id)
            
            cursor.execute('''
                UPDATE conversation_branches 
                SET prompt_versions = ?
                WHERE branch_id = ?
            ''', (json.dumps(current_versions), branch_id))
        
        conn.commit()
        conn.close()


def main():
    """Test the brainstorming engine system"""
    print("🧠 Testing Brainstorming Engine System")
    print("=" * 50)
    
    # Initialize brainstorming engine
    engine = BrainstormEngine(session_id="test_brainstorm")
    
    # Start brainstorming session
    print("\n🚀 Starting brainstorming session:")
    session_id = engine.start_brainstorming_session(
        initial_prompt="Write a story about AI",
        refinement_goal="create_compelling_narrative",
        success_criteria=["engaging", "creative", "well-structured"]
    )
    
    # Test refinement
    print("\n🔄 Testing prompt refinement:")
    refined = engine.refine_prompt(
        feedback="Make it more specific - focus on AI consciousness and include dialogue",
        refinement_type="enhancement"
    )
    print(f"Refined prompt (first 100 chars): {refined.content[:100]}...")
    
    # Test branching
    print("\n🌟 Testing conversation branching:")
    alt_branch = engine.create_conversation_branch(
        branch_type=BranchType.ALTERNATIVE,
        exploration_focus="dystopian_perspective",
        alternative_prompt="Write a dark story about AI taking over the world"
    )
    
    # Test suggestions
    print("\n💡 Testing refinement suggestions:")
    suggestions = engine.get_refinement_suggestions(refined.content)
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"{i}. {suggestion}")
    
    # Test version comparison
    print("\n📊 Testing version comparison:")
    comparison = engine.compare_versions([
        engine.refinement_history[0] if engine.refinement_history else refined.version_id
    ])
    print(f"Quality metrics: {comparison.get('quality_comparison', {})}")
    
    # Finalize session
    print("\n🎉 Finalizing session:")
    summary = engine.finalize_session()
    print(f"Session summary: {summary}")
    
    print(f"\n✅ BrainstormEngine system test completed!")


if __name__ == "__main__":
    main()