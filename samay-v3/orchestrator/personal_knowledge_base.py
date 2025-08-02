"""
Personal Knowledge Base for Samay v3 - Phase 4
Provides intelligent knowledge management, context preservation, and learning capabilities
"""

import sqlite3
import json
import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import re
from collections import defaultdict

class KnowledgeType(Enum):
    DOCUMENT = "document"
    CONVERSATION = "conversation"
    PROJECT = "project"
    CONTACT = "contact"
    INSIGHT = "insight"
    TEMPLATE = "template"
    REFERENCE = "reference"

class AccessLevel(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"

@dataclass
class KnowledgeItem:
    id: Optional[int]
    title: str
    content: str
    knowledge_type: KnowledgeType
    category: str
    tags: List[str]
    access_level: AccessLevel
    metadata: Dict[str, Any]
    relationships: List[int]  # IDs of related items
    embedding_vector: Optional[List[float]]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_accessed: datetime.datetime
    access_count: int

@dataclass
class SearchResult:
    item: KnowledgeItem
    relevance_score: float
    match_type: str  # exact, semantic, fuzzy, context
    matched_content: str

class PersonalKnowledgeBase:
    def __init__(self, db_path: str = "memory/knowledge_base.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Knowledge processing settings
        self.max_content_length = 10000
        self.similarity_threshold = 0.7
        self.relationship_score_threshold = 0.6
    
    def _init_database(self):
        """Initialize the knowledge base database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,  -- JSON array
                    access_level TEXT NOT NULL,
                    metadata TEXT,  -- JSON object
                    relationships TEXT,  -- JSON array of IDs
                    embedding_vector TEXT,  -- JSON array of floats
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_item_id INTEGER NOT NULL,
                    to_item_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL NOT NULL,  -- 0.0 to 1.0
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_item_id) REFERENCES knowledge_items (id),
                    FOREIGN KEY (to_item_id) REFERENCES knowledge_items (id)
                );
                
                CREATE TABLE IF NOT EXISTS knowledge_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    parent_category_id INTEGER,
                    color TEXT,
                    icon TEXT,
                    item_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_category_id) REFERENCES knowledge_categories (id)
                );
                
                CREATE TABLE IF NOT EXISTS knowledge_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results_count INTEGER,
                    search_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS knowledge_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    related_items TEXT,  -- JSON array of IDs
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,  -- JSON
                    frequency REAL,
                    last_occurrence TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for better search performance
                CREATE INDEX IF NOT EXISTS idx_knowledge_content ON knowledge_items(content);
                CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_items(tags);
                CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_items(category);
                CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items(knowledge_type);
                CREATE INDEX IF NOT EXISTS idx_relationships_from ON knowledge_relationships(from_item_id);
                CREATE INDEX IF NOT EXISTS idx_relationships_to ON knowledge_relationships(to_item_id);
            """)
    
    # Core Knowledge Management
    
    def add_knowledge_item(self, title: str, content: str, knowledge_type: KnowledgeType,
                          category: str = "general", tags: List[str] = None,
                          access_level: AccessLevel = AccessLevel.PRIVATE,
                          metadata: Dict[str, Any] = None) -> int:
        """Add a new knowledge item"""
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}
        
        # Auto-extract tags from content if none provided
        if not tags:
            tags = self._extract_tags_from_content(content)
        
        # Generate embedding vector (simplified - would use actual embeddings)
        embedding_vector = self._generate_embedding(content)
        
        now = datetime.datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO knowledge_items 
                (title, content, knowledge_type, category, tags, access_level,
                 metadata, relationships, embedding_vector, created_at, updated_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, content, knowledge_type.value, category, json.dumps(tags),
                  access_level.value, json.dumps(metadata), json.dumps([]),
                  json.dumps(embedding_vector), now, now, now))
            
            item_id = cursor.lastrowid
            
            # Update category count
            self._update_category_count(category, 1)
            
            # Update tag usage
            for tag in tags:
                self._update_tag_usage(tag)
            
            # Find and create relationships
            self._auto_create_relationships(item_id, content, tags)
            
            return item_id
    
    def search_knowledge(self, query: str, search_type: str = "hybrid",
                        categories: List[str] = None, tags: List[str] = None,
                        knowledge_types: List[KnowledgeType] = None,
                        limit: int = 10) -> List[SearchResult]:
        """Search the knowledge base with various search strategies"""
        
        # Log search
        self._log_search(query, search_type)
        
        results = []
        
        if search_type in ["exact", "hybrid"]:
            results.extend(self._exact_search(query, categories, tags, knowledge_types))
        
        if search_type in ["semantic", "hybrid"]:
            results.extend(self._semantic_search(query, categories, tags, knowledge_types))
        
        if search_type in ["fuzzy", "hybrid"]:
            results.extend(self._fuzzy_search(query, categories, tags, knowledge_types))
        
        if search_type in ["context", "hybrid"]:
            results.extend(self._context_search(query, categories, tags, knowledge_types))
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in results:
            item_id = result.item.id
            if item_id not in unique_results or result.relevance_score > unique_results[item_id].relevance_score:
                unique_results[item_id] = result
        
        sorted_results = sorted(unique_results.values(), 
                              key=lambda x: x.relevance_score, reverse=True)
        
        # Update access counts
        for result in sorted_results[:limit]:
            self._update_access_count(result.item.id)
        
        return sorted_results[:limit]
    
    def _exact_search(self, query: str, categories: List[str] = None,
                     tags: List[str] = None, knowledge_types: List[KnowledgeType] = None) -> List[SearchResult]:
        """Perform exact text search"""
        results = []
        
        # Build query conditions
        conditions = ["(title LIKE ? OR content LIKE ?)"]
        params = [f"%{query}%", f"%{query}%"]
        
        if categories:
            conditions.append(f"category IN ({','.join(['?' for _ in categories])})")
            params.extend(categories)
        
        if knowledge_types:
            type_values = [kt.value for kt in knowledge_types]
            conditions.append(f"knowledge_type IN ({','.join(['?' for _ in type_values])})")
            params.extend(type_values)
        
        where_clause = " AND ".join(conditions)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"""
                SELECT * FROM knowledge_items 
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN title LIKE ? THEN 1 ELSE 2 END,
                    access_count DESC
            """, params + [f"%{query}%"])
            
            for row in cursor.fetchall():
                item = self._row_to_knowledge_item(row)
                
                # Calculate relevance score
                title_match = query.lower() in item.title.lower()
                content_match = query.lower() in item.content.lower()
                
                relevance_score = 0.0
                if title_match:
                    relevance_score += 0.8
                if content_match:
                    relevance_score += 0.6
                
                # Boost based on access count
                relevance_score += min(item.access_count * 0.01, 0.2)
                
                # Find matched content snippet
                matched_content = self._extract_match_snippet(item.content, query)
                
                results.append(SearchResult(
                    item=item,
                    relevance_score=min(relevance_score, 1.0),
                    match_type="exact",
                    matched_content=matched_content
                ))
        
        return results
    
    def _semantic_search(self, query: str, categories: List[str] = None,
                        tags: List[str] = None, knowledge_types: List[KnowledgeType] = None) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        results = []
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # For this implementation, we'll use a simplified semantic search
        # In a real system, this would use actual vector similarity
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM knowledge_items")
            
            for row in cursor.fetchall():
                item = self._row_to_knowledge_item(row)
                
                # Skip if filters don't match
                if categories and item.category not in categories:
                    continue
                if knowledge_types and item.knowledge_type not in knowledge_types:
                    continue
                
                # Calculate semantic similarity (simplified)
                semantic_score = self._calculate_semantic_similarity(query, item.content)
                
                if semantic_score > 0.3:  # Threshold for semantic relevance
                    results.append(SearchResult(
                        item=item,
                        relevance_score=semantic_score,
                        match_type="semantic",
                        matched_content=self._extract_match_snippet(item.content, query)
                    ))
        
        return results
    
    def _fuzzy_search(self, query: str, categories: List[str] = None,
                     tags: List[str] = None, knowledge_types: List[KnowledgeType] = None) -> List[SearchResult]:
        """Perform fuzzy search for typos and variations"""
        results = []
        
        # Simple fuzzy search using LIKE with wildcards
        query_words = query.split()
        fuzzy_patterns = []
        
        for word in query_words:
            if len(word) > 3:  # Only fuzzy search longer words
                # Add patterns for common typos
                fuzzy_patterns.append(f"%{word}%")
                if len(word) > 4:
                    # Allow one character difference
                    for i in range(len(word)):
                        pattern = word[:i] + "_" + word[i+1:]
                        fuzzy_patterns.append(f"%{pattern}%")
        
        if not fuzzy_patterns:
            return results
        
        with sqlite3.connect(self.db_path) as conn:
            for pattern in fuzzy_patterns[:5]:  # Limit patterns to avoid too many results
                cursor = conn.execute("""
                    SELECT * FROM knowledge_items 
                    WHERE content LIKE ?
                    LIMIT 10
                """, (pattern,))
                
                for row in cursor.fetchall():
                    item = self._row_to_knowledge_item(row)
                    
                    # Skip if filters don't match
                    if categories and item.category not in categories:
                        continue
                    if knowledge_types and item.knowledge_type not in knowledge_types:
                        continue
                    
                    # Calculate fuzzy relevance
                    fuzzy_score = self._calculate_fuzzy_similarity(query, item.content)
                    
                    if fuzzy_score > 0.4:
                        results.append(SearchResult(
                            item=item,
                            relevance_score=fuzzy_score,
                            match_type="fuzzy",
                            matched_content=self._extract_match_snippet(item.content, query)
                        ))
        
        return results
    
    def _context_search(self, query: str, categories: List[str] = None,
                       tags: List[str] = None, knowledge_types: List[KnowledgeType] = None) -> List[SearchResult]:
        """Perform context-aware search using relationships"""
        results = []
        
        # First find directly relevant items
        direct_results = self._exact_search(query, categories, tags, knowledge_types)
        
        # Then find related items
        for result in direct_results[:3]:  # Look at top 3 direct results
            related_items = self._get_related_items(result.item.id)
            
            for related_item in related_items:
                # Check if related item is contextually relevant
                context_score = self._calculate_context_relevance(query, related_item.content)
                
                if context_score > 0.3:
                    results.append(SearchResult(
                        item=related_item,
                        relevance_score=context_score * 0.8,  # Reduce score for indirect match
                        match_type="context",
                        matched_content=self._extract_match_snippet(related_item.content, query)
                    ))
        
        return results
    
    # Relationship Management
    
    def create_relationship(self, from_item_id: int, to_item_id: int,
                          relationship_type: str, strength: float = 0.5,
                          context: str = "") -> int:
        """Create a relationship between knowledge items"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO knowledge_relationships 
                (from_item_id, to_item_id, relationship_type, strength, context)
                VALUES (?, ?, ?, ?, ?)
            """, (from_item_id, to_item_id, relationship_type, strength, context))
            
            relationship_id = cursor.lastrowid
            
            # Update relationship lists in both items
            self._update_item_relationships(from_item_id, to_item_id)
            self._update_item_relationships(to_item_id, from_item_id)
            
            return relationship_id
    
    def _auto_create_relationships(self, item_id: int, content: str, tags: List[str]):
        """Automatically create relationships based on content similarity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, content, tags FROM knowledge_items 
                WHERE id != ?
            """, (item_id,))
            
            for row in cursor.fetchall():
                other_id, other_title, other_content, other_tags_json = row
                other_tags = json.loads(other_tags_json) if other_tags_json else []
                
                # Calculate relationship strength
                strength = self._calculate_relationship_strength(
                    content, tags, other_content, other_tags
                )
                
                if strength > self.relationship_score_threshold:
                    self.create_relationship(
                        item_id, other_id, "related", strength,
                        f"Auto-created based on content similarity ({strength:.2f})"
                    )
    
    def _calculate_relationship_strength(self, content1: str, tags1: List[str],
                                       content2: str, tags2: List[str]) -> float:
        """Calculate strength of relationship between two items"""
        strength = 0.0
        
        # Tag overlap
        common_tags = set(tags1) & set(tags2)
        if tags1 and tags2:
            tag_overlap = len(common_tags) / max(len(set(tags1) | set(tags2)), 1)
            strength += tag_overlap * 0.4
        
        # Content similarity (simplified)
        content_similarity = self._calculate_semantic_similarity(content1, content2)
        strength += content_similarity * 0.6
        
        return min(strength, 1.0)
    
    def _get_related_items(self, item_id: int) -> List[KnowledgeItem]:
        """Get items related to the given item"""
        related_items = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT ki.* FROM knowledge_items ki
                JOIN knowledge_relationships kr ON 
                    (kr.from_item_id = ? AND kr.to_item_id = ki.id) OR
                    (kr.to_item_id = ? AND kr.from_item_id = ki.id)
                WHERE kr.strength > ?
                ORDER BY kr.strength DESC
                LIMIT 10
            """, (item_id, item_id, self.relationship_score_threshold))
            
            for row in cursor.fetchall():
                related_items.append(self._row_to_knowledge_item(row))
        
        return related_items
    
    # Knowledge Analytics and Insights
    
    def generate_knowledge_insights(self) -> List[Dict[str, Any]]:
        """Generate insights about the knowledge base"""
        insights = []
        
        # Most accessed items
        popular_items = self._get_popular_items()
        if popular_items:
            insights.append({
                "type": "popular_content",
                "title": "Most Accessed Knowledge",
                "description": f"Your most referenced items are in {popular_items[0]['category']} category",
                "data": popular_items[:5]
            })
        
        # Knowledge gaps
        gaps = self._identify_knowledge_gaps()
        if gaps:
            insights.append({
                "type": "knowledge_gaps",
                "title": "Potential Knowledge Gaps",
                "description": "Areas where you might want to add more information",
                "data": gaps
            })
        
        # Relationship patterns
        patterns = self._analyze_relationship_patterns()
        if patterns:
            insights.append({
                "type": "relationship_patterns",
                "title": "Knowledge Connections",
                "description": "How your knowledge items are interconnected",
                "data": patterns
            })
        
        # Category distribution
        distribution = self._get_category_distribution()
        insights.append({
            "type": "category_distribution",
            "title": "Knowledge Distribution",
            "description": "How your knowledge is organized across categories",
            "data": distribution
        })
        
        return insights
    
    def _get_popular_items(self) -> List[Dict[str, Any]]:
        """Get most popular knowledge items"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT title, category, access_count, knowledge_type
                FROM knowledge_items 
                WHERE access_count > 0
                ORDER BY access_count DESC
                LIMIT 10
            """)
            
            return [
                {
                    "title": row[0],
                    "category": row[1],
                    "access_count": row[2],
                    "type": row[3]
                } for row in cursor.fetchall()
            ]
    
    def _identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Identify potential gaps in knowledge"""
        gaps = []
        
        with sqlite3.connect(self.db_path) as conn:
            # Find categories with few items
            cursor = conn.execute("""
                SELECT category, COUNT(*) as item_count
                FROM knowledge_items 
                GROUP BY category
                HAVING item_count < 3
                ORDER BY item_count ASC
            """)
            
            for row in cursor.fetchall():
                gaps.append({
                    "type": "sparse_category",
                    "category": row[0],
                    "item_count": row[1],
                    "suggestion": f"Consider adding more items to {row[0]} category"
                })
        
        return gaps
    
    def _analyze_relationship_patterns(self) -> Dict[str, Any]:
        """Analyze relationship patterns in the knowledge base"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT relationship_type, COUNT(*) as count, AVG(strength) as avg_strength
                FROM knowledge_relationships 
                GROUP BY relationship_type
                ORDER BY count DESC
            """)
            
            patterns = {}
            for row in cursor.fetchall():
                patterns[row[0]] = {
                    "count": row[1],
                    "average_strength": round(row[2], 2)
                }
        
        return patterns
    
    def _get_category_distribution(self) -> Dict[str, int]:
        """Get distribution of items across categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM knowledge_items 
                GROUP BY category
                ORDER BY count DESC
            """)
            
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    # Helper Methods
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract potential tags from content"""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Z][a-z]+\b', content)  # Capitalized words
        technical_terms = re.findall(r'\b[a-z]+_[a-z]+\b', content)  # Snake_case terms
        
        tags = list(set(words + technical_terms))
        return tags[:10]  # Limit to 10 tags
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text (simplified implementation)"""
        # In a real implementation, this would use actual embedding models
        # For now, create a simple hash-based vector
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert to float vector
        vector = []
        for i in range(0, len(hash_hex), 2):
            vector.append(int(hash_hex[i:i+2], 16) / 255.0)
        
        return vector[:50]  # 50-dimensional vector
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Simplified implementation using word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Boost for longer common phrases
        common_phrases = 0
        for word in intersection:
            if len(word) > 5:  # Longer words are more meaningful
                common_phrases += 1
        
        phrase_boost = min(common_phrases * 0.1, 0.3)
        
        return min(jaccard_similarity + phrase_boost, 1.0)
    
    def _calculate_fuzzy_similarity(self, query: str, content: str) -> float:
        """Calculate fuzzy similarity for typo tolerance"""
        query_words = query.lower().split()
        content_words = content.lower().split()
        
        matches = 0
        for q_word in query_words:
            for c_word in content_words:
                if self._fuzzy_match(q_word, c_word):
                    matches += 1
                    break
        
        return matches / max(len(query_words), 1)
    
    def _fuzzy_match(self, word1: str, word2: str) -> bool:
        """Check if two words match with fuzzy logic"""
        if word1 == word2:
            return True
        
        if abs(len(word1) - len(word2)) > 2:
            return False
        
        # Simple edit distance check
        if len(word1) > 3 and len(word2) > 3:
            # Allow one character difference for longer words
            differences = sum(c1 != c2 for c1, c2 in zip(word1, word2))
            return differences <= 1
        
        return False
    
    def _calculate_context_relevance(self, query: str, content: str) -> float:
        """Calculate contextual relevance"""
        # Simplified context calculation
        query_concepts = self._extract_concepts(query)
        content_concepts = self._extract_concepts(content)
        
        if not query_concepts or not content_concepts:
            return 0.0
        
        concept_overlap = len(set(query_concepts) & set(content_concepts))
        return concept_overlap / max(len(query_concepts), 1)
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple concept extraction
        words = text.lower().split()
        # Filter out common words and keep meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        concepts = [word for word in words if len(word) > 3 and word not in stop_words]
        return concepts[:10]
    
    def _extract_match_snippet(self, content: str, query: str, snippet_length: int = 150) -> str:
        """Extract a snippet showing the match context"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Find the first occurrence of any query word
        match_pos = -1
        for word in query.split():
            pos = content_lower.find(word.lower())
            if pos != -1:
                match_pos = pos
                break
        
        if match_pos == -1:
            return content[:snippet_length] + "..." if len(content) > snippet_length else content
        
        # Extract snippet around the match
        start = max(0, match_pos - snippet_length // 2)
        end = min(len(content), start + snippet_length)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _update_category_count(self, category: str, delta: int):
        """Update item count for a category"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO knowledge_categories (name, item_count)
                VALUES (?, 0)
            """, (category,))
            
            conn.execute("""
                UPDATE knowledge_categories 
                SET item_count = item_count + ?
                WHERE name = ?
            """, (delta, category))
    
    def _update_tag_usage(self, tag: str):
        """Update usage count for a tag"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO knowledge_tags (name, usage_count)
                VALUES (?, 0)
            """, (tag,))
            
            conn.execute("""
                UPDATE knowledge_tags 
                SET usage_count = usage_count + 1
                WHERE name = ?
            """, (tag,))
    
    def _update_access_count(self, item_id: int):
        """Update access count for an item"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE knowledge_items 
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ?
            """, (datetime.datetime.now(), item_id))
    
    def _update_item_relationships(self, item_id: int, related_id: int):
        """Update the relationships list for an item"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT relationships FROM knowledge_items WHERE id = ?
            """, (item_id,))
            
            result = cursor.fetchone()
            if result:
                relationships = json.loads(result[0]) if result[0] else []
                if related_id not in relationships:
                    relationships.append(related_id)
                    
                    conn.execute("""
                        UPDATE knowledge_items 
                        SET relationships = ?, updated_at = ?
                        WHERE id = ?
                    """, (json.dumps(relationships), datetime.datetime.now(), item_id))
    
    def _log_search(self, query: str, search_type: str):
        """Log search for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO search_history (query, search_type)
                VALUES (?, ?)
            """, (query, search_type))
    
    def _row_to_knowledge_item(self, row) -> KnowledgeItem:
        """Convert database row to KnowledgeItem object"""
        return KnowledgeItem(
            id=row[0],
            title=row[1],
            content=row[2],
            knowledge_type=KnowledgeType(row[3]),
            category=row[4] or "general",
            tags=json.loads(row[5]) if row[5] else [],
            access_level=AccessLevel(row[6]),
            metadata=json.loads(row[7]) if row[7] else {},
            relationships=json.loads(row[8]) if row[8] else [],
            embedding_vector=json.loads(row[9]) if row[9] else None,
            created_at=datetime.datetime.fromisoformat(row[10]),
            updated_at=datetime.datetime.fromisoformat(row[11]),
            last_accessed=datetime.datetime.fromisoformat(row[12]),
            access_count=row[13]
        )
    
    def get_knowledge_analytics(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base analytics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total items
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_items")
            total_items = cursor.fetchone()[0]
            
            # Items by type
            cursor = conn.execute("""
                SELECT knowledge_type, COUNT(*) FROM knowledge_items 
                GROUP BY knowledge_type
            """)
            items_by_type = dict(cursor.fetchall())
            
            # Recent activity
            cursor = conn.execute("""
                SELECT COUNT(*) FROM knowledge_items 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_additions = cursor.fetchone()[0]
            
            # Most used tags
            cursor = conn.execute("""
                SELECT name, usage_count FROM knowledge_tags 
                ORDER BY usage_count DESC LIMIT 10
            """)
            popular_tags = dict(cursor.fetchall())
            
            # Search activity
            cursor = conn.execute("""
                SELECT COUNT(*) FROM search_history 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            recent_searches = cursor.fetchone()[0]
            
            return {
                "total_items": total_items,
                "items_by_type": items_by_type,
                "recent_additions": recent_additions,
                "popular_tags": popular_tags,
                "recent_searches": recent_searches,
                "categories": self._get_category_distribution(),
                "insights": self.generate_knowledge_insights()
            }

# Example usage and testing
if __name__ == "__main__":
    kb = PersonalKnowledgeBase()
    
    # Add some sample knowledge items
    doc_id = kb.add_knowledge_item(
        title="Samay v3 Architecture",
        content="Samay v3 is a multi-agent AI orchestration platform with companion features, iterative refinement, and web service integration.",
        knowledge_type=KnowledgeType.DOCUMENT,
        category="projects",
        tags=["samay", "ai", "architecture", "companion"]
    )
    
    insight_id = kb.add_knowledge_item(
        title="AI Companion Design Principles",
        content="Key principles for AI companion design include persistent memory, adaptive personality, proactive assistance, and contextual understanding.",
        knowledge_type=KnowledgeType.INSIGHT,
        category="ai_design",
        tags=["ai", "companion", "design", "principles"]
    )
    
    # Search for knowledge
    results = kb.search_knowledge("AI companion", search_type="hybrid")
    print("Search results:")
    for result in results:
        print(f"- {result.item.title} (score: {result.relevance_score:.2f})")
        print(f"  {result.matched_content[:100]}...")
    
    # Get analytics
    analytics = kb.get_knowledge_analytics()
    print(f"\nKnowledge Base Analytics:")
    print(f"Total items: {analytics['total_items']}")
    print(f"Recent additions: {analytics['recent_additions']}")
    print(f"Categories: {analytics['categories']}")
    
    print("Personal Knowledge Base ready!")