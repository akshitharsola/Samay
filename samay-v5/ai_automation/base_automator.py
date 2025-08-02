"""
Base Automator Class
Abstract base class for all AI service automators
"""

import asyncio
import logging
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from seleniumbase import BaseCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomationStrategy(Enum):
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    UNDETECTED_CHROME = "undetected_chrome"


class DetectionLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AutomationConfig:
    service_name: str
    url: str
    selectors: Dict[str, str]
    strategy: AutomationStrategy
    detection_level: DetectionLevel
    profile_path: Optional[str] = None
    headless: bool = False
    timeout: int = 30
    natural_delay_min: float = 1.0
    natural_delay_max: float = 3.0


@dataclass
class AutomationResult:
    success: bool
    content: str
    metadata: Dict[str, Any]
    response_time: float
    error: Optional[str] = None


class BaseAutomator(ABC):
    """Abstract base class for all AI service automators"""
    
    def __init__(self, config: AutomationConfig):
        self.config = config
        self.driver = None
        self.wait = None
        self.session_active = False
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    async def send_query(self, query: str) -> AutomationResult:
        """Send a query to the service"""
        pass
    
    @abstractmethod
    async def extract_response(self) -> str:
        """Extract the response from the service"""
        pass
    
    @abstractmethod
    def get_service_specific_config(self) -> Dict[str, Any]:
        """Get service-specific configuration"""
        pass

    async def initialize_driver(self):
        """Initialize the browser driver based on strategy"""
        try:
            if self.config.strategy == AutomationStrategy.UNDETECTED_CHROME:
                await self._init_undetected_chrome()
            else:
                await self._init_selenium_driver()
                
            self.wait = WebDriverWait(self.driver, self.config.timeout)
            logger.info(f"Initialized {self.config.strategy.value} driver for {self.config.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    async def _init_undetected_chrome(self):
        """Initialize undetected Chrome driver"""
        options = uc.ChromeOptions()
        
        # Profile configuration
        if self.config.profile_path:
            profile_path = Path(self.config.profile_path)
            profile_path.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile_path}")
            
        # Stealth options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Anti-detection based on level
        if self.config.detection_level == DetectionLevel.HIGH:
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-extensions")
            
        if self.config.headless:
            options.add_argument("--headless")
            
        self.driver = uc.Chrome(options=options)
        
        # Execute script to hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def _init_selenium_driver(self):
        """Initialize regular Selenium driver with SeleniumBase"""
        # This would integrate with SeleniumBase for enhanced automation
        pass

    async def navigate_to_service(self):
        """Navigate to the service URL"""
        try:
            logger.info(f"Navigating to {self.config.url}")
            self.driver.get(self.config.url)
            
            # Wait for page to load
            await self.natural_delay()
            
            # Check if we're on the correct page
            if self.config.url not in self.driver.current_url:
                logger.warning(f"Unexpected URL: {self.driver.current_url}")
                
        except Exception as e:
            logger.error(f"Failed to navigate to service: {e}")
            raise

    async def natural_delay(self, min_delay: float = None, max_delay: float = None):
        """Add natural human-like delay"""
        min_delay = min_delay or self.config.natural_delay_min
        max_delay = max_delay or self.config.natural_delay_max
        
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    def find_element_safe(self, selector: str, timeout: int = None) -> Optional[Any]:
        """Safely find element with timeout"""
        try:
            timeout = timeout or self.config.timeout
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"Element not found: {selector}")
            return None

    def find_element_clickable(self, selector: str, timeout: int = None) -> Optional[Any]:
        """Find clickable element with timeout"""
        try:
            timeout = timeout or self.config.timeout
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"Clickable element not found: {selector}")
            return None

    async def type_naturally(self, element, text: str):
        """Type text with natural human-like timing"""
        for char in text:
            element.send_keys(char)
            # Random typing delay between 50-150ms
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def scroll_into_view(self, element):
        """Scroll element into view"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        await self.natural_delay(0.5, 1.0)

    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot for debugging"""
        if not filename:
            timestamp = int(time.time())
            filename = f"screenshots/{self.config.service_name}_{timestamp}.png"
            
        screenshot_path = Path(filename)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.driver.save_screenshot(str(screenshot_path))
        return str(screenshot_path)

    def get_page_source(self) -> str:
        """Get current page source"""
        return self.driver.page_source

    def get_current_url(self) -> str:
        """Get current URL"""
        return self.driver.current_url

    async def handle_popups_and_modals(self):
        """Handle common popups and modals"""
        # Common selectors for popups
        popup_selectors = [
            '[aria-label*="close"]',
            '[data-testid*="close"]',
            '.modal-close',
            '.popup-close',
            'button:contains("Close")',
            'button:contains("Dismiss")',
            'button:contains("OK")'
        ]
        
        for selector in popup_selectors:
            try:
                element = self.find_element_safe(selector, timeout=2)
                if element and element.is_displayed():
                    await self.scroll_into_view(element)
                    element.click()
                    await self.natural_delay()
                    logger.info(f"Closed popup using selector: {selector}")
                    break
            except Exception:
                continue

    async def wait_for_response(self, response_selector: str, max_wait: int = 60) -> bool:
        """Wait for response to appear"""
        try:
            # Wait for response element to appear
            WebDriverWait(self.driver, max_wait).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, response_selector))
            )
            
            # Additional wait for content to load
            await self.natural_delay(2.0, 4.0)
            return True
            
        except TimeoutException:
            logger.error(f"Response not received within {max_wait} seconds")
            return False

    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        # Default implementation - can be overridden
        try:
            # Look for common authentication indicators
            auth_indicators = [
                '[data-testid*="user"]',
                '[aria-label*="user"]',
                '.user-menu',
                '.profile-menu',
                '[href*="profile"]',
                '[href*="account"]'
            ]
            
            for selector in auth_indicators:
                element = self.find_element_safe(selector, timeout=2)
                if element:
                    return True
                    
            return False
            
        except Exception:
            return False

    async def handle_rate_limiting(self):
        """Handle rate limiting from service"""
        # Look for rate limit indicators
        rate_limit_selectors = [
            ':contains("rate limit")',
            ':contains("too many requests")',
            ':contains("please wait")',
            '.rate-limit',
            '.error-message'
        ]
        
        for selector in rate_limit_selectors:
            try:
                element = self.find_element_safe(selector, timeout=2)
                if element and "rate" in element.text.lower():
                    logger.warning("Rate limiting detected, waiting...")
                    await self.natural_delay(30, 60)  # Wait 30-60 seconds
                    return True
            except Exception:
                continue
                
        return False

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.session_active = False
            logger.info(f"Cleaned up {self.config.service_name} automator")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def execute_automation(self, query: str) -> AutomationResult:
        """Main automation execution flow"""
        start_time = time.time()
        
        try:
            # Initialize if not already done
            if not self.driver:
                await self.initialize_driver()
                
            # Navigate to service
            await self.navigate_to_service()
            
            # Handle popups
            await self.handle_popups_and_modals()
            
            # Authenticate if needed
            if not self.is_authenticated():
                auth_success = await self.authenticate()
                if not auth_success:
                    return AutomationResult(
                        success=False,
                        content="",
                        metadata={},
                        response_time=time.time() - start_time,
                        error="Authentication failed"
                    )
            
            # Check for rate limiting
            if await self.handle_rate_limiting():
                return AutomationResult(
                    success=False,
                    content="",
                    metadata={},
                    response_time=time.time() - start_time,
                    error="Rate limited"
                )
            
            # Send query
            result = await self.send_query(query)
            result.response_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Automation execution failed: {e}")
            return AutomationResult(
                success=False,
                content="",
                metadata={"error_details": str(e)},
                response_time=time.time() - start_time,
                error=str(e)
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.cleanup())


# Example implementation
class ExampleAutomator(BaseAutomator):
    """Example implementation of base automator"""
    
    async def authenticate(self) -> bool:
        return True
    
    async def send_query(self, query: str) -> AutomationResult:
        return AutomationResult(
            success=True,
            content=f"Example response for query: {query}",
            metadata={},
            response_time=1.0
        )
    
    async def extract_response(self) -> str:
        return "Example response"
    
    def get_service_specific_config(self) -> Dict[str, Any]:
        return {"example": "config"}


# Utility functions
def create_automation_config(service_name: str, config_data: Dict[str, Any]) -> AutomationConfig:
    """Create automation config from service configuration"""
    return AutomationConfig(
        service_name=service_name,
        url=config_data.get('url', ''),
        selectors=config_data.get('selectors', {}),
        strategy=AutomationStrategy.UNDETECTED_CHROME,
        detection_level=DetectionLevel.HIGH,
        profile_path=f"./profiles/{service_name}",
        headless=False,
        timeout=30,
        natural_delay_min=1.0,
        natural_delay_max=3.0
    )