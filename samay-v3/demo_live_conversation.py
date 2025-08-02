#!/usr/bin/env python3
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
    print(f"\n{'='*50}")
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
        
        print(f"\n📨 API Response:")
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
    
    print("\n🎉 LIVE DEMO COMPLETE!")
    print("✨ You've just seen your Samay v3 platform in action!")

if __name__ == "__main__":
    demo_conversation()
