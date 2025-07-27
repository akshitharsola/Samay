#!/usr/bin/env python3
"""
Test Claude Desktop Automation
==============================
Test script for Claude desktop automation functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import our modules
from desktop_automation.claude_desktop_automator import ClaudeDesktopAutomator

def main():
    """Test Claude desktop automation"""
    print("🧪 Testing Claude Desktop Automation")
    print("=" * 50)
    
    # Load config (simplified for testing)
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
            "startup_timeout": 10,
            "shutdown_timeout": 5
        }
    }
    
    try:
        # Initialize automator
        print("\n1. Initializing Claude automator...")
        automator = ClaudeDesktopAutomator(config)
        print("✅ Automator initialized")
        
        # Test detection
        print("\n2. Testing app detection...")
        if automator.detect_app():
            print("✅ Claude detected successfully")
        else:
            print("❌ Claude not detected")
            return
        
        # Test health check
        print("\n3. Running health check...")
        health_result = automator.health_check()
        print(f"Health check result: {health_result.status.value}")
        if health_result.error_message:
            print(f"Error: {health_result.error_message}")
        
        if health_result.status.value == "success":
            print("✅ Claude automation is working!")
            
            # Ask user if they want to test a real query
            print("\n4. Ready for query testing")
            print("To test a real query interaction:")
            print("- Uncomment the test_query section below")
            print("- Run this script again")
            
            # Uncomment these lines to test a real query:
            # print("\n5. Testing real query...")
            # query_result = automator.perform_query("Hello Claude, please respond with a simple greeting.")
            # print(f"Query result: {query_result.status.value}")
            # if query_result.data:
            #     print(f"Response: {query_result.data[:200]}...")
            # if query_result.error_message:
            #     print(f"Error: {query_result.error_message}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()