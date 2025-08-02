"""
Samay v5 Weather API Integration
Provides weather data for location-based queries
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WeatherAPI:
    """Weather API service using OpenWeatherMap"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo_key"  # For demo purposes
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """Get current weather for a location"""
        try:
            if self.api_key == "demo_key":
                # Return demo data for testing
                return self._get_demo_weather(location)
                
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_weather_data(data)
                else:
                    logger.error(f"Weather API error: {response.status}")
                    return self._get_demo_weather(location)
                    
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return self._get_demo_weather(location)
            
    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for a location"""
        try:
            if self.api_key == "demo_key":
                return self._get_demo_forecast(location, days)
                
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_forecast_data(data)
                else:
                    logger.error(f"Forecast API error: {response.status}")
                    return self._get_demo_forecast(location, days)
                    
        except Exception as e:
            logger.error(f"Forecast API error: {str(e)}")
            return self._get_demo_forecast(location, days)
            
    def _format_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format weather API response"""
        return {
            "location": data.get("name", "Unknown"),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": round(data.get("main", {}).get("temp", 0)),
            "feels_like": round(data.get("main", {}).get("feels_like", 0)),
            "humidity": data.get("main", {}).get("humidity", 0),
            "pressure": data.get("main", {}).get("pressure", 0),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "wind_speed": data.get("wind", {}).get("speed", 0),
            "visibility": data.get("visibility", 0) / 1000,  # Convert to km
            "timestamp": datetime.now().isoformat(),
            "source": "OpenWeatherMap"
        }
        
    def _format_forecast_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format forecast API response"""
        forecasts = []
        for item in data.get("list", []):
            forecasts.append({
                "datetime": item.get("dt_txt", ""),
                "temperature": round(item.get("main", {}).get("temp", 0)),
                "description": item.get("weather", [{}])[0].get("description", ""),
                "humidity": item.get("main", {}).get("humidity", 0),
                "wind_speed": item.get("wind", {}).get("speed", 0)
            })
            
        return {
            "location": data.get("city", {}).get("name", "Unknown"),
            "country": data.get("city", {}).get("country", ""),
            "forecasts": forecasts,
            "timestamp": datetime.now().isoformat(),
            "source": "OpenWeatherMap"
        }
        
    def _get_demo_weather(self, location: str) -> Dict[str, Any]:
        """Return demo weather data"""
        # Simulate different weather for different cities
        demo_data = {
            "ahmedabad": {
                "temperature": 28,
                "feels_like": 32,
                "humidity": 65,
                "description": "partly cloudy",
                "wind_speed": 12
            },
            "mumbai": {
                "temperature": 26,
                "feels_like": 30,
                "humidity": 78,
                "description": "humid and cloudy",
                "wind_speed": 8
            },
            "delhi": {
                "temperature": 22,
                "feels_like": 25,
                "humidity": 45,
                "description": "clear sky",
                "wind_speed": 15
            }
        }
        
        city_key = location.lower()
        weather = demo_data.get(city_key, demo_data["ahmedabad"])
        
        return {
            "location": location.title(),
            "country": "IN",
            "temperature": weather["temperature"],
            "feels_like": weather["feels_like"],
            "humidity": weather["humidity"],
            "pressure": 1013,
            "description": weather["description"],
            "wind_speed": weather["wind_speed"],
            "visibility": 10,
            "timestamp": datetime.now().isoformat(),
            "source": "Demo Data"
        }
        
    def _get_demo_forecast(self, location: str, days: int) -> Dict[str, Any]:
        """Return demo forecast data"""
        forecasts = []
        base_temp = 25
        
        for day in range(days):
            for hour in [6, 12, 18]:  # Morning, noon, evening
                forecasts.append({
                    "datetime": f"2024-08-0{day+1} {hour:02d}:00:00",
                    "temperature": base_temp + (day * 2) + (hour - 12) // 6,
                    "description": "partly cloudy" if day % 2 == 0 else "sunny",
                    "humidity": 60 + (day * 5),
                    "wind_speed": 10 + day
                })
                
        return {
            "location": location.title(),
            "country": "IN",
            "forecasts": forecasts,
            "timestamp": datetime.now().isoformat(),
            "source": "Demo Data"
        }

# Global weather API instance
weather_api = WeatherAPI()

async def get_weather_for_location(location: str) -> Dict[str, Any]:
    """Get weather data for a specific location"""
    async with WeatherAPI() as api:
        return await api.get_weather(location)

async def get_forecast_for_location(location: str, days: int = 5) -> Dict[str, Any]:
    """Get weather forecast for a specific location"""
    async with WeatherAPI() as api:
        return await api.get_forecast(location, days)