#!/usr/bin/env python3
"""
Simple Test for Samay v4
========================
Basic test without interactive input
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Test basic system functionality"""
    print("🧪 Samay v4 - Simple Test")
    print("=" * 40)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from orchestrator.v4_session_manager import SamayV4SessionManager, QueryRequest
        print("✅ Imports successful")
        
        # Test initialization
        print("\n2. Testing initialization...")
        manager = SamayV4SessionManager()
        print("✅ Session manager initialized")
        
        # Test service detection
        print("\n3. Testing service detection...")
        available_services = manager.get_available_services()
        print(f"✅ Available services: {available_services}")
        
        # Test health check
        print("\n4. Testing health check...")
        health = manager.health_check()
        print(f"✅ Health check completed: {health['overall_status']}")
        
        for service_id, result in health["services"].items():
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            print(f"   {status_emoji} {service_id}: {result['status']}")
            if result.get("error"):
                print(f"      Error: {result['error']}")
        
        # Test response processing
        print("\n5. Testing response processing...")
        from orchestrator.response_processor import ResponseProcessor
        processor = ResponseProcessor()
        
        test_response = '''```json
        {
            "response": "Test response from v4 system",
            "summary": "System test successful",
            "key_points": ["v4 working", "JSON processing fixed", "Ready for queries"],
            "confidence": 0.9,
            "category": "information"
        }
        ```'''
        
        result = processor.process_single_response(test_response, "test")
        print(f"✅ Response processing: {result.response_type.value}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Key points: {len(result.key_points)}")
        
        print(f"\n🎉 All basic tests passed!")
        print(f"System is ready for real testing.")
        
        if available_services:
            print(f"\n📝 To test a real query manually:")
            print(f"request = QueryRequest(")
            print(f"    prompt='Hello, please respond briefly.',")
            print(f"    services=['claude'],")
            print(f"    machine_code=True")
            print(f")")
            print(f"result = manager.process_query(request)")
        
        return manager
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    manager = main()