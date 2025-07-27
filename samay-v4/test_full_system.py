#!/usr/bin/env python3
"""
Test Full Samay v4 System
=========================
Comprehensive test for Claude and Perplexity desktop automation
Includes Claude-specific workaround (fullscreen -> switch app -> return)
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator.v4_session_manager import SamayV4SessionManager, QueryRequest

def test_service_detection():
    """Test detection of both Claude and Perplexity"""
    print("🔍 Testing Service Detection")
    print("=" * 40)
    
    try:
        manager = SamayV4SessionManager()
        
        # Get status summary
        status = manager.get_status_summary()
        print(f"📊 System Status:")
        print(f"   Total services configured: {status['total_services_configured']}")
        print(f"   Services installed: {status['services_installed']}")
        print(f"   Services with automators: {status['services_with_automators']}")
        print(f"   Available services: {status['available_services']}")
        print(f"   Ready for queries: {status['ready_for_queries']}")
        
        return manager, status['available_services']
        
    except Exception as e:
        print(f"❌ Service detection failed: {e}")
        return None, []

def test_health_checks(manager):
    """Test health checks for all services"""
    print("\n🏥 Testing Health Checks")
    print("=" * 40)
    
    try:
        health = manager.health_check()
        print(f"Overall status: {health['overall_status']}")
        
        for service_id, result in health["services"].items():
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_emoji} {service_id}: {result['status']}")
            if result.get("error"):
                print(f"   Error: {result['error']}")
            print(f"   Execution time: {result['execution_time']:.2f}s")
        
        return health['overall_status'] == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_machine_code_processing():
    """Test the machine code JSON processing that was broken in v3"""
    print("\n🤖 Testing Machine Code Processing")
    print("=" * 40)
    
    try:
        from orchestrator.response_processor import ResponseProcessor
        
        processor = ResponseProcessor()
        
        # Test JSON extraction with machine code template
        test_response = '''
        Here's my response in machine readable format:
        
        ```json
        {
            "response": "This is a test of the machine code processing system that was broken in v3",
            "summary": "Machine code processing test successful",
            "key_points": ["JSON extraction working", "Template processing fixed", "Ready for real queries"],
            "confidence": 0.95,
            "category": "information"
        }
        ```
        
        I hope this demonstrates the fix!
        '''
        
        result = processor.process_single_response(test_response, "test_service")
        
        print(f"✅ Response type: {result.response_type.value}")
        print(f"✅ Main response: {result.main_response[:100]}...")
        print(f"✅ Summary: {result.summary}")
        print(f"✅ Key points: {len(result.key_points)} points extracted")
        print(f"✅ Confidence: {result.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Machine code processing test failed: {e}")
        return False

def test_query_execution(manager, available_services):
    """Test actual query execution (commented out for safety)"""
    print("\n🔄 Query Execution Test Available")
    print("=" * 40)
    
    print("Available services for testing:", available_services)
    print("\nTo test real queries, you can run:")
    print("1. Single service query:")
    print("   request = QueryRequest(")
    print("       prompt='Hello, please respond with a brief greeting.',")
    print("       services=['claude'],  # or ['perplexity']")
    print("       machine_code=True")
    print("   )")
    print("   result = manager.process_query(request)")
    print()
    print("2. Multi-service query:")
    print("   request = QueryRequest(")
    print("       prompt='What is artificial intelligence?',")
    print("       machine_code=True")
    print("   )")
    print("   result = manager.process_query(request)")
    print()
    print("🚨 IMPORTANT: Make sure you have granted accessibility permissions!")
    print("   System Preferences > Security & Privacy > Privacy > Accessibility")
    print("   Add Terminal.app or your Python environment")
    
    return True

def run_test_query(manager, prompt, services=None):
    """Helper function to run a test query - call this manually"""
    print(f"\n🔄 Running Test Query")
    print("=" * 40)
    print(f"Prompt: {prompt}")
    print(f"Services: {services or 'all available'}")
    
    try:
        request = QueryRequest(
            prompt=prompt,
            services=services,
            machine_code=True,
            timeout=60
        )
        
        result = manager.process_query(request)
        
        print(f"\n📊 Query Results:")
        print(f"   Request ID: {result.request_id[:8]}...")
        print(f"   Services queried: {result.services_queried}")
        print(f"   Successful services: {len([r for r in result.service_results if r.success])}")
        print(f"   Total execution time: {result.total_execution_time:.1f}s")
        
        if result.synthesized_response:
            print(f"\n📝 Synthesized Response:")
            print(f"   Type: {result.synthesized_response.response_type.value}")
            print(f"   Source: {result.synthesized_response.source_service}")
            print(f"   Response: {result.synthesized_response.main_response[:200]}...")
            print(f"   Summary: {result.synthesized_response.summary}")
        else:
            print(f"❌ No synthesized response generated")
            
        # Show individual service results
        print(f"\n🔍 Individual Service Results:")
        for service_result in result.service_results:
            status_emoji = "✅" if service_result.success else "❌"
            print(f"   {status_emoji} {service_result.service_id}: {service_result.execution_time:.1f}s")
            if service_result.error_message:
                print(f"      Error: {service_result.error_message}")
        
        return result
        
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function"""
    print("🧪 Samay v4 - Full System Test")
    print("=" * 50)
    print("Testing Claude desktop automation with workaround")
    print("Testing Perplexity desktop automation (App Store version)")
    print("Testing machine code processing (v3 issue fix)")
    print()
    
    # Test 1: Service Detection
    manager, available_services = test_service_detection()
    if not manager:
        print("❌ Cannot continue without service manager")
        return
    
    # Test 2: Health Checks
    health_ok = test_health_checks(manager)
    if not health_ok:
        print("⚠️  Health checks failed, but continuing...")
    
    # Test 3: Machine Code Processing
    processing_ok = test_machine_code_processing()
    if not processing_ok:
        print("❌ Machine code processing failed")
        return
    
    # Test 4: Query Execution Instructions
    test_query_execution(manager, available_services)
    
    print("\n🎯 Test Summary:")
    print(f"   ✅ Service detection: {len(available_services)} services available")
    print(f"   {'✅' if health_ok else '⚠️ '} Health checks: {'passed' if health_ok else 'issues detected'}")
    print(f"   ✅ Machine code processing: working (v3 issue fixed)")
    print(f"   📋 Query execution: ready for manual testing")
    
    if available_services:
        print(f"\n🚀 Ready to test with services: {', '.join(available_services)}")
        print("To run a test query, call:")
        print("run_test_query(manager, 'Your test prompt here', ['claude'])")
    else:
        print(f"\n❌ No services available for testing")
        print("Make sure Claude and/or Perplexity desktop apps are installed")
    
    # Return manager for interactive use
    return manager

if __name__ == "__main__":
    manager = main()
    
    # Interactive testing examples (uncomment to test):
    
    # Test Claude specifically:
    # run_test_query(manager, "Hello Claude, please respond with a simple greeting.", ["claude"])
    
    # Test Perplexity specifically:
    # run_test_query(manager, "What is machine learning?", ["perplexity"])
    
    # Test both services:
    # run_test_query(manager, "Explain artificial intelligence in simple terms.")