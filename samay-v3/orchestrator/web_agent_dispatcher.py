#!/usr/bin/env python3
"""
Samay v3 - Web Agent Dispatcher System
=====================================
Phase 3: Machine-Language Communication via Web Interfaces
"""

import json
import asyncio
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum
import sqlite3
import re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .local_llm import LocalLLMClient
from .drivers import SamayDriverFactory


# Service-specific selectors for browser automation
SERVICE_SELECTORS = {
    "claude": {
        "input": 'div[contenteditable="true"]',
        "send_button": 'button[aria-label="Send Message"]',
        "response_container": '.prose',
        "loading_indicator": '.animate-pulse',
        "end_marker": '.cursor-pointer:not(.animate-pulse)'
    },
    "gemini": {
        "input": 'div[contenteditable="true"]',
        "send_button": 'button[aria-label="Send message"]',
        "response_container": '.model-response-text',
        "loading_indicator": '.loading-dots',
        "end_marker": '.response-complete'
    },
    "perplexity": {
        "input": 'textarea[placeholder*="Ask anything"]',
        "send_button": 'button[aria-label="Submit"]',
        "response_container": '.prose-base',
        "loading_indicator": '.animate-spin',
        "end_marker": '.text-complete'
    }
}


class ServiceType(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"


class RequestStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REFINEMENT_NEEDED = "refinement_needed"
    FAILED = "failed"


class OutputFormat(Enum):
    JSON = "json"
    STRUCTURED_TEXT = "structured_text"
    MARKDOWN = "markdown"
    XML = "xml"


@dataclass
class WebRequest:
    """Represents a request to a web service"""
    request_id: str
    service: ServiceType
    prompt: str
    expected_format: OutputFormat
    expected_structure: Dict[str, Any]
    refinement_criteria: List[str]
    max_refinements: int
    created_at: str


@dataclass
class WebResponse:
    """Represents a response from a web service"""
    response_id: str
    request_id: str
    service: ServiceType
    raw_output: str
    parsed_output: Optional[Dict[str, Any]]
    status: RequestStatus
    refinement_count: int
    quality_score: float
    timestamp: str


@dataclass
class RefinementAttempt:
    """Represents a refinement attempt"""
    attempt_id: str
    request_id: str
    refinement_prompt: str
    issue_detected: str
    expected_correction: str
    timestamp: str


class WebAgentDispatcher:
    """Intelligent dispatcher for web-based AI service communication"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "web_dispatcher.db"
        self.session_id = session_id
        self.llm_client = LocalLLMClient()
        
        # Initialize SeleniumBase UC Mode driver factory
        self.driver_factory = SamayDriverFactory()
        
        # Service session tracking
        self.active_sessions = {
            ServiceType.CLAUDE: {"logged_in": False, "session_data": {}},
            ServiceType.GEMINI: {"logged_in": False, "session_data": {}},
            ServiceType.PERPLEXITY: {"logged_in": False, "session_data": {}}
        }
        
        # Active drivers (keep connections alive)
        self.active_drivers = {}
        
        # Request tracking
        self.active_requests = {}
        self.refinement_history = {}
        
        # Machine language templates
        self.output_templates = self._load_output_templates()
        
        # Rate limiting (messages per service)
        self.last_request_time = {}
        self.min_request_interval = 5  # seconds between requests per service
        
        self.init_database()
        print(f"🌐 WebAgentDispatcher initialized for session {session_id}")
        print(f"🔗 Ready for web interface communication with UC Mode automation")
    
    def init_database(self):
        """Initialize web dispatcher database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Web requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_requests (
                request_id TEXT PRIMARY KEY,
                session_id TEXT,
                service TEXT,
                prompt TEXT,
                expected_format TEXT,
                expected_structure TEXT,
                refinement_criteria TEXT,
                max_refinements INTEGER,
                created_at TEXT
            )
        ''')
        
        # Web responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_responses (
                response_id TEXT PRIMARY KEY,
                request_id TEXT,
                service TEXT,
                raw_output TEXT,
                parsed_output TEXT,
                status TEXT,
                refinement_count INTEGER,
                quality_score REAL,
                timestamp TEXT,
                FOREIGN KEY (request_id) REFERENCES web_requests (request_id)
            )
        ''')
        
        # Refinement attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refinement_attempts (
                attempt_id TEXT PRIMARY KEY,
                request_id TEXT,
                refinement_prompt TEXT,
                issue_detected TEXT,
                expected_correction TEXT,
                timestamp TEXT,
                FOREIGN KEY (request_id) REFERENCES web_requests (request_id)
            )
        ''')
        
        # Service sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_sessions (
                session_id TEXT,
                service TEXT,
                login_status BOOLEAN,
                session_data TEXT,
                last_activity TEXT,
                PRIMARY KEY (session_id, service)
            )
        ''')
        
        # Communication logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communication_logs (
                log_id TEXT PRIMARY KEY,
                session_id TEXT,
                service TEXT,
                direction TEXT,
                content TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_service_session(self, service: ServiceType, session_data: Dict[str, Any]):
        """Register that a service is logged in and ready"""
        
        self.active_sessions[service] = {
            "logged_in": True,
            "session_data": session_data,
            "last_activity": datetime.now().isoformat()
        }
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO service_sessions 
            (session_id, service, login_status, session_data, last_activity)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            service.value,
            True,
            json.dumps(session_data),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        print(f"✅ {service.value.title()} session registered and ready")
    
    async def execute_intelligent_request(
        self,
        prompt: str,
        services: List[ServiceType],
        expected_output: str,
        output_format: OutputFormat = OutputFormat.JSON,
        max_refinements: int = 3
    ) -> Dict[str, WebResponse]:
        """Execute request across multiple services with intelligent refinement"""
        
        # Generate machine-optimized prompts for each service
        optimized_prompts = await self._generate_service_prompts(
            prompt, services, expected_output, output_format
        )
        
        # Create requests
        requests = {}
        for service in services:
            if not self.active_sessions[service]["logged_in"]:
                print(f"⚠️ {service.value} not logged in, skipping")
                continue
            
            request = WebRequest(
                request_id=str(uuid.uuid4()),
                service=service,
                prompt=optimized_prompts[service],
                expected_format=output_format,
                expected_structure=self._parse_expected_structure(expected_output),
                refinement_criteria=self._generate_refinement_criteria(expected_output),
                max_refinements=max_refinements,
                created_at=datetime.now().isoformat()
            )
            
            requests[service] = request
            self.active_requests[request.request_id] = request
            self._store_web_request(request)
        
        # Execute requests in parallel
        tasks = [
            self._execute_single_request(request)
            for request in requests.values()
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process responses
        result = {}
        for i, response in enumerate(responses):
            service = list(requests.keys())[i]
            if isinstance(response, Exception):
                print(f"❌ {service.value} failed: {response}")
                continue
            result[service] = response
        
        return result
    
    async def _execute_single_request(self, request: WebRequest) -> WebResponse:
        """Execute a single request with refinement loop"""
        
        refinement_count = 0
        current_prompt = request.prompt
        
        while refinement_count <= request.max_refinements:
            # Send request to web service (this would interface with web automation)
            raw_response = await self._send_web_request(request.service, current_prompt)
            
            # Log communication
            self._log_communication(request.service, "sent", current_prompt)
            self._log_communication(request.service, "received", raw_response)
            
            # Parse and validate response
            parsed_output, quality_score = self._parse_and_validate_response(
                raw_response, request.expected_structure, request.refinement_criteria
            )
            
            # Check if refinement is needed
            refinement_needed, issues = self._check_refinement_needed(
                parsed_output, request.expected_structure, request.refinement_criteria
            )
            
            # Create response object
            response = WebResponse(
                response_id=str(uuid.uuid4()),
                request_id=request.request_id,
                service=request.service,
                raw_output=raw_response,
                parsed_output=parsed_output,
                status=RequestStatus.REFINEMENT_NEEDED if refinement_needed else RequestStatus.COMPLETED,
                refinement_count=refinement_count,
                quality_score=quality_score,
                timestamp=datetime.now().isoformat()
            )
            
            # Store response
            self._store_web_response(response)
            
            # If no refinement needed, return success
            if not refinement_needed:
                response.status = RequestStatus.COMPLETED
                print(f"✅ {request.service.value} completed successfully (refinements: {refinement_count})")
                return response
            
            # Generate refinement prompt
            if refinement_count < request.max_refinements:
                refinement_prompt = await self._generate_refinement_prompt(
                    request, raw_response, issues
                )
                
                # Store refinement attempt
                attempt = RefinementAttempt(
                    attempt_id=str(uuid.uuid4()),
                    request_id=request.request_id,
                    refinement_prompt=refinement_prompt,
                    issue_detected="; ".join(issues),
                    expected_correction=str(request.expected_structure),
                    timestamp=datetime.now().isoformat()
                )
                self._store_refinement_attempt(attempt)
                
                current_prompt = refinement_prompt
                refinement_count += 1
                
                print(f"🔄 {request.service.value} refinement {refinement_count}: {issues[0][:50]}...")
            else:
                print(f"❌ {request.service.value} failed after {request.max_refinements} refinements")
                response.status = RequestStatus.FAILED
                return response
        
        return response
    
    async def _send_web_request(self, service: ServiceType, prompt: str) -> str:
        """Send request to web service using SeleniumBase UC Mode automation"""
        
        service_name = service.value
        
        # Rate limiting
        await self._enforce_rate_limit(service_name)
        
        try:
            # Get or create driver for service
            driver = await self._get_service_driver(service_name)
            
            # Navigate to service if needed
            await self._ensure_service_page(driver, service_name)
            
            # Send message with human-like typing
            await self._send_message_human_like(driver, service_name, prompt)
            
            # Capture streaming response
            response = await self._capture_streaming_response(driver, service_name)
            
            # Update last request time
            self.last_request_time[service_name] = time.time()
            
            return response
            
        except Exception as e:
            print(f"❌ Browser automation failed for {service_name}: {e}")
            # Fallback to basic response to maintain functionality
            return f"Browser automation error for {service_name}: {str(e)}"
    
    async def _enforce_rate_limit(self, service_name: str):
        """Enforce rate limiting between requests"""
        if service_name in self.last_request_time:
            elapsed = time.time() - self.last_request_time[service_name]
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                print(f"⏳ Rate limiting: waiting {wait_time:.1f}s for {service_name}")
                await asyncio.sleep(wait_time)
    
    async def _get_service_driver(self, service_name: str):
        """Get or create driver for service"""
        if service_name not in self.active_drivers:
            print(f"🚀 Starting UC Mode driver for {service_name}")
            # This is a synchronous call wrapped in async
            driver_context = self.driver_factory.get_driver(service_name, headed=True)
            driver = driver_context.__enter__()
            self.active_drivers[service_name] = {"driver": driver, "context": driver_context}
        
        return self.active_drivers[service_name]["driver"]
    
    async def _ensure_service_page(self, driver, service_name: str):
        """Navigate to service page if needed"""
        config = self.driver_factory.services[service_name]
        current_url = driver.get_current_url()
        
        # Check if we're on the right domain
        if config["url"].split("//")[1].split("/")[0] not in current_url:
            print(f"🌐 Navigating to {service_name}: {config['url']}")
            driver.open(config["url"])
            
            # Wait for page load
            await asyncio.sleep(random.uniform(2, 4))
    
    async def _send_message_human_like(self, driver, service_name: str, message: str):
        """Send message with human-like typing patterns"""
        selectors = SERVICE_SELECTORS.get(service_name, {})
        input_selector = selectors.get("input", 'textarea, div[contenteditable="true"]')
        
        try:
            # Wait for input element
            wait = WebDriverWait(driver, 10)
            input_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, input_selector))
            )
            
            # Clear existing content
            input_element.clear()
            
            # Human-like typing with random delays
            for char in message:
                input_element.send_keys(char)
                # Random typing delay between 50-200ms
                await asyncio.sleep(random.uniform(0.05, 0.2))
            
            # Random pause before sending
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Send the message
            send_button_selector = selectors.get("send_button", 'button[type="submit"]')
            try:
                send_button = driver.find_element(By.CSS_SELECTOR, send_button_selector)
                send_button.click()
            except:
                # Fallback: try Enter key
                input_element.send_keys(Keys.ENTER)
            
            print(f"✅ Message sent to {service_name}: {message[:50]}...")
            
        except Exception as e:
            print(f"❌ Failed to send message to {service_name}: {e}")
            raise
    
    async def _capture_streaming_response(self, driver, service_name: str) -> str:
        """Capture streaming response from service"""
        selectors = SERVICE_SELECTORS.get(service_name, {})
        response_selector = selectors.get("response_container", ".response, .message")
        loading_selector = selectors.get("loading_indicator", ".loading, .spinner")
        
        response_text = ""
        max_wait_time = 60  # Maximum wait time in seconds
        start_time = time.time()
        
        try:
            # Wait for response to start
            await asyncio.sleep(2)
            
            while (time.time() - start_time) < max_wait_time:
                try:
                    # Check if still loading
                    loading_elements = driver.find_elements(By.CSS_SELECTOR, loading_selector)
                    is_loading = any(elem.is_displayed() for elem in loading_elements)
                    
                    # Get latest response content
                    response_elements = driver.find_elements(By.CSS_SELECTOR, response_selector)
                    if response_elements:
                        # Get the last response element (most recent)
                        latest_response = response_elements[-1]
                        current_text = latest_response.text.strip()
                        
                        if current_text and current_text != response_text:
                            response_text = current_text
                    
                    # Check if response is complete
                    if not is_loading and response_text and len(response_text) > 10:
                        # Additional wait to ensure response is complete
                        await asyncio.sleep(2)
                        
                        # Final check for any new content
                        final_elements = driver.find_elements(By.CSS_SELECTOR, response_selector)
                        if final_elements:
                            final_text = final_elements[-1].text.strip()
                            if final_text:
                                response_text = final_text
                        
                        break
                    
                    # Small delay between checks
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"⚠️ Error during response capture: {e}")
                    await asyncio.sleep(1)
            
            if not response_text:
                response_text = "No response captured - check service selectors"
            
            print(f"📥 Captured response from {service_name}: {len(response_text)} characters")
            return response_text
            
        except Exception as e:
            print(f"❌ Failed to capture response from {service_name}: {e}")
            return f"Response capture failed: {str(e)}"
    
    def cleanup_drivers(self):
        """Cleanup active drivers"""
        for service_name, driver_info in self.active_drivers.items():
            try:
                driver_info["context"].__exit__(None, None, None)
                print(f"🛑 Closed driver for {service_name}")
            except Exception as e:
                print(f"⚠️ Error closing driver for {service_name}: {e}")
        
        self.active_drivers.clear()
    
    def verify_service_sessions(self):
        """Verify which services have active sessions"""
        profiles = self.driver_factory.list_profiles()
        
        for service_name, profile_info in profiles.items():
            if profile_info["ready"]:
                service_type = ServiceType(service_name)
                self.active_sessions[service_type] = {
                    "logged_in": True,
                    "session_data": {"profile_ready": True},
                    "last_activity": datetime.now().isoformat()
                }
                print(f"✅ {service_name.title()} session verified")
            else:
                print(f"⚠️ {service_name.title()} profile not ready")
        
        return self.active_sessions
    
    async def _generate_service_prompts(
        self,
        base_prompt: str,
        services: List[ServiceType],
        expected_output: str,
        output_format: OutputFormat
    ) -> Dict[ServiceType, str]:
        """Generate optimized prompts for each service"""
        
        prompts = {}
        
        for service in services:
            # Service-specific optimization
            service_template = self._get_service_template(service, output_format)
            
            # Generate optimized prompt using local LLM
            optimization_prompt = f"""
            Optimize this prompt for {service.value} to ensure machine-readable output:
            
            BASE PROMPT: {base_prompt}
            EXPECTED OUTPUT: {expected_output}
            FORMAT: {output_format.value}
            
            Create a prompt that:
            1. Clearly requests {output_format.value} format
            2. Specifies exact structure needed
            3. Includes validation instructions
            4. Uses {service.value}-specific best practices
            
            Return only the optimized prompt.
            """
            
            system_prompt = f"You are an expert at optimizing prompts for {service.value}. Focus on machine-readable outputs."
            
            response = self.llm_client.generate_response(optimization_prompt, system_prompt)
            
            if response.success:
                optimized = response.response.strip()
                # Add service template
                prompts[service] = service_template.format(
                    prompt=optimized,
                    format=output_format.value,
                    structure=expected_output
                )
            else:
                # Fallback to basic template
                prompts[service] = service_template.format(
                    prompt=base_prompt,
                    format=output_format.value,
                    structure=expected_output
                )
        
        return prompts
    
    def _get_service_template(self, service: ServiceType, output_format: OutputFormat) -> str:
        """Get service-specific prompt template"""
        
        templates = {
            ServiceType.CLAUDE: """
{prompt}

IMPORTANT: Provide your response in {format} format with this exact structure:
{structure}

Ensure the output is machine-readable and follows the specified format precisely.
""",
            ServiceType.GEMINI: """
{prompt}

Please format your response as {format} with the following structure:
{structure}

Make sure the output is properly structured and parseable.
""",
            ServiceType.PERPLEXITY: """
{prompt}

Return results in {format} format structured as:
{structure}

Focus on accurate, structured information that can be programmatically processed.
"""
        }
        
        return templates.get(service, "{prompt}\n\nFormat: {format}\nStructure: {structure}")
    
    def _parse_expected_structure(self, expected_output: str) -> Dict[str, Any]:
        """Parse expected output into structure"""
        
        # Try to parse as JSON first
        try:
            return json.loads(expected_output)
        except:
            # Fall back to text analysis
            return {
                "type": "text",
                "description": expected_output,
                "required_elements": self._extract_required_elements(expected_output)
            }
    
    def _extract_required_elements(self, text: str) -> List[str]:
        """Extract required elements from text description"""
        
        # Simple keyword extraction
        keywords = []
        key_phrases = ["must include", "should contain", "need to have", "required:", "include:"]
        
        text_lower = text.lower()
        for phrase in key_phrases:
            if phrase in text_lower:
                # Extract text after the phrase
                parts = text_lower.split(phrase)
                if len(parts) > 1:
                    following_text = parts[1].split('.')[0].strip()
                    keywords.extend([w.strip() for w in following_text.split(',')])
        
        return list(set(keywords))
    
    def _generate_refinement_criteria(self, expected_output: str) -> List[str]:
        """Generate criteria for checking if refinement is needed"""
        
        criteria = [
            "Output must be in the specified format",
            "All required fields must be present",
            "Data must be properly structured",
            "Content must match the request"
        ]
        
        # Add specific criteria based on expected output
        if "json" in expected_output.lower():
            criteria.append("Must be valid JSON")
        
        if "list" in expected_output.lower():
            criteria.append("Must contain list elements")
        
        return criteria
    
    def _parse_and_validate_response(
        self,
        raw_response: str,
        expected_structure: Dict[str, Any],
        criteria: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """Parse response and calculate quality score"""
        
        parsed = None
        quality_score = 0.0
        
        # Try JSON parsing
        try:
            parsed = json.loads(raw_response)
            quality_score += 0.3  # Valid format bonus
        except:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    quality_score += 0.2
                except:
                    pass
        
        # Structure validation
        if parsed and expected_structure.get("type") != "text":
            structure_score = self._validate_structure(parsed, expected_structure)
            quality_score += structure_score * 0.4
        
        # Content quality
        content_score = self._assess_content_quality(raw_response, criteria)
        quality_score += content_score * 0.3
        
        return parsed, min(quality_score, 1.0)
    
    def _validate_structure(self, parsed: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Validate parsed output against expected structure"""
        
        if not isinstance(parsed, dict) or not isinstance(expected, dict):
            return 0.0
        
        matches = 0
        total = len(expected)
        
        for key, expected_value in expected.items():
            if key in parsed:
                matches += 1
                # Could add deeper validation here
        
        return matches / total if total > 0 else 0.0
    
    def _assess_content_quality(self, content: str, criteria: List[str]) -> float:
        """Assess content quality against criteria"""
        
        score = 0.0
        
        # Length check
        if len(content) > 50:
            score += 0.2
        
        # Format indicators
        if any(indicator in content.lower() for indicator in ['{', '}', '[', ']', ':']):
            score += 0.3
        
        # Criteria matching (simplified)
        criteria_met = 0
        for criterion in criteria:
            if any(word in content.lower() for word in criterion.lower().split()):
                criteria_met += 1
        
        if criteria:
            score += (criteria_met / len(criteria)) * 0.5
        
        return min(score, 1.0)
    
    def _check_refinement_needed(
        self,
        parsed_output: Optional[Dict[str, Any]],
        expected_structure: Dict[str, Any],
        criteria: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check if refinement is needed and return issues"""
        
        issues = []
        
        # Check if parsing failed
        if parsed_output is None:
            issues.append("Failed to parse output in expected format")
        
        # Check structure completeness
        if parsed_output and expected_structure.get("type") != "text":
            missing_fields = []
            for key in expected_structure.keys():
                if key not in parsed_output:
                    missing_fields.append(key)
            
            if missing_fields:
                issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check against criteria (simplified)
        # This would be more sophisticated in practice
        
        return len(issues) > 0, issues
    
    async def _generate_refinement_prompt(
        self,
        original_request: WebRequest,
        failed_response: str,
        issues: List[str]
    ) -> str:
        """Generate refinement prompt to fix issues"""
        
        refinement_prompt = f"""
Your previous response had these issues:
{chr(10).join(f'- {issue}' for issue in issues)}

PREVIOUS RESPONSE:
{failed_response}

ORIGINAL REQUEST:
{original_request.prompt}

Please provide a corrected response that:
1. Fixes all identified issues
2. Follows the exact format: {original_request.expected_format.value}
3. Includes all required structure elements
4. Is properly formatted for machine processing

Corrected response:
"""
        
        return refinement_prompt
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get statistics about web communications"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total requests
        cursor.execute('SELECT COUNT(*) FROM web_requests WHERE session_id = ?', (self.session_id,))
        total_requests = cursor.fetchone()[0]
        
        # Successful requests
        cursor.execute('''
            SELECT COUNT(*) FROM web_responses 
            WHERE status = "completed" AND request_id IN 
            (SELECT request_id FROM web_requests WHERE session_id = ?)
        ''', (self.session_id,))
        successful_requests = cursor.fetchone()[0]
        
        # Average refinements
        cursor.execute('''
            SELECT AVG(refinement_count) FROM web_responses 
            WHERE status = "completed" AND request_id IN 
            (SELECT request_id FROM web_requests WHERE session_id = ?)
        ''', (self.session_id,))
        avg_refinements = cursor.fetchone()[0] or 0
        
        # Service usage
        cursor.execute('''
            SELECT service, COUNT(*) FROM web_requests 
            WHERE session_id = ? GROUP BY service
        ''', (self.session_id,))
        service_usage = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "average_refinements": round(avg_refinements, 2),
            "service_usage": service_usage,
            "active_services": [s.value for s, data in self.active_sessions.items() if data["logged_in"]]
        }
    
    # Database storage methods
    def _store_web_request(self, request: WebRequest):
        """Store web request in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO web_requests 
            (request_id, session_id, service, prompt, expected_format, expected_structure, refinement_criteria, max_refinements, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.request_id,
            self.session_id,
            request.service.value,
            request.prompt,
            request.expected_format.value,
            json.dumps(request.expected_structure),
            json.dumps(request.refinement_criteria),
            request.max_refinements,
            request.created_at
        ))
        conn.commit()
        conn.close()
    
    def _store_web_response(self, response: WebResponse):
        """Store web response in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO web_responses 
            (response_id, request_id, service, raw_output, parsed_output, status, refinement_count, quality_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            response.response_id,
            response.request_id,
            response.service.value,
            response.raw_output,
            json.dumps(response.parsed_output) if response.parsed_output else None,
            response.status.value,
            response.refinement_count,
            response.quality_score,
            response.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _store_refinement_attempt(self, attempt: RefinementAttempt):
        """Store refinement attempt in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO refinement_attempts 
            (attempt_id, request_id, refinement_prompt, issue_detected, expected_correction, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            attempt.attempt_id,
            attempt.request_id,
            attempt.refinement_prompt,
            attempt.issue_detected,
            attempt.expected_correction,
            attempt.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _log_communication(self, service: ServiceType, direction: str, content: str):
        """Log communication with service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO communication_logs 
            (log_id, session_id, service, direction, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            self.session_id,
            service.value,
            direction,
            content[:1000],  # Limit content length
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _load_output_templates(self) -> Dict[str, str]:
        """Load output format templates"""
        return {
            "json": '{"result": "{}", "confidence": 0.0, "metadata": {}}',
            "structured_text": "Result: {}\nConfidence: {}\nDetails: {}",
            "markdown": "## Result\n{}\n\n**Confidence:** {}\n\n### Details\n{}",
            "xml": "<result><content>{}</content><confidence>{}</confidence><metadata>{}</metadata></result>"
        }


async def test_web_automation():
    """Test the enhanced web automation capabilities"""
    print("🌐 Testing Enhanced Web Agent Dispatcher with UC Mode Automation")
    print("=" * 70)
    
    # Initialize dispatcher
    dispatcher = WebAgentDispatcher(session_id="test_web_automation")
    
    try:
        # Verify service sessions
        print("\n🔍 Verifying service sessions...")
        sessions = dispatcher.verify_service_sessions()
        
        ready_services = [service for service, data in sessions.items() if data["logged_in"]]
        if not ready_services:
            print("❌ No services ready. Please initialize profiles first:")
            print("   python orchestrator/drivers.py")
            return
        
        print(f"✅ Ready services: {[s.value for s in ready_services]}")
        
        # Test single service request
        if ready_services:
            test_service = ready_services[0]
            print(f"\n🧪 Testing {test_service.value} automation...")
            
            test_prompt = "Hello! Please respond with a simple greeting in JSON format like: {\"message\": \"your response\", \"timestamp\": \"current time\"}"
            
            try:
                response = await dispatcher._send_web_request(test_service, test_prompt)
                print(f"📥 Response: {response[:200]}...")
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        # Test communication stats
        print("\n📊 Communication stats:")
        stats = dispatcher.get_communication_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up drivers...")
        dispatcher.cleanup_drivers()
    
    print(f"\n✅ Enhanced WebAgentDispatcher test completed!")


def main():
    """Main entry point for testing"""
    import asyncio
    asyncio.run(test_web_automation())


if __name__ == "__main__":
    main()