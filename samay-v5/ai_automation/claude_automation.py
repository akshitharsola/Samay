"""
Claude AI Automation
Service-specific automation for Claude Pro accounts
"""

import asyncio
import logging
import time
import re
from typing import Dict, Any, Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_automator import BaseAutomator, AutomationResult, AutomationConfig, DetectionLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeAutomator(BaseAutomator):
    """
    Claude-specific automation for Pro accounts
    
    UI Characteristics:
    - ContentEditable div for input (not textarea)
    - Dynamic conversation threads
    - Pro-only features: longer context, faster responses
    - Artifacts and code execution capabilities
    """
    
    def __init__(self, config: AutomationConfig):
        super().__init__(config)
        self.conversation_id = None
        self.current_thread = None
        self.pro_features_available = False

    def get_service_specific_config(self) -> Dict[str, Any]:
        """Get Claude-specific configuration"""
        return {
            'service': 'claude',
            'requires_pro': True,
            'features': ['artifacts', 'opus_model', 'long_context'],
            'selectors': {
                'input': 'div[contenteditable="true"]',
                'submit': 'button[aria-label*="Send"]',
                'response': 'div[data-testid*="message"]',
                'new_chat': 'button:has-text("New Chat")',
                'pro_badge': '[data-testid="pro-badge"]',
                'conversation_list': '[data-testid="conversation-list"]',
                'thinking_indicator': '[data-testid="thinking"]',
                'artifact': '[data-testid="artifact"]'
            }
        }

    async def authenticate(self) -> bool:
        """Authenticate with Claude service"""
        try:
            logger.info("Checking Claude authentication status...")
            
            # Check if already authenticated
            if self.is_authenticated():
                logger.info("Already authenticated with Claude")
                return await self._verify_pro_features()
            
            # Look for login button
            login_selectors = [
                'button:contains("Log in")',
                'a[href*="login"]',
                '[data-testid="login-button"]'
            ]
            
            login_element = None
            for selector in login_selectors:
                login_element = self.find_element_safe(selector, timeout=5)
                if login_element:
                    break
                    
            if login_element:
                logger.info("Found login button, authentication required")
                await self.scroll_into_view(login_element)
                login_element.click()
                await self.natural_delay(2, 4)
                
                # Wait for manual login or redirect
                await self._wait_for_authentication()
                
            return await self._verify_pro_features()
            
        except Exception as e:
            logger.error(f"Claude authentication failed: {e}")
            return False

    async def _wait_for_authentication(self, max_wait: int = 300):
        """Wait for user to complete authentication"""
        logger.info("Waiting for authentication completion...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.is_authenticated():
                logger.info("Authentication completed successfully")
                return True
                
            await asyncio.sleep(2)
            
        logger.error("Authentication timeout")
        return False

    async def _verify_pro_features(self) -> bool:
        """Verify Pro subscription features are available"""
        try:
            # Look for Pro badge or indicators
            pro_indicators = [
                '[data-testid="pro-badge"]',
                '.pro-badge',
                ':contains("Claude Pro")',
                '[aria-label*="Pro"]'
            ]
            
            for selector in pro_indicators:
                element = self.find_element_safe(selector, timeout=3)
                if element:
                    self.pro_features_available = True
                    logger.info("Claude Pro features detected")
                    return True
                    
            # Check if we can access Pro-only features
            if await self._check_opus_access():
                self.pro_features_available = True
                return True
                
            logger.warning("Claude Pro features not detected")
            return True  # Continue even without Pro for basic functionality
            
        except Exception as e:
            logger.error(f"Failed to verify Pro features: {e}")
            return True

    async def _check_opus_access(self) -> bool:
        """Check if Claude-3 Opus model is available"""
        try:
            # Look for model selector
            model_selector = self.find_element_safe('[data-testid="model-selector"]', timeout=3)
            if model_selector:
                model_selector.click()
                await self.natural_delay()
                
                # Look for Opus option
                opus_option = self.find_element_safe(':contains("Opus")', timeout=3)
                if opus_option:
                    # Close model selector
                    model_selector.click()
                    return True
                    
            return False
            
        except Exception:
            return False

    async def send_query(self, query: str) -> AutomationResult:
        """Send a query to Claude"""
        start_time = time.time()
        
        try:
            logger.info(f"Sending query to Claude: {query[:50]}...")
            
            # Find the input element (contenteditable div)
            input_selector = self.config.selectors.get('input', 'div[contenteditable="true"]')
            input_element = self.find_element_safe(input_selector, timeout=10)
            
            if not input_element:
                return AutomationResult(
                    success=False,
                    content="",
                    metadata={},
                    response_time=time.time() - start_time,
                    error="Input element not found"
                )
            
            # Clear any existing content
            await self.scroll_into_view(input_element)
            input_element.click()
            await self.natural_delay()
            
            # Select all and delete
            input_element.send_keys(Keys.COMMAND + "a")
            input_element.send_keys(Keys.DELETE)
            await self.natural_delay()
            
            # Type the query naturally
            await self.type_naturally(input_element, query)
            await self.natural_delay(1, 2)
            
            # Find and click send button
            submit_selector = self.config.selectors.get('submit', 'button[aria-label*="Send"]')
            submit_element = self.find_element_clickable(submit_selector, timeout=5)
            
            if not submit_element:
                # Try alternative submit methods
                input_element.send_keys(Keys.ENTER)
            else:
                submit_element.click()
                
            await self.natural_delay(1, 2)
            
            # Wait for response
            response_content = await self.extract_response()
            
            # Check for artifacts
            artifacts = await self._extract_artifacts()
            
            metadata = {
                'conversation_id': self.conversation_id,
                'pro_features_used': self.pro_features_available,
                'artifacts': artifacts,
                'response_length': len(response_content)
            }
            
            return AutomationResult(
                success=bool(response_content),
                content=response_content,
                metadata=metadata,
                response_time=time.time() - start_time,
                error=None if response_content else "No response received"
            )
            
        except Exception as e:
            logger.error(f"Failed to send query to Claude: {e}")
            return AutomationResult(
                success=False,
                content="",
                metadata={},
                response_time=time.time() - start_time,
                error=str(e)
            )

    async def extract_response(self) -> str:
        """Extract the response from Claude"""
        try:
            # Wait for thinking indicator to disappear
            await self._wait_for_thinking_completion()
            
            # Get response selector
            response_selector = self.config.selectors.get('response', 'div[data-testid*="message"]')
            
            # Wait for response to appear
            if not await self.wait_for_response(response_selector, max_wait=120):
                return ""
            
            # Find all message elements
            response_elements = self.driver.find_elements(By.CSS_SELECTOR, response_selector)
            
            if not response_elements:
                logger.warning("No response elements found")
                return ""
            
            # Get the last message (most recent response)
            last_response = response_elements[-1]
            response_text = last_response.text.strip()
            
            # Extract additional content types
            code_blocks = await self._extract_code_blocks(last_response)
            if code_blocks:
                response_text += "\n\n" + "\n".join(code_blocks)
            
            logger.info(f"Extracted Claude response: {len(response_text)} characters")
            return response_text
            
        except Exception as e:
            logger.error(f"Failed to extract Claude response: {e}")
            return ""

    async def _wait_for_thinking_completion(self, max_wait: int = 120):
        """Wait for Claude to finish thinking"""
        thinking_selector = self.config.selectors.get('thinking_indicator', '[data-testid="thinking"]')
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            thinking_element = self.find_element_safe(thinking_selector, timeout=1)
            if not thinking_element or not thinking_element.is_displayed():
                break
                
            await asyncio.sleep(1)
            
        # Additional delay for content to stabilize
        await self.natural_delay(2, 4)

    async def _extract_code_blocks(self, response_element) -> List[str]:
        """Extract code blocks from response"""
        try:
            code_blocks = []
            
            # Look for code elements
            code_selectors = [
                'pre code',
                '.code-block',
                '[data-testid="code-block"]'
            ]
            
            for selector in code_selectors:
                code_elements = response_element.find_elements(By.CSS_SELECTOR, selector)
                for code_elem in code_elements:
                    code_text = code_elem.text.strip()
                    if code_text:
                        code_blocks.append(f"```\n{code_text}\n```")
                        
            return code_blocks
            
        except Exception as e:
            logger.error(f"Failed to extract code blocks: {e}")
            return []

    async def _extract_artifacts(self) -> List[Dict[str, Any]]:
        """Extract artifacts from Claude response"""
        try:
            artifacts = []
            artifact_selector = self.config.selectors.get('artifact', '[data-testid="artifact"]')
            
            artifact_elements = self.driver.find_elements(By.CSS_SELECTOR, artifact_selector)
            
            for artifact_elem in artifact_elements:
                try:
                    artifact_type = artifact_elem.get_attribute('data-artifact-type') or 'unknown'
                    artifact_title = artifact_elem.get_attribute('data-artifact-title') or 'Untitled'
                    artifact_content = artifact_elem.text.strip()
                    
                    artifacts.append({
                        'type': artifact_type,
                        'title': artifact_title,
                        'content': artifact_content
                    })
                    
                except Exception:
                    continue
                    
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to extract artifacts: {e}")
            return []

    async def start_new_conversation(self) -> bool:
        """Start a new conversation thread"""
        try:
            new_chat_selector = self.config.selectors.get('new_chat', 'button:has-text("New Chat")')
            new_chat_element = self.find_element_clickable(new_chat_selector, timeout=5)
            
            if new_chat_element:
                new_chat_element.click()
                await self.natural_delay(2, 3)
                
                # Update conversation ID
                current_url = self.get_current_url()
                self.conversation_id = self._extract_conversation_id(current_url)
                
                logger.info(f"Started new Claude conversation: {self.conversation_id}")
                return True
            else:
                logger.warning("New chat button not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start new conversation: {e}")
            return False

    def _extract_conversation_id(self, url: str) -> Optional[str]:
        """Extract conversation ID from URL"""
        try:
            # Claude URLs typically have format: https://claude.ai/chat/[conversation-id]
            match = re.search(r'/chat/([a-zA-Z0-9-]+)', url)
            return match.group(1) if match else None
        except Exception:
            return None

    async def switch_to_opus_model(self) -> bool:
        """Switch to Claude-3 Opus model (Pro feature)"""
        if not self.pro_features_available:
            logger.warning("Pro features not available, cannot switch to Opus")
            return False
            
        try:
            # Find model selector
            model_selector = self.find_element_safe('[data-testid="model-selector"]', timeout=5)
            if not model_selector:
                return False
                
            model_selector.click()
            await self.natural_delay()
            
            # Look for Opus option
            opus_selectors = [
                ':contains("Claude-3 Opus")',
                ':contains("Opus")',
                '[data-model="opus"]'
            ]
            
            for selector in opus_selectors:
                opus_option = self.find_element_safe(selector, timeout=3)
                if opus_option:
                    opus_option.click()
                    await self.natural_delay()
                    logger.info("Switched to Claude-3 Opus model")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Failed to switch to Opus model: {e}")
            return False

    async def handle_pro_features(self):
        """Leverage Pro subscription capabilities"""
        if not self.pro_features_available:
            return
            
        try:
            # Switch to Opus for better responses
            await self.switch_to_opus_model()
            
            # Enable any other Pro features available
            await self._enable_advanced_features()
            
        except Exception as e:
            logger.error(f"Failed to handle Pro features: {e}")

    async def _enable_advanced_features(self):
        """Enable advanced Pro features"""
        try:
            # Look for advanced settings or features
            settings_selectors = [
                '[data-testid="settings"]',
                '[aria-label*="settings"]',
                '.settings-button'
            ]
            
            for selector in settings_selectors:
                settings_element = self.find_element_safe(selector, timeout=2)
                if settings_element:
                    # Could enable features like:
                    # - Extended context length
                    # - Advanced reasoning mode
                    # - Custom instructions
                    break
                    
        except Exception as e:
            logger.error(f"Failed to enable advanced features: {e}")

    async def manage_conversation_threads(self):
        """Navigate between conversation threads"""
        try:
            # Get conversation list
            conv_list_selector = self.config.selectors.get('conversation_list', '[data-testid="conversation-list"]')
            conv_list = self.find_element_safe(conv_list_selector, timeout=5)
            
            if conv_list:
                # Get all conversation items
                conversations = conv_list.find_elements(By.CSS_SELECTOR, '[data-testid="conversation-item"]')
                logger.info(f"Found {len(conversations)} conversation threads")
                
                # Store conversation metadata
                self.current_thread = {
                    'total_conversations': len(conversations),
                    'current_index': 0  # Assuming we're in the first/newest
                }
                
        except Exception as e:
            logger.error(f"Failed to manage conversation threads: {e}")

    def is_authenticated(self) -> bool:
        """Check if currently authenticated with Claude"""
        try:
            # Claude-specific authentication indicators
            auth_indicators = [
                '[data-testid="user-menu"]',
                '[data-testid="profile-menu"]',
                'div[contenteditable="true"]',  # Input field only appears when logged in
                '[data-testid="pro-badge"]'
            ]
            
            for selector in auth_indicators:
                element = self.find_element_safe(selector, timeout=3)
                if element:
                    return True
                    
            # Check URL patterns
            current_url = self.get_current_url()
            if '/chat' in current_url and 'claude.ai' in current_url:
                return True
                
            return False
            
        except Exception:
            return False

    async def handle_claude_specific_errors(self) -> bool:
        """Handle Claude-specific error conditions"""
        try:
            # Look for common Claude errors
            error_selectors = [
                ':contains("Something went wrong")',
                ':contains("Error")',
                '.error-message',
                '[data-testid="error"]'
            ]
            
            for selector in error_selectors:
                error_element = self.find_element_safe(selector, timeout=2)
                if error_element:
                    error_text = error_element.text.lower()
                    
                    if 'rate limit' in error_text or 'too many' in error_text:
                        logger.warning("Rate limit detected in Claude")
                        await self.natural_delay(60, 120)  # Wait 1-2 minutes
                        return True
                    elif 'network' in error_text or 'connection' in error_text:
                        logger.warning("Network error in Claude, retrying...")
                        await self.natural_delay(10, 20)
                        return True
                        
            return False
            
        except Exception:
            return False


# Factory function
def create_claude_automator(config_data: Dict[str, Any]) -> ClaudeAutomator:
    """Create Claude automator with configuration"""
    config = AutomationConfig(
        service_name="claude",
        url=config_data.get('url', 'https://claude.ai'),
        selectors=config_data.get('selectors', {}),
        strategy=config_data.get('strategy', 'undetected_chrome'),
        detection_level=DetectionLevel.HIGH,
        profile_path=config_data.get('profile_path', './profiles/claude'),
        headless=config_data.get('headless', False),
        timeout=config_data.get('timeout', 30)
    )
    
    return ClaudeAutomator(config)