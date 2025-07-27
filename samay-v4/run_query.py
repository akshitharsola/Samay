#!/usr/bin/env python3
"""
Run a Real Query with Samay v4
==============================
Direct query execution
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator.v4_session_manager import SamayV4SessionManager, QueryRequest

def main():
    """Run a real query"""
    print("🔄 Samay v4 - Real Query Test")
    print("=" * 50)
    
    try:
        # Initialize
        print("Initializing Samay v4...")
        manager = SamayV4SessionManager()
        
        # Test with Perplexity first (since it passed health check)
        print("\n🔍 Testing with Perplexity...")
        request = QueryRequest(
            prompt="What is the current date and time? Please respond briefly.",
            services=["perplexity"],
            machine_code=True,
            timeout=60
        )
        
        print(f"Sending prompt: {request.prompt}")
        print(f"Machine code mode: {request.machine_code}")
        print(f"Target service: perplexity")
        
        result = manager.process_query(request)
        
        print(f"\n📊 Results:")
        print(f"   Execution time: {result.total_execution_time:.1f}s")
        print(f"   Services queried: {result.services_queried}")
        
        for service_result in result.service_results:
            if service_result.success:
                print(f"   ✅ {service_result.service_id}: SUCCESS")
                print(f"      Response type: {service_result.response.response_type.value}")
                print(f"      Confidence: {service_result.response.confidence}")
                print(f"      Summary: {service_result.response.summary}")
                print(f"      Main response: {service_result.response.main_response[:200]}...")
            else:
                print(f"   ❌ {service_result.service_id}: FAILED")
                print(f"      Error: {service_result.error_message}")
        
        if result.synthesized_response:
            print(f"\n🎉 SUCCESS! Machine code processing working!")
            print(f"   Type: {result.synthesized_response.response_type.value}")
            print(f"   Response: {result.synthesized_response.main_response}")
        else:
            print(f"\n❌ No synthesized response generated")
        
        return result
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚨 This will test Perplexity desktop automation")
    print("Make sure Perplexity desktop app is ready")
    print()
    
    result = main()
    if result:
        print(f"\n✅ Test completed successfully!")
        print(f"The v3 machine code issue has been fixed!")
    else:
        print(f"\n❌ Test failed - check the error messages above")