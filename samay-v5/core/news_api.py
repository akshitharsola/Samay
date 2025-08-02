"""
Samay v5 News API Integration
Provides news data for current events queries
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAPI:
    """News API service using NewsAPI.org"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo_key"  # For demo purposes
        self.base_url = "https://newsapi.org/v2"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_top_headlines(self, country: str = "in", category: Optional[str] = None) -> Dict[str, Any]:
        """Get top headlines for a country/category"""
        try:
            if self.api_key == "demo_key":
                return self._get_demo_headlines(country, category)
                
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/top-headlines"
            params = {
                "apiKey": self.api_key,
                "country": country,
                "pageSize": 10
            }
            
            if category:
                params["category"] = category
                
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_news_data(data, "top_headlines")
                else:
                    logger.error(f"News API error: {response.status}")
                    return self._get_demo_headlines(country, category)
                    
        except Exception as e:
            logger.error(f"News API error: {str(e)}")
            return self._get_demo_headlines(country, category)
            
    async def search_news(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Search for news articles by query"""
        try:
            if self.api_key == "demo_key":
                return self._get_demo_search_results(query)
                
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/everything"
            params = {
                "apiKey": self.api_key,
                "q": query,
                "language": language,
                "sortBy": "relevancy",
                "pageSize": 10
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_news_data(data, "search")
                else:
                    logger.error(f"News search API error: {response.status}")
                    return self._get_demo_search_results(query)
                    
        except Exception as e:
            logger.error(f"News search API error: {str(e)}")
            return self._get_demo_search_results(query)
            
    def _format_news_data(self, data: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """Format news API response"""
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", ""),
                "author": article.get("author", ""),
                "published_at": article.get("publishedAt", ""),
                "url_to_image": article.get("urlToImage", "")
            })
            
        return {
            "total_results": data.get("totalResults", 0),
            "articles": articles,
            "query_type": query_type,
            "timestamp": datetime.now().isoformat(),
            "source": "NewsAPI.org"
        }
        
    def _get_demo_headlines(self, country: str, category: Optional[str]) -> Dict[str, Any]:
        """Return demo headlines"""
        demo_articles = [
            {
                "title": "India's Tech Sector Shows Strong Growth in Q3 2024",
                "description": "Indian technology companies report significant revenue increases driven by AI and automation projects.",
                "url": "https://example.com/tech-growth",
                "source": "Tech Times India",
                "author": "Priya Sharma",
                "published_at": datetime.now().isoformat(),
                "url_to_image": ""
            },
            {
                "title": "Monsoon Season Brings Relief to Drought-Affected Regions",
                "description": "Good rainfall across western and central India improves water levels and agricultural outlook.",
                "url": "https://example.com/monsoon-update",
                "source": "Weather News",
                "author": "Raj Patel",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "url_to_image": ""
            },
            {
                "title": "New Infrastructure Projects Announced for Gujarat",
                "description": "State government announces major transportation and digital infrastructure investments.",
                "url": "https://example.com/gujarat-infrastructure",
                "source": "Gujarat Today",
                "author": "Amit Shah",
                "published_at": (datetime.now() - timedelta(hours=4)).isoformat(),
                "url_to_image": ""
            },
            {
                "title": "Renewable Energy Milestone: India Crosses 100GW Solar Capacity",
                "description": "The country achieves a significant milestone in its renewable energy journey.",
                "url": "https://example.com/solar-milestone",
                "source": "Green Energy India",
                "author": "Sunita Gupta",
                "published_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                "url_to_image": ""
            },
            {
                "title": "Cricket World Cup: India Advances to Semi-Finals",
                "description": "Strong performance by the Indian cricket team secures semi-final spot.",
                "url": "https://example.com/cricket-semis",
                "source": "Sports Central",
                "author": "Rohit Kumar",
                "published_at": (datetime.now() - timedelta(hours=8)).isoformat(),
                "url_to_image": ""
            }
        ]
        
        # Filter by category if specified
        if category == "technology":
            demo_articles = [a for a in demo_articles if "tech" in a["title"].lower() or "tech" in a["description"].lower()]
        elif category == "sports":
            demo_articles = [a for a in demo_articles if "cricket" in a["title"].lower() or "sport" in a["description"].lower()]
        elif category == "business":
            demo_articles = [a for a in demo_articles if "growth" in a["title"].lower() or "infrastructure" in a["title"].lower()]
            
        return {
            "total_results": len(demo_articles),
            "articles": demo_articles,
            "query_type": "top_headlines",
            "timestamp": datetime.now().isoformat(),
            "source": "Demo Data"
        }
        
    def _get_demo_search_results(self, query: str) -> Dict[str, Any]:
        """Return demo search results"""
        # Generate relevant articles based on query
        query_lower = query.lower()
        
        if "weather" in query_lower:
            articles = [
                {
                    "title": "Extreme Weather Events Increase Globally",
                    "description": "Climate scientists report rising frequency of severe weather patterns worldwide.",
                    "url": "https://example.com/weather-patterns",
                    "source": "Climate News",
                    "author": "Dr. Sarah Johnson",
                    "published_at": datetime.now().isoformat(),
                    "url_to_image": ""
                }
            ]
        elif "technology" in query_lower or "ai" in query_lower:
            articles = [
                {
                    "title": "Artificial Intelligence Transforms Healthcare Industry",
                    "description": "AI applications in medical diagnosis and treatment show promising results.",
                    "url": "https://example.com/ai-healthcare",
                    "source": "Medical Tech Today",
                    "author": "Dr. Michael Chen",
                    "published_at": datetime.now().isoformat(),
                    "url_to_image": ""
                }
            ]
        else:
            articles = [
                {
                    "title": f"Latest Updates on {query.title()}",
                    "description": f"Comprehensive coverage of recent developments related to {query}.",
                    "url": f"https://example.com/{query.lower().replace(' ', '-')}",
                    "source": "News Today",
                    "author": "News Team",
                    "published_at": datetime.now().isoformat(),
                    "url_to_image": ""
                }
            ]
            
        return {
            "total_results": len(articles),
            "articles": articles,
            "query_type": "search",
            "timestamp": datetime.now().isoformat(),
            "source": "Demo Data"
        }

# Global news API instance
news_api = NewsAPI()

async def get_headlines(country: str = "in", category: Optional[str] = None) -> Dict[str, Any]:
    """Get top headlines"""
    async with NewsAPI() as api:
        return await api.get_top_headlines(country, category)

async def search_news_articles(query: str, language: str = "en") -> Dict[str, Any]:
    """Search news articles"""
    async with NewsAPI() as api:
        return await api.search_news(query, language)