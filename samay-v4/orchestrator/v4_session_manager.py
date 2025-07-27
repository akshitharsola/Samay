#!/usr/bin/env python3
"""
Samay v4 - Session Manager  
==========================
Main orchestrator for desktop-first multi-agent AI queries
Integrates desktop automation with response processing
"""

import time
import uuid
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our v4 components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from desktop_automation.claude_desktop_automator import ClaudeDesktopAutomator
from desktop_automation.perplexity_desktop_automator import PerplexityDesktopAutomator
from desktop_automation.base_automator import AutomationStatus
from orchestrator.response_processor import ResponseProcessor, ProcessedResponse
from orchestrator.desktop_service_manager import DesktopServiceManager

@dataclass
class QueryRequest:
    prompt: str
    services: List[str] = None
    machine_code: bool = False
    timeout: int = 60
    session_id: str = None

@dataclass
class ServiceResult:
    service_id: str
    success: bool
    response: Optional[ProcessedResponse] = None
    error_message: str = ""
    execution_time: float = 0.0

@dataclass
class QueryResult:
    request_id: str
    session_id: str
    original_prompt: str
    final_prompt: str
    services_queried: List[str]
    service_results: List[ServiceResult]
    synthesized_response: Optional[ProcessedResponse] = None
    total_execution_time: float = 0.0
    timestamp: float = 0.0

class SamayV4SessionManager:
    """Main orchestrator for Samay v4 desktop-first automation"""
    
    def __init__(self, config_path: str = "config/desktop_services.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize core components
        self.service_manager = DesktopServiceManager(config_path)
        self.response_processor = ResponseProcessor(self.config.get("response_processing", {}))
        
        # Initialize service automators
        self.automators = {}
        self._initialize_automators()
        
        print(f"🚀 Samay v4 Session Manager initialized")
        print(f"📁 Config: {config_path}")
        print(f"🖥️  Available services: {list(self.automators.keys())}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Failed to load config: {e}")
            return {}
    
    def _initialize_automators(self):
        """Initialize desktop automators for available services"""
        services = self.config.get("services", {})
        
        for service_id, service_config in services.items():
            if not service_config.get("enabled", True):
                continue
                
            try:
                if service_id == "claude":
                    automator = ClaudeDesktopAutomator(service_config)
                    if automator.detect_app():
                        self.automators[service_id] = automator
                        print(f"✅ {service_id} automator ready")
                    else:
                        print(f"❌ {service_id} not detected")
                        
                elif service_id == "perplexity":
                    automator = PerplexityDesktopAutomator(service_config)
                    if automator.detect_app():
                        self.automators[service_id] = automator
                        print(f"✅ {service_id} automator ready")
                    else:
                        print(f"❌ {service_id} not detected")
                        
                # TODO: Add Gemini PWA automator
                # elif service_id == "gemini":
                #     automator = GeminiPWAAutomator(service_config)
                    
            except Exception as e:
                print(f"❌ Failed to initialize {service_id}: {e}")
    
    def get_available_services(self) -> List[str]:
        """Get list of available and ready services"""
        return list(self.automators.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        results = {}
        
        for service_id, automator in self.automators.items():
            try:
                health_result = automator.health_check()
                results[service_id] = {
                    "status": health_result.status.value,
                    "error": health_result.error_message,
                    "execution_time": health_result.execution_time
                }
            except Exception as e:
                results[service_id] = {
                    "status": "error",
                    "error": str(e),
                    "execution_time": 0.0
                }
        
        return {
            "overall_status": "healthy" if any(r["status"] == "success" for r in results.values()) else "degraded",
            "services": results,
            "timestamp": time.time()
        }
    
    def process_query(self, request: QueryRequest) -> QueryResult:
        """Process a multi-agent query using desktop automation"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        
        print(f"🔄 Processing query {request_id[:8]}...")
        print(f"📝 Prompt: {request.prompt[:100]}...")
        
        # Determine which services to use
        target_services = request.services or self.get_available_services()
        available_services = [s for s in target_services if s in self.automators]
        
        if not available_services:
            return QueryResult(
                request_id=request_id,
                session_id=session_id,
                original_prompt=request.prompt,
                final_prompt=request.prompt,
                services_queried=[],
                service_results=[],
                total_execution_time=time.time() - start_time,
                timestamp=time.time()
            )
        
        # Prepare the final prompt (handle machine code mode)
        final_prompt = self._prepare_prompt(request.prompt, request.machine_code)
        
        print(f"🎯 Querying services: {available_services}")
        if request.machine_code:
            print(f"🤖 Machine code mode enabled")
        
        # Execute queries in parallel
        service_results = self._execute_parallel_queries(available_services, final_prompt, request.timeout)
        
        # Process and synthesize responses
        synthesized_response = self._synthesize_responses(service_results)
        
        total_time = time.time() - start_time
        print(f"✅ Query completed in {total_time:.1f}s")
        
        return QueryResult(
            request_id=request_id,
            session_id=session_id,
            original_prompt=request.prompt,
            final_prompt=final_prompt,
            services_queried=available_services,
            service_results=service_results,
            synthesized_response=synthesized_response,
            total_execution_time=total_time,
            timestamp=time.time()
        )
    
    def _prepare_prompt(self, original_prompt: str, machine_code: bool) -> str:
        """Prepare the final prompt, adding machine code template if requested"""
        if machine_code:
            # Add the machine code template - this fixes the v3 issue where 
            # the user question was buried at the bottom
            return f'''Please respond to the following question in structured machine-readable format using this JSON template:

```json
{{
  "response": "your detailed response to the question here",
  "summary": "brief one-sentence summary of your response",
  "key_points": ["key point 1", "key point 2", "key point 3"],
  "confidence": 0.95,
  "category": "information|question|task|other"
}}
```

IMPORTANT: Please answer this question thoroughly: {original_prompt}'''
        else:
            return original_prompt
    
    def _execute_parallel_queries(self, services: List[str], prompt: str, timeout: int) -> List[ServiceResult]:
        """Execute queries across multiple services in parallel"""
        results = []
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=len(services)) as executor:
            # Submit all queries
            future_to_service = {}
            for service_id in services:
                future = executor.submit(self._query_single_service, service_id, prompt, timeout)
                future_to_service[future] = service_id
            
            # Collect results as they complete
            for future in as_completed(future_to_service.keys()):
                service_id = future_to_service[future]
                try:
                    result = future.result(timeout=timeout + 10)  # Add buffer for processing
                    results.append(result)
                    print(f"✅ {service_id}: {result.success}")
                except Exception as e:
                    results.append(ServiceResult(
                        service_id=service_id,
                        success=False,
                        error_message=f"Query execution failed: {str(e)}",
                        execution_time=0.0
                    ))
                    print(f"❌ {service_id}: {str(e)}")
        
        return results
    
    def _query_single_service(self, service_id: str, prompt: str, timeout: int) -> ServiceResult:
        """Query a single service and process the response"""
        start_time = time.time()
        
        try:
            automator = self.automators[service_id]
            
            # Perform the query
            query_result = automator.perform_query(prompt, timeout)
            
            if query_result.status == AutomationStatus.SUCCESS and query_result.data:
                # Process the raw response
                processed_response = self.response_processor.process_single_response(
                    query_result.data, service_id
                )
                
                return ServiceResult(
                    service_id=service_id,
                    success=True,
                    response=processed_response,
                    execution_time=time.time() - start_time
                )
            else:
                return ServiceResult(
                    service_id=service_id,
                    success=False,
                    error_message=query_result.error_message or "Unknown error",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ServiceResult(
                service_id=service_id,
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _synthesize_responses(self, service_results: List[ServiceResult]) -> Optional[ProcessedResponse]:
        """Synthesize responses from multiple services"""
        successful_responses = [r.response for r in service_results if r.success and r.response]
        
        if not successful_responses:
            return None
        
        return self.response_processor.synthesize_multi_service_responses(successful_responses)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the system status"""
        service_status = self.service_manager.get_summary()
        available_automators = list(self.automators.keys())
        
        return {
            "total_services_configured": service_status["total_services"],
            "services_installed": service_status["installed_services"],
            "services_with_automators": len(available_automators),
            "available_services": available_automators,
            "platform": service_status["platform"],
            "ready_for_queries": len(available_automators) > 0
        }


def main():
    """Test the v4 session manager"""
    print("🧪 Testing Samay v4 Session Manager")
    print("=" * 50)
    
    try:
        # Initialize session manager
        print("\n1. Initializing session manager...")
        manager = SamayV4SessionManager()
        
        # Get status summary
        print("\n2. System status:")
        status = manager.get_status_summary()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Health check
        print("\n3. Health check:")
        health = manager.health_check()
        print(f"   Overall status: {health['overall_status']}")
        for service_id, result in health["services"].items():
            print(f"   {service_id}: {result['status']}")
            if result.get("error"):
                print(f"      Error: {result['error']}")
        
        # Test query (commented out for safety - requires manual approval)
        print("\n4. Query testing available")
        print("To test a real query, uncomment the following lines:")
        print("# request = QueryRequest(")
        print("#     prompt='Hello, please respond with a simple greeting.',")
        print("#     machine_code=True")
        print("# )")
        print("# result = manager.process_query(request)")
        print("# print(f'Query result: {result.synthesized_response.main_response if result.synthesized_response else \"No response\"}')")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()