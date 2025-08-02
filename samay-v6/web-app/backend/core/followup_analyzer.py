"""
Follow-up Analyzer - Intelligent Follow-up Question Generation
Analyzes responses to determine if follow-up questions would improve results
"""

import logging
from typing import Dict, List, Optional, Any, NamedTuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FollowupAnalysis(NamedTuple):
    """Result of follow-up analysis"""
    needs_followup: bool
    reasoning: str
    questions: Dict[str, str]  # service -> question
    confidence: float

class FollowupAnalyzer:
    """Analyzer for determining follow-up question needs"""
    
    def __init__(self, local_assistant):
        self.local_assistant = local_assistant
        self.analysis_count = 0
        
    async def analyze_responses(self, responses: Dict[str, str]) -> FollowupAnalysis:
        """Analyze responses to determine if follow-up questions are needed"""
        try:
            self.analysis_count += 1
            logger.info(f"🔍 Starting follow-up analysis #{self.analysis_count}")
            
            if not self.local_assistant or not self.local_assistant.is_initialized:
                return self._fallback_analysis(responses)
            
            # Use local assistant for intelligent analysis
            analysis_result = await self.local_assistant.analyze_responses(responses)
            
            # Extract follow-up questions if needed
            questions = {}
            if analysis_result.get('followup_needed', False):
                questions = await self._generate_followup_questions(responses, analysis_result)
            
            logger.info(f"✅ Follow-up analysis #{self.analysis_count} completed")
            
            return FollowupAnalysis(
                needs_followup=analysis_result.get('followup_needed', False),
                reasoning=analysis_result.get('reasoning', 'Analysis completed'),
                questions=questions,
                confidence=analysis_result.get('confidence', 0.7)
            )
            
        except Exception as e:
            logger.error(f"❌ Follow-up analysis failed: {e}")
            return self._fallback_analysis(responses)
    
    async def _generate_followup_questions(self, responses: Dict[str, str], analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate specific follow-up questions for each service"""
        questions = {}
        
        try:
            gaps = analysis.get('identified_gaps', [])
            if not gaps:
                return questions
            
            # Generate service-specific follow-up questions
            for service in responses.keys():
                if service == 'chatgpt':
                    questions[service] = f"Can you provide more details about: {', '.join(gaps[:2])}?"
                elif service == 'claude':
                    questions[service] = f"Please elaborate on the following aspects: {', '.join(gaps[:2])}"
                elif service == 'gemini':
                    questions[service] = f"What additional information can you provide about: {', '.join(gaps[:2])}?"
                elif service == 'perplexity':
                    questions[service] = f"Can you research and provide more context on: {', '.join(gaps[:2])}?"
            
            logger.info(f"📝 Generated {len(questions)} follow-up questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Follow-up question generation failed: {e}")
            return {}
    
    def _fallback_analysis(self, responses: Dict[str, str]) -> FollowupAnalysis:
        """Fallback analysis when local assistant is unavailable"""
        logger.info("⚠️ Using fallback follow-up analysis")
        
        # Simple heuristic: if responses are short, suggest follow-up
        avg_length = sum(len(response) for response in responses.values()) / len(responses)
        needs_followup = avg_length < 500  # If average response is less than 500 chars
        
        questions = {}
        if needs_followup:
            # Generate basic follow-up questions
            questions = {
                service: "Can you provide more detailed information about this topic?"
                for service in responses.keys()
            }
        
        return FollowupAnalysis(
            needs_followup=needs_followup,
            reasoning=f"Fallback analysis: Average response length is {avg_length:.0f} characters",
            questions=questions,
            confidence=0.6
        )
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about follow-up analyses performed"""
        return {
            "total_analyses": self.analysis_count,
            "timestamp": datetime.utcnow().isoformat()
        }