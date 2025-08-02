"""
Synthesis Engine - Advanced Response Synthesis
Handles intelligent synthesis of multiple AI responses
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SynthesisEngine:
    """Engine for synthesizing multiple AI responses into comprehensive answers"""
    
    def __init__(self, local_assistant):
        self.local_assistant = local_assistant
        self.synthesis_count = 0
        
    async def synthesize_responses(self, original: Dict[str, str], followups: Optional[Dict[str, str]] = None) -> str:
        """Generate comprehensive synthesis from multiple AI responses"""
        try:
            self.synthesis_count += 1
            logger.info(f"🎯 Starting synthesis #{self.synthesis_count}")
            
            if not self.local_assistant or not self.local_assistant.is_initialized:
                return self._fallback_synthesis(original, followups)
            
            # Use local assistant for intelligent synthesis
            synthesis = await self.local_assistant.generate_synthesis(original, followups)
            
            logger.info(f"✅ Synthesis #{self.synthesis_count} completed")
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Synthesis failed: {e}")
            return self._fallback_synthesis(original, followups)
    
    def _fallback_synthesis(self, original: Dict[str, str], followups: Optional[Dict[str, str]] = None) -> str:
        """Fallback synthesis when local assistant is unavailable"""
        logger.info("⚠️ Using fallback synthesis")
        
        synthesis = "# Multi-AI Response Synthesis\n\n"
        
        # Add original responses
        for service, response in original.items():
            synthesis += f"## {service.upper()} Response\n\n"
            synthesis += f"{response}\n\n"
        
        # Add follow-up responses if available
        if followups:
            synthesis += "## Follow-up Responses\n\n"
            for service, response in followups.items():
                synthesis += f"### {service.upper()} Follow-up\n\n"
                synthesis += f"{response}\n\n"
        
        # Add basic summary
        synthesis += "## Summary\n\n"
        synthesis += f"This synthesis combines responses from {len(original)} AI services"
        if followups:
            synthesis += f" with {len(followups)} follow-up responses"
        synthesis += ". Each service provides unique perspectives on the query.\n\n"
        
        synthesis += f"*Generated: {datetime.utcnow().isoformat()}*"
        
        return synthesis