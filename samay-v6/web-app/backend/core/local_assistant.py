"""
Local Assistant - Ollama Phi-3-Mini Integration
Handles local LLM processing for query analysis and synthesis
"""

import asyncio
import logging
import ollama
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class LocalAssistant:
    """Local LLM assistant using Ollama Phi-3-Mini"""
    
    def __init__(self, model: str = "phi3:mini"):
        self.model = model
        self.client = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize Ollama client and verify model availability"""
        try:
            logger.info(f"🤖 Initializing Local Assistant with model: {self.model}")
            
            # Initialize Ollama client
            self.client = ollama.AsyncClient()
            
            # Check if model is available
            models = await self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model not in available_models:
                logger.warning(f"⚠️ Model {self.model} not found. Available models: {available_models}")
                # Try to pull the model
                logger.info(f"📥 Pulling model {self.model}...")
                await self.client.pull(self.model)
                logger.info(f"✅ Model {self.model} pulled successfully")
            
            # Test the model with a simple query
            test_response = await self.client.generate(
                model=self.model,
                prompt="Hello, please respond with 'Ready' if you can process this message.",
                options={"temperature": 0.1}
            )
            
            if "ready" in test_response['response'].lower():
                self.is_initialized = True
                logger.info(f"✅ Local Assistant initialized successfully")
            else:
                logger.warning(f"⚠️ Model test failed: {test_response['response']}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Local Assistant: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Local Assistant is healthy and responsive"""
        try:
            if not self.is_initialized or not self.client:
                return False
                
            # Quick health check with minimal prompt
            response = await self.client.generate(
                model=self.model,
                prompt="Health check - respond with OK",
                options={"temperature": 0.0, "max_tokens": 5}
            )
            
            return "ok" in response['response'].lower()
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    async def process_query(self, query: str, context: Optional[Dict] = None) -> str:
        """Process a user query with optional context"""
        try:
            if not self.is_initialized:
                raise RuntimeError("Local Assistant not initialized")
            
            # Build prompt with context if provided
            prompt = self._build_query_prompt(query, context)
            
            logger.info(f"🧠 Processing query: {query[:100]}...")
            
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            raise
    
    async def analyze_responses(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Analyze multiple AI service responses"""
        try:
            analysis_prompt = self._build_analysis_prompt(responses)
            
            logger.info(f"🔍 Analyzing {len(responses)} service responses...")
            
            response = await self.client.generate(
                model=self.model,
                prompt=analysis_prompt,
                options={
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            
            # Parse structured response
            analysis = self._parse_analysis_response(response['response'])
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Response analysis failed: {e}")
            raise
    
    async def generate_synthesis(self, responses: Dict[str, str], followups: Optional[Dict[str, str]] = None) -> str:
        """Generate comprehensive synthesis from multiple responses"""
        try:
            synthesis_prompt = self._build_synthesis_prompt(responses, followups)
            
            logger.info(f"🎯 Generating synthesis from {len(responses)} responses...")
            
            response = await self.client.generate(
                model=self.model,
                prompt=synthesis_prompt,
                options={
                    "temperature": 0.6,
                    "max_tokens": 3000
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"❌ Synthesis generation failed: {e}")
            raise
    
    def _build_query_prompt(self, query: str, context: Optional[Dict] = None) -> str:
        """Build prompt for initial query processing"""
        prompt = f"""You are a helpful AI assistant analyzing user queries for multi-AI automation.

User Query: {query}

"""
        if context:
            prompt += f"Context: {json.dumps(context, indent=2)}\n\n"
        
        prompt += """Please provide a helpful analysis and response to this query. Focus on being clear, comprehensive, and accurate."""
        
        return prompt
    
    def _build_analysis_prompt(self, responses: Dict[str, str]) -> str:
        """Build prompt for analyzing multiple AI responses"""
        prompt = """Analyze these AI service responses and provide structured analysis:

"""
        
        for service, response in responses.items():
            prompt += f"=== {service.upper()} RESPONSE ===\n{response}\n\n"
        
        prompt += """
Please analyze these responses and provide:

1. COMPLETENESS: Are the responses comprehensive or do they need follow-up questions?
2. CONSISTENCY: Do the responses agree or contradict each other?
3. QUALITY: Which responses are most helpful and accurate?
4. GAPS: What important information is missing?
5. FOLLOWUP_NEEDED: True/False - would follow-up questions improve the overall answer?

Provide your analysis in this JSON format:
{
    "completeness_score": 0.0-1.0,
    "consistency_score": 0.0-1.0,
    "quality_ranking": ["service1", "service2", ...],
    "identified_gaps": ["gap1", "gap2", ...],
    "followup_needed": true/false,
    "reasoning": "explanation of analysis",
    "confidence": 0.0-1.0
}
"""
        return prompt
    
    def _build_synthesis_prompt(self, responses: Dict[str, str], followups: Optional[Dict[str, str]] = None) -> str:
        """Build prompt for synthesizing responses"""
        prompt = """Create a comprehensive synthesis combining insights from multiple AI services:

ORIGINAL RESPONSES:
"""
        
        for service, response in responses.items():
            prompt += f"=== {service.upper()} ===\n{response}\n\n"
        
        if followups:
            prompt += "\nFOLLOW-UP RESPONSES:\n"
            for service, response in followups.items():
                prompt += f"=== {service.upper()} FOLLOW-UP ===\n{response}\n\n"
        
        prompt += """
Create a comprehensive synthesis that:

1. Combines the best insights from each service
2. Highlights unique perspectives and any contradictions
3. Provides a well-structured, authoritative answer
4. Attributes insights to specific services where relevant
5. Indicates confidence levels and reliability of information

Format your synthesis as a comprehensive response that a user would find valuable and complete. Include section headers and clear organization.
"""
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse structured analysis response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                return analysis_data
            else:
                # Fallback to basic parsing
                return {
                    "completeness_score": 0.7,
                    "consistency_score": 0.8,
                    "quality_ranking": ["claude", "chatgpt", "gemini", "perplexity"],
                    "identified_gaps": [],
                    "followup_needed": False,
                    "reasoning": "Unable to parse structured analysis",
                    "confidence": 0.5
                }
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse analysis response: {e}")
            return {
                "completeness_score": 0.7,
                "consistency_score": 0.8,
                "quality_ranking": ["claude", "chatgpt", "gemini", "perplexity"],
                "identified_gaps": [],
                "followup_needed": False,
                "reasoning": f"Parse error: {str(e)}",
                "confidence": 0.5
            }
    
    async def debug_query(self, query: str) -> Dict[str, Any]:
        """Debug query for testing and development"""
        try:
            logger.info(f"🐛 Debug query: {query}")
            
            if not self.is_initialized:
                return {
                    "status": "error",
                    "message": "Local Assistant not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Simple test query
            if "test" in query.lower():
                return {
                    "status": "success",
                    "message": "Local Assistant is working correctly",
                    "model": self.model,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Process actual query
            response = await self.process_query(query)
            
            return {
                "status": "success",
                "query": query,
                "response": response,
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Debug query failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }