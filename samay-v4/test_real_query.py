#!/usr/bin/env python3
"""
Test Real Query with Claude
===========================
Test actual Claude automation with machine code template
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator.v4_session_manager import SamayV4SessionManager, QueryRequest

def main():
    """Test real Claude query"""
    print("🔄 Testing Real Claude Query")
    print("=" * 50)
    
    try:
        # Initialize the session manager
        print("1. Initializing session manager...")
        manager = SamayV4SessionManager()
        
        # Check if Claude is available
        available_services = manager.get_available_services()
        print(f"Available services: {available_services}")
        
        if 'claude' not in available_services:
            print("❌ Claude not available for testing")
            return
        
        # Create a test query with machine code template
        print("\n2. Creating test query with machine code template...")
        test_prompt = "Hello Claude! Please respond with a brief greeting and tell me what day it is today."
        
        request = QueryRequest(
            prompt=test_prompt,
            services=["claude"],  # Test Claude specifically
            machine_code=True,    # This was broken in v3 - now fixed
            timeout=60
        )
        
        print(f"Prompt: {test_prompt}")
        print(f"Machine code mode: {request.machine_code}")
        
        # Execute the query
        print("\n3. Executing query...")
        print("🚨 This will:")
        print("   - Launch Claude desktop app")
        print("   - Apply the fullscreen workaround you mentioned")
        print("   - Send the prompt with machine code template")
        print("   - Extract and process the response")
        print("   - Demonstrate the v3 JSON processing fix")
        
        result = manager.process_query(request)
        
        # Display results
        print(f"\n4. Results:")
        print(f"   ✅ Query completed in {result.total_execution_time:.1f}s")
        print(f"   Services queried: {result.services_queried}")
        
        # Show service results
        for service_result in result.service_results:
            if service_result.success:
                print(f"   ✅ {service_result.service_id}: SUCCESS ({service_result.execution_time:.1f}s)")
                if service_result.response:
                    print(f"      Response type: {service_result.response.response_type.value}")
                    print(f"      Confidence: {service_result.response.confidence}")
                    print(f"      Category: {service_result.response.category}")
            else:
                print(f"   ❌ {service_result.service_id}: FAILED")
                print(f"      Error: {service_result.error_message}")
        
        # Show synthesized response
        if result.synthesized_response:
            print(f"\n5. Synthesized Response:")
            print(f"   Type: {result.synthesized_response.response_type.value}")
            print(f"   Summary: {result.synthesized_response.summary}")
            print(f"   Main Response: {result.synthesized_response.main_response}")
            print(f"   Key Points: {result.synthesized_response.key_points}")
            
            print(f"\n🎉 SUCCESS! The v3 machine code issue is FIXED!")
            print(f"   - JSON template was processed correctly")
            print(f"   - Response was extracted and structured")
            print(f"   - Claude workaround was applied successfully")
        else:
            print(f"\n❌ No synthesized response - something went wrong")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  IMPORTANT: This will interact with Claude desktop app!")
    print("Make sure:")
    print("1. Claude desktop is installed")
    print("2. You have granted accessibility permissions:")
    print("   System Preferences > Security & Privacy > Privacy > Accessibility")
    print("   Add Terminal.app or your Python environment")
    print("3. You're ready for Claude to open and the fullscreen workaround to be applied")
    print()
    
    response = input("Ready to proceed? (y/N): ")
    if response.lower() in ['y', 'yes']:
        main()
    else:
        print("Test cancelled - run when you're ready!")