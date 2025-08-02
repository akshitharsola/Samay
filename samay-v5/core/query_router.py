"""
Intelligent Query Router
Routes queries to optimal services based on content and availability
"""

import asyncio
import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    FACTUAL = "factual"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    WEATHER = "weather"
    NEWS = "news"
    TRANSLATION = "translation"
    CURRENCY = "currency"
    MAPS = "maps"
    STOCK = "stock"
    TECHNICAL = "technical"
    GENERAL = "general"


class ServicePriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ServiceCapability:
    service_name: str
    query_types: List[QueryType]
    strengths: List[str]
    limitations: List[str]
    cost_per_query: float
    rate_limit_per_minute: int
    response_time_avg: float
    reliability_score: float


@dataclass
class RoutingDecision:
    selected_services: List[str]
    routing_strategy: str
    estimated_cost: float
    estimated_time: float
    confidence_score: float
    reasoning: str


class QueryRouter:
    """Route queries to optimal services based on content and availability"""
    
    def __init__(self, config_path: str = "config/rate_limits.yaml"):
        self.config_path = config_path
        self.service_capabilities = self._load_service_capabilities()
        self.routing_rules = self._load_routing_rules()
        self.service_status: Dict[str, Any] = {}
        
    def _load_service_capabilities(self) -> Dict[str, ServiceCapability]:
        """Load service capabilities and characteristics"""
        capabilities = {
            'claude': ServiceCapability(
                service_name='claude',
                query_types=[QueryType.CREATIVE, QueryType.ANALYTICAL, QueryType.TECHNICAL, QueryType.GENERAL],
                strengths=['creative_writing', 'code_analysis', 'reasoning', 'long_context'],
                limitations=['real_time_info', 'web_search'],
                cost_per_query=0.01,
                rate_limit_per_minute=20,
                response_time_avg=15.0,
                reliability_score=0.95
            ),
            
            'gemini': ServiceCapability(
                service_name='gemini',
                query_types=[QueryType.FACTUAL, QueryType.ANALYTICAL, QueryType.TECHNICAL, QueryType.GENERAL],
                strengths=['factual_accuracy', 'multimodal', 'google_integration', 'recent_info'],
                limitations=['creative_tasks', 'long_conversations'],
                cost_per_query=0.008,
                rate_limit_per_minute=15,
                response_time_avg=12.0,
                reliability_score=0.92
            ),
            
            'perplexity': ServiceCapability(
                service_name='perplexity',
                query_types=[QueryType.FACTUAL, QueryType.NEWS, QueryType.ANALYTICAL],
                strengths=['web_search', 'current_events', 'citations', 'research'],
                limitations=['creative_writing', 'personal_assistance'],
                cost_per_query=0.005,
                rate_limit_per_minute=25,
                response_time_avg=10.0,
                reliability_score=0.90
            ),
            
            'weather': ServiceCapability(
                service_name='weather',
                query_types=[QueryType.WEATHER],
                strengths=['real_time_weather', 'forecasts', 'location_based'],
                limitations=['non_weather_queries'],
                cost_per_query=0.0001,
                rate_limit_per_minute=60,
                response_time_avg=2.0,
                reliability_score=0.98
            ),
            
            'news': ServiceCapability(
                service_name='news',
                query_types=[QueryType.NEWS],
                strengths=['breaking_news', 'headlines', 'source_variety'],
                limitations=['analysis', 'historical_news'],
                cost_per_query=0.0002,
                rate_limit_per_minute=30,
                response_time_avg=3.0,
                reliability_score=0.95
            ),
            
            'translate': ServiceCapability(
                service_name='translate',
                query_types=[QueryType.TRANSLATION],
                strengths=['language_pairs', 'accuracy', 'free_tier'],
                limitations=['context_awareness', 'cultural_nuances'],
                cost_per_query=0.0,
                rate_limit_per_minute=100,
                response_time_avg=1.5,
                reliability_score=0.85
            ),
            
            'currency': ServiceCapability(
                service_name='currency',
                query_types=[QueryType.CURRENCY],
                strengths=['real_time_rates', 'multiple_currencies', 'historical_data'],
                limitations=['non_currency_queries', 'analysis'],
                cost_per_query=0.0001,
                rate_limit_per_minute=10,
                response_time_avg=2.5,
                reliability_score=0.96
            ),
            
            'maps': ServiceCapability(
                service_name='maps',
                query_types=[QueryType.MAPS],
                strengths=['geocoding', 'location_info', 'coordinates'],
                limitations=['routing', 'real_time_traffic'],
                cost_per_query=0.0002,
                rate_limit_per_minute=20,
                response_time_avg=3.0,
                reliability_score=0.94
            ),
            
            'stock': ServiceCapability(
                service_name='stock',
                query_types=[QueryType.STOCK],
                strengths=['stock_prices', 'financial_data', 'market_info'],
                limitations=['analysis', 'predictions', 'advice'],
                cost_per_query=0.001,
                rate_limit_per_minute=5,
                response_time_avg=4.0,
                reliability_score=0.93
            )
        }
        
        return capabilities

    def _load_routing_rules(self) -> Dict[str, Any]:
        """Load routing rules and strategies"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('intelligent_routing', {})
        except Exception as e:
            logger.error(f"Failed to load routing rules: {e}")
            
        # Default routing rules
        return {
            'priority_levels': {
                'high': ['weather', 'currency', 'translate'],
                'medium': ['news', 'maps', 'stock'],
                'low': ['claude', 'gemini', 'perplexity']
            },
            'fallback_strategy': {
                'primary': 'local_llm',
                'secondary': 'cached_response'
            },
            'cost_optimization': {
                'prefer_free_apis': True,
                'daily_budget_usd': 5.0,
                'cost_tracking': True
            }
        }

    def analyze_query_type(self, query: str) -> QueryType:
        """Classify query type based on content analysis"""
        query_lower = query.lower()
        
        # Define patterns for each query type
        patterns = {
            QueryType.WEATHER: [
                r'\b(weather|temperature|rain|snow|forecast|climate|humid|wind|storm)\b',
                r'\bhow.*(hot|cold|warm|cool|sunny|cloudy)\b',
                r'\bwhat.*(weather|temperature)\b'
            ],
            
            QueryType.NEWS: [
                r'\b(news|headlines|breaking|current events|latest|recent|today)\b',
                r'\bwhat.*(happen|news|latest)\b',
                r'\btell me about.*(news|events)\b'
            ],
            
            QueryType.TRANSLATION: [
                r'\b(translate|translation|mean in|say in|how to say)\b',
                r'\bin (spanish|french|german|italian|chinese|japanese|korean|arabic)\b',
                r'\bwhat does.*(mean|translate)\b'
            ],
            
            QueryType.CURRENCY: [
                r'\b(currency|exchange rate|convert|dollars|euros|yen|pounds)\b',
                r'\b(usd|eur|gbp|jpy|cad|aud|chf)\b',
                r'\bhow much.*(cost|worth|exchange)\b'
            ],
            
            QueryType.MAPS: [
                r'\b(location|address|coordinates|latitude|longitude|geocode)\b',
                r'\bwhere is\b',
                r'\bfind.*(location|place|address)\b'
            ],
            
            QueryType.STOCK: [
                r'\b(stock|shares|market|nasdaq|dow|s&p|trading|price)\b',
                r'\b(aapl|googl|msft|tsla|amzn)\b',
                r'\bstock price\b'
            ],
            
            QueryType.CREATIVE: [
                r'\b(write|create|story|poem|creative|imagine|draft|compose)\b',
                r'\bwrite me\b',
                r'\bcreate a\b'
            ],
            
            QueryType.ANALYTICAL: [
                r'\b(analyze|compare|evaluate|pros and cons|analysis|assess)\b',
                r'\bcompare\b',
                r'\bwhat are the (advantages|disadvantages|benefits|drawbacks)\b'
            ],
            
            QueryType.TECHNICAL: [
                r'\b(code|programming|debug|algorithm|function|class|api)\b',
                r'\bhow to (code|program|implement)\b',
                r'\b(python|javascript|java|c\+\+|react|node)\b'
            ]
        }
        
        # Score each query type
        scores = {}
        for query_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            scores[query_type] = score
        
        # Return the highest scoring type, or GENERAL if no clear match
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0:
                return best_type
                
        # Fallback logic for questions
        if any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            return QueryType.FACTUAL
            
        return QueryType.GENERAL

    def select_optimal_services(self, query: str, query_type: QueryType, available_services: List[str] = None) -> RoutingDecision:
        """Choose best services based on query type and constraints"""
        
        if available_services is None:
            available_services = list(self.service_capabilities.keys())
        
        # Filter services that can handle this query type
        suitable_services = []
        for service_name in available_services:
            if service_name in self.service_capabilities:
                capability = self.service_capabilities[service_name]
                if query_type in capability.query_types:
                    suitable_services.append(service_name)
        
        # If no suitable services, fall back to general AI services
        if not suitable_services:
            suitable_services = [s for s in available_services if s in ['claude', 'gemini', 'perplexity']]
        
        # Apply routing strategy based on query type
        selected_services = self._apply_routing_strategy(query_type, suitable_services, query)
        
        # Calculate estimates
        estimated_cost = self._calculate_estimated_cost(selected_services)
        estimated_time = self._calculate_estimated_time(selected_services)
        confidence_score = self._calculate_confidence_score(query_type, selected_services)
        
        # Generate reasoning
        reasoning = self._generate_routing_reasoning(query_type, selected_services, suitable_services)
        
        return RoutingDecision(
            selected_services=selected_services,
            routing_strategy=self._get_strategy_name(query_type),
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            confidence_score=confidence_score,
            reasoning=reasoning
        )

    def _apply_routing_strategy(self, query_type: QueryType, suitable_services: List[str], query: str) -> List[str]:
        """Apply routing strategy based on query type and preferences"""
        
        cost_optimization = self.routing_rules.get('cost_optimization', {})
        prefer_free = cost_optimization.get('prefer_free_apis', True)
        
        # Strategy 1: Direct API routing for specific services
        if query_type in [QueryType.WEATHER, QueryType.NEWS, QueryType.TRANSLATION, 
                         QueryType.CURRENCY, QueryType.MAPS, QueryType.STOCK]:
            # Use direct API for these specific query types
            return [query_type.value]
        
        # Strategy 2: Multiple AI services for complex queries
        elif query_type in [QueryType.ANALYTICAL, QueryType.TECHNICAL]:
            # Use multiple AI services for comprehensive analysis
            ai_services = [s for s in suitable_services if s in ['claude', 'gemini', 'perplexity']]
            return ai_services[:3]  # Limit to 3 services
        
        # Strategy 3: Creative tasks - prefer Claude
        elif query_type == QueryType.CREATIVE:
            if 'claude' in suitable_services:
                return ['claude']
            else:
                return suitable_services[:1]
        
        # Strategy 4: Factual queries - prefer Perplexity + Gemini
        elif query_type == QueryType.FACTUAL:
            preferred_order = ['perplexity', 'gemini', 'claude']
            selected = []
            for service in preferred_order:
                if service in suitable_services and len(selected) < 2:
                    selected.append(service)
            return selected or suitable_services[:1]
        
        # Strategy 5: General queries - use best available service
        else:
            # Sort by reliability and cost
            if prefer_free:
                free_services = [s for s in suitable_services 
                               if self.service_capabilities.get(s, ServiceCapability('', [], [], [], 1.0, 1, 1.0, 0.0)).cost_per_query == 0.0]
                if free_services:
                    return free_services[:1]
            
            # Sort by reliability score
            sorted_services = sorted(
                suitable_services,
                key=lambda s: self.service_capabilities.get(s, ServiceCapability('', [], [], [], 1.0, 1, 1.0, 0.0)).reliability_score,
                reverse=True
            )
            
            return sorted_services[:1]

    def _calculate_estimated_cost(self, services: List[str]) -> float:
        """Calculate estimated cost for selected services"""
        total_cost = 0.0
        for service in services:
            if service in self.service_capabilities:
                total_cost += self.service_capabilities[service].cost_per_query
        return total_cost

    def _calculate_estimated_time(self, services: List[str]) -> float:
        """Calculate estimated response time"""
        if not services:
            return 0.0
            
        # For parallel execution, use the slowest service time
        max_time = 0.0
        for service in services:
            if service in self.service_capabilities:
                service_time = self.service_capabilities[service].response_time_avg
                max_time = max(max_time, service_time)
                
        return max_time

    def _calculate_confidence_score(self, query_type: QueryType, services: List[str]) -> float:
        """Calculate confidence score for routing decision"""
        if not services:
            return 0.0
            
        # Base confidence on service reliability
        total_reliability = 0.0
        for service in services:
            if service in self.service_capabilities:
                capability = self.service_capabilities[service]
                # Bonus for query type match
                type_bonus = 1.2 if query_type in capability.query_types else 1.0
                total_reliability += capability.reliability_score * type_bonus
                
        avg_reliability = total_reliability / len(services)
        
        # Bonus for multiple services
        multi_service_bonus = min(len(services) * 0.1, 0.3)
        
        return min(avg_reliability + multi_service_bonus, 1.0)

    def _generate_routing_reasoning(self, query_type: QueryType, selected_services: List[str], 
                                  suitable_services: List[str]) -> str:
        """Generate human-readable reasoning for routing decision"""
        reasoning_parts = []
        
        # Query type analysis
        reasoning_parts.append(f"Analyzed query as type: {query_type.value}")
        
        # Service selection reasoning
        if query_type in [QueryType.WEATHER, QueryType.NEWS, QueryType.TRANSLATION, 
                         QueryType.CURRENCY, QueryType.MAPS, QueryType.STOCK]:
            reasoning_parts.append(f"Using direct API service for {query_type.value} queries")
        elif len(selected_services) > 1:
            reasoning_parts.append(f"Using multiple services ({', '.join(selected_services)}) for comprehensive response")
        else:
            service = selected_services[0] if selected_services else "none"
            if service in self.service_capabilities:
                strengths = self.service_capabilities[service].strengths
                reasoning_parts.append(f"Selected {service} for its strengths in: {', '.join(strengths[:2])}")
        
        # Cost consideration
        total_cost = self._calculate_estimated_cost(selected_services)
        if total_cost == 0.0:
            reasoning_parts.append("Using free tier services to minimize cost")
        elif total_cost < 0.01:
            reasoning_parts.append("Low-cost routing strategy applied")
        
        return ". ".join(reasoning_parts)

    def _get_strategy_name(self, query_type: QueryType) -> str:
        """Get strategy name for query type"""
        strategy_mapping = {
            QueryType.WEATHER: "direct_api",
            QueryType.NEWS: "direct_api", 
            QueryType.TRANSLATION: "direct_api",
            QueryType.CURRENCY: "direct_api",
            QueryType.MAPS: "direct_api",
            QueryType.STOCK: "direct_api",
            QueryType.ANALYTICAL: "multi_service",
            QueryType.TECHNICAL: "multi_service",
            QueryType.CREATIVE: "specialized_ai",
            QueryType.FACTUAL: "research_focused",
            QueryType.GENERAL: "best_available"
        }
        
        return strategy_mapping.get(query_type, "default")

    def update_service_status(self, service_status: Dict[str, Any]):
        """Update service availability status"""
        self.service_status = service_status

    def get_available_services(self) -> List[str]:
        """Get list of currently available services"""
        available = []
        for service, status in self.service_status.items():
            if status in ['available', 'authenticated']:
                available.append(service)
        
        # If no status info, assume all services are available
        if not available:
            available = list(self.service_capabilities.keys())
            
        return available

    def estimate_costs(self, services: List[str], queries_per_day: int = 100) -> Dict[str, float]:
        """Calculate estimated daily/monthly costs"""
        costs = {
            'per_query': self._calculate_estimated_cost(services),
            'daily': 0.0,
            'monthly': 0.0,
            'yearly': 0.0
        }
        
        costs['daily'] = costs['per_query'] * queries_per_day
        costs['monthly'] = costs['daily'] * 30
        costs['yearly'] = costs['daily'] * 365
        
        return costs

    def get_service_recommendations(self, query_history: List[str]) -> Dict[str, Any]:
        """Analyze query history and recommend optimal service configuration"""
        if not query_history:
            return {'recommendations': [], 'analysis': 'No query history available'}
        
        # Analyze query types distribution
        type_counts = {}
        for query in query_history:
            query_type = self.analyze_query_type(query)
            type_counts[query_type] = type_counts.get(query_type, 0) + 1
        
        # Generate recommendations
        recommendations = []
        total_queries = len(query_history)
        
        for query_type, count in type_counts.items():
            percentage = (count / total_queries) * 100
            if percentage > 20:  # If more than 20% of queries are this type
                optimal_services = self._get_optimal_services_for_type(query_type)
                recommendations.append({
                    'query_type': query_type.value,
                    'percentage': percentage,
                    'recommended_services': optimal_services,
                    'reason': f"High frequency of {query_type.value} queries"
                })
        
        analysis = f"Analyzed {total_queries} queries. Most common types: {', '.join([qt.value for qt in sorted(type_counts.keys(), key=type_counts.get, reverse=True)[:3]])}"
        
        return {
            'recommendations': recommendations,
            'analysis': analysis,
            'query_type_distribution': {qt.value: count for qt, count in type_counts.items()}
        }

    def _get_optimal_services_for_type(self, query_type: QueryType) -> List[str]:
        """Get optimal services for a specific query type"""
        suitable_services = []
        for service_name, capability in self.service_capabilities.items():
            if query_type in capability.query_types:
                suitable_services.append({
                    'service': service_name,
                    'score': capability.reliability_score - (capability.cost_per_query * 10)  # Factor in cost
                })
        
        # Sort by score and return top services
        suitable_services.sort(key=lambda x: x['score'], reverse=True)
        return [s['service'] for s in suitable_services[:3]]


# Example usage
async def main():
    """Test the query router"""
    router = QueryRouter()
    
    test_queries = [
        "What's the weather like in Tokyo?",
        "Write a creative story about space exploration",
        "Compare Python and JavaScript for web development",
        "Translate 'Hello World' to Spanish",
        "What's the latest news about AI?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        query_type = router.analyze_query_type(query)
        print(f"Type: {query_type}")
        
        decision = router.select_optimal_services(query, query_type)
        print(f"Services: {decision.selected_services}")
        print(f"Strategy: {decision.routing_strategy}")
        print(f"Cost: ${decision.estimated_cost:.4f}")
        print(f"Time: {decision.estimated_time:.1f}s")
        print(f"Confidence: {decision.confidence_score:.2f}")
        print(f"Reasoning: {decision.reasoning}")


if __name__ == "__main__":
    asyncio.run(main())