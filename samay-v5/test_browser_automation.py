#!/usr/bin/env python3
"""
Test script for the new browser automation framework
"""

import asyncio
import logging
from core.browser_automation import test_open_service_pages

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Test the browser automation"""
    print("🧪 Testing Browser Automation Framework")
    print("=" * 50)
    
    print("🚀 This will open a single Chrome window with 4 tabs:")
    print("   - Tab 1: ChatGPT")
    print("   - Tab 2: Claude") 
    print("   - Tab 3: Gemini")
    print("   - Tab 4: Perplexity")
    print("")
    print("⚠️  Browser will stay open for manual login")
    print("   You can login to each service and browser will remain open")
    print("")
    
    # Get user confirmation
    confirm = input("Ready to test? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Test cancelled.")
        return
    
    try:
        result = await test_open_service_pages()
        
        print("\n" + "="*50)
        print("📊 Test Results:")
        print("="*50)
        
        for service, response in result.items():
            status_icon = "✅" if response['status'] == 'success' else "❌"
            print(f"{status_icon} {service.value}: {response['response']}")
            if response['error']:
                print(f"   Error: {response['error']}")
        
        print("\n🎯 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())