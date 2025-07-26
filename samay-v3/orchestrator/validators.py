#!/usr/bin/env python3
"""
Samay v3 - Session Validators
============================
Detects if sessions are still authenticated and handles login flows
Based on Comprehensive Implementation Plan
"""

import os
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()


class SessionValidator:
    """Validates and maintains authentication sessions"""
    
    def __init__(self):
        self.service_configs = {
            "claude": {
                "test_url": "https://claude.ai/chats",
                "auth_selectors": [
                    "[data-testid='user-menu']",
                    ".user-avatar", 
                    "[aria-label='User menu']",
                    "button[data-testid='sidebar-user-menu-button']"
                ],
                "login_indicators": ["login", "signin", "auth"],
                "timeout": 10
            },
            "gemini": {
                "test_url": "https://gemini.google.com/app",
                "auth_selectors": [
                    "[data-testid='user-button']",
                    ".gb_d",  # Google account button
                    "[aria-label='Google Account']",
                    "img[alt*='Profile']"
                ],
                "login_indicators": ["accounts.google.com", "signin"],
                "timeout": 8
            },
            "perplexity": {
                "test_url": "https://www.perplexity.ai",
                "auth_selectors": [
                    "[data-testid='user-avatar']",
                    ".user-menu",
                    "[aria-label='User menu']",
                    "img[alt*='User']"
                ],
                "login_indicators": ["signin", "login"],
                "timeout": 8
            }
        }
    
    def is_logged_in(self, driver, service: str) -> bool:
        """
        Check if user is logged in to the specified service
        
        Uses multiple validation strategies:
        1. URL-based redirect detection
        2. DOM element presence
        3. Title/content analysis
        """
        if service not in self.service_configs:
            raise ValueError(f"Unknown service: {service}")
        
        config = self.service_configs[service]
        
        try:
            print(f"🔍 Validating {service} session...")
            
            # Navigate to authenticated page
            driver.open(config["test_url"])
            time.sleep(3)  # Allow page to load
            
            current_url = driver.get_current_url().lower()
            print(f"📍 Current URL: {current_url}")
            
            # Strategy 1: Check for login redirect
            for login_indicator in config["login_indicators"]:
                if login_indicator in current_url:
                    print(f"❌ Detected login redirect: {login_indicator}")
                    return False
            
            # Strategy 3: Service-specific checks (moved up for faster detection)
            if service == "claude":
                # Check for authenticated URLs first (most reliable)
                if any(path in current_url for path in ["/new", "/chats", "/chat"]):
                    print("✅ Claude authenticated (authenticated URL)")
                    return True
                
                # Claude shows user avatar when logged in
                page_title = driver.get_title().lower()
                if "claude" in page_title and "login" not in page_title:
                    print("✅ Claude authenticated (title check)")
                    return True
            
            elif service == "gemini":
                # Gemini redirects to accounts.google.com when not logged in
                if "accounts.google.com" not in current_url:
                    print("✅ Gemini authenticated (no Google redirect)")
                    return True
                    
            elif service == "perplexity":
                # Check for authenticated URLs first
                if current_url == "https://www.perplexity.ai/" and "signin" not in current_url:
                    print("✅ Perplexity authenticated (main page, no signin)")
                    return True
                
                # Perplexity shows different content when logged in
                try:
                    driver.wait_for_element_visible("nav", timeout=5)
                    print("✅ Perplexity authenticated (nav visible)")
                    return True
                except:
                    pass
            
            # Strategy 2: Look for authenticated user elements (fallback)
            for selector in config["auth_selectors"]:
                try:
                    driver.wait_for_element_visible(selector, timeout=config["timeout"])
                    print(f"✅ Found auth element: {selector}")
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            print(f"❌ No authentication indicators found for {service}")
            return False
            
        except Exception as e:
            print(f"❌ Session validation error for {service}: {e}")
            return False
    
    def wait_for_login(self, driver, service: str, max_attempts: int = 30) -> bool:
        """
        Wait for user to complete manual login
        
        Polls every 5 seconds to check if login is complete
        """
        print(f"⏳ Waiting for {service} login completion...")
        
        for attempt in range(max_attempts):
            if self.is_logged_in(driver, service):
                print(f"✅ {service} login detected!")
                return True
            
            if attempt < max_attempts - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts} - checking again in 5s...")
                time.sleep(5)
        
        print(f"❌ Login timeout for {service} after {max_attempts * 5} seconds")
        return False
    
    def perform_login_flow(self, driver, service: str) -> bool:
        """
        Handle the login flow for a service
        
        For now, this guides the user through manual login.
        TODO: Add OTP automation
        """
        if service not in self.service_configs:
            raise ValueError(f"Unknown service: {service}")
        
        print(f"\n🔑 {service.title()} Login Required")
        print("=" * 40)
        
        if service == "claude":
            return self._claude_login_flow(driver)
        elif service == "gemini":
            return self._gemini_login_flow(driver)
        elif service == "perplexity":
            return self._perplexity_login_flow(driver)
        else:
            return self._generic_login_flow(driver, service)
    
    def _claude_login_flow(self, driver) -> bool:
        """Handle Claude-specific login flow"""
        print("📋 Claude Login Instructions:")
        print("   1. Navigate to login page")
        print("   2. Enter your email address")
        print("   3. Check your email for OTP code")
        print("   4. Enter the 6-digit code")
        print("   5. Complete login process")
        
        try:
            # Navigate to login
            driver.open("https://claude.ai/login")
            time.sleep(2)
            
            print(f"\n🌐 Opened Claude login page")
            print(f"📍 Current URL: {driver.get_current_url()}")
            
            # Wait for user to complete login
            return self.wait_for_login(driver, "claude", max_attempts=36)  # 3 minutes
            
        except Exception as e:
            print(f"❌ Claude login flow failed: {e}")
            return False
    
    def _gemini_login_flow(self, driver) -> bool:
        """Handle Gemini-specific login flow"""
        print("📋 Gemini Login Instructions:")
        print("   1. Navigate to Gemini")
        print("   2. Click 'Sign in' or 'Continue with Google'")
        print("   3. Enter Google credentials")
        print("   4. Complete any 2FA if required")
        
        try:
            driver.open("https://gemini.google.com")
            time.sleep(2)
            
            print(f"\n🌐 Opened Gemini page")
            
            return self.wait_for_login(driver, "gemini", max_attempts=36)
            
        except Exception as e:
            print(f"❌ Gemini login flow failed: {e}")
            return False
    
    def _perplexity_login_flow(self, driver) -> bool:
        """Handle Perplexity-specific login flow"""
        print("📋 Perplexity Login Instructions:")
        print("   1. Navigate to Perplexity")
        print("   2. Click 'Sign in'")
        print("   3. Choose your preferred login method")
        print("   4. Complete authentication")
        
        try:
            driver.open("https://www.perplexity.ai")
            time.sleep(2)
            
            print(f"\n🌐 Opened Perplexity page")
            
            return self.wait_for_login(driver, "perplexity", max_attempts=36)
            
        except Exception as e:
            print(f"❌ Perplexity login flow failed: {e}")
            return False
    
    def _generic_login_flow(self, driver, service: str) -> bool:
        """Generic login flow for unknown services"""
        print(f"📋 {service.title()} Login Instructions:")
        print("   1. Complete login in the browser window")
        print("   2. Ensure you reach the main authenticated interface")
        print("   3. The system will detect when login is complete")
        
        return self.wait_for_login(driver, service)
    
    def ensure_authenticated(self, driver, service: str) -> bool:
        """
        Ensure the driver is authenticated for the service
        
        If not authenticated, attempts to login
        Returns True if authenticated, False if login failed
        """
        print(f"\n🛡️  Ensuring {service} authentication...")
        
        if self.is_logged_in(driver, service):
            print(f"✅ {service} already authenticated!")
            return True
        
        print(f"🔑 {service} authentication required")
        return self.perform_login_flow(driver, service)
    
    def ensure_service_ready(self, service: str, driver_factory) -> bool:
        """
        Ensure a service is ready for use
        
        Checks if profile exists and authentication is valid
        """
        # Check profile exists
        profiles = driver_factory.list_profiles()
        if not profiles[service]["ready"]:
            print(f"❌ {service} profile not initialized")
            return False
        
        # Check authentication
        try:
            with driver_factory.get_driver(service, headed=False) as driver:
                if self.is_logged_in(driver, service):
                    return True
                else:
                    print(f"🔑 {service} needs authentication")
                    return False
        except Exception as e:
            print(f"❌ Error checking {service}: {e}")
            return False

    def health_check_all(self, driver_factory) -> dict:
        """
        Perform health check on all service profiles
        
        Returns dict with service status
        """
        results = {}
        
        print("\n🏥 Health Check: All Services")
        print("=" * 40)
        
        for service in driver_factory.services.keys():
            try:
                print(f"\n🔍 Checking {service}...")
                
                # Check if profile exists
                profiles = driver_factory.list_profiles()
                if not profiles[service]["ready"]:
                    results[service] = {
                        "status": "not_initialized",
                        "message": "Profile not initialized"
                    }
                    print(f"❌ {service}: Profile not initialized")
                    continue
                
                # Test authentication
                with driver_factory.get_driver(service, headed=False) as driver:
                    if self.is_logged_in(driver, service):
                        results[service] = {
                            "status": "authenticated", 
                            "message": "Session active"
                        }
                        print(f"✅ {service}: Authenticated")
                    else:
                        results[service] = {
                            "status": "needs_login",
                            "message": "Session expired"
                        }
                        print(f"⚠️  {service}: Needs login")
                        
            except Exception as e:
                results[service] = {
                    "status": "error",
                    "message": str(e)
                }
                print(f"❌ {service}: Error - {e}")
        
        return results


def main():
    """Test the session validator"""
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from orchestrator.drivers import SamayDriverFactory
    
    validator = SessionValidator()
    factory = SamayDriverFactory()
    
    print("🚀 Samay v3 - Session Validator Test")
    print("=" * 50)
    
    print("\n🎛️  Options:")
    print("1. Health check all services")
    print("2. Test specific service authentication")
    print("3. Force login flow for service")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        results = validator.health_check_all(factory)
        
        print(f"\n📊 Health Check Summary:")
        print("=" * 30)
        for service, info in results.items():
            status = info["status"]
            emoji = "✅" if status == "authenticated" else "⚠️" if status == "needs_login" else "❌"
            print(f"   {service.title()}: {emoji} {info['message']}")
    
    elif choice == "2":
        services = list(factory.services.keys())
        print("\nAvailable services:")
        for i, service in enumerate(services, 1):
            print(f"   {i}. {service.title()}")
        
        try:
            service_num = int(input("Select service: "))
            if 1 <= service_num <= len(services):
                service = services[service_num - 1]
                
                with factory.get_driver(service) as driver:
                    if validator.is_logged_in(driver, service):
                        print(f"✅ {service} is authenticated!")
                    else:
                        print(f"❌ {service} is NOT authenticated")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    elif choice == "3":
        services = list(factory.services.keys())
        print("\nAvailable services:")
        for i, service in enumerate(services, 1):
            print(f"   {i}. {service.title()}")
        
        try:
            service_num = int(input("Select service: "))
            if 1 <= service_num <= len(services):
                service = services[service_num - 1]
                
                with factory.get_driver(service) as driver:
                    validator.perform_login_flow(driver, service)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()