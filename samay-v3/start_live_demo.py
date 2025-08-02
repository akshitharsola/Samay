#!/usr/bin/env python3
"""
Samay v3 - Live UI Demonstration
===============================

This script will help you start and test the complete Samay v3 platform
with visible UI and live service demonstrations.
"""

import os
import sys
import asyncio
import json
import time
import subprocess
from datetime import datetime

def print_demo_header(title, description=""):
    """Print formatted demo header."""
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    if description:
        print(f"📋 {description}")
    print(f"{'='*70}")

def print_step(step_num, title, details=""):
    """Print demo step."""
    print(f"\n{step_num}. 🎯 {title}")
    if details:
        print(f"   💡 {details}")

def check_dependencies():
    """Check if required dependencies are available."""
    print_demo_header("CHECKING SYSTEM DEPENDENCIES")
    
    dependencies = {
        "Python": {"command": "python --version", "required": True},
        "Node.js": {"command": "node --version", "required": True},
        "npm": {"command": "npm --version", "required": True},
        "FastAPI": {"command": "python -c 'import fastapi; print(fastapi.__version__)'", "required": False},
        "React": {"command": "cd frontend && npm list react", "required": False}
    }
    
    results = {}
    for dep, config in dependencies.items():
        try:
            result = subprocess.run(config["command"], shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                results[dep] = {"available": True, "version": result.stdout.strip()}
                print(f"✅ {dep}: {result.stdout.strip()}")
            else:
                results[dep] = {"available": False, "error": result.stderr.strip()}
                print(f"❌ {dep}: Not available")
        except Exception as e:
            results[dep] = {"available": False, "error": str(e)}
            print(f"❌ {dep}: Error - {str(e)}")
    
    return results

def create_startup_script():
    """Create a script to start both backend and frontend."""
    script_content = '''#!/bin/bash

echo "🚀 STARTING SAMAY V3 LIVE DEMO"
echo "================================"

# Function to handle cleanup
cleanup() {
    echo "🛑 Shutting down Samay v3..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📡 Starting FastAPI Backend..."
cd "$(dirname "$0")"
python -m uvicorn web_api:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "⏳ Waiting for backend to start..."
sleep 5

echo "🎨 Starting React Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

echo "✅ SAMAY V3 IS NOW RUNNING!"
echo "🌐 Backend API: http://localhost:8000"
echo "🎨 Frontend UI: http://localhost:3000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 The browser should open automatically to the frontend"
echo "🛑 Press Ctrl+C to stop both services"
echo ""

# Wait for user interrupt
wait
'''

    with open('start_samay_live.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('start_samay_live.sh', 0o755)
    print("✅ Created startup script: start_samay_live.sh")

def create_demo_conversation_script():
    """Create a script to demonstrate live conversation with all service modalities."""
    demo_script = '''#!/usr/bin/env python3
"""
Live Demo Conversation Script
============================
This demonstrates actual API calls to your running Samay v3 system.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_step(step, title):
    print(f"\\n{'='*50}")
    print(f"🎯 STEP {step}: {title}")
    print(f"{'='*50}")

def make_api_call(endpoint, method="GET", data=None):
    """Make API call and show request/response."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"📡 API Request:")
    print(f"   Method: {method}")
    print(f"   URL: {url}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"\\n📨 API Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def demo_conversation():
    """Demonstrate live conversation with Samay."""
    print("🎭 SAMAY V3 LIVE CONVERSATION DEMO")
    print("This will make actual API calls to your running system")
    print("="*60)
    
    # Step 1: Health Check
    print_step(1, "SYSTEM HEALTH CHECK")
    health = make_api_call("/health")
    
    # Step 2: Start Companion Chat
    print_step(2, "COMPANION CONVERSATION")
    chat_data = {
        "message": "Hello! I'm testing my Samay v3 platform. Can you help me understand how you work?",
        "session_id": "demo_session_001"
    }
    chat_response = make_api_call("/companion/chat", "POST", chat_data)
    
    # Step 3: Test Memory
    print_step(3, "MEMORY RETRIEVAL TEST")
    memory_data = {
        "message": "What platform was I just testing?",
        "session_id": "demo_session_001"
    }
    memory_response = make_api_call("/companion/chat", "POST", memory_data)
    
    # Step 4: Create Smart Task
    print_step(4, "SMART TASK CREATION")
    task_data = {
        "title": "Complete live demo testing",
        "description": "Test all Samay v3 features with visible UI",
        "priority": "high",
        "estimated_duration": 30,
        "category": "testing"
    }
    task_response = make_api_call("/tasks/create", "POST", task_data)
    
    # Step 5: Get Proactive Suggestions
    print_step(5, "PROACTIVE SUGGESTIONS")
    suggestions_data = {
        "user_context": {
            "current_activity": "testing",
            "energy_level": "high",
            "time_of_day": "evening"
        }
    }
    suggestions_response = make_api_call("/assistant/suggestions", "POST", suggestions_data)
    
    # Step 6: Web Services (if available)
    print_step(6, "WEB SERVICES INTEGRATION")
    web_data = {
        "prompt": "What are the key features of a good AI companion?",
        "services": ["claude", "gemini", "perplexity"],
        "output_format": "json"
    }
    web_response = make_api_call("/webservices/query", "POST", web_data)
    
    # Step 7: Get Analytics
    print_step(7, "PRODUCTIVITY ANALYTICS")
    analytics = make_api_call("/analytics/productivity")
    
    print("\\n🎉 LIVE DEMO COMPLETE!")
    print("✨ You've just seen your Samay v3 platform in action!")

if __name__ == "__main__":
    demo_conversation()
'''

    with open('demo_live_conversation.py', 'w') as f:
        f.write(demo_script)
    
    os.chmod('demo_live_conversation.py', 0o755)
    print("✅ Created live demo script: demo_live_conversation.py")

def provide_instructions():
    """Provide step-by-step instructions for running the live demo."""
    print_demo_header("LIVE DEMO INSTRUCTIONS", "How to see your Samay v3 platform in action")
    
    instructions = [
        {
            "step": 1,
            "title": "Start the Complete System",
            "command": "./start_samay_live.sh",
            "description": "This starts both backend (port 8000) and frontend (port 3000)",
            "expected": "Browser opens to http://localhost:3000 showing React UI"
        },
        {
            "step": 2,
            "title": "Open Multiple Browser Tabs",
            "command": "Manual",
            "description": "Open these URLs in separate tabs:",
            "expected": "• http://localhost:3000 - React Frontend UI\n                • http://localhost:8000/docs - API Documentation\n                • http://localhost:8000 - API Status"
        },
        {
            "step": 3,
            "title": "Test Frontend Interaction",
            "command": "Manual UI Testing",
            "description": "In the React UI, try the different tabs:",
            "expected": "• Smart Dashboard with real-time data\n                • Enhanced Chat with companion\n                • Web Services panel\n                • Workflow Builder\n                • Knowledge Panel"
        },
        {
            "step": 4,
            "title": "Run Live API Demo",
            "command": "python demo_live_conversation.py",
            "description": "This makes actual API calls showing the complete flow",
            "expected": "See requests/responses for all service modalities"
        },
        {
            "step": 5,
            "title": "Test Service Modalities",
            "command": "Manual Testing",
            "description": "Test different modes in the UI:",
            "expected": "• Local LLM responses\n                • Confidential mode (local only)\n                • Web services (if configured)\n                • Multi-service parallel queries"
        }
    ]
    
    for instruction in instructions:
        print_step(instruction["step"], instruction["title"])
        print(f"   📝 Description: {instruction['description']}")
        print(f"   💻 Command: {instruction['command']}")
        print(f"   ✅ Expected: {instruction['expected']}")

def create_manual_test_guide():
    """Create a manual testing guide for the UI."""
    guide_content = '''# Samay v3 Manual Testing Guide

## 🎯 Frontend UI Testing

### Tab 1: Smart Dashboard
- ✅ View real-time productivity metrics
- ✅ See today's schedule with time blocks  
- ✅ Check proactive suggestions panel
- ✅ Use quick action buttons

### Tab 2: Enhanced Chat
- ✅ Start conversation with companion
- ✅ Test memory: "What did I just ask about?"
- ✅ See proactive suggestions appear
- ✅ Watch personality adaptation

### Tab 3: Web Services Panel  
- ✅ Submit query to multiple services
- ✅ Select output format (JSON/Text/Markdown)
- ✅ See parallel processing status
- ✅ Review response quality scores

### Tab 4: Workflow Builder
- ✅ Create new workflow
- ✅ Add triggers and steps
- ✅ Execute workflow and see status
- ✅ View execution history

### Tab 5: Knowledge Panel
- ✅ Add knowledge item
- ✅ Test different search modes
- ✅ View AI-generated insights
- ✅ See relationship mapping

## 🔄 Service Modality Testing

### Local LLM Mode
1. Go to Enhanced Chat
2. Type: "Use local mode only"
3. Ask: "What are good productivity tips?"
4. ✅ Should process locally with Phi-3-Mini

### Confidential Mode  
1. In Web Services panel
2. Enable "Confidential Mode"
3. Submit sensitive query
4. ✅ Should process locally without external calls

### Web Services Mode
1. In Web Services panel
2. Select all services: Claude, Gemini, Perplexity
3. Submit: "Latest AI development trends"
4. ✅ Should show parallel processing to all services

## 📊 Visual Flow Demonstration

1. **Input**: Type message in Enhanced Chat
2. **Processing**: See "Thinking..." indicator
3. **Memory**: Previous context retrieved and displayed
4. **Suggestions**: Proactive suggestions appear in sidebar
5. **Output**: Formatted response with metadata
6. **Analytics**: Dashboard updates with new interaction

## 🔍 API Inspection

1. Open browser dev tools (F12)
2. Go to Network tab
3. Interact with UI
4. ✅ See actual API calls being made
5. ✅ Inspect request/response data
6. ✅ Verify WebSocket connections for real-time updates

## 🧪 Error Testing

1. Try invalid inputs
2. Test with no internet (web services)
3. Submit extremely long messages
4. ✅ Should show graceful error handling
5. ✅ Should fallback to local processing when needed
'''

    with open('MANUAL_TESTING_GUIDE.md', 'w') as f:
        f.write(guide_content)
    
    print("✅ Created manual testing guide: MANUAL_TESTING_GUIDE.md")

def main():
    """Main function to set up live demo."""
    print_demo_header("SAMAY V3 LIVE DEMO SETUP", "Preparing visible UI demonstration")
    
    # Check dependencies
    deps = check_dependencies()
    
    # Create startup scripts
    print_step(1, "Creating Startup Scripts")
    create_startup_script()
    create_demo_conversation_script()
    create_manual_test_guide()
    
    # Provide instructions
    provide_instructions()
    
    print_demo_header("QUICK START COMMANDS")
    print("🚀 To start the live demo right now:")
    print()
    print("1. Start the system:")
    print("   ./start_samay_live.sh")
    print()
    print("2. In another terminal, run the API demo:")
    print("   python demo_live_conversation.py")
    print()
    print("3. Open your browser to:")
    print("   http://localhost:3000 (React Frontend)")
    print("   http://localhost:8000/docs (API Documentation)")
    print()
    print("🎭 WHAT YOU'LL SEE:")
    print("• Complete React UI with all 6 tabs functional")
    print("• Real-time API calls and responses")
    print("• Local LLM processing with Phi-3-Mini")
    print("• Web services integration (if configured)")
    print("• Live companion conversations with memory")
    print("• Proactive suggestions and task management")
    print("• Visual workflow building and execution")
    print("• Knowledge management with search")
    print()
    print("📋 For detailed testing, see: MANUAL_TESTING_GUIDE.md")

if __name__ == "__main__":
    main()