#!/usr/bin/env python3
"""
Simple Knowledge Base Test
==========================
"""

import sys
sys.path.append('orchestrator')

def test_kb():
    try:
        from personal_knowledge_base import PersonalKnowledgeBase, KnowledgeType
        
        # Use in-memory database to avoid file locking
        kb = PersonalKnowledgeBase(":memory:")
        # Ensure database is initialized
        kb._init_database()
        
        # Add knowledge item
        item_id = kb.add_knowledge_item(
            title="Test Knowledge",
            content="This is a test knowledge item",
            knowledge_type=KnowledgeType.DOCUMENT,
            category="testing"
        )
        
        print(f"✅ Added knowledge item: {item_id}")
        
        # Search
        results = kb.search_knowledge("test")
        print(f"✅ Search found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ KB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Knowledge Base...")
    success = test_kb()
    print("✅ Success!" if success else "❌ Failed")