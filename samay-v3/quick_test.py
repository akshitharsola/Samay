#!/usr/bin/env python3
"""
Quick test of companion functionality
"""

import sys
from pathlib import Path
import traceback

# Add orchestrator to path
sys.path.append(str(Path(__file__).parent / "orchestrator"))

from companion_interface import CompanionInterface

def quick_test():
    print("🚀 Quick Companion Test")
    print("=" * 30)
    
    try:
        # Initialize companion
        print("1. Initializing companion...")
        companion = CompanionInterface(user_id="quick_test")
        print("✅ Companion initialized")
        
        # Test basic conversation
        print("\n2. Testing basic conversation...")
        response = companion.process_companion_input("Hello, can you help me with my tasks?")
        print(f"✅ Response: {response.content[:100]}...")
        print(f"   Type: {response.response_type}")
        
        # Test memory functionality
        print("\n3. Testing memory...")
        memory_stats = companion.memory.get_memory_stats()
        print(f"✅ Memory: {memory_stats['total_conversations']} conversations")
        
        # Test personality
        print("\n4. Testing personality...")
        summary = companion.get_conversation_summary()
        print(f"✅ Personality: {summary['personality']['communication_style']} style")
        
        # Test proactive suggestions
        print("\n5. Testing proactive suggestions...")
        suggestions = companion.get_proactive_suggestions()
        print(f"✅ Suggestions: {len(suggestions)} generated")
        
        print(f"\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")