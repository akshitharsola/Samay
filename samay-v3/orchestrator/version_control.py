#!/usr/bin/env python3
"""
Samay v3 - Version Control System
=================================
Phase 2: Prompt evolution tracking and branching management
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum
import hashlib

from brainstorm_engine import PromptVersion, ConversationBranch, RefinementStage, BranchType


class ChangeType(Enum):
    CREATE = "create"
    MODIFY = "modify"
    BRANCH = "branch"
    MERGE = "merge"
    REVERT = "revert"


class MergeStrategy(Enum):
    BEST_QUALITY = "best_quality"
    HYBRID = "hybrid"
    MANUAL = "manual"
    LATEST = "latest"


@dataclass
class VersionChange:
    """Represents a change between versions"""
    change_id: str
    from_version: str
    to_version: str
    change_type: ChangeType
    change_summary: str
    diff_data: Dict[str, Any]
    timestamp: str


@dataclass
class MergeOperation:
    """Represents a merge between branches"""
    merge_id: str
    source_branch: str
    target_branch: str
    merge_strategy: MergeStrategy
    merged_version_id: str
    conflict_resolution: Dict[str, Any]
    merge_quality_score: float
    timestamp: str


class VersionControl:
    """Advanced version control for prompt evolution"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "version_control.db"
        self.session_id = session_id
        
        # Version tracking state
        self.version_tree = {}
        self.branch_heads = {}
        self.merge_history = []
        
        self.init_database()
        print(f"🔄 VersionControl initialized for session {session_id}")
    
    def init_database(self):
        """Initialize version control database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Version changes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_changes (
                change_id TEXT PRIMARY KEY,
                session_id TEXT,
                from_version TEXT,
                to_version TEXT,
                change_type TEXT,
                change_summary TEXT,
                diff_data TEXT,
                timestamp TEXT
            )
        ''')
        
        # Merge operations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS merge_operations (
                merge_id TEXT PRIMARY KEY,
                session_id TEXT,
                source_branch TEXT,
                target_branch TEXT,
                merge_strategy TEXT,
                merged_version_id TEXT,
                conflict_resolution TEXT,
                merge_quality_score REAL,
                timestamp TEXT
            )
        ''')
        
        # Version lineage table (for tracking ancestry)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_lineage (
                version_id TEXT,
                parent_version TEXT,
                branch_id TEXT,
                generation INTEGER,
                lineage_path TEXT,
                timestamp TEXT,
                PRIMARY KEY (version_id, parent_version)
            )
        ''')
        
        # Branch metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branch_metadata (
                branch_id TEXT PRIMARY KEY,
                session_id TEXT,
                branch_name TEXT,
                description TEXT,
                created_from TEXT,
                head_version TEXT,
                is_active BOOLEAN,
                quality_trend TEXT,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_version_change(
        self, 
        from_version: str, 
        to_version: str, 
        change_type: ChangeType,
        change_summary: str = ""
    ) -> str:
        """Track a change between versions"""
        
        # Calculate diff between versions
        diff_data = self._calculate_version_diff(from_version, to_version)
        
        change = VersionChange(
            change_id=str(uuid.uuid4()),
            from_version=from_version,
            to_version=to_version,
            change_type=change_type,
            change_summary=change_summary or self._generate_change_summary(diff_data),
            diff_data=diff_data,
            timestamp=datetime.now().isoformat()
        )
        
        # Store change
        self._store_version_change(change)
        
        print(f"📝 Tracked {change_type.value} change: {change.change_summary}")
        return change.change_id
    
    def create_branch_snapshot(self, branch_id: str, branch_name: str, description: str = "") -> bool:
        """Create a snapshot of a branch state"""
        
        # Get branch information from brainstorming database
        branch_info = self._get_branch_info(branch_id)
        if not branch_info:
            return False
        
        # Store branch metadata
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO branch_metadata 
            (branch_id, session_id, branch_name, description, created_from, head_version, is_active, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            branch_id,
            self.session_id,
            branch_name,
            description,
            branch_info.get("parent_branch"),
            branch_info.get("head_version"),
            True,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        # Update branch tracking
        self.branch_heads[branch_id] = branch_info.get("head_version")
        
        print(f"📸 Created branch snapshot: {branch_name}")
        return True
    
    def get_version_history(self, version_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """Get the history of a version"""
        
        history = []
        current_version = version_id
        depth = 0
        
        while current_version and depth < max_depth:
            # Get version info
            version_info = self._get_version_info(current_version)
            if not version_info:
                break
            
            # Get changes for this version
            changes = self._get_changes_to_version(current_version)
            
            history.append({
                "version_id": current_version,
                "stage": version_info.get("stage", "unknown"),
                "quality_score": version_info.get("quality_score", 0),
                "created_at": version_info.get("created_at", ""),
                "changes": changes,
                "parent_version": version_info.get("parent_version")
            })
            
            current_version = version_info.get("parent_version")
            depth += 1
        
        return history
    
    def compare_branches(self, branch_id1: str, branch_id2: str) -> Dict[str, Any]:
        """Compare two branches comprehensively"""
        
        branch1_info = self._get_branch_info(branch_id1)
        branch2_info = self._get_branch_info(branch_id2)
        
        if not branch1_info or not branch2_info:
            return {"error": "One or both branches not found"}
        
        # Get head versions
        head1 = branch1_info.get("head_version")
        head2 = branch2_info.get("head_version")
        
        # Compare versions
        version_diff = self._calculate_version_diff(head1, head2) if head1 and head2 else {}
        
        # Quality comparison
        quality1 = self._get_version_quality(head1) if head1 else 0
        quality2 = self._get_version_quality(head2) if head2 else 0
        
        # Lineage analysis
        common_ancestor = self._find_common_ancestor(head1, head2)
        
        comparison = {
            "branch_1": {
                "id": branch_id1,
                "head_version": head1,
                "quality_score": quality1,
                "version_count": len(branch1_info.get("prompt_versions", []))
            },
            "branch_2": {
                "id": branch_id2,
                "head_version": head2,
                "quality_score": quality2,
                "version_count": len(branch2_info.get("prompt_versions", []))
            },
            "comparison": {
                "quality_difference": quality2 - quality1,
                "better_branch": branch_id2 if quality2 > quality1 else branch_id1,
                "common_ancestor": common_ancestor,
                "content_similarity": version_diff.get("similarity_score", 0)
            },
            "differences": version_diff,
            "merge_feasibility": self._assess_merge_feasibility(branch_id1, branch_id2)
        }
        
        return comparison
    
    def merge_branches(
        self, 
        source_branch: str, 
        target_branch: str, 
        strategy: MergeStrategy = MergeStrategy.BEST_QUALITY
    ) -> Optional[str]:
        """Merge two branches using specified strategy"""
        
        # Get branch information
        source_info = self._get_branch_info(source_branch)
        target_info = self._get_branch_info(target_branch)
        
        if not source_info or not target_info:
            print("❌ Cannot merge: branch information not found")
            return None
        
        # Get head versions
        source_head = source_info.get("head_version")
        target_head = target_info.get("head_version")
        
        if not source_head or not target_head:
            print("❌ Cannot merge: missing head versions")
            return None
        
        # Execute merge strategy
        merged_content, conflict_resolution = self._execute_merge_strategy(
            source_head, target_head, strategy
        )
        
        if not merged_content:
            print("❌ Merge failed: could not resolve content")
            return None
        
        # Create merged version
        merged_version_id = str(uuid.uuid4())
        merged_version = {
            "version_id": merged_version_id,
            "content": merged_content,
            "stage": "merged",
            "quality_score": self._assess_merged_quality(source_head, target_head, merged_content),
            "metadata": {
                "merge_type": strategy.value,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "parent_versions": [source_head, target_head]
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Store merged version (would need to interface with brainstorm_engine)
        merge_quality = merged_version["quality_score"]
        
        # Record merge operation
        merge_op = MergeOperation(
            merge_id=str(uuid.uuid4()),
            source_branch=source_branch,
            target_branch=target_branch,
            merge_strategy=strategy,
            merged_version_id=merged_version_id,
            conflict_resolution=conflict_resolution,
            merge_quality_score=merge_quality,
            timestamp=datetime.now().isoformat()
        )
        
        self._store_merge_operation(merge_op)
        self.merge_history.append(merge_op)
        
        print(f"✅ Successfully merged branches")
        print(f"🔗 Merged version ID: {merged_version_id}")
        print(f"📊 Merge quality: {merge_quality:.2f}")
        
        return merged_version_id
    
    def revert_to_version(self, target_version_id: str, branch_id: str) -> bool:
        """Revert a branch to a previous version"""
        
        # Verify version exists in branch lineage
        if not self._version_in_branch_lineage(target_version_id, branch_id):
            print("❌ Cannot revert: version not in branch lineage")
            return False
        
        # Get current head
        branch_info = self._get_branch_info(branch_id)
        current_head = branch_info.get("head_version") if branch_info else None
        
        if not current_head:
            print("❌ Cannot revert: no current head version")
            return False
        
        # Create revert change record
        revert_change_id = self.track_version_change(
            current_head,
            target_version_id,
            ChangeType.REVERT,
            f"Reverted to version {target_version_id[:8]}"
        )
        
        # Update branch head (would need to interface with brainstorm_engine)
        self.branch_heads[branch_id] = target_version_id
        
        print(f"↩️ Reverted branch to version {target_version_id[:8]}")
        return True
    
    def get_quality_evolution(self, branch_id: str) -> Dict[str, Any]:
        """Analyze quality evolution over time in a branch"""
        
        branch_info = self._get_branch_info(branch_id)
        if not branch_info:
            return {"error": "Branch not found"}
        
        versions = branch_info.get("prompt_versions", [])
        quality_data = []
        
        for version_id in versions:
            version_info = self._get_version_info(version_id)
            if version_info:
                quality_data.append({
                    "version_id": version_id,
                    "quality_score": version_info.get("quality_score", 0),
                    "timestamp": version_info.get("created_at", ""),
                    "stage": version_info.get("stage", "unknown")
                })
        
        # Calculate trends
        if len(quality_data) >= 2:
            scores = [item["quality_score"] for item in quality_data]
            trend = "improving" if scores[-1] > scores[0] else "declining"
            improvement = scores[-1] - scores[0]
        else:
            trend = "insufficient_data"
            improvement = 0
        
        return {
            "branch_id": branch_id,
            "quality_data": quality_data,
            "trend": trend,
            "total_improvement": improvement,
            "peak_quality": max(item["quality_score"] for item in quality_data) if quality_data else 0,
            "version_count": len(quality_data)
        }
    
    def export_branch_history(self, branch_id: str, format: str = "json") -> str:
        """Export complete branch history"""
        
        branch_info = self._get_branch_info(branch_id)
        if not branch_info:
            return ""
        
        # Gather complete history
        history_data = {
            "branch_id": branch_id,
            "export_timestamp": datetime.now().isoformat(),
            "versions": [],
            "changes": [],
            "merges": []
        }
        
        # Get all versions in branch
        for version_id in branch_info.get("prompt_versions", []):
            version_info = self._get_version_info(version_id)
            if version_info:
                history_data["versions"].append(version_info)
        
        # Get all changes
        changes = self._get_branch_changes(branch_id)
        history_data["changes"] = changes
        
        # Get merge operations
        merges = self._get_branch_merges(branch_id)
        history_data["merges"] = merges
        
        if format == "json":
            return json.dumps(history_data, indent=2)
        elif format == "markdown":
            return self._format_history_as_markdown(history_data)
        
        return str(history_data)
    
    # Private helper methods
    def _calculate_version_diff(self, version1_id: str, version2_id: str) -> Dict[str, Any]:
        """Calculate detailed diff between two versions"""
        
        v1_info = self._get_version_info(version1_id)
        v2_info = self._get_version_info(version2_id)
        
        if not v1_info or not v2_info:
            return {"error": "Version not found"}
        
        content1 = v1_info.get("content", "")
        content2 = v2_info.get("content", "")
        
        # Simple diff metrics
        diff_data = {
            "content_length_change": len(content2) - len(content1),
            "word_count_change": len(content2.split()) - len(content1.split()),
            "quality_score_change": v2_info.get("quality_score", 0) - v1_info.get("quality_score", 0),
            "similarity_score": self._calculate_similarity(content1, content2),
            "stage_change": {
                "from": v1_info.get("stage", "unknown"),
                "to": v2_info.get("stage", "unknown")
            }
        }
        
        return diff_data
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_change_summary(self, diff_data: Dict[str, Any]) -> str:
        """Generate human-readable change summary"""
        
        if diff_data.get("error"):
            return "Change summary unavailable"
        
        summary_parts = []
        
        # Length changes
        length_change = diff_data.get("content_length_change", 0)
        if length_change > 50:
            summary_parts.append("expanded content")
        elif length_change < -50:
            summary_parts.append("condensed content")
        
        # Quality changes
        quality_change = diff_data.get("quality_score_change", 0)
        if quality_change > 0.1:
            summary_parts.append("improved quality")
        elif quality_change < -0.1:
            summary_parts.append("decreased quality")
        
        # Stage changes
        stage_change = diff_data.get("stage_change", {})
        if stage_change.get("from") != stage_change.get("to"):
            summary_parts.append(f"stage: {stage_change.get('from')} → {stage_change.get('to')}")
        
        return ", ".join(summary_parts) if summary_parts else "minor changes"
    
    def _get_branch_info(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """Get branch information from brainstorming database"""
        
        # This would interface with the brainstorm_engine database
        brainstorm_db = self.memory_dir / "brainstorming.db"
        if not brainstorm_db.exists():
            return None
        
        conn = sqlite3.connect(brainstorm_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT branch_type, parent_branch, prompt_versions, quality_metrics, exploration_focus
            FROM conversation_branches WHERE branch_id = ?
        ''', (branch_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            prompt_versions = json.loads(row[2]) if row[2] else []
            return {
                "branch_type": row[0],
                "parent_branch": row[1],
                "prompt_versions": prompt_versions,
                "head_version": prompt_versions[-1] if prompt_versions else None,
                "quality_metrics": json.loads(row[3]) if row[3] else {},
                "exploration_focus": row[4]
            }
        
        return None
    
    def _get_version_info(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get version information from brainstorming database"""
        
        brainstorm_db = self.memory_dir / "brainstorming.db"
        if not brainstorm_db.exists():
            return None
        
        conn = sqlite3.connect(brainstorm_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content, stage, quality_score, metadata, parent_version, created_at
            FROM prompt_versions WHERE version_id = ?
        ''', (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "content": row[0],
                "stage": row[1],
                "quality_score": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "parent_version": row[4],
                "created_at": row[5]
            }
        
        return None
    
    def _store_version_change(self, change: VersionChange):
        """Store version change in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO version_changes 
            (change_id, session_id, from_version, to_version, change_type, change_summary, diff_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            change.change_id,
            self.session_id,
            change.from_version,
            change.to_version,
            change.change_type.value,
            change.change_summary,
            json.dumps(change.diff_data),
            change.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _store_merge_operation(self, merge_op: MergeOperation):
        """Store merge operation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO merge_operations 
            (merge_id, session_id, source_branch, target_branch, merge_strategy, merged_version_id, conflict_resolution, merge_quality_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            merge_op.merge_id,
            self.session_id,
            merge_op.source_branch,
            merge_op.target_branch,
            merge_op.merge_strategy.value,
            merge_op.merged_version_id,
            json.dumps(merge_op.conflict_resolution),
            merge_op.merge_quality_score,
            merge_op.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _execute_merge_strategy(self, source_version: str, target_version: str, strategy: MergeStrategy) -> Tuple[Optional[str], Dict]:
        """Execute merge strategy between two versions"""
        
        source_info = self._get_version_info(source_version)
        target_info = self._get_version_info(target_version)
        
        if not source_info or not target_info:
            return None, {"error": "Version info not found"}
        
        source_content = source_info.get("content", "")
        target_content = target_info.get("content", "")
        source_quality = source_info.get("quality_score", 0)
        target_quality = target_info.get("quality_score", 0)
        
        conflict_resolution = {}
        
        if strategy == MergeStrategy.BEST_QUALITY:
            if source_quality > target_quality:
                merged_content = source_content
                conflict_resolution["chosen"] = "source"
                conflict_resolution["reason"] = f"Higher quality score ({source_quality:.2f} vs {target_quality:.2f})"
            else:
                merged_content = target_content
                conflict_resolution["chosen"] = "target"
                conflict_resolution["reason"] = f"Higher quality score ({target_quality:.2f} vs {source_quality:.2f})"
        
        elif strategy == MergeStrategy.LATEST:
            # Choose based on timestamp (target is usually newer in merge context)
            merged_content = target_content
            conflict_resolution["chosen"] = "target"
            conflict_resolution["reason"] = "Latest version selected"
        
        elif strategy == MergeStrategy.HYBRID:
            # Simple hybrid: combine both (this could be enhanced with LLM)
            merged_content = f"{source_content}\n\n---\n\n{target_content}"
            conflict_resolution["chosen"] = "hybrid"
            conflict_resolution["reason"] = "Combined both versions"
        
        else:  # MANUAL - would require user input
            merged_content = target_content  # Default fallback
            conflict_resolution["chosen"] = "manual_fallback"
            conflict_resolution["reason"] = "Manual resolution required but defaulted to target"
        
        return merged_content, conflict_resolution
    
    def _assess_merge_feasibility(self, branch1: str, branch2: str) -> Dict[str, Any]:
        """Assess how feasible a merge would be"""
        
        branch1_info = self._get_branch_info(branch1)
        branch2_info = self._get_branch_info(branch2)
        
        if not branch1_info or not branch2_info:
            return {"feasible": False, "reason": "Branch info not available"}
        
        # Get head versions for comparison
        head1 = branch1_info.get("head_version")
        head2 = branch2_info.get("head_version")
        
        if not head1 or not head2:
            return {"feasible": False, "reason": "Missing head versions"}
        
        # Calculate similarity
        diff = self._calculate_version_diff(head1, head2)
        similarity = diff.get("similarity_score", 0)
        
        # Assess feasibility
        if similarity > 0.7:
            feasibility = "high"
            reason = "High content similarity"
        elif similarity > 0.4:
            feasibility = "medium"
            reason = "Moderate content similarity"
        else:
            feasibility = "low"
            reason = "Low content similarity - may require manual resolution"
        
        return {
            "feasible": True,
            "feasibility_level": feasibility,
            "reason": reason,
            "similarity_score": similarity,
            "recommended_strategy": MergeStrategy.BEST_QUALITY.value
        }
    
    def _find_common_ancestor(self, version1: str, version2: str) -> Optional[str]:
        """Find common ancestor of two versions"""
        
        # Get lineage for both versions
        lineage1 = self._get_version_lineage(version1)
        lineage2 = self._get_version_lineage(version2)
        
        # Find intersection
        common_versions = set(lineage1).intersection(set(lineage2))
        
        if common_versions:
            # Return the most recent common ancestor
            return min(common_versions, key=lambda v: lineage1.index(v) if v in lineage1 else float('inf'))
        
        return None
    
    def _get_version_lineage(self, version_id: str) -> List[str]:
        """Get complete lineage of a version"""
        
        lineage = []
        current = version_id
        
        while current:
            lineage.append(current)
            version_info = self._get_version_info(current)
            current = version_info.get("parent_version") if version_info else None
        
        return lineage
    
    def _get_version_quality(self, version_id: str) -> float:
        """Get quality score for a version"""
        version_info = self._get_version_info(version_id)
        return version_info.get("quality_score", 0) if version_info else 0
    
    def _assess_merged_quality(self, source_version: str, target_version: str, merged_content: str) -> float:
        """Assess quality of merged content"""
        
        # Simple heuristic - could be enhanced with LLM evaluation
        source_quality = self._get_version_quality(source_version)
        target_quality = self._get_version_quality(target_version)
        
        # Base quality is average of parents
        base_quality = (source_quality + target_quality) / 2
        
        # Adjust based on content length (longer might be more comprehensive)
        length_bonus = min(len(merged_content) / 1000, 0.1)  # Up to 0.1 bonus
        
        return min(base_quality + length_bonus, 1.0)
    
    def _version_in_branch_lineage(self, version_id: str, branch_id: str) -> bool:
        """Check if version exists in branch lineage"""
        branch_info = self._get_branch_info(branch_id)
        if not branch_info:
            return False
        
        return version_id in branch_info.get("prompt_versions", [])
    
    def _get_changes_to_version(self, version_id: str) -> List[Dict[str, Any]]:
        """Get changes that led to a version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT change_type, change_summary, timestamp
            FROM version_changes WHERE to_version = ?
        ''', (version_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{"type": row[0], "summary": row[1], "timestamp": row[2]} for row in rows]
    
    def _get_branch_changes(self, branch_id: str) -> List[Dict[str, Any]]:
        """Get all changes in a branch"""
        # This would need to correlate with branch versions
        return []  # Simplified for now
    
    def _get_branch_merges(self, branch_id: str) -> List[Dict[str, Any]]:
        """Get merge operations involving a branch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT merge_id, source_branch, target_branch, merge_strategy, merge_quality_score, timestamp
            FROM merge_operations WHERE source_branch = ? OR target_branch = ?
        ''', (branch_id, branch_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "merge_id": row[0],
            "source_branch": row[1],
            "target_branch": row[2],
            "strategy": row[3],
            "quality_score": row[4],
            "timestamp": row[5]
        } for row in rows]
    
    def _format_history_as_markdown(self, history_data: Dict[str, Any]) -> str:
        """Format history data as markdown"""
        
        md_lines = [
            f"# Branch History: {history_data['branch_id']}",
            f"*Exported: {history_data['export_timestamp']}*",
            "",
            "## Versions",
            ""
        ]
        
        for version in history_data.get("versions", []):
            md_lines.extend([
                f"### Version {version.get('version_id', 'unknown')[:8]}",
                f"- **Stage**: {version.get('stage', 'unknown')}",
                f"- **Quality**: {version.get('quality_score', 0):.2f}",
                f"- **Created**: {version.get('created_at', 'unknown')}",
                f"- **Content**: {version.get('content', '')[:200]}...",
                ""
            ])
        
        return "\n".join(md_lines)


def main():
    """Test the version control system"""
    print("🔄 Testing Version Control System")
    print("=" * 50)
    
    # Initialize version control
    vc = VersionControl(session_id="test_version_control")
    
    # Test would require actual brainstorming data
    print("✅ VersionControl system initialized!")
    print("🔧 Full testing requires integration with brainstorming engine")


if __name__ == "__main__":
    main()