#!/usr/bin/env python3
"""
Quick Phase 2 Test
==================
Simple validation of Phase 2 components
"""

import sys
from pathlib import Path

# Add orchestrator to path
sys.path.append(str(Path(__file__).parent / "orchestrator"))

def test_imports():
    """Test that all Phase 2 components can be imported"""
    print("📦 Testing Phase 2 imports...")
    
    try:
        from brainstorm_engine import BrainstormEngine
        print("✅ BrainstormEngine imported")
        
        from version_control import VersionControl
        print("✅ VersionControl imported")
        
        from quality_assessment import QualityAssessor
        print("✅ QualityAssessor imported")
        
        from companion_interface import CompanionInterface
        print("✅ CompanionInterface imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_initialization():
    """Test basic initialization"""
    print("\n🔧 Testing initialization...")
    
    try:
        from companion_interface import CompanionInterface
        
        companion = CompanionInterface(user_id="quick_test")
        print("✅ CompanionInterface initialized")
        
        # Test that Phase 2 components are available
        if hasattr(companion, 'brainstorm_engine'):
            print("✅ BrainstormEngine component available")
        
        if hasattr(companion, 'version_control'):
            print("✅ VersionControl component available")
            
        if hasattr(companion, 'quality_assessor'):
            print("✅ QualityAssessor component available")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_basic_functionality():
    """Test basic Phase 2 functionality"""
    print("\n⚙️ Testing basic functionality...")
    
    try:
        from companion_interface import CompanionInterface
        
        companion = CompanionInterface(user_id="func_test")
        
        # Test mode switching
        result = companion.switch_conversation_mode("brainstorming")
        print(f"✅ Mode switching: {result[:50]}...")
        
        # Test suggestions (without full LLM)
        suggestions = companion.get_brainstorming_suggestions("test prompt")
        print(f"✅ Generated {len(suggestions)} suggestions")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False

def main():
    """Run quick Phase 2 validation"""
    print("🚀 Quick Phase 2 Validation")
    print("=" * 30)
    
    tests = [
        ("Imports", test_imports),
        ("Initialization", test_initialization),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 30)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Phase 2 components are working!")
    else:
        print("⚠️ Some issues detected")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")