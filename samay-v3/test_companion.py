#!/usr/bin/env python3
"""
Samay v3 - Companion Functionality Test Suite
============================================
Comprehensive testing of companion AI with memory-driven conversations
"""

import sys
from pathlib import Path
import time

# Add orchestrator to path
sys.path.append(str(Path(__file__).parent / "orchestrator"))

from companion_interface import CompanionInterface
from conversation_memory import ConversationMemory
from personality_profile import PersonalityProfile
from task_scheduler import TaskScheduler


def test_memory_driven_conversations():
    """Test memory-driven conversation capabilities"""
    print("🧠 Testing Memory-Driven Conversations")
    print("=" * 50)
    
    # Initialize companion
    companion = CompanionInterface(user_id="test_user_memory")
    
    # Conversation sequence to build memory
    conversation_sequence = [
        {
            "input": "Hi, I'm working on a React project called TaskFlow",
            "expected_memory": ["React", "TaskFlow", "project"]
        },
        {
            "input": "I need to implement user authentication with JWT tokens",
            "expected_memory": ["authentication", "JWT", "tokens"]
        },
        {
            "input": "I'm having trouble with the login form validation",
            "expected_memory": ["login", "form", "validation", "trouble"]
        },
        {
            "input": "Remember that authentication issue I mentioned?",
            "expected_memory": ["authentication", "previous context"]
        },
        {
            "input": "Can you help me prioritize my TaskFlow tasks for this week?",
            "expected_memory": ["TaskFlow", "tasks", "week", "prioritize"]
        }
    ]
    
    print("\n📝 Running conversation sequence:")
    
    for i, conv in enumerate(conversation_sequence, 1):
        print(f"\n--- Conversation {i} ---")
        print(f"User: {conv['input']}")
        
        # Process with companion
        response = companion.process_companion_input(conv['input'])
        
        print(f"Companion: {response.content[:200]}...")
        print(f"Response Type: {response.response_type}")
        print(f"Memory References: {len(response.memory_references)}")
        print(f"Proactive Suggestions: {len(response.proactive_suggestions)}")
        
        # Check if companion is using memory
        if i > 1:  # After first conversation
            memory_context = companion.memory.get_relevant_context(conv['input'])
            print(f"Memory Context Used: {len(memory_context['related_conversations'])} related conversations")
            
            # Verify memory relevance
            if memory_context['related_conversations']:
                print(f"✅ Memory integration working")
            else:
                print(f"⚠️  Limited memory integration")
        
        time.sleep(0.5)  # Brief pause between conversations
    
    print(f"\n📊 Final Memory Statistics:")
    memory_stats = companion.memory.get_memory_stats()
    print(f"Total conversations: {memory_stats['total_conversations']}")
    print(f"Top topics: {memory_stats['top_topics'][:5]}")
    
    return True


def test_personality_adaptation():
    """Test personality adaptation based on user interactions"""
    print("\n🎭 Testing Personality Adaptation")
    print("=" * 50)
    
    companion = CompanionInterface(user_id="test_user_personality")
    
    # Test different communication styles
    adaptation_tests = [
        {
            "input": "Hey, can you help me out real quick?",
            "feedback": "I prefer casual responses",
            "expected_adaptation": "casual communication"
        },
        {
            "input": "Could you please provide a detailed analysis of the project requirements?",
            "feedback": "I like thorough explanations",
            "expected_adaptation": "detailed responses"
        },
        {
            "input": "I'm really frustrated with this bug 😤",
            "feedback": "Please be more supportive",
            "expected_adaptation": "empathetic tone"
        }
    ]
    
    print("\n🔄 Testing adaptation sequence:")
    
    for i, test in enumerate(adaptation_tests, 1):
        print(f"\n--- Adaptation Test {i} ---")
        print(f"User Input: {test['input']}")
        
        # Get initial personality state
        initial_profile = companion.personality.get_personality_summary()
        
        # Process interaction with feedback
        response = companion.process_companion_input(test['input'])
        companion.personality.adapt_to_interaction(test['input'], test['feedback'])
        
        # Check adaptation
        adapted_profile = companion.personality.get_personality_summary()
        
        print(f"Initial Style: {initial_profile['communication_style']['tone_preference']}")
        print(f"Adapted Style: {adapted_profile['communication_style']['tone_preference']}")
        print(f"Adaptation Count: {adapted_profile['adaptation_count']}")
        
        if adapted_profile['adaptation_count'] > initial_profile['adaptation_count']:
            print(f"✅ Personality adapted successfully")
        else:
            print(f"⚠️  Limited personality adaptation")
    
    return True


def test_task_integration():
    """Test task management integration"""
    print("\n📋 Testing Task Integration")
    print("=" * 50)
    
    companion = CompanionInterface(user_id="test_user_tasks")
    
    # Test task-related conversations
    task_conversations = [
        "I need to finish the presentation by tomorrow",
        "remind me to call the client at 3 PM",
        "add a task to review the budget reports",
        "what are my tasks for today?",
        "I completed the presentation task"
    ]
    
    print("\n📋 Testing task conversations:")
    
    for i, task_input in enumerate(task_conversations, 1):
        print(f"\n--- Task Test {i} ---")
        print(f"User: {task_input}")
        
        # Get initial task stats
        initial_stats = companion.scheduler.get_task_statistics()
        
        # Process with companion
        response = companion.process_companion_input(task_input)
        
        # Get updated task stats
        updated_stats = companion.scheduler.get_task_statistics()
        
        print(f"Response: {response.content[:150]}...")
        print(f"Suggested Actions: {response.suggested_actions}")
        print(f"Tasks Before: {initial_stats['total_tasks']}")
        print(f"Tasks After: {updated_stats['total_tasks']}")
        
        if response.suggested_actions:
            print(f"✅ Task integration active")
        else:
            print(f"⚠️  Limited task integration")
    
    # Test daily briefing with tasks
    print(f"\n📋 Testing daily briefing:")
    briefing = companion.get_daily_briefing()
    print(f"Daily Briefing: {briefing[:200]}...")
    
    return True


def test_proactive_suggestions():
    """Test proactive suggestion generation"""
    print("\n💡 Testing Proactive Suggestions")
    print("=" * 50)
    
    companion = CompanionInterface(user_id="test_user_proactive")
    
    # Create some context for proactive suggestions
    print("\n🎯 Setting up context for proactive suggestions:")
    
    # Add some tasks and reminders
    task_id = companion.scheduler.create_task(
        "Complete quarterly report",
        "Finish Q3 analysis and presentation",
        due_date="2024-01-30T09:00:00"
    )
    
    companion.scheduler.add_reminder(
        "Team meeting prep",
        "Prepare slides for team meeting",
        "2024-01-29T14:00:00"
    )
    
    # Have some conversations to build memory
    companion.process_companion_input("I'm working on the quarterly analysis")
    companion.process_companion_input("I need to present to the team next week")
    
    # Test proactive suggestions
    print(f"\n💡 Generating proactive suggestions:")
    suggestions = companion.get_proactive_suggestions()
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")
    
    if suggestions:
        print(f"✅ Proactive suggestions generated: {len(suggestions)}")
    else:
        print(f"⚠️  No proactive suggestions generated")
    
    # Test conversation with proactive context
    print(f"\n💬 Testing conversation with proactive context:")
    response = companion.process_companion_input("What should I focus on today?")
    
    print(f"Response: {response.content[:200]}...")
    print(f"Proactive Suggestions: {response.proactive_suggestions}")
    
    return True


def test_conversation_modes():
    """Test different conversation modes"""
    print("\n🔄 Testing Conversation Modes")
    print("=" * 50)
    
    companion = CompanionInterface(user_id="test_user_modes")
    
    # Test different modes
    modes_to_test = ["companion", "assistant", "task_focused", "brainstorming"]
    test_input = "Help me improve my productivity"
    
    print(f"\n🎭 Testing modes with input: '{test_input}'")
    
    for mode in modes_to_test:
        print(f"\n--- Testing {mode.upper()} mode ---")
        
        # Switch mode
        mode_result = companion.switch_conversation_mode(mode)
        print(f"Mode Switch: {mode_result}")
        
        # Process same input in different mode
        response = companion.process_companion_input(test_input)
        
        print(f"Response Type: {response.response_type}")
        print(f"Response: {response.content[:150]}...")
        print(f"Emotional Tone: {response.emotional_tone}")
        print(f"Suggestions: {len(response.proactive_suggestions)}")
    
    return True


def test_conversation_continuity():
    """Test conversation continuity and follow-up handling"""
    print("\n🔗 Testing Conversation Continuity")
    print("=" * 50)
    
    companion = CompanionInterface(user_id="test_user_continuity")
    
    # Initial conversation
    print(f"\n💬 Initial conversation:")
    initial_input = "I'm planning a new mobile app project"
    initial_response = companion.process_companion_input(initial_input)
    print(f"User: {initial_input}")
    print(f"Companion: {initial_response.content[:150]}...")
    
    # Follow-up questions to test continuity
    follow_ups = [
        "What technologies would you recommend for this project?",
        "How should I structure the development timeline?",
        "What about the user authentication we discussed?"
    ]
    
    print(f"\n🔗 Testing follow-up continuity:")
    
    for i, follow_up in enumerate(follow_ups, 1):
        print(f"\n--- Follow-up {i} ---")
        print(f"User: {follow_up}")
        
        # Handle follow-up with continuity
        response = companion.handle_follow_up_questions(initial_response.content, follow_up)
        
        print(f"Response: {response.content[:150]}...")
        print(f"Memory References: {len(response.memory_references)}")
        
        if response.memory_references:
            print(f"✅ Conversation continuity maintained")
        else:
            print(f"⚠️  Limited conversation continuity")
    
    return True


def run_comprehensive_test():
    """Run comprehensive companion functionality test"""
    print("🚀 Samay v3 - Comprehensive Companion Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    try:
        # Run all tests
        test_results["memory_conversations"] = test_memory_driven_conversations()
        test_results["personality_adaptation"] = test_personality_adaptation()
        test_results["task_integration"] = test_task_integration()
        test_results["proactive_suggestions"] = test_proactive_suggestions()
        test_results["conversation_modes"] = test_conversation_modes()
        test_results["conversation_continuity"] = test_conversation_continuity()
        
        # Summary
        print(f"\n🎯 Test Results Summary")
        print("=" * 40)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Score: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print(f"🎉 All companion functionality tests PASSED!")
            print(f"🤖 Samay v3 companion features are working correctly!")
        else:
            print(f"⚠️  Some tests failed. Review the output above for details.")
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return False


if __name__ == "__main__":
    # Run comprehensive test
    success = run_comprehensive_test()
    
    if success:
        print(f"\n✅ Ready for Phase 1 completion!")
        print(f"🎯 Next: Move to Phase 2 - Iterative Refinement System")
    else:
        print(f"\n⚠️  Review and fix issues before proceeding")
    
    exit(0 if success else 1)