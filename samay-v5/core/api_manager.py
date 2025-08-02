"""
Universal API Service Manager
Provides unified interface for all AI service APIs and utility APIs
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import yaml
import os
from pathlib import Path

import httpx
import aiohttp
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceType(Enum):
    AI_SERVICE = "ai_service"
    UTILITY_API = "utility_api"
    LOCAL_LLM = "local_llm"


class ServiceStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class APIResponse:
    service: str
    content: str
    status_code: int
    response_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ServiceConfig:
    name: str
    service_type: ServiceType
    provider: str
    method: str
    url: str
    rate_limit: Dict[str, Any]
    selectors: Optional[Dict[str, str]] = None
    endpoints: Optional[Dict[str, str]] = None
    api_key_env: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self):
        self.call_times: Dict[str, List[float]] = {}
        
    def can_make_request(self, service: str, limit_per_minute: int) -> bool:
        now = time.time()
        if service not in self.call_times:
            self.call_times[service] = []
            
        # Clean old entries (older than 1 minute)
        self.call_times[service] = [
            t for t in self.call_times[service] 
            if now - t < 60
        ]
        
        return len(self.call_times[service]) < limit_per_minute
    
    def record_request(self, service: str):
        now = time.time()
        if service not in self.call_times:
            self.call_times[service] = []
        self.call_times[service].append(now)


class APIServiceManager:
    """Universal interface for all AI service APIs"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_services.yaml")
        self.services: Dict[str, ServiceConfig] = {}
        self.rate_limiter = RateLimiter()
        self.session_cache: Dict[str, Any] = {}
        
        # Load configuration
        self._load_configuration()
        
        # Initialize HTTP clients
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    def _load_configuration(self):
        """Load service configurations from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                return
                
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            # Load AI services
            if 'ai_services' in config_data:
                for name, service_config in config_data['ai_services'].items():
                    self.services[name] = ServiceConfig(
                        name=name,
                        service_type=ServiceType.AI_SERVICE,
                        provider=service_config.get('provider'),
                        method=service_config.get('method'),
                        url=service_config.get('url'),
                        rate_limit=service_config.get('rate_limit', {}),
                        selectors=service_config.get('selectors')
                    )
                    
            # Load utility APIs
            if 'utility_apis' in config_data:
                for name, api_config in config_data['utility_apis'].items():
                    self.services[name] = ServiceConfig(
                        name=name,
                        service_type=ServiceType.UTILITY_API,
                        provider=api_config.get('provider'),
                        method='api_call',
                        url=api_config.get('endpoint', ''),
                        rate_limit=api_config.get('free_tier', {}),
                        endpoints=api_config.get('endpoints'),
                        api_key_env=api_config.get('api_key_env')
                    )
                    
            logger.info(f"Loaded {len(self.services)} service configurations")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    async def query_service(self, service: str, prompt: str, **kwargs) -> APIResponse:
        """Universal API query with error handling and retries"""
        start_time = time.time()
        
        if service not in self.services:
            return APIResponse(
                service=service,
                content="",
                status_code=404,
                response_time=time.time() - start_time,
                metadata={},
                error=f"Service '{service}' not found"
            )
            
        service_config = self.services[service]
        
        try:
            # Check rate limits
            if not self._check_rate_limit(service):
                return APIResponse(
                    service=service,
                    content="",
                    status_code=429,
                    response_time=time.time() - start_time,
                    metadata={},
                    error="Rate limit exceeded"
                )
            
            # Route to appropriate handler
            if service_config.service_type == ServiceType.AI_SERVICE:
                response = await self._handle_ai_service(service_config, prompt, **kwargs)
            elif service_config.service_type == ServiceType.UTILITY_API:
                response = await self._handle_utility_api(service_config, prompt, **kwargs)
            else:
                response = APIResponse(
                    service=service,
                    content="",
                    status_code=501,
                    response_time=time.time() - start_time,
                    metadata={},
                    error="Service type not implemented"
                )
                
            # Record successful request
            self.rate_limiter.record_request(service)
            response.response_time = time.time() - start_time
            
            return response
            
        except Exception as e:
            logger.error(f"Error querying service {service}: {e}")
            return APIResponse(
                service=service,
                content="",
                status_code=500,
                response_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )

    async def query_multiple(self, services: List[str], prompt: str, **kwargs) -> List[APIResponse]:
        """Parallel multi-service queries with response synthesis"""
        tasks = [
            self.query_service(service, prompt, **kwargs) 
            for service in services
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in responses
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                valid_responses.append(APIResponse(
                    service=services[i],
                    content="",
                    status_code=500,
                    response_time=0.0,
                    metadata={},
                    error=str(response)
                ))
            else:
                valid_responses.append(response)
                
        return valid_responses

    async def _handle_ai_service(self, config: ServiceConfig, prompt: str, **kwargs) -> APIResponse:
        """Handle AI service requests (browser automation)"""
        start_time = time.time()
        
        try:
            # Try to import browser automation
            from .browser_automation import query_ai_services, AIService
            
            # Map service names to AIService enum
            service_mapping = {
                'chatgpt': AIService.CHATGPT,
                'claude': AIService.CLAUDE,
                'gemini': AIService.GEMINI,
                'perplexity': AIService.PERPLEXITY
            }
            
            if config.name.lower() not in service_mapping:
                return APIResponse(
                    service=config.name,
                    content="",
                    status_code=404,
                    response_time=time.time() - start_time,
                    metadata={},
                    error=f"AI service '{config.name}' not supported"
                )
            
            ai_service = service_mapping[config.name.lower()]
            logger.info(f"Starting browser automation for {config.name} with query: {prompt}")
            
            # Call browser automation
            result = await query_ai_services([ai_service], prompt)
            
            if result and ai_service in result:
                service_result = result[ai_service]
                return APIResponse(
                    service=config.name,
                    content=service_result.get('response', ''),
                    status_code=200 if service_result.get('status') == 'success' else 500,
                    response_time=time.time() - start_time,
                    metadata={
                        "method": "browser_automation",
                        "provider": config.provider,
                        "browser_status": service_result.get('status', 'unknown')
                    },
                    error=service_result.get('error')
                )
            else:
                return APIResponse(
                    service=config.name,
                    content="",
                    status_code=500,
                    response_time=time.time() - start_time,
                    metadata={"method": "browser_automation"},
                    error="No response from browser automation"
                )
                
        except ImportError:
            logger.warning(f"Browser automation not available for {config.name}")
            return APIResponse(
                service=config.name,
                content="",
                status_code=503,
                response_time=time.time() - start_time,
                metadata={"method": "browser_automation"},
                error="Browser automation dependencies not available"
            )
        except Exception as e:
            logger.error(f"Browser automation failed for {config.name}: {e}")
            return APIResponse(
                service=config.name,
                content="",
                status_code=500,
                response_time=time.time() - start_time,
                metadata={"method": "browser_automation"},
                error=str(e)
            )

    async def _handle_utility_api(self, config: ServiceConfig, query: str, **kwargs) -> APIResponse:
        """Handle utility API requests"""
        api_key = os.getenv(config.api_key_env) if config.api_key_env else None
        
        if config.name == "weather":
            return await self._handle_weather_api(config, query, api_key, **kwargs)
        elif config.name == "news":
            return await self._handle_news_api(config, query, api_key, **kwargs)
        elif config.name == "currency":
            return await self._handle_currency_api(config, query, api_key, **kwargs)
        elif config.name == "translate":
            return await self._handle_translate_api(config, query, **kwargs)
        else:
            return APIResponse(
                service=config.name,
                content="",
                status_code=501,
                response_time=0.0,
                metadata={},
                error=f"Utility API handler not implemented for {config.name}"
            )

    async def _handle_weather_api(self, config: ServiceConfig, query: str, api_key: str, **kwargs) -> APIResponse:
        """Handle weather API requests"""
        if not api_key:
            return APIResponse(
                service="weather",
                content="",
                status_code=401,
                response_time=0.0,
                metadata={},
                error="Weather API key not configured"
            )
        
        # Extract location from query (simplified)
        location = kwargs.get('location', 'London')  # Default location
        
        url = f"{config.endpoints['current']}?q={location}&appid={api_key}&units=metric"
        
        try:
            async with self.http_client as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    weather_info = f"""Weather in {data['name']}: 
                    Temperature: {data['main']['temp']}°C
                    Description: {data['weather'][0]['description']}
                    Humidity: {data['main']['humidity']}%
                    Wind Speed: {data['wind']['speed']} m/s"""
                    
                    return APIResponse(
                        service="weather",
                        content=weather_info,
                        status_code=200,
                        response_time=0.0,
                        metadata=data
                    )
                else:
                    return APIResponse(
                        service="weather",
                        content="",
                        status_code=response.status_code,
                        response_time=0.0,
                        metadata={},
                        error=f"Weather API error: {response.text}"
                    )
                    
        except Exception as e:
            return APIResponse(
                service="weather",
                content="",
                status_code=500,
                response_time=0.0,
                metadata={},
                error=f"Weather API request failed: {e}"
            )

    async def _handle_news_api(self, config: ServiceConfig, query: str, api_key: str, **kwargs) -> APIResponse:
        """Handle news API requests"""
        if not api_key:
            return APIResponse(
                service="news",
                content="",
                status_code=401,
                response_time=0.0,
                metadata={},
                error="News API key not configured"
            )
        
        # Use the query as search term
        search_term = kwargs.get('q', query)
        url = f"{config.endpoints['everything']}?q={search_term}&apiKey={api_key}&pageSize=5"
        
        try:
            async with self.http_client as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    news_summary = "Latest News:\n"
                    for article in articles[:5]:
                        news_summary += f"• {article['title']}\n"
                        news_summary += f"  Source: {article['source']['name']}\n"
                        news_summary += f"  {article['description'][:100]}...\n\n"
                    
                    return APIResponse(
                        service="news",
                        content=news_summary,
                        status_code=200,
                        response_time=0.0,
                        metadata=data
                    )
                else:
                    return APIResponse(
                        service="news",
                        content="",
                        status_code=response.status_code,
                        response_time=0.0,
                        metadata={},
                        error=f"News API error: {response.text}"
                    )
                    
        except Exception as e:
            return APIResponse(
                service="news",
                content="",
                status_code=500,
                response_time=0.0,
                metadata={},
                error=f"News API request failed: {e}"
            )

    async def _handle_currency_api(self, config: ServiceConfig, query: str, api_key: str, **kwargs) -> APIResponse:
        """Handle currency conversion API requests"""
        if not api_key:
            return APIResponse(
                service="currency",
                content="",
                status_code=401,
                response_time=0.0,
                metadata={},
                error="Currency API key not configured"
            )
        
        from_currency = kwargs.get('from', 'USD')
        to_currency = kwargs.get('to', 'EUR')
        amount = kwargs.get('amount', 1)
        
        url = f"{config.url}/{api_key}/pair/{from_currency}/{to_currency}/{amount}"
        
        try:
            async with self.http_client as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('result') == 'success':
                        conversion_result = f"""Currency Conversion:
                        {amount} {from_currency} = {data['conversion_result']} {to_currency}
                        Exchange Rate: {data['conversion_rate']}
                        Last Updated: {data['time_last_update_utc']}"""
                        
                        return APIResponse(
                            service="currency",
                            content=conversion_result,
                            status_code=200,
                            response_time=0.0,
                            metadata=data
                        )
                    else:
                        return APIResponse(
                            service="currency",
                            content="",
                            status_code=400,
                            response_time=0.0,
                            metadata={},
                            error=f"Currency API error: {data.get('error-type', 'Unknown error')}"
                        )
                else:
                    return APIResponse(
                        service="currency",
                        content="",
                        status_code=response.status_code,
                        response_time=0.0,
                        metadata={},
                        error=f"Currency API error: {response.text}"
                    )
                    
        except Exception as e:
            return APIResponse(
                service="currency",
                content="",
                status_code=500,
                response_time=0.0,
                metadata={},
                error=f"Currency API request failed: {e}"
            )

    async def _handle_translate_api(self, config: ServiceConfig, query: str, **kwargs) -> APIResponse:
        """Handle translation API requests (MyMemory - free)"""
        text = kwargs.get('text', query)
        from_lang = kwargs.get('from', 'en')
        to_lang = kwargs.get('to', 'es')
        
        url = f"{config.url}?q={text}&langpair={from_lang}|{to_lang}"
        
        try:
            async with self.http_client as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    translated_text = data['responseData']['translatedText']
                    
                    translation_result = f"""Translation:
                    Original ({from_lang}): {text}
                    Translated ({to_lang}): {translated_text}
                    Match Quality: {data['responseData'].get('match', 'N/A')}"""
                    
                    return APIResponse(
                        service="translate",
                        content=translation_result,
                        status_code=200,
                        response_time=0.0,
                        metadata=data
                    )
                else:
                    return APIResponse(
                        service="translate",
                        content="",
                        status_code=response.status_code,
                        response_time=0.0,
                        metadata={},
                        error=f"Translation API error: {response.text}"
                    )
                    
        except Exception as e:
            return APIResponse(
                service="translate",
                content="",
                status_code=500,
                response_time=0.0,
                metadata={},
                error=f"Translation API request failed: {e}"
            )

    def _check_rate_limit(self, service: str) -> bool:
        """Check if service is within rate limits"""
        # Simple rate limiting - can be enhanced
        return self.rate_limiter.can_make_request(service, 60)  # 60 requests per minute default

    def get_service_status(self) -> Dict[str, ServiceStatus]:
        """Check all service availability and rate limit status"""
        status = {}
        for service_name in self.services.keys():
            # Simple status check - can be enhanced with actual health checks
            if self._check_rate_limit(service_name):
                status[service_name] = ServiceStatus.AVAILABLE
            else:
                status[service_name] = ServiceStatus.RATE_LIMITED
        return status

    async def close(self):
        """Clean up resources"""
        await self.http_client.aclose()


# Example usage
async def main():
    """Test the API manager"""
    manager = APIServiceManager()
    
    # Test weather API
    weather_response = await manager.query_service("weather", "weather", location="London")
    print(f"Weather: {weather_response.content}")
    
    # Test multiple services
    responses = await manager.query_multiple(["weather", "news"], "test query")
    for response in responses:
        print(f"{response.service}: {response.status_code}")
    
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())