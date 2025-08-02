#!/usr/bin/env python3
"""
Samay v3 - Session Manager
==========================
Main orchestrator that combines all components for persistent sessions
Based on Comprehensive Implementation Plan
"""

import os
import time
from pathlib import Path
from typing import List
from dotenv import load_dotenv

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.drivers import SamayDriverFactory
from orchestrator.validators import SessionValidator
from orchestrator.prompt_dispatcher import PromptDispatcher, PromptRequest
from orchestrator.response_aggregator import ResponseAggregator
# from otp_service.gmail_fetcher import GmailOTPFetcher  # Commented out to avoid dependency issues

load_dotenv()


class SamaySessionManager:
    """Main session manager that orchestrates all components"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.driver_factory = SamayDriverFactory(base_dir)
        self.validator = SessionValidator()
        # self.otp_fetcher = GmailOTPFetcher()  # Commented out to avoid dependency issues
        self.prompt_dispatcher = PromptDispatcher(base_dir)
        self.response_aggregator = ResponseAggregator(str(self.base_dir / "reports"))
        
        print("🚀 Samay v3 - Session Manager Initialized")
        print(f"📁 Base directory: {self.base_dir.absolute()}")
        print("🤖 Multi-agent prompt dispatcher ready")
        print("📊 Advanced response aggregator ready")
    
    def setup_service(self, service: str) -> bool:
        """
        Complete setup for a service (one-time)
        
        1. Initialize UC profile
        2. Handle login with OTP automation
        3. Validate session persistence
        """
        print(f"\n🔧 Setting up {service.title()}")
        print("=" * 50)
        
        # Check if already set up
        profiles = self.driver_factory.list_profiles()
        if profiles[service]["ready"]:
            print(f"✅ {service} profile already exists")
            
            # Test if it's still authenticated
            try:
                with self.driver_factory.get_driver(service, headed=False) as driver:
                    if self.validator.is_logged_in(driver, service):
                        print(f"✅ {service} is already authenticated!")
                        return True
                    else:
                        print(f"⚠️  {service} profile exists but session expired")
            except Exception as e:
                print(f"⚠️  Error testing {service} profile: {e}")
        
        # Initialize profile
        print(f"\n📋 Step 1: Initialize {service} Profile")
        if not self.driver_factory.initialize_profile(service):
            print(f"❌ Failed to initialize {service} profile")
            return False
        
        # Validate authentication
        print(f"\n📋 Step 2: Validate {service} Authentication")
        try:
            with self.driver_factory.get_driver(service, headed=False) as driver:
                if self.validator.is_logged_in(driver, service):
                    print(f"✅ {service} setup complete!")
                    return True
                else:
                    print(f"❌ {service} authentication validation failed")
                    return False
        except Exception as e:
            print(f"❌ {service} validation error: {e}")
            return False
    
    def ensure_service_ready(self, service: str, auto_login: bool = True) -> bool:
        """
        Ensure a service is ready for use
        
        Handles both profile initialization and authentication
        """
        print(f"\n🛡️  Ensuring {service} is ready...")
        
        # Check profile exists
        profiles = self.driver_factory.list_profiles()
        if not profiles[service]["ready"]:
            print(f"❌ {service} profile not initialized")
            if auto_login:
                print(f"🔧 Auto-initializing {service} profile...")
                return self.setup_service(service)
            else:
                return False
        
        # Check authentication
        try:
            with self.driver_factory.get_driver(service, headed=False) as driver:
                if self.validator.is_logged_in(driver, service):
                    print(f"✅ {service} ready!")
                    return True
                else:
                    print(f"🔑 {service} needs authentication")
                    if auto_login:
                        return self.validator.ensure_authenticated(driver, service)
                    else:
                        return False
        except Exception as e:
            print(f"❌ Error checking {service}: {e}")
            return False
    
    def health_check(self) -> dict:
        """Perform health check on all services"""
        print("\n🏥 Samay Health Check")
        print("=" * 40)
        
        results = self.validator.health_check_all(self.driver_factory)
        
        # Summary
        authenticated = sum(1 for r in results.values() if r["status"] == "authenticated")
        total = len(results)
        
        print(f"\n📊 Summary: {authenticated}/{total} services ready")
        
        return results
    
    def interactive_setup(self) -> None:
        """Interactive setup wizard"""
        print("\n🧙‍♂️ Samay Setup Wizard")
        print("=" * 40)
        
        services = list(self.driver_factory.services.keys())
        profiles = self.driver_factory.list_profiles()
        
        print("\n📋 Current Status:")
        for service in services:
            status = "✅ Ready" if profiles[service]["ready"] else "❌ Not setup"
            print(f"   {service.title()}: {status}")
        
        print("\n🎛️  Setup Options:")
        print("1. Setup all services")
        print("2. Setup specific service")
        print("3. Test existing setups")
        print("4. Health check")
        print("5. Reset service (clear profile)")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            print("\n🚀 Setting up all services...")
            for service in services:
                success = self.setup_service(service)
                if not success:
                    print(f"⚠️  {service} setup incomplete")
                print()  # Add spacing
        
        elif choice == "2":
            print("\nAvailable services:")
            for i, service in enumerate(services, 1):
                status = "✅" if profiles[service]["ready"] else "❌"
                print(f"   {i}. {service.title()} {status}")
            
            try:
                service_num = int(input("Select service: "))
                if 1 <= service_num <= len(services):
                    service = services[service_num - 1]
                    self.setup_service(service)
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
        
        elif choice == "3":
            print("\n🧪 Testing existing setups...")
            for service in services:
                if profiles[service]["ready"]:
                    try:
                        with self.driver_factory.get_driver(service, headed=False) as driver:
                            if self.validator.is_logged_in(driver, service):
                                print(f"✅ {service}: Working")
                            else:
                                print(f"❌ {service}: Authentication failed")
                    except Exception as e:
                        print(f"❌ {service}: Error - {e}")
                else:
                    print(f"⚠️  {service}: Not setup")
        
        elif choice == "4":
            self.health_check()
        
        elif choice == "5":
            print("\nAvailable services to reset:")
            ready_services = [s for s in services if profiles[s]["ready"]]
            
            if not ready_services:
                print("❌ No services to reset")
                return
            
            for i, service in enumerate(ready_services, 1):
                print(f"   {i}. {service.title()}")
            
            try:
                service_num = int(input("Select service to reset: "))
                if 1 <= service_num <= len(ready_services):
                    service = ready_services[service_num - 1]
                    
                    print(f"⚠️  This will delete the {service} profile and all saved data")
                    confirm = input("Are you sure? (y/N): ").strip().lower()
                    
                    if confirm in ['y', 'yes']:
                        import shutil
                        profile_path = Path(self.driver_factory.services[service]["profile_dir"])
                        if profile_path.exists():
                            shutil.rmtree(profile_path)
                            print(f"✅ {service} profile reset")
                        else:
                            print(f"⚠️  {service} profile directory not found")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
        
        else:
            print("❌ Invalid choice")
    
    def quick_test(self, service: str) -> bool:
        """Quick test of a service"""
        print(f"\n🧪 Quick test: {service}")
        
        if not self.ensure_service_ready(service, auto_login=False):
            print(f"❌ {service} not ready")
            return False
        
        try:
            with self.driver_factory.get_driver(service, headed=True) as driver:
                config = self.driver_factory.services[service]
                driver.open(config["url"])
                
                print(f"📍 URL: {driver.get_current_url()}")
                print(f"📄 Title: {driver.get_title()}")
                
                if self.validator.is_logged_in(driver, service):
                    print(f"✅ {service} is working correctly!")
                    input("Press Enter to close browser...")
                    return True
                else:
                    print(f"❌ {service} authentication check failed")
                    return False
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def get_status_summary(self) -> dict:
        """Get a summary of all service statuses"""
        profiles = self.driver_factory.list_profiles()
        
        summary = {
            "total_services": len(profiles),
            "ready_services": sum(1 for p in profiles.values() if p["ready"]),
            "services": {}
        }
        
        for service, info in profiles.items():
            summary["services"][service] = {
                "ready": info["ready"],
                "profile_path": info["profile_path"]
            }
        
        return summary
    
    def multi_agent_query(self, prompt: str, services: List[str] = None, timeout: int = 60, confidential: bool = False) -> dict:
        """
        Send a prompt to multiple AI services in parallel
        
        Args:
            prompt: The prompt to send
            services: List of services to query (default: all available)
            timeout: Timeout per service in seconds
            confidential: Use local LLM only for confidential data
            
        Returns:
            Aggregated response from all services or local LLM
        """
        if services is None and not confidential:
            services = list(self.driver_factory.services.keys())
        elif confidential:
            services = ["local_phi3"]  # Override for confidential mode
        
        # Create prompt request
        request = PromptRequest(
            prompt=prompt,
            services=services,
            timeout=timeout,
            retry_count=2,
            confidential=confidential
        )
        
        # Dispatch to all services
        response = self.prompt_dispatcher.dispatch_prompt(request)
        
        # Generate comprehensive reports
        reports = self.response_aggregator.generate_full_report_suite(response)
        
        # Also save JSON response to logs (for backward compatibility)
        self.prompt_dispatcher.save_response(response)
        
        return {
            "request_id": response.request_id,
            "prompt": response.prompt,
            "total_time": response.total_execution_time,
            "successful_services": response.successful_services,
            "failed_services": response.failed_services,
            "reports": reports,
            "responses": [
                {
                    "service": r.service,
                    "success": r.success,
                    "response": r.response,
                    "error": r.error_message if not r.success else None,
                    "execution_time": r.execution_time
                }
                for r in response.responses
            ]
        }


def main():
    """Main interface for Samay Session Manager"""
    print("🚀 Samay v3 - Multi-Agent Session Manager")
    print("=" * 60)
    print("🔬 Research-based solution for persistent AI sessions")
    print("🛡️  Anti-bot protection + Profile persistence + OTP automation")
    
    # Change to the samay-v3 directory
    os.chdir(Path(__file__).parent.parent)
    
    manager = SamaySessionManager()
    
    # Show current status
    summary = manager.get_status_summary()
    print(f"\n📊 Status: {summary['ready_services']}/{summary['total_services']} services ready")
    
    print("\n🎛️  Main Options:")
    print("1. 🔧 Setup wizard (first-time setup)")
    print("2. 🏥 Health check all services")
    print("3. 🧪 Quick test specific service")
    print("4. 🤖 Multi-agent query (parallel dispatch)")
    print("5. 🔒 Confidential query (local LLM only)")
    print("6. 📋 Show detailed status")
    print("7. ❌ Exit")
    
    while True:
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            manager.interactive_setup()
            break
        
        elif choice == "2":
            manager.health_check()
            break
        
        elif choice == "3":
            services = list(manager.driver_factory.services.keys())
            print("\nAvailable services:")
            for i, service in enumerate(services, 1):
                print(f"   {i}. {service.title()}")
            
            try:
                service_num = int(input("Select service: "))
                if 1 <= service_num <= len(services):
                    service = services[service_num - 1]
                    manager.quick_test(service)
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
            break
        
        elif choice == "4":
            # Multi-agent query
            print("\n🤖 Multi-Agent Query Mode")
            print("=" * 40)
            
            # Check service status
            summary = manager.get_status_summary()
            ready_services = [s for s, info in summary["services"].items() if info["ready"]]
            
            if not ready_services:
                print("❌ No services are ready. Run setup wizard first.")
                continue
            
            print(f"✅ {len(ready_services)} services ready: {', '.join(ready_services)}")
            
            # Get prompt from user
            prompt = input("\n📝 Enter your prompt: ").strip()
            if not prompt:
                print("❌ Empty prompt. Cancelling.")
                continue
            
            # Ask which services to use
            print(f"\n🎯 Select services (default: all {len(ready_services)} services):")
            for i, service in enumerate(ready_services, 1):
                print(f"   {i}. {service.title()}")
            print(f"   {len(ready_services) + 1}. Use all services")
            
            service_choice = input(f"Select services (1-{len(ready_services) + 1}, or press Enter for all): ").strip()
            
            if service_choice and service_choice != str(len(ready_services) + 1):
                try:
                    service_num = int(service_choice)
                    if 1 <= service_num <= len(ready_services):
                        selected_services = [ready_services[service_num - 1]]
                    else:
                        print("❌ Invalid selection, using all services")
                        selected_services = ready_services
                except ValueError:
                    print("❌ Invalid input, using all services")
                    selected_services = ready_services
            else:
                selected_services = ready_services
            
            print(f"\n🚀 Dispatching to: {', '.join(selected_services)}")
            
            # Execute multi-agent query
            try:
                result = manager.multi_agent_query(prompt, selected_services)
                
                # Display results
                print(f"\n📊 Results (ID: {result['request_id']}):")
                print(f"⏱️  Total time: {result['total_time']:.1f}s")
                print(f"✅ Success: {result['successful_services']}")
                print(f"❌ Failed: {result['failed_services']}")
                
                for response in result["responses"]:
                    status = "✅" if response["success"] else "❌"
                    print(f"\n{status} {response['service'].title()} ({response['execution_time']:.1f}s):")
                    
                    if response["success"]:
                        # Truncate long responses for display
                        content = response["response"][:300] + "..." if len(response["response"]) > 300 else response["response"]
                        print(f"   {content}")
                    else:
                        print(f"   Error: {response['error']}")
                
                print(f"\n📄 Reports generated:")
                print(f"   📊 JSON Summary: {result['reports']['json_summary']}")
                print(f"   📝 Markdown Report: {result['reports']['markdown_report']}")
                print(f"   💾 Raw JSON: logs/response_{result['request_id']}.json")
                
            except Exception as e:
                print(f"❌ Multi-agent query failed: {e}")
            
            break
        
        elif choice == "5":
            # Confidential query (local LLM only)
            print("\n🔒 Confidential Query Mode")
            print("=" * 40)
            print("🏠 Using local Phi-3-Mini model only")
            print("🔐 Data stays on your device")
            
            # Check if local LLM is available
            try:
                # Test local LLM availability
                from orchestrator.local_llm import LocalLLMClient
                local_client = LocalLLMClient()
                if not local_client.is_available():
                    print("❌ Local LLM not available. Check if Ollama is running with phi3:mini model.")
                    continue
            except Exception as e:
                print(f"❌ Local LLM error: {e}")
                continue
            
            # Get confidential prompt
            prompt = input("\n📝 Enter your confidential prompt: ").strip()
            if not prompt:
                print("❌ Empty prompt. Cancelling.")
                continue
            
            # Select data type for processing
            print(f"\n🎯 Select processing type:")
            print("1. General assistant")
            print("2. Grammar correction")
            print("3. Text summarization")
            print("4. Data analysis")
            print("5. Text refinement")
            
            data_type_choice = input("Select type (1-5, or Enter for general): ").strip()
            data_types = {
                "1": "general", "2": "grammar", "3": "summarization", 
                "4": "analysis", "5": "refinement"
            }
            data_type = data_types.get(data_type_choice, "general")
            
            print(f"\n🚀 Processing confidentially with {data_type} mode...")
            
            # Execute confidential query
            try:
                result = manager.multi_agent_query(prompt, confidential=True)
                
                # Display results
                print(f"\n📊 Confidential Results (ID: {result['request_id']}):")
                print(f"⏱️  Processing time: {result['total_time']:.1f}s")
                print(f"🧠 Model: Phi-3-Mini (local)")
                
                for response in result["responses"]:
                    status = "✅" if response["success"] else "❌"
                    print(f"\n{status} Local LLM ({response['execution_time']:.1f}s):")
                    
                    if response["success"]:
                        print(f"   {response['response']}")
                    else:
                        print(f"   Error: {response['error']}")
                
                print(f"\n📄 Reports generated:")
                print(f"   📊 JSON Summary: {result['reports']['json_summary']}")
                print(f"   📝 Markdown Report: {result['reports']['markdown_report']}")
                print("🔒 All data processed locally - no cloud services used")
                
            except Exception as e:
                print(f"❌ Confidential query failed: {e}")
            
            break
        
        elif choice == "6":
            summary = manager.get_status_summary()
            print(f"\n📋 Detailed Status:")
            print("=" * 30)
            
            for service, info in summary["services"].items():
                status = "✅ Ready" if info["ready"] else "❌ Not setup"
                print(f"   {service.title()}: {status}")
                print(f"      Path: {info['profile_path']}")
            
            print(f"\n📊 Summary: {summary['ready_services']}/{summary['total_services']} ready")
            break
        
        elif choice == "7":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice, please try again")


if __name__ == "__main__":
    main()