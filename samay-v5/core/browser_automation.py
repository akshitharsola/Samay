"""
Samay v5 Browser Automation Framework
Fixed implementation using proven SeleniumBase UC Mode from v3
Single window with multiple tabs approach for all 4 AI services
"""

import asyncio
import logging
import json
import os
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from contextlib import contextmanager

try:
    from seleniumbase import Driver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("SeleniumBase not available - browser automation disabled")

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    LOGIN_REQUIRED = "login_required"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class AIService(Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"

@dataclass
class ServiceResponse:
    service: AIService
    response: str
    status: ServiceStatus
    timestamp: float
    processing_time: float
    metadata: Dict[str, Any]

class BrowserAutomationFramework:
    """Main browser automation framework using proven SeleniumBase UC Mode"""
    
    def __init__(self, profile_dir: str = None):
        if not SELENIUM_AVAILABLE:
            logger.warning("Browser automation disabled - SeleniumBase not available")
            return
            
        self.profile_dir = profile_dir or os.path.join(os.getcwd(), "profiles")
        self.driver = None
        self.service_configs = self._load_service_configs()
        self.tabs = {}  # Track which tab has which service
        
    async def initialize(self):
        """Initialize browser automation framework"""
        if not SELENIUM_AVAILABLE:
            logger.error("Cannot initialize - SeleniumBase not available")
            return False
            
        try:
            os.makedirs(self.profile_dir, exist_ok=True)
            logger.info("Browser automation framework initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize framework: {e}")
            return False
            
    def _load_service_configs(self) -> Dict[AIService, Dict[str, Any]]:
        """Load service-specific configurations with all 4 services"""
        return {
            AIService.CHATGPT: {
                "url": "https://chat.openai.com/",
                "selectors": {
                    "chat_input": "textarea[data-id='root']",
                    "send_button": "button[data-testid='send-button']",
                    "response_area": "div[data-message-author-role='assistant']",
                    "login_button": "button:contains('Log in')"
                },
                "wait_timeout": 30,
                "retry_attempts": 3
            },
            AIService.CLAUDE: {
                "url": "https://claude.ai/",
                "selectors": {
                    "chat_input": "div[contenteditable='true']",
                    "send_button": "button[aria-label*='Send']",
                    "response_area": "div[data-testid*='message']",
                    "login_button": "button:contains('Continue')"
                },
                "wait_timeout": 30,
                "retry_attempts": 3
            },
            AIService.GEMINI: {
                "url": "https://gemini.google.com/",
                "selectors": {
                    "chat_input": "rich-textarea textarea",
                    "send_button": "button[aria-label*='Send message']",
                    "response_area": "div[data-testid*='response']",
                    "login_button": "button:contains('Sign in')"
                },
                "wait_timeout": 30,
                "retry_attempts": 3
            },
            AIService.PERPLEXITY: {
                "url": "https://www.perplexity.ai/",
                "selectors": {
                    "chat_input": "textarea[placeholder*='Ask anything']",
                    "send_button": "button[aria-label*='Submit']",
                    "response_area": "div[class*='prose']",
                    "login_button": "button:contains('Sign Up')"
                },
                "wait_timeout": 30,
                "retry_attempts": 3
            }
        }
        
    def clean_lock_files(self) -> None:
        """Remove stale Chrome lock files that prevent profile reuse"""
        profile_path = Path(self.profile_dir)
        
        if not profile_path.exists():
            return
        
        # Remove singleton lock files
        for lock_pattern in ["Singleton*", "*.lock"]:
            for lock_file in profile_path.rglob(lock_pattern):
                try:
                    lock_file.unlink()
                    logger.info(f"🧹 Removed stale lock: {lock_file}")
                except OSError:
                    pass  # File might be in use
                    
    @contextmanager
    def get_driver(self, headed: bool = True):
        """Create UC Mode driver with persistent profile - proven approach from v3"""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("SeleniumBase not available")
            
        # Clean any stale lock files
        self.clean_lock_files()
        
        # Ensure profile directory exists
        os.makedirs(self.profile_dir, exist_ok=True)
        
        # Driver options using proven v3 configuration
        driver_opts = {
            "uc": True,  # Enable UC Mode for anti-bot protection
            "user_data_dir": self.profile_dir,  # Persistent profile
            "headed": headed  # Show browser for manual login
        }
        
        logger.info(f"🚀 Starting UC Mode driver with profile: {self.profile_dir}")
        
        driver = Driver(**driver_opts)
        
        try:
            # Add human-like startup delay
            startup_delay = random.uniform(1.8, 4.2)
            logger.info(f"⏳ Human-like startup delay: {startup_delay:.1f}s")
            time.sleep(startup_delay)
            
            yield driver
            
        finally:
            logger.info("🛑 Closing UC Mode driver")
            driver.quit()
            
            # Allow Chrome to close cleanly
            time.sleep(2)
            
    async def open_all_service_tabs(self) -> bool:
        """Open single window with 4 tabs for all AI services"""
        if not SELENIUM_AVAILABLE:
            logger.error("Browser automation not available")
            return False
            
        try:
            logger.info("🚀 Opening single window with 4 AI service tabs...")
            
            with self.get_driver(headed=True) as driver:
                self.driver = driver
                
                # Get list of services in preferred order
                services = [AIService.CHATGPT, AIService.CLAUDE, AIService.GEMINI, AIService.PERPLEXITY]
                
                for i, service in enumerate(services):
                    config = self.service_configs[service]
                    
                    if i == 0:
                        # First service - open in current tab
                        logger.info(f"🌐 Opening {service.value} in main window...")
                        driver.open(config["url"])
                        self.tabs[0] = service
                        
                        # Wait for page to load
                        await asyncio.sleep(random.uniform(3, 5))
                        logger.info(f"✅ {service.value} loaded in tab 1")
                        
                    else:
                        # Subsequent services - open in new tabs
                        logger.info(f"🌐 Opening {service.value} in new tab {i+1}...")
                        
                        # Use SeleniumBase method to open new tab
                        driver.open_new_tab()
                        await asyncio.sleep(2)  # Wait for tab to open
                        
                        # Navigate to service URL in new tab
                        driver.open(config["url"])
                        self.tabs[i] = service
                        
                        # Wait for page to load
                        await asyncio.sleep(random.uniform(3, 5))
                        logger.info(f"✅ {service.value} loaded in tab {i+1}")
                
                logger.info("🎯 All 4 services opened successfully!")
                logger.info("📋 Services opened:")
                for tab_num, service in self.tabs.items():
                    logger.info(f"   Tab {tab_num + 1}: {service.value}")
                
                # Check login status for each service
                await self._check_all_login_status()
                
                # Keep browser open for manual login
                logger.info("\n" + "="*60)
                logger.info("🔑 MANUAL LOGIN INSTRUCTIONS")
                logger.info("="*60)
                logger.info("1. Four tabs are now open with all AI services")
                logger.info("2. Go through each tab and login if required:")
                logger.info("   - Tab 1: ChatGPT (chat.openai.com)")
                logger.info("   - Tab 2: Claude (claude.ai)")
                logger.info("   - Tab 3: Gemini (gemini.google.com)")
                logger.info("   - Tab 4: Perplexity (perplexity.ai)")
                logger.info("3. UC Mode will handle anti-bot detection automatically")
                logger.info("4. Once logged in, sessions will persist for future use")
                logger.info("5. Browser will stay open for 10 minutes for login")
                logger.info("="*60)
                
                # Keep the browser open for 10 minutes (600 seconds) for login
                logger.info("⏰ Browser will stay open for 10 minutes for manual login...")
                logger.info("💡 You can close this terminal or press Ctrl+C to keep browser open longer")
                
                try:
                    # Wait for 10 minutes or until user interrupts
                    await asyncio.sleep(600)  # 10 minutes
                    logger.info("⏰ 10 minutes elapsed - browser will close")
                except KeyboardInterrupt:
                    logger.info("⚠️ User interrupted - keeping browser open indefinitely")
                    logger.info("🔒 Browser will stay open until manually closed")
                    try:
                        while True:
                            await asyncio.sleep(60)  # Keep alive
                    except KeyboardInterrupt:
                        logger.info("🛑 Final interrupt - browser will close")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to open service tabs: {e}")
            import traceback
            logger.error(f"Full error: {traceback.format_exc()}")
            return False
            
    async def _check_all_login_status(self):
        """Check login status for all services in their respective tabs"""
        if not self.driver:
            return
            
        logger.info("🔍 Checking login status for all services...")
        
        # Get current number of tabs
        tab_count = len(self.driver.window_handles)
        logger.info(f"📊 Found {tab_count} open tabs")
        
        for tab_index in range(tab_count):
            if tab_index in self.tabs:
                service = self.tabs[tab_index]
                
                try:
                    # Switch to tab
                    self.driver.switch_to.window(self.driver.window_handles[tab_index])
                    await asyncio.sleep(1)
                    
                    # Check if logged in
                    is_logged_in = await self._check_service_login_status(service)
                    status = "✅ Logged in" if is_logged_in else "🔑 Login required"
                    logger.info(f"   Tab {tab_index + 1} ({service.value}): {status}")
                    
                except Exception as e:
                    logger.warning(f"   Tab {tab_index + 1} ({service.value}): ❌ Error checking - {e}")
                    
    async def _check_service_login_status(self, service: AIService) -> bool:
        """Check if a service is logged in by looking for chat input"""
        if not self.driver:
            return False
            
        try:
            config = self.service_configs[service]
            
            # Look for chat input - indicates logged in state
            wait = WebDriverWait(self.driver, 5)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, config["selectors"]["chat_input"])))
            return True
            
        except TimeoutException:
            return False
        except Exception as e:
            logger.warning(f"Error checking login for {service.value}: {e}")
            return False
            
    async def send_query(self, service: AIService, query: str) -> ServiceResponse:
        """Send query to specific AI service (for future implementation)"""
        start_time = time.time()
        
        # This would be implemented later for actual query automation
        # For now, return a placeholder response
        return ServiceResponse(
            service=service,
            response="Service ready for manual interaction",
            status=ServiceStatus.LOGIN_REQUIRED,
            timestamp=time.time(),
            processing_time=time.time() - start_time,
            metadata={"note": "Browser opened for manual login"}
        )
        
    async def query_all_services(self, query: str) -> List[ServiceResponse]:
        """Query all available AI services (placeholder for future implementation)"""
        services = [AIService.CHATGPT, AIService.CLAUDE, AIService.GEMINI, AIService.PERPLEXITY]
        
        logger.info("🎯 Browser automation: Opening all services for manual interaction")
        
        # Open all service tabs
        success = await self.open_all_service_tabs()
        
        if success:
            responses = []
            for service in services:
                response = await self.send_query(service, query)
                responses.append(response)
            return responses
        else:
            # Return error responses
            return [
                ServiceResponse(
                    service=service,
                    response="Failed to open browser",
                    status=ServiceStatus.ERROR,
                    timestamp=time.time(),
                    processing_time=0.0,
                    metadata={"error": "browser_open_failed"}
                )
                for service in services
            ]

# Global automation framework instance
automation_framework = None

async def get_automation_framework() -> BrowserAutomationFramework:
    """Get or create global automation framework instance (lazy loading)"""
    global automation_framework
    if automation_framework is None:
        logger.info("🔧 Lazy loading browser automation framework...")
        automation_framework = BrowserAutomationFramework()
        initialized = await automation_framework.initialize()
        if initialized:
            logger.info("✅ Browser automation framework ready")
        else:
            logger.error("❌ Browser automation framework failed to initialize")
    return automation_framework

async def query_ai_services(services: List[AIService], query: str) -> Dict[AIService, Dict[str, Any]]:
    """Query specified AI services with the given query"""
    framework = await get_automation_framework()
    
    if not SELENIUM_AVAILABLE:
        # Return error for all services
        result = {}
        for service in services:
            result[service] = {
                'response': 'Browser automation not available - SeleniumBase not installed',
                'status': 'error',
                'error': 'selenium_not_available'
            }
        return result
    
    responses = await framework.query_all_services(query)
    
    # Convert to the expected format
    result = {}
    for response in responses:
        result[response.service] = {
            'response': response.response,
            'status': response.status.value,
            'error': response.metadata.get('error') if response.status == ServiceStatus.ERROR else None
        }
    
    return result

async def test_open_service_pages() -> Dict[AIService, Dict[str, Any]]:
    """Test opening all service pages using browser-based automation (JavaScript)"""
    result = {}
    services = [AIService.CHATGPT, AIService.CLAUDE, AIService.GEMINI, AIService.PERPLEXITY]
    
    # Return JavaScript-based approach for frontend to execute
    for service in services:
        result[service] = {
            'response': f"Ready to open {service.value} - will use browser automation from current tab",
            'status': 'success',
            'error': None,
            'browser_automation': True,  # Flag for frontend to handle
            'javascript_action': True
        }
    
    logger.info("🧪 Using browser-based automation (JavaScript) for tab opening")
    return result

# Dependencies check for user guidance
def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    
    if not SELENIUM_AVAILABLE:
        missing.append("seleniumbase")
    
    if missing:
        logger.error("❌ Missing dependencies for browser automation:")
        for dep in missing:
            logger.error(f"   - {dep}")
        logger.error("Install with: pip install seleniumbase")
        return False
    
    logger.info("✅ All browser automation dependencies available")
    return True