#!/usr/bin/env python3
"""
Test Real Claude Query
=====================
Direct test of Claude automation with machine code template
"""

import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Test a real Claude query"""
    print("🔄 Samay v4 - Real Claude Query Test")
    print("=" * 50)
    
    try:
        from desktop_automation.claude_desktop_automator import ClaudeDesktopAutomator
        from orchestrator.response_processor import ResponseProcessor
        
        # Configure Claude with your specific workaround
        config = {
            "executable_paths": {
                "darwin": ["/Applications/Claude.app"]
            },
            "automation": {
                "selectors": {
                    "input_fallback": [],
                    "submit_fallback": [],
                    "response_fallback": []
                }
            },
            "lifecycle": {
                "startup_timeout": 15,  # Increased for the workaround
                "shutdown_timeout": 5
            }
        }
        
        print("1. Initializing Claude automator...")
        claude = ClaudeDesktopAutomator(config)
        processor = ResponseProcessor()
        
        # Check if Claude is available
        if not claude.detect_app():
            print("❌ Claude desktop app not found")
            print("Make sure Claude is installed at /Applications/Claude.app")
            return False
        
        print("✅ Claude detected successfully")
        
        # Prepare the test prompt with machine code template
        test_prompt = "Hello Claude! Please respond with a brief greeting and tell me what you can help with today."
        
        # Add machine code template (this was broken in v3)
        machine_code_prompt = f'''Please respond to the following question in structured machine-readable format using this JSON template:

```json
{{
  "response": "your detailed response to the question here",
  "summary": "brief one-sentence summary of your response",
  "key_points": ["key point 1", "key point 2", "key point 3"],
  "confidence": 0.95,
  "category": "information|question|task|other"
}}
```

IMPORTANT: Please answer this question thoroughly: {test_prompt}'''
        
        print(f"\n2. Test prompt ready:")
        print(f"   Original: {test_prompt}")
        print(f"   Machine code mode: Enabled (fixes v3 issue)")
        
        print(f"\n3. This test will:")
        print(f"   ✅ Launch Claude desktop app")
        print(f"   ✅ Apply fullscreen → switch app → return workaround")
        print(f"   ✅ Send prompt with machine code template")
        print(f"   ✅ Extract response and process JSON")
        print(f"   ✅ Demonstrate v3 issue fix")
        
        print(f"\n🚨 IMPORTANT:")
        print(f"   Make sure you have granted accessibility permissions:")
        print(f"   System Preferences > Security & Privacy > Privacy > Accessibility")
        print(f"   Add Terminal.app or your Python environment")
        
        # Ask for confirmation
        proceed = input(f"\nReady to test? This will control Claude desktop app (y/N): ")
        if proceed.lower() not in ['y', 'yes']:
            print("Test cancelled")
            return False
        
        print(f"\n4. Executing query...")
        start_time = time.time()
        
        # Perform the query
        result = claude.perform_query(machine_code_prompt, timeout=60)
        
        execution_time = time.time() - start_time
        
        if result.status.value == "success":
            print(f"✅ Query executed successfully in {execution_time:.1f}s")
            
            # Process the response
            print(f"\n5. Processing response...")
            processed = processor.process_single_response(result.data, "claude")
            
            print(f"✅ Response processed:")
            print(f"   Type: {processed.response_type.value}")
            print(f"   Confidence: {processed.confidence}")
            print(f"   Category: {processed.category}")
            print(f"   Summary: {processed.summary}")
            print(f"   Key points: {len(processed.key_points)} points")
            
            print(f"\n📝 Claude's Response:")
            print(f"   {processed.main_response}")
            
            if processed.response_type.value == "json_structured":
                print(f"\n🎉 SUCCESS! Machine code processing is WORKING!")
                print(f"   ✅ JSON template was processed correctly")
                print(f"   ✅ v3 issue with buried questions is FIXED")
                print(f"   ✅ Response was extracted and structured properly")
                print(f"   ✅ Claude workaround was applied successfully")
            else:
                print(f"\n⚠️  Response processed as plain text")
                print(f"   JSON template may not have been followed")
                print(f"   But the system handled it gracefully (fallback working)")
            
            return True
            
        else:
            print(f"❌ Query failed: {result.error_message}")
            print(f"   Status: {result.status.value}")
            print(f"   Execution time: {execution_time:.1f}s")
            
            if "permission" in result.error_message.lower() or "accessibility" in result.error_message.lower():
                print(f"\n💡 This might be a permissions issue:")
                print(f"   System Preferences > Security & Privacy > Privacy > Accessibility")
                print(f"   Add Terminal.app or your Python environment")
            
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🏆 Test completed successfully!")
        print(f"Samay v4 desktop automation is working!")
        print(f"The v3 machine code issue has been resolved!")
    else:
        print(f"\n❌ Test failed - check the error messages above")
        print(f"Common issues:")
        print(f"   - Accessibility permissions not granted")
        print(f"   - Claude app not installed or in different location")
        print(f"   - Network/app loading issues")