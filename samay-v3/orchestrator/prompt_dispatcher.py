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
        
        # Service configurations for prompt submission
        self.service_configs = {
            "claude": {
                "prompt_selector": 'div[contenteditable="true"]',
                "submit_selector": 'button[aria-label="Send Message"]',
                "response_selector": '.font-claude-message',
                "wait_for_response": 3
            },
            "gemini": {
                "prompt_selector": 'div[contenteditable="true"]',
                "submit_selector": 'button[aria-label="Send message"]',
                "response_selector": '.model-response-text',
                "wait_for_response": 3
            },
            "perplexity": {
                "prompt_selector": 'textarea[placeholder*="Ask anything"]',
                "submit_selector": 'button[aria-label="Submit"]',
                "response_selector": '.prose',
                "wait_for_response": 5
            }
        }
        
        print("🚀 Prompt Dispatcher initialized")
    
    def _submit_prompt_to_service(self, service: str, prompt: str, timeout: int = 60, retry_count: int = 2) -> ServiceResponse:
        """Submit prompt to a specific service and get response"""
        start_time = time.time()
        
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
                
                # Execute prompt submission
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
                    
                    # Find and fill prompt input
                    try:
                        prompt_element = driver.wait_for_element_visible(
                            config["prompt_selector"], timeout=10
                        )
                        
                        # Clear and enter prompt
                        driver.clear(config["prompt_selector"])
                        driver.type(config["prompt_selector"], prompt)
                        
                        # Submit prompt
                        driver.click(config["submit_selector"])
                        
                        # Wait for response to appear
                        time.sleep(config["wait_for_response"])
                        
                        # Extract response
                        try:
                            response_elements = driver.find_elements(config["response_selector"])
                            if response_elements:
                                # Get the last response (most recent)
                                response_text = response_elements[-1].text.strip()
                                
                                return ServiceResponse(
                                    service=service,
                                    success=True,
                                    response=response_text,
                                    execution_time=time.time() - start_time,
                                    retry_count=attempt
                                )
                            else:
                                # If no response found, wait a bit more and try again
                                if attempt < retry_count:
                                    time.sleep(2)
                                    continue
                                
                                return ServiceResponse(
                                    service=service,
                                    success=False,
                                    error_message="No response found",
                                    execution_time=time.time() - start_time,
                                    retry_count=attempt
                                )
                        
                        except Exception as e:
                            return ServiceResponse(
                                service=service,
                                success=False,
                                error_message=f"Failed to extract response: {str(e)}",
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
                            error_message=f"Failed to submit prompt: {str(e)}",
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
        
        # Execute in parallel using ThreadPool
        responses = []
        
        with ThreadPoolExecutor(max_workers=len(valid_services)) as executor:
            # Submit all tasks
            future_to_service = {
                executor.submit(
                    self._submit_prompt_to_service,
                    service,
                    request.prompt,
                    request.timeout,
                    request.retry_count
                ): service
                for service in valid_services
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_service):
                service = future_to_service[future]
                try:
                    response = future.result()
                    responses.append(response)
                    
                    status = "✅" if response.success else "❌"
                    print(f"{status} {service}: {response.execution_time:.1f}s")
                    
                except Exception as e:
                    print(f"❌ {service}: Exception - {e}")
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