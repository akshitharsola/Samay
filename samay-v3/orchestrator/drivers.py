#!/usr/bin/env python3
"""
Samay v3 - Driver Factory
=========================
Creates and manages UC Mode drivers with persistent profiles
Based on Comprehensive Implementation Plan
"""

import os
import time
import random
from contextlib import contextmanager
from seleniumbase import Driver
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class SamayDriverFactory:
    """Factory for creating persistent, anti-bot resistant drivers"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.profiles_dir = self.base_dir / "profiles"
        
        # Service configurations
        self.services = {
            "claude": {
                "url": "https://claude.ai",
                "login_url": "https://claude.ai/login",
                "profile_dir": str(self.profiles_dir / "claude"),
                "proxy": os.getenv("CLAUDE_PROXY")
            },
            "gemini": {
                "url": "https://gemini.google.com", 
                "login_url": "https://accounts.google.com/signin",
                "profile_dir": str(self.profiles_dir / "gemini"),
                "proxy": os.getenv("GEMINI_PROXY")
            },
            "perplexity": {
                "url": "https://www.perplexity.ai",
                "login_url": "https://www.perplexity.ai/signin", 
                "profile_dir": str(self.profiles_dir / "perplexity"),
                "proxy": os.getenv("PERPLEXITY_PROXY")
            }
        }
    
    def clean_lock_files(self, service: str) -> None:
        """Remove stale Chrome lock files that prevent profile reuse"""
        profile_dir = Path(self.services[service]["profile_dir"])
        
        if not profile_dir.exists():
            return
        
        # Remove singleton lock files
        for lock_pattern in ["Singleton*", "*.lock"]:
            for lock_file in profile_dir.rglob(lock_pattern):
                try:
                    lock_file.unlink()
                    print(f"🧹 Removed stale lock: {lock_file}")
                except OSError:
                    pass  # File might be in use
    
    @contextmanager
    def get_driver(self, service: str, headed: bool = None):
        """
        Create a UC Mode driver with persistent profile
        
        Args:
            service: One of 'claude', 'gemini', 'perplexity'
            headed: Override headless mode (None = use env setting)
        """
        if service not in self.services:
            raise ValueError(f"Unknown service: {service}. Available: {list(self.services.keys())}")
        
        config = self.services[service]
        
        # Clean any stale lock files
        self.clean_lock_files(service)
        
        # Ensure profile directory exists
        os.makedirs(config["profile_dir"], exist_ok=True)
        
        # Driver options
        driver_opts = {
            "uc": True,  # Enable UC Mode for anti-bot protection
            "user_data_dir": config["profile_dir"],  # Persistent profile
            "headed": headed if headed is not None else not os.getenv("HEADLESS_MODE", "false").lower() == "true"
        }
        
        # Add proxy if configured
        if config["proxy"]:
            driver_opts["proxy"] = config["proxy"]
        
        print(f"🚀 Starting {service} driver with profile: {config['profile_dir']}")
        
        driver = Driver(**driver_opts)
        
        try:
            # Add human-like startup delay
            startup_delay = random.uniform(1.8, 4.2)
            print(f"⏳ Human-like startup delay: {startup_delay:.1f}s")
            time.sleep(startup_delay)
            
            yield driver
            
        finally:
            print(f"🛑 Closing {service} driver")
            driver.quit()
            
            # Allow Chrome to close cleanly
            time.sleep(2)
    
    def initialize_profile(self, service: str) -> bool:
        """
        Initialize a fresh UC profile for a service (one-time setup)
        
        This creates the profile directory and opens the service for manual login.
        Only needs to be run once per service.
        """
        if service not in self.services:
            print(f"❌ Unknown service: {service}")
            return False
        
        config = self.services[service]
        
        print(f"\n🔧 Initializing {service.title()} Profile")
        print("=" * 50)
        print(f"📁 Profile will be created at: {config['profile_dir']}")
        print("⚠️  This is a ONE-TIME setup per service")
        
        try:
            with self.get_driver(service, headed=True) as driver:
                print(f"🌐 Opening {config['url']}...")
                driver.open(config["url"])
                
                print(f"\n🔑 Manual Login Required")
                print("=" * 30)
                print(f"📋 Instructions:")
                print(f"   1. Complete login in the {service} browser window")
                print(f"   2. UC Mode will handle anti-bot detection")
                print(f"   3. Once logged in, your session will be saved to the profile")
                print(f"   4. Future runs will automatically use this profile")
                print(f"   5. Come back here when login is complete")
                
                input(f"\nPress Enter when {service} login is complete: ")
                
                # Verify profile was created
                profile_path = Path(config["profile_dir"])
                default_profile = profile_path / "Default"
                
                if default_profile.exists():
                    print(f"✅ Profile created successfully!")
                    print(f"📁 Profile location: {config['profile_dir']}")
                    
                    # List some key profile files to confirm
                    key_files = ["Cookies", "Local Storage", "Preferences"]
                    found_files = []
                    for key_file in key_files:
                        if (default_profile / key_file).exists():
                            found_files.append(key_file)
                    
                    if found_files:
                        print(f"🔍 Profile contains: {', '.join(found_files)}")
                    
                    return True
                else:
                    print(f"❌ Profile creation failed - Default directory not found")
                    return False
                    
        except Exception as e:
            print(f"❌ Profile initialization failed: {e}")
            return False
    
    def list_profiles(self) -> dict:
        """List status of all service profiles"""
        status = {}
        
        for service, config in self.services.items():
            profile_path = Path(config["profile_dir"])
            default_path = profile_path / "Default"
            
            status[service] = {
                "profile_exists": profile_path.exists(),
                "default_exists": default_path.exists(),
                "profile_path": str(profile_path),
                "ready": profile_path.exists() and default_path.exists()
            }
        
        return status


def main():
    """Test the driver factory"""
    factory = SamayDriverFactory()
    
    print("🚀 Samay v3 - Driver Factory Test")
    print("=" * 50)
    
    # Show profile status
    print("\n📊 Profile Status:")
    profiles = factory.list_profiles()
    for service, info in profiles.items():
        status = "✅ Ready" if info["ready"] else "❌ Not initialized"
        print(f"   {service.title()}: {status}")
    
    print("\n🎛️  Options:")
    print("1. Initialize new profile")
    print("2. Test existing profile")
    print("3. Show detailed profile info")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        print("\nAvailable services:")
        for i, service in enumerate(factory.services.keys(), 1):
            print(f"   {i}. {service.title()}")
        
        try:
            service_num = int(input("Select service: "))
            services = list(factory.services.keys())
            if 1 <= service_num <= len(services):
                service = services[service_num - 1]
                factory.initialize_profile(service)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    elif choice == "2":
        ready_services = [s for s, info in profiles.items() if info["ready"]]
        if not ready_services:
            print("❌ No profiles ready. Initialize profiles first.")
            return
        
        print("\nReady services:")
        for i, service in enumerate(ready_services, 1):
            print(f"   {i}. {service.title()}")
        
        try:
            service_num = int(input("Select service: "))
            if 1 <= service_num <= len(ready_services):
                service = ready_services[service_num - 1]
                print(f"\n🧪 Testing {service} profile...")
                
                with factory.get_driver(service) as driver:
                    config = factory.services[service]
                    driver.open(config["url"])
                    print(f"📍 Opened: {driver.get_current_url()}")
                    print(f"📄 Title: {driver.get_title()}")
                    
                    input("Press Enter to close browser...")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    elif choice == "3":
        print("\n📋 Detailed Profile Information:")
        for service, info in profiles.items():
            print(f"\n🔍 {service.title()}:")
            print(f"   Profile Path: {info['profile_path']}")
            print(f"   Profile Exists: {'✅' if info['profile_exists'] else '❌'}")
            print(f"   Default Exists: {'✅' if info['default_exists'] else '❌'}")
            print(f"   Status: {'✅ Ready' if info['ready'] else '❌ Needs initialization'}")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()