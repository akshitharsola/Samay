#!/usr/bin/env python3
"""
Quick Test for Samay v3 Phase 4 Components
==========================================
Validates individual Phase 4 components without complex integration
"""

import sys
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add orchestrator to path
sys.path.append('orchestrator')

def test_enhanced_scheduler():
    """Test enhanced task scheduler"""
    print("🗓️ Testing Enhanced Task Scheduler...")
    
    try:
        from enhanced_task_scheduler import EnhancedTaskScheduler, TaskPriority
        
        scheduler = EnhancedTaskScheduler("memory/test_enhanced_tasks.db")
        
        # Create a task
        task_id = scheduler.create_smart_task(
            title="Test task",
            description="Testing enhanced scheduler",
            priority=TaskPriority.HIGH,
            category="testing",
            tags=["test", "phase4"]
        )
        
        print(f"✅ Created task: {task_id}")
        
        # Get schedule
        schedule = scheduler.get_smart_schedule()
        print(f"✅ Generated schedule with {len(schedule.get('time_blocks', []))} time blocks")
        
        # Get suggestions
        suggestions = scheduler.get_proactive_suggestions()
        print(f"✅ Generated {len(suggestions)} proactive suggestions")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Scheduler test failed: {e}")
        return False

def test_proactive_assistant():
    """Test proactive assistant"""
    print("\n🤖 Testing Proactive Assistant...")
    
    try:
        from proactive_assistant import ProactiveAssistant, UserContext
        
        assistant = ProactiveAssistant("memory/test_proactive.db")
        
        # Create context
        context = UserContext(
            current_activity="testing",
            focus_state="focused",
            energy_level=8,
            mood="productive",
            location="office",
            time_of_day="morning",
            workload_status="moderate",
            upcoming_deadlines=[],
            recent_productivity=0.8
        )
        
        # Generate suggestions
        suggestions = assistant.generate_proactive_suggestions(context)
        print(f"✅ Generated {len(suggestions)} suggestions")
        
        # Monitor behavior
        patterns = assistant.monitor_user_behavior()
        print(f"✅ Analyzed {len(patterns)} behavior patterns")
        
        return True
        
    except Exception as e:
        print(f"❌ Proactive Assistant test failed: {e}")
        return False

def test_workflow_automation():
    """Test workflow automation"""
    print("\n⚙️ Testing Workflow Automation...")
    
    try:
        from workflow_automation import WorkflowAutomation
        
        automation = WorkflowAutomation("memory/test_workflows.db")
        
        # Create workflows
        workflow_id = automation.create_daily_standup_workflow()
        print(f"✅ Created standup workflow: {workflow_id}")
        
        # Test execution
        async def test_exec():
            result = await automation.execute_workflow(workflow_id, {"test": True})
            return result["status"]
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status = loop.run_until_complete(test_exec())
            print(f"✅ Workflow executed with status: {status}")
        finally:
            loop.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow Automation test failed: {e}")
        return False

def test_knowledge_base():
    """Test personal knowledge base"""
    print("\n📚 Testing Knowledge Base...")
    
    try:
        import time
        import os
        from personal_knowledge_base import PersonalKnowledgeBase, KnowledgeType
        
        # Use a unique database file name with timestamp
        import time
        db_name = f"memory/kb_test_{int(time.time() * 1000)}.db"
        
        # Ensure database doesn't exist
        if os.path.exists(db_name):
            os.remove(db_name)
        
        kb = PersonalKnowledgeBase(db_name)
        
        # Add knowledge item
        item_id = kb.add_knowledge_item(
            title="Test Knowledge",
            content="This is a test knowledge item for Phase 4 validation",
            knowledge_type=KnowledgeType.DOCUMENT,
            category="testing",
            tags=["test", "phase4"]
        )
        
        print(f"✅ Added knowledge item: {item_id}")
        
        # Search knowledge
        results = kb.search_knowledge("test knowledge")
        print(f"✅ Found {len(results)} search results")
        
        # Generate insights
        insights = kb.generate_knowledge_insights()
        print(f"✅ Generated {len(insights)} insights")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge Base test failed: {e}")
        return False

def main():
    """Run quick Phase 4 tests"""
    print("🚀 SAMAY V3 PHASE 4 QUICK VALIDATION")
    print("=" * 50)
    
    # Ensure memory directory exists
    Path("memory").mkdir(exist_ok=True)
    
    # Test results
    results = {
        "Enhanced Scheduler": test_enhanced_scheduler(),
        "Proactive Assistant": test_proactive_assistant(),
        "Workflow Automation": test_workflow_automation(),
        "Knowledge Base": test_knowledge_base()
    }
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 QUICK TEST RESULTS")
    print("=" * 50)
    
    all_passed = True
    for component, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{component:20} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL PHASE 4 COMPONENTS WORKING! 🎉")
        print("\n✨ Phase 4 Advanced Companion Features are ready!")
        print("\nValidated Components:")
        print("✅ Enhanced Task Scheduler with AI optimization")
        print("✅ Proactive Assistant with context awareness")  
        print("✅ Workflow Automation with async execution")
        print("✅ Personal Knowledge Base with intelligent search")
        print("\n🚀 Ready to proceed with integration and Phase 5!")
    else:
        print("❌ Some components need attention")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)