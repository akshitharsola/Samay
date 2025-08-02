#!/usr/bin/env python3
"""Debug knowledge base initialization"""

import sys
import sqlite3
sys.path.append('orchestrator')

def debug_kb():
    try:
        print("1. Testing direct SQLite connection...")
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        print("✅ Direct SQLite works")
        conn.close()
        
        print("2. Testing knowledge base import...")
        from personal_knowledge_base import PersonalKnowledgeBase
        print("✅ Import successful")
        
        print("3. Testing knowledge base initialization...")
        kb = PersonalKnowledgeBase(":memory:")
        print("✅ Knowledge base created")
        
        print("4. Testing direct database query...")
        with sqlite3.connect(kb.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Tables found: {[t[0] for t in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_kb()