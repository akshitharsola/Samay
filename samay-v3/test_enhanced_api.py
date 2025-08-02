#!/usr/bin/env python3
"""
Test Enhanced API with Phase 4 Capabilities
==========================================
Test all the new companion features API endpoints
"""

import requests
import json
import asyncio
import websockets
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test basic API health"""
    print("🏥 Testing API Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_companion_chat():
    """Test enhanced companion chat"""
    print("\n🤖 Testing Companion Chat...")
    
    try:
        chat_data = {
            "message": "Hello! I need help organizing my day and getting some proactive suggestions.",
            "include_suggestions": True,
            "session_id": "test_session_123"
        }
        
        response = requests.post(f"{BASE_URL}/companion/chat", json=chat_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat Response: {len(data['response']['content'])} characters")
            print(f"✅ Suggestions: {len(data['suggestions'])} provided")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def test_smart_tasks():
    """Test smart task creation and scheduling"""
    print("\n📅 Testing Smart Tasks...")
    
    try:
        # Create a task
        task_data = {
            "title": "Complete Phase 5 UI Integration",
            "description": "Build the frontend components for all Phase 4 features",
            "priority": "high",
            "category": "development",
            "tags": ["ui", "phase5", "integration"]
        }
        
        response = requests.post(f"{BASE_URL}/tasks/create", json=task_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Task Created: {data['task_id']}")
            
            # Get smart schedule
            schedule_response = requests.get(f"{BASE_URL}/tasks/schedule")
            if schedule_response.status_code == 200:
                schedule_data = schedule_response.json()
                print(f"✅ Schedule Retrieved: {len(schedule_data['schedule'].get('time_blocks', []))} time blocks")
                return True
            else:
                print(f"❌ Schedule failed: {schedule_response.status_code}")
                return False
        else:
            print(f"❌ Task creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Smart tasks error: {e}")
        return False

def test_proactive_assistant():
    """Test proactive assistant suggestions"""
    print("\n🧠 Testing Proactive Assistant...")
    
    try:
        context_data = {
            "current_activity": "coding",
            "focus_state": "focused",
            "energy_level": 8,
            "mood": "productive",
            "location": "office",
            "time_of_day": "morning",
            "workload_status": "high"
        }
        
        response = requests.post(f"{BASE_URL}/assistant/suggestions", json=context_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Suggestions Generated: {len(data['suggestions'])} items")
            if data['suggestions']:
                print(f"   First suggestion: {data['suggestions'][0].get('content', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Suggestions failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Proactive assistant error: {e}")
        return False

def test_workflow_automation():
    """Test workflow automation"""
    print("\n⚙️ Testing Workflow Automation...")
    
    try:
        # Get templates first
        templates_response = requests.get(f"{BASE_URL}/workflows/templates")
        if templates_response.status_code == 200:
            templates = templates_response.json()
            print(f"✅ Templates Available: {len(templates['templates'])}")
            
            # Create a custom workflow
            workflow_data = {
                "name": "Daily Setup Automation",
                "description": "Automated daily setup routine",
                "trigger_type": "time",
                "trigger_data": {"time": "09:00"},
                "steps": [
                    {"action": "create_task", "params": {"title": "Review priorities"}},
                    {"action": "send_reminder", "params": {"message": "Time for daily standup"}}
                ]
            }
            
            response = requests.post(f"{BASE_URL}/workflows/create", json=workflow_data)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Workflow Created: {data['workflow_id']}")
                return True
            else:
                print(f"❌ Workflow creation failed: {response.status_code}")
                return False
        else:
            print(f"❌ Templates failed: {templates_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Workflow automation error: {e}")
        return False

def test_knowledge_base():
    """Test personal knowledge base"""
    print("\n📚 Testing Knowledge Base...")
    
    try:
        # Add knowledge item
        knowledge_data = {
            "title": "Phase 5 Implementation Notes",
            "content": "Enhanced UI integration requires connecting all Phase 4 features to the web interface. Key components include smart dashboard, companion chat, and automation panels.",
            "knowledge_type": "document",
            "category": "development",
            "tags": ["phase5", "ui", "integration", "notes"]
        }
        
        response = requests.post(f"{BASE_URL}/knowledge/add", json=knowledge_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Knowledge Added: {data['item_id']}")
            
            # Search knowledge
            search_response = requests.get(f"{BASE_URL}/knowledge/search?query=Phase 5&search_mode=semantic")
            if search_response.status_code == 200:
                search_data = search_response.json()
                print(f"✅ Search Results: {len(search_data['results'])} items")
                
                # Get insights
                insights_response = requests.get(f"{BASE_URL}/knowledge/insights")
                if insights_response.status_code == 200:
                    insights_data = insights_response.json()
                    print(f"✅ Insights Generated: {len(insights_data['insights'])} items")
                    return True
                else:
                    print(f"❌ Insights failed: {insights_response.status_code}")
                    return False
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                return False
        else:
            print(f"❌ Knowledge add failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Knowledge base error: {e}")
        return False

def test_web_services():
    """Test web services automation status"""
    print("\n🌐 Testing Web Services...")
    
    try:
        response = requests.get(f"{BASE_URL}/webservices/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Web Services Status Retrieved")
            
            ready_services = sum(1 for service, status in data['service_status'].items() 
                               if status.get('logged_in', False))
            print(f"   Ready services: {ready_services}/3")
            print(f"   Communication stats: {data['communication_stats']}")
            return True
        else:
            print(f"❌ Web services status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web services error: {e}")
        return False

def test_productivity_analytics():
    """Test productivity analytics"""
    print("\n📊 Testing Productivity Analytics...")
    
    try:
        response = requests.get(f"{BASE_URL}/analytics/productivity")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Productivity Insights Retrieved")
            insights = data.get('insights', {})
            print(f"   Task completion rate: {insights.get('task_completion_rate', 'N/A')}")
            print(f"   Productivity trends: {len(insights.get('productivity_trends', []))} data points")
            return True
        else:
            print(f"❌ Analytics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return False

def main():
    """Run comprehensive API tests"""
    print("🚀 ENHANCED API COMPREHENSIVE TEST")
    print("=" * 50)
    
    tests = [
        ("API Health", test_api_health),
        ("Companion Chat", test_companion_chat),
        ("Smart Tasks", test_smart_tasks),
        ("Proactive Assistant", test_proactive_assistant),
        ("Workflow Automation", test_workflow_automation),
        ("Knowledge Base", test_knowledge_base),
        ("Web Services", test_web_services),
        ("Productivity Analytics", test_productivity_analytics)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\n📈 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL ENHANCED API FEATURES WORKING!")
        print("\n✨ Phase 5 API Integration Complete:")
        print("✅ Enhanced companion chat with proactive suggestions")
        print("✅ Smart task scheduling with AI optimization")
        print("✅ Context-aware proactive assistant")
        print("✅ Workflow automation with template system")
        print("✅ Intelligent knowledge base with search")
        print("✅ Web service automation status monitoring")
        print("✅ Comprehensive productivity analytics")
        print("\n🚀 Ready for frontend dashboard development!")
    else:
        print(f"\n⚠️ {total - passed} tests need attention")
        print("💡 Start the API server: python web_api.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)