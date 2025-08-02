#!/usr/bin/env python3
"""
Samay v3 - Prompt Dispatcher
============================
Fan-out controller for parallel prompt dispatch to multiple AI services
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .drivers import SamayDriverFactory
from .validators import SessionValidator
from .local_llm import LocalLLMClient


@dataclass
class PromptRequest:
    """Structure for prompt requests"""
    prompt: str
    services: List[str]  # Which services to query
    timeout: int = 60  # Timeout per service in seconds
    retry_count: int = 2  # Number of retries per service
    metadata: Dict[str, Any] = None
    confidential: bool = False  # Route to local LLM if True


@dataclass
class ServiceResponse:
    """Structure for individual service responses"""
    service: str
    success: bool
    response: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = None


@dataclass
class AggregatedResponse:
    """Structure for final aggregated response"""
    request_id: str
    prompt: str
    responses: List[ServiceResponse]
    total_execution_time: float
    successful_services: int
    failed_services: int
    timestamp: float


class PromptDispatcher:
    """Main orchestrator for parallel AI service queries"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.driver_factory = SamayDriverFactory(base_dir)
        self.validator = SessionValidator()
        self.local_llm = LocalLLMClient()
        
        # Service configurations for prompt submission (updated for 2025 DOM)
        self.service_configs = {
            "claude": {
                "prompt_selector": 'div[contenteditable="true"]',
                "submit_selector": 'button[aria-label*="Send"]',
                "response_selector": 'div[data-testid*="message"]',
                "wait_for_response": 8,
                "backup_selectors": {
                    "prompt": ['textarea[placeholder*="Message"]', 'div[role="textbox"]', '.ProseMirror'],
                    "submit": ['button[type="submit"]', '[data-testid*="send-button"]', 'button[aria-label*="send"]'],
                    "response": ['div[role="article"]', '.message-content', '[data-testid*="bot-message"]']
                }
            },
            "gemini": {
                "prompt_selector": 'rich-textarea > div > p',
                "submit_selector": 'button[aria-label*="Send message"]',
                "response_selector": 'div[data-testid*="response"]',
                "wait_for_response": 8,
                "backup_selectors": {
                    "prompt": ['textarea[placeholder*="Enter a prompt"]', 'div[contenteditable="true"]', '[data-testid*="input-textarea"]'],
                    "submit": ['button[type="submit"]', '[data-testid*="send-button"]', 'button[aria-label*="Send"]'],
                    "response": ['div[role="main"]', '.response-container', '[data-testid*="answer"]']
                }
            },
            "perplexity": {
                "prompt_selector": 'input[placeholder*="Ask anything"]',
                "submit_selector": 'button[aria-label*="Submit"]',
                "response_selector": '#main',
                "wait_for_response": 10,
                "backup_selectors": {
                    "prompt": ['textarea[placeholder*="Ask"]', 'div[contenteditable="true"]', '#searchBox'],
                    "submit": ['button[type="submit"]', '[data-testid*="search-button"]', 'button[aria-label*="ask"]'],
                    "response": ['.answer-content', 'div[data-testid*="answer"]', '.search-result']
                }
            }
        }
        
        print("🚀 Prompt Dispatcher initialized")
    
    def _find_element_with_fallback(self, driver, service: str, element_type: str, timeout: int = 10):
        """Find element using primary selector with backup options"""
        config = self.service_configs[service]
        
        # Try primary selector first
        primary_selector = config[f"{element_type}_selector"]
        try:
            return driver.wait_for_element_visible(primary_selector, timeout=timeout)
        except Exception as e:
            print(f"⚠️ {service}: Primary {element_type} selector failed: {primary_selector}")
            
            # Try backup selectors
            backup_selectors = config["backup_selectors"][element_type]
            for backup_selector in backup_selectors:
                try:
                    print(f"🔄 {service}: Trying backup {element_type} selector: {backup_selector}")
                    return driver.wait_for_element_visible(backup_selector, timeout=timeout//2)
                except Exception:
                    continue
            
            # If all selectors fail, raise the original exception
            raise e
    
    def _submit_prompt_to_service(self, service: str, prompt: str, timeout: int = 60, retry_count: int = 2) -> ServiceResponse:
        """Submit prompt to a specific service and get response with human-like timing"""
        import random
        start_time = time.time()
        
        # Human-like startup delay (1-5 seconds, staggered)
        startup_delay = random.uniform(1.0, 5.0)
        print(f"🚀 Starting {service} driver with profile: profiles/{service}")
        print(f"⏳ Human-like startup delay: {startup_delay:.1f}s")
        time.sleep(startup_delay)
        
        for attempt in range(retry_count + 1):
            try:
                # Ensure service is ready
                if not self.validator.ensure_service_ready(service, self.driver_factory):
                    return ServiceResponse(
                        service=service,
                        success=False,
                        error_message=f"Service {service} not ready",
                        execution_time=time.time() - start_time,
                        retry_count=attempt
                    )
                
                # Get service configuration
                config = self.service_configs.get(service)
                if not config:
                    return ServiceResponse(
                        service=service,
                        success=False,
                        error_message=f"No configuration found for service {service}",
                        execution_time=time.time() - start_time,
                        retry_count=attempt
                    )
                
                # Execute prompt submission with better error handling
                try:
                    with self.driver_factory.get_driver(service, headed=False) as driver:
                        # Navigate to service
                        service_url = self.driver_factory.services[service]["url"]
                        driver.open(service_url)
                        
                        # Wait for page to load and verify login
                        driver.wait_for_element_visible("body", timeout=10)
                        
                        if not self.validator.is_logged_in(driver, service):
                            return ServiceResponse(
                                service=service,
                                success=False,
                                error_message=f"Not logged in to {service}",
                                execution_time=time.time() - start_time,
                                retry_count=attempt
                            )
                        
                        print(f"✅ {service}: Authentication verified, proceeding to prompt submission...")
                
                        # Find and fill prompt input with improved error handling
                        try:
                            # Find prompt input element with fallback selectors
                            print(f"🔍 {service}: Locating prompt input...")
                            prompt_element = self._find_element_with_fallback(driver, service, "prompt", timeout=10)
                            print(f"✅ {service}: Found prompt input element")
                            
                            # Clear existing content and focus
                            prompt_element.click()
                            prompt_element.clear()
                            
                            # Human-like typing delay (0.5-1.5 seconds to "think")
                            thinking_delay = random.uniform(0.5, 1.5)
                            print(f"💭 {service}: Human-like thinking delay: {thinking_delay:.1f}s")
                            time.sleep(thinking_delay)
                            
                            # Type the prompt with human-like timing
                            print(f"⌨️  {service}: Typing prompt...")
                            prompt_element.send_keys(prompt)
                            
                            # Human-like delay before clicking submit (0.3-0.8 seconds)
                            submit_delay = random.uniform(0.3, 0.8)
                            print(f"⏳ {service}: Pre-submit delay: {submit_delay:.1f}s")
                            time.sleep(submit_delay)
                            
                            # Find and click submit button
                            print(f"🔍 {service}: Locating submit button...")
                            submit_element = self._find_element_with_fallback(driver, service, "submit", timeout=10)
                            print(f"✅ {service}: Found submit button")
                            
                            submit_element.click()
                            print(f"📤 {service}: Prompt submitted! Waiting for response...")
                            
                            # Wait for response to appear with exponential backoff
                            base_wait = config["wait_for_response"]
                            response_wait = base_wait + random.uniform(0.0, 2.0)  # Add variance
                            max_response_wait = 15  # Maximum wait time
                            
                            print(f"⏳ {service}: Waiting {response_wait:.1f}s for initial response...")
                            time.sleep(response_wait)
                            
                            # Try to find response with multiple attempts
                            response_text = None
                            for response_attempt in range(3):
                                try:
                                    print(f"🔍 {service}: Looking for response (attempt {response_attempt + 1}/3)...")
                                    response_element = self._find_element_with_fallback(driver, service, "response", timeout=5)
                                    response_text = response_element.text.strip()
                                    
                                    if response_text and len(response_text) > 10:  # Ensure we got substantial content
                                        print(f"✅ {service}: Response captured ({len(response_text)} chars)")
                                        break
                                    else:
                                        print(f"⚠️ {service}: Response too short, waiting longer...")
                                        time.sleep(3)
                                        
                                except Exception as resp_e:
                                    print(f"⚠️ {service}: Response attempt {response_attempt + 1} failed: {resp_e}")
                                    if response_attempt < 2:  # Not the last attempt
                                        time.sleep(3)
                                        continue
                                    else:
                                        raise resp_e
                            
                            if response_text and len(response_text) > 10:
                                return ServiceResponse(
                                    service=service,
                                    success=True,
                                    response=response_text,
                                    execution_time=time.time() - start_time,
                                    retry_count=attempt
                                )
                            else:
                                return ServiceResponse(
                                    service=service,
                                    success=False,
                                    error_message=f"No valid response found (got: '{response_text[:50]}...')",
                                    execution_time=time.time() - start_time,
                                    retry_count=attempt
                                )
                        
                        except Exception as e:
                            error_msg = f"Failed to submit prompt: {str(e)}"
                            print(f"❌ {service}: {error_msg}")
                            return ServiceResponse(
                                service=service,
                                success=False,
                                error_message=error_msg,
                                execution_time=time.time() - start_time,
                                retry_count=attempt
                            )
                
                except Exception as browser_error:
                    if attempt < retry_count:
                        print(f"🔄 {service} browser error, retrying ({attempt + 1}/{retry_count}): {str(browser_error)[:100]}")
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        return ServiceResponse(
                            service=service,
                            success=False,
                            error_message=f"Browser error: {str(browser_error)[:200]}",
                            execution_time=time.time() - start_time,
                            retry_count=attempt
                        )
            
            except Exception as e:
                if attempt < retry_count:
                    print(f"⚠️  {service} attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2)
                    continue
                
                return ServiceResponse(
                    service=service,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time,
                    retry_count=attempt
                )
        
        # Should not reach here, but fallback
        return ServiceResponse(
            service=service,
            success=False,
            error_message="Max retries exceeded",
            execution_time=time.time() - start_time,
            retry_count=retry_count
        )
    
    def _handle_confidential_request(self, request: PromptRequest) -> AggregatedResponse:
        """
        Handle confidential requests using local LLM only
        
        Args:
            request: PromptRequest marked as confidential
            
        Returns:
            AggregatedResponse with local LLM result only
        """
        start_time = time.time()
        request_id = f"conf_{int(start_time * 1000)}"
        
        print(f"\n🔒 Processing CONFIDENTIAL request locally")
        print(f"📋 Request ID: {request_id}")
        print(f"📝 Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
        print("🏠 Using local Phi-3-Mini model only")
        
        # Process with local LLM
        local_response = self.local_llm.process_confidential_data(request.prompt, "general")
        
        # Convert to ServiceResponse format
        service_response = ServiceResponse(
            service="local_phi3",
            success=local_response.success,
            response=local_response.response,
            error_message=local_response.error_message,
            execution_time=local_response.execution_time,
            retry_count=0,
            metadata={
                "model": local_response.model_name,
                "tokens_generated": local_response.tokens_generated,
                "confidential": True
            }
        )
        
        total_time = time.time() - start_time
        
        print(f"{'✅' if local_response.success else '❌'} Local LLM: {local_response.execution_time:.1f}s")
        
        return AggregatedResponse(
            request_id=request_id,
            prompt=request.prompt,
            responses=[service_response],
            total_execution_time=total_time,
            successful_services=1 if local_response.success else 0,
            failed_services=0 if local_response.success else 1,
            timestamp=start_time
        )

    def dispatch_prompt(self, request: PromptRequest) -> AggregatedResponse:
        """
        Dispatch prompt to multiple services in parallel
        
        Args:
            request: PromptRequest object containing prompt and target services
            
        Returns:
            AggregatedResponse with results from all services
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        # Check if this is a confidential request
        if request.confidential:
            return self._handle_confidential_request(request)
        
        print(f"\n🚀 Dispatching prompt to {len(request.services)} services")
        print(f"📋 Request ID: {request_id}")
        print(f"📝 Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
        print(f"🎯 Target services: {', '.join(request.services)}")
        
        # Validate services
        valid_services = []
        for service in request.services:
            if service in self.driver_factory.services:
                valid_services.append(service)
            else:
                print(f"⚠️  Unknown service: {service}")
        
        if not valid_services:
            return AggregatedResponse(
                request_id=request_id,
                prompt=request.prompt,
                responses=[],
                total_execution_time=time.time() - start_time,
                successful_services=0,
                failed_services=0,
                timestamp=start_time
            )
        
        # Execute sequentially to avoid Chrome profile conflicts, but with human-like timing
        import random
        responses = []
        
        print(f"🚀 Processing {len(valid_services)} services sequentially (with human-like timing)...")
        print("📝 Note: Sequential execution prevents Chrome profile conflicts")
        
        for i, service in enumerate(valid_services, 1):
            try:
                print(f"\n[{i}/{len(valid_services)}] 🚀 Starting {service}...")
                
                # Add inter-service delay (except for first service)
                if i > 1:
                    inter_service_delay = random.uniform(2.0, 4.0)
                    print(f"⏳ Inter-service delay: {inter_service_delay:.1f}s")
                    time.sleep(inter_service_delay)
                
                response = self._submit_prompt_to_service(
                    service,
                    request.prompt,
                    request.timeout,
                    request.retry_count
                )
                responses.append(response)
                
                status = "✅" if response.success else "❌"
                print(f"{status} {service}: {response.execution_time:.1f}s ({i}/{len(valid_services)} complete)")
                
            except Exception as e:
                print(f"❌ {service}: Exception - {e} ({i}/{len(valid_services)} complete)")
                responses.append(ServiceResponse(
                    service=service,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                ))
        
        # Calculate summary stats
        successful = sum(1 for r in responses if r.success)
        failed = len(responses) - successful
        total_time = time.time() - start_time
        
        print(f"\n📊 Results: {successful}/{len(responses)} successful in {total_time:.1f}s")
        
        return AggregatedResponse(
            request_id=request_id,
            prompt=request.prompt,
            responses=responses,
            total_execution_time=total_time,
            successful_services=successful,
            failed_services=failed,
            timestamp=start_time
        )
    
    def save_response(self, response: AggregatedResponse, output_dir: str = "logs") -> str:
        """Save aggregated response to JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        filename = f"response_{response.request_id}.json"
        filepath = output_path / filename
        
        # Convert to dict for JSON serialization
        response_dict = asdict(response)
        
        with open(filepath, 'w') as f:
            json.dump(response_dict, f, indent=2)
        
        print(f"💾 Response saved to: {filepath}")
        return str(filepath)
    
    def format_response_summary(self, response: AggregatedResponse) -> str:
        """Format a human-readable summary of the aggregated response"""
        lines = [
            f"🤖 Multi-Agent Response Summary",
            f"=" * 50,
            f"📋 Request ID: {response.request_id}",
            f"📝 Prompt: {response.prompt}",
            f"⏱️  Total Time: {response.total_execution_time:.1f}s",
            f"📊 Success Rate: {response.successful_services}/{response.successful_services + response.failed_services}",
            ""
        ]
        
        for resp in response.responses:
            status = "✅" if resp.success else "❌"
            lines.append(f"{status} {resp.service.title()} ({resp.execution_time:.1f}s)")
            
            if resp.success:
                # Truncate long responses
                content = resp.response[:200] + "..." if len(resp.response) > 200 else resp.response
                lines.append(f"   {content}")
            else:
                lines.append(f"   Error: {resp.error_message}")
            
            lines.append("")
        
        return "\n".join(lines)


def main():
    """Test the prompt dispatcher"""
    dispatcher = PromptDispatcher()
    
    print("🚀 Samay v3 - Prompt Dispatcher Test")
    print("=" * 50)
    
    # Example prompt request
    test_prompt = input("Enter a test prompt: ").strip()
    if not test_prompt:
        test_prompt = "What is the capital of France?"
    
    # Create request
    request = PromptRequest(
        prompt=test_prompt,
        services=["claude", "gemini", "perplexity"],
        timeout=30,
        retry_count=1
    )
    
    # Dispatch and get results
    response = dispatcher.dispatch_prompt(request)
    
    # Show formatted summary
    print(dispatcher.format_response_summary(response))
    
    # Save to file
    dispatcher.save_response(response)


if __name__ == "__main__":
    main()