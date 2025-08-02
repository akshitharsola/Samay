#!/usr/bin/env python3
"""
Test Phase 3 - Machine-Language Communication
===========================================
Comprehensive testing of web dispatcher, ML optimizer, and parallel manager
"""

import sys
from pathlib import Path
import traceback

# Add orchestrator to path
sys.path.append(str(Path(__file__).parent / "orchestrator"))

from companion_interface import CompanionInterface
from web_agent_dispatcher import WebAgentDispatcher, ServiceType, OutputFormat
from machine_language_optimizer import MachineLanguageOptimizer, PromptCategory, OptimizationStrategy
from parallel_session_manager import ParallelSessionManager, ExecutionMode


def test_web_dispatcher():
    """Test web agent dispatcher functionality"""
    print("🌐 Testing Web Agent Dispatcher")
    print("=" * 40)
    
    try:
        # Initialize dispatcher
        dispatcher = WebAgentDispatcher(session_id="test_web_dispatcher")
        
        # Test service registration
        print("\n1️⃣ Testing service registration...")
        dispatcher.register_service_session(ServiceType.CLAUDE, {"token": "mock_claude_token"})
        dispatcher.register_service_session(ServiceType.GEMINI, {"token": "mock_gemini_token"})
        dispatcher.register_service_session(ServiceType.PERPLEXITY, {"token": "mock_perplexity_token"})
        print("✅ All services registered successfully")
        
        # Test communication stats
        print("\n2️⃣ Testing communication stats...")
        stats = dispatcher.get_communication_stats()
        print(f"✅ Stats retrieved:")
        print(f"   Active services: {stats['active_services']}")
        print(f"   Total requests: {stats['total_requests']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web dispatcher test failed: {e}")
        traceback.print_exc()
        return False


def test_ml_optimizer():
    """Test machine language optimizer functionality"""
    print("\n🔧 Testing Machine Language Optimizer")
    print("=" * 40)
    
    try:
        # Initialize optimizer
        optimizer = MachineLanguageOptimizer(session_id="test_ml_optimizer")
        
        # Test prompt optimization
        print("\n1️⃣ Testing prompt optimization...")
        test_prompt = "Can you please help me extract company information from this text and provide it structured"
        expected_output = '{"companies": [{"name": "", "industry": "", "founded": ""}], "count": 0}'
        
        optimization = optimizer.optimize_for_service(
            test_prompt,
            ServiceType.CLAUDE,
            expected_output,
            OutputFormat.JSON,
            OptimizationStrategy.STRUCTURE_ENFORCEMENT
        )
        
        print(f"✅ Optimization completed!")
        print(f"   Token reduction: {optimization.token_reduction}")
        print(f"   Clarity score: {optimization.clarity_score:.2f}")
        print(f"   Structure compliance: {optimization.structure_compliance:.2f}")
        
        # Test parallel optimization
        print("\n2️⃣ Testing parallel optimization...")
        parallel_prompts = optimizer.optimize_for_parallel_execution(
            "Research AI trends and provide analysis",
            [ServiceType.CLAUDE, ServiceType.GEMINI],
            '{"trends": [], "analysis": ""}',
            OutputFormat.JSON
        )
        
        print(f"✅ Parallel optimization completed for {len(parallel_prompts)} services")
        
        # Test effectiveness analysis
        print("\n3️⃣ Testing effectiveness analysis...")
        effectiveness = optimizer.analyze_optimization_effectiveness()
        print(f"✅ Analysis completed:")
        print(f"   Total optimizations: {effectiveness['token_savings']['optimizations_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML optimizer test failed: {e}")
        traceback.print_exc()
        return False


def test_parallel_manager():
    """Test parallel session manager functionality"""
    print("\n⚡ Testing Parallel Session Manager")
    print("=" * 40)
    
    try:
        # Initialize manager
        manager = ParallelSessionManager(session_id="test_parallel_manager")
        
        # Test service registration
        print("\n1️⃣ Testing service registration...")
        manager.register_service_session(ServiceType.CLAUDE, {"token": "mock_claude"}, 2)
        manager.register_service_session(ServiceType.GEMINI, {"token": "mock_gemini"}, 2)
        print("✅ Services registered successfully")
        
        # Test analytics
        print("\n2️⃣ Testing performance analytics...")
        analytics = manager.get_performance_analytics()
        print(f"✅ Analytics retrieved:")
        print(f"   Services tracked: {len(analytics['service_performance'])}")
        print(f"   Recommendations: {len(analytics['recommendations'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parallel manager test failed: {e}")
        traceback.print_exc()
        return False


def test_companion_integration():
    """Test Phase 3 integration with companion system"""
    print("\n🤖 Testing Companion Integration")
    print("=" * 40)
    
    try:
        # Initialize companion with Phase 3 capabilities
        companion = CompanionInterface(user_id="phase3_test")
        
        print("\n1️⃣ Testing companion initialization...")
        summary = companion.get_conversation_summary()
        print(f"✅ Companion ready!")
        print(f"   Mode: {summary['conversation_mode']}")
        print(f"   Readiness: {summary['companion_readiness']:.1%}")
        
        # Test web service registration
        print("\n2️⃣ Testing web service registration...")
        companion.register_web_service(ServiceType.CLAUDE, {"session_token": "mock_claude_session"})
        companion.register_web_service(ServiceType.GEMINI, {"session_token": "mock_gemini_session"})
        print("✅ Web services registered with companion")
        
        # Test prompt optimization
        print("\n3️⃣ Testing prompt optimization...")
        test_query = "Extract key information about AI companies from recent news"
        optimized_prompts = companion.optimize_prompt_for_web_services(
            test_query,
            [ServiceType.CLAUDE, ServiceType.GEMINI],
            '{"companies": [], "news_items": []}'
        )
        print(f"✅ Generated optimized prompts for {len(optimized_prompts)} services")
        
        # Test web mode switching
        print("\n4️⃣ Testing web mode switching...")
        mode_result = companion.switch_to_web_mode()
        print(f"✅ {mode_result}")
        
        # Test analytics
        print("\n5️⃣ Testing web service analytics...")
        analytics = companion.get_web_service_analytics()
        print(f"✅ Analytics retrieved:")
        print(f"   Total requests: {analytics['summary']['total_requests']}")
        print(f"   Active services: {analytics['summary']['active_services']}")
        
        # Test recommendations
        print("\n6️⃣ Testing recommendations...")
        recommendations = companion.get_web_service_recommendations()
        print(f"✅ Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations[:2], 1):
            print(f"   {i}. {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Companion integration test failed: {e}")
        traceback.print_exc()
        return False


def test_end_to_end_workflow():
    """Test end-to-end Phase 3 workflow"""
    print("\n🔄 Testing End-to-End Workflow")
    print("=" * 40)
    
    try:
        # Initialize companion
        companion = CompanionInterface(user_id="e2e_test")
        
        # Setup web services
        print("\n1️⃣ Setting up web services...")
        companion.register_web_service(ServiceType.CLAUDE, {"mock": "session"})
        companion.register_web_service(ServiceType.GEMINI, {"mock": "session"})
        
        # Switch to web mode
        companion.switch_to_web_mode()
        print("✅ Web mode activated")
        
        # Test intelligent query (mock execution)
        print("\n2️⃣ Testing intelligent query processing...")
        query = "What are the latest trends in artificial intelligence?"
        
        # This would normally execute web requests, but we'll test the setup
        optimized = companion.optimize_prompt_for_web_services(
            query,
            [ServiceType.CLAUDE, ServiceType.GEMINI],
            '{"trends": [], "analysis": "", "sources": []}'
        )
        print(f"✅ Query optimized for {len(optimized)} services")
        
        # Test memory integration
        print("\n3️⃣ Testing memory integration...")
        response = companion.process_companion_input(
            "I want to use web services for better research capabilities"
        )
        print(f"✅ Response generated:")
        print(f"   Type: {response.response_type}")
        print(f"   Content preview: {response.content[:100]}...")
        
        # Final analytics
        print("\n4️⃣ Final system analytics...")
        analytics = companion.get_web_service_analytics()
        recommendations = companion.get_web_service_recommendations()
        
        print(f"✅ End-to-end workflow completed!")
        print(f"   Processed requests: {analytics['summary']['total_requests']}")
        print(f"   System recommendations: {len(recommendations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run comprehensive Phase 3 tests"""
    print("🚀 Phase 3 - Machine-Language Communication Tests")
    print("=" * 60)
    
    test_results = {
        "web_dispatcher": False,
        "ml_optimizer": False,
        "parallel_manager": False,
        "companion_integration": False,
        "end_to_end_workflow": False
    }
    
    # Run all tests
    test_results["web_dispatcher"] = test_web_dispatcher()
    test_results["ml_optimizer"] = test_ml_optimizer()
    test_results["parallel_manager"] = test_parallel_manager()
    test_results["companion_integration"] = test_companion_integration()
    test_results["end_to_end_workflow"] = test_end_to_end_workflow()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Phase 3 Test Results Summary")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All Phase 3 tests passed! Machine-Language Communication is ready!")
        print("🌐 Web dispatcher, ML optimizer, and parallel manager operational")
        print("🤖 Companion system enhanced with web service capabilities")
    else:
        print(f"\n⚠️ {total-passed} test(s) failed. Review issues above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")