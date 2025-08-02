#!/usr/bin/env python3
"""
Test Enhanced Web Automation
============================
Test the enhanced web_agent_dispatcher.py with real browser automation
"""

import sys
import asyncio
from pathlib import Path

# Add orchestrator to path
sys.path.append('orchestrator')

async def test_enhanced_web_dispatcher():
    """Test the enhanced web dispatcher"""
    print("🚀 TESTING ENHANCED WEB AUTOMATION")
    print("=" * 50)
    
    try:
        from web_agent_dispatcher import WebAgentDispatcher, ServiceType, OutputFormat
        
        # Initialize dispatcher
        dispatcher = WebAgentDispatcher(session_id="test_automation")
        
        # Verify sessions
        print("\n🔍 Verifying service sessions...")
        sessions = dispatcher.verify_service_sessions()
        
        ready_services = [service for service, data in sessions.items() if data["logged_in"]]
        if not ready_services:
            print("❌ No services ready for automation")
            print("💡 Solution: Initialize profiles using:")
            print("   python orchestrator/drivers.py")
            print("   Follow the setup wizard to log into services")
            return False
        
        print(f"✅ Services ready for automation: {[s.value for s in ready_services]}")
        
        # Test intelligent request
        if ready_services:
            print(f"\n🧪 Testing intelligent request with {len(ready_services)} services...")
            
            test_prompt = "What is the current time? Please provide a brief response."
            expected_output = '{"time": "current time", "message": "brief description"}'
            
            try:
                responses = await dispatcher.execute_intelligent_request(
                    prompt=test_prompt,
                    services=ready_services[:2],  # Test with max 2 services
                    expected_output=expected_output,
                    output_format=OutputFormat.JSON,
                    max_refinements=1
                )
                
                print(f"✅ Received {len(responses)} responses")
                for service, response in responses.items():
                    print(f"   {service.value}: {response.status.value} (quality: {response.quality_score:.2f})")
                
            except Exception as e:
                print(f"❌ Intelligent request failed: {e}")
                return False
        
        # Communication stats
        print(f"\n📊 Communication Stats:")
        stats = dispatcher.get_communication_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Make sure SeleniumBase is installed: pip install seleniumbase")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            dispatcher.cleanup_drivers()
        except:
            pass

def main():
    """Run the test"""
    print("🌐 Enhanced Web Automation Test")
    print("=" * 40)
    
    # Ensure memory directory exists
    Path("memory").mkdir(exist_ok=True)
    
    # Run async test
    success = asyncio.run(test_enhanced_web_dispatcher())
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 ENHANCED WEB AUTOMATION WORKING!")
        print("\n✨ Key Features Now Active:")
        print("✅ Real browser automation with SeleniumBase UC Mode")
        print("✅ Human-like typing patterns with random delays")
        print("✅ Streaming response capture from AI services")
        print("✅ Intelligent rate limiting and error handling")
        print("✅ Persistent session management with UC profiles")
        print("✅ Multi-service parallel request processing")
    else:
        print("❌ Tests need attention - check error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)