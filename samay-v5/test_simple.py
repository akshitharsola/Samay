#!/usr/bin/env python3
"""
Simple test script for browser automation dependencies
"""

import asyncio
import logging
from core.browser_automation import check_dependencies, SELENIUM_AVAILABLE

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Test the browser automation dependencies"""
    print("🧪 Testing Browser Automation Dependencies")
    print("=" * 50)
    
    print(f"SeleniumBase available: {SELENIUM_AVAILABLE}")
    deps_ok = check_dependencies()
    print(f"Dependencies check: {'✅ OK' if deps_ok else '❌ Failed'}")
    
    if SELENIUM_AVAILABLE:
        print("✅ Browser automation ready!")
        print("🎯 To test browser opening, run the debug command in the UI:")
        print("   - Start backend and frontend")
        print("   - Type 'debug ai services' in the chat")
        print("   - This will open single window with 4 AI service tabs")
    else:
        print("❌ Browser automation not available")

if __name__ == "__main__":
    asyncio.run(main())