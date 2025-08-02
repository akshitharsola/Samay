"""
Response Synthesis Engine
Combines multiple API responses intelligently into coherent, comprehensive answers
"""

import asyncio
import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict

import ollama
from textblob import TextBlob  # For sentiment analysis and text processing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SynthesisStrategy(Enum):
    MERGE = "merge"
    COMPARE = "compare"
    PRIORITIZE = "prioritize"
    COMPLEMENT = "complement"
    FACT_CHECK = "fact_check"


class ContentType(Enum):
    FACTUAL = "factual"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    TECHNICAL = "technical"
    NEWS = "news"
    DATA = "data"


@dataclass
class ServiceResponse:
    service: str
    content: str
    status_code: int
    response_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None
    confidence_score: float = 0.0
    content_type: Optional[ContentType] = None
    key_facts: List[str] = None
    sources: List[str] = None


@dataclass
class SynthesisResult:
    synthesized_content: str
    strategy_used: SynthesisStrategy
    service_contributions: Dict[str, float]
    confidence_score: float
    fact_check_results: Dict[str, Any]
    contradictions: List[Dict[str, str]]
    unique_insights: Dict[str, List[str]]
    sources: List[str]
    processing_time: float


class ResponseSynthesizer:
    """Combine multiple API responses intelligently"""
    
    def __init__(self, local_model: str = "phi3:mini", ollama_base_url: str = "http://localhost:11434"):
        self.local_model = local_model
        self.ollama_base_url = ollama_base_url
        self.ollama_client = ollama.Client(host=ollama_base_url)
        
        # Response analysis cache
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        # Service reliability weights
        self.service_weights = {
            'claude': 0.95,
            'gemini': 0.92,
            'perplexity': 0.90,
            'weather': 0.98,
            'news': 0.85,
            'translate': 0.80,
            'currency': 0.95,
            'maps': 0.90,
            'stock': 0.88
        }

    async def synthesize_responses(self, responses: List[ServiceResponse], 
                                 original_query: str, 
                                 synthesis_strategy: SynthesisStrategy = None) -> SynthesisResult:
        """Main synthesis function that combines multiple service responses"""
        start_time = time.time()
        
        # Filter successful responses
        successful_responses = [r for r in responses if r.content and not r.error]
        
        if not successful_responses:
            return SynthesisResult(
                synthesized_content="No successful responses received from services.",
                strategy_used=SynthesisStrategy.MERGE,
                service_contributions={},
                confidence_score=0.0,
                fact_check_results={},
                contradictions=[],
                unique_insights={},
                sources=[],
                processing_time=time.time() - start_time
            )
        
        # Analyze responses
        analyzed_responses = await self._analyze_responses(successful_responses)
        
        # Determine synthesis strategy if not provided
        if not synthesis_strategy:
            synthesis_strategy = self._determine_synthesis_strategy(analyzed_responses, original_query)
        
        # Perform synthesis based on strategy
        synthesized_content = await self._perform_synthesis(
            analyzed_responses, original_query, synthesis_strategy
        )
        
        # Calculate service contributions
        service_contributions = self._calculate_service_contributions(analyzed_responses)
        
        # Perform fact checking
        fact_check_results = await self._perform_fact_checking(analyzed_responses)
        
        # Identify contradictions
        contradictions = await self._identify_contradictions(analyzed_responses)
        
        # Extract unique insights
        unique_insights = await self._extract_unique_insights(analyzed_responses)
        
        # Calculate overall confidence score
        confidence_score = self._calculate_overall_confidence(analyzed_responses, contradictions)
        
        # Collect sources
        sources = self._collect_sources(analyzed_responses)
        
        return SynthesisResult(
            synthesized_content=synthesized_content,
            strategy_used=synthesis_strategy,
            service_contributions=service_contributions,
            confidence_score=confidence_score,
            fact_check_results=fact_check_results,
            contradictions=contradictions,
            unique_insights=unique_insights,
            sources=sources,
            processing_time=time.time() - start_time
        )

    async def _analyze_responses(self, responses: List[ServiceResponse]) -> List[ServiceResponse]:
        """Analyze each response for content type, key facts, and confidence"""
        analyzed_responses = []
        
        for response in responses:
            # Extract key facts
            key_facts = await self._extract_key_facts(response.content)
            
            # Determine content type
            content_type = self._determine_content_type(response.content)
            
            # Calculate confidence score
            confidence_score = self._calculate_response_confidence(response)
            
            # Extract sources if available
            sources = self._extract_sources_from_content(response.content)
            
            # Create analyzed response
            analyzed_response = ServiceResponse(
                service=response.service,
                content=response.content,
                status_code=response.status_code,
                response_time=response.response_time,
                metadata=response.metadata,
                error=response.error,
                confidence_score=confidence_score,
                content_type=content_type,
                key_facts=key_facts,
                sources=sources
            )
            
            analyzed_responses.append(analyzed_response)
            
        return analyzed_responses

    async def _extract_key_facts(self, content: str) -> List[str]:
        """Extract key facts from response content"""
        try:
            extraction_prompt = f"""Extract the key facts from this text. Return them as a simple list, one fact per line.

Text: {content[:1000]}...

Key facts:"""
            
            response = self.ollama_client.chat(
                model=self.local_model,
                messages=[{'role': 'user', 'content': extraction_prompt}]
            )
            
            facts_text = response['message']['content']
            facts = [fact.strip() for fact in facts_text.split('\n') if fact.strip() and not fact.strip().startswith('#')]
            
            return facts[:10]  # Limit to 10 key facts
            
        except Exception as e:
            logger.error(f"Failed to extract key facts: {e}")
            return []

    def _determine_content_type(self, content: str) -> ContentType:
        """Determine the type of content based on patterns"""
        content_lower = content.lower()
        
        # Technical content patterns
        if any(keyword in content_lower for keyword in ['code', 'function', 'algorithm', 'programming', 'api', 'data structure']):
            return ContentType.TECHNICAL
            
        # News content patterns
        if any(keyword in content_lower for keyword in ['reported', 'according to', 'sources say', 'breaking', 'announced']):
            return ContentType.NEWS
            
        # Data content patterns
        if re.search(r'\d+%|\$\d+|\d+\.\d+|statistics|data shows|research indicates', content_lower):
            return ContentType.DATA
            
        # Creative content patterns
        if any(keyword in content_lower for keyword in ['story', 'imagine', 'creative', 'narrative', 'character']):
            return ContentType.CREATIVE
            
        # Analytical content patterns
        if any(keyword in content_lower for keyword in ['analysis', 'compare', 'evaluate', 'pros and cons', 'assessment']):
            return ContentType.ANALYTICAL
            
        return ContentType.FACTUAL

    def _calculate_response_confidence(self, response: ServiceResponse) -> float:
        """Calculate confidence score for a response"""
        base_confidence = self.service_weights.get(response.service, 0.5)
        
        # Adjust based on response characteristics
        content_length = len(response.content)
        if content_length < 50:
            base_confidence *= 0.7  # Very short responses are less confident
        elif content_length > 500:
            base_confidence *= 1.1  # Detailed responses are more confident
            
        # Adjust based on response time (faster might be cached/simple)
        if response.response_time < 2.0:
            base_confidence *= 1.05  # Quick response bonus
        elif response.response_time > 30.0:
            base_confidence *= 0.9  # Very slow response penalty
            
        # Check for uncertainty indicators
        uncertainty_indicators = ['might be', 'possibly', 'perhaps', 'unsure', 'not certain']
        if any(indicator in response.content.lower() for indicator in uncertainty_indicators):
            base_confidence *= 0.8
            
        return min(base_confidence, 1.0)

    def _extract_sources_from_content(self, content: str) -> List[str]:
        """Extract source references from content"""
        sources = []
        
        # Look for URL patterns
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, content)
        sources.extend(urls)
        
        # Look for citation patterns
        citation_patterns = [
            r'according to ([^,\n]+)',
            r'source: ([^,\n]+)',
            r'from ([A-Z][^,\n]+)',
            r'\[(\d+)\]'  # Numbered citations
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            sources.extend(matches)
            
        return list(set(sources))  # Remove duplicates

    def _determine_synthesis_strategy(self, responses: List[ServiceResponse], 
                                    query: str) -> SynthesisStrategy:
        """Determine the best synthesis strategy based on responses and query"""
        
        # If only one response, use merge
        if len(responses) == 1:
            return SynthesisStrategy.MERGE
            
        # Check for conflicting information
        if self._has_conflicting_info(responses):
            return SynthesisStrategy.FACT_CHECK
            
        # Check for complementary information
        content_types = [r.content_type for r in responses]
        if len(set(content_types)) > 1:
            return SynthesisStrategy.COMPLEMENT
            
        # Check for comparison query
        if any(word in query.lower() for word in ['compare', 'vs', 'versus', 'difference', 'better']):
            return SynthesisStrategy.COMPARE
            
        # Check for varied service types
        service_types = [r.service for r in responses]
        if len(set(service_types)) >= 3:
            return SynthesisStrategy.MERGE
            
        return SynthesisStrategy.PRIORITIZE

    def _has_conflicting_info(self, responses: List[ServiceResponse]) -> bool:
        """Check if responses contain conflicting information"""
        # Simple heuristic: look for contradictory keywords
        contradictory_pairs = [
            ('yes', 'no'),
            ('true', 'false'),
            ('increase', 'decrease'),
            ('more', 'less'),
            ('better', 'worse')
        ]
        
        all_content = ' '.join([r.content.lower() for r in responses])
        
        for pair in contradictory_pairs:
            if pair[0] in all_content and pair[1] in all_content:
                return True
                
        return False

    async def _perform_synthesis(self, responses: List[ServiceResponse], 
                               query: str, strategy: SynthesisStrategy) -> str:
        """Perform the actual synthesis based on strategy"""
        
        if strategy == SynthesisStrategy.MERGE:
            return await self._merge_responses(responses, query)
        elif strategy == SynthesisStrategy.COMPARE:
            return await self._compare_responses(responses, query)
        elif strategy == SynthesisStrategy.PRIORITIZE:
            return await self._prioritize_responses(responses, query)
        elif strategy == SynthesisStrategy.COMPLEMENT:
            return await self._complement_responses(responses, query)
        elif strategy == SynthesisStrategy.FACT_CHECK:
            return await self._fact_check_synthesis(responses, query)
        else:
            return await self._merge_responses(responses, query)

    async def _merge_responses(self, responses: List[ServiceResponse], query: str) -> str:
        """Merge responses into a coherent narrative"""
        
        # Prepare responses for merging
        response_texts = []
        for response in responses:
            service_name = response.service.upper()
            response_texts.append(f"From {service_name}:\n{response.content}")
        
        merge_prompt = f"""Combine these responses into a single, coherent answer to the query: "{query}"

Responses:
{chr(10).join(response_texts)}

Create a comprehensive response that:
1. Integrates information from all sources
2. Removes redundancy while preserving important details
3. Maintains a natural, flowing narrative
4. Highlights the most valuable insights

Comprehensive Answer:"""
        
        try:
            response = self.ollama_client.chat(
                model=self.local_model,
                messages=[{'role': 'user', 'content': merge_prompt}]
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to merge responses: {e}")
            return self._fallback_merge(responses)

    async def _compare_responses(self, responses: List[ServiceResponse], query: str) -> str:
        """Compare and contrast different responses"""
        
        response_texts = []
        for i, response in enumerate(responses):
            service_name = response.service.upper()
            response_texts.append(f"Response {i+1} ({service_name}):\n{response.content}")
        
        compare_prompt = f"""Compare and analyze these different responses to: "{query}"

{chr(10).join(response_texts)}

Provide a comparative analysis that:
1. Identifies key similarities and differences
2. Evaluates the strengths of each response
3. Highlights unique insights from each source
4. Provides a balanced conclusion

Comparative Analysis:"""
        
        try:
            response = self.ollama_client.chat(
                model=self.local_model,
                messages=[{'role': 'user', 'content': compare_prompt}]
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to compare responses: {e}")
            return self._fallback_merge(responses)

    async def _prioritize_responses(self, responses: List[ServiceResponse], query: str) -> str:
        """Prioritize responses based on confidence and relevance"""
        
        # Sort responses by confidence score
        sorted_responses = sorted(responses, key=lambda r: r.confidence_score, reverse=True)
        
        primary_response = sorted_responses[0]
        supporting_responses = sorted_responses[1:]
        
        prioritize_prompt = f"""Create a comprehensive answer to: "{query}"

Primary source ({primary_response.service.upper()}):
{primary_response.content}

Supporting information:
{chr(10).join([f"From {r.service.upper()}: {r.content[:200]}..." for r in supporting_responses])}

Provide an answer that:
1. Uses the primary source as the main foundation
2. Incorporates supporting details from other sources
3. Maintains consistency and coherence
4. Indicates confidence levels where appropriate

Prioritized Answer:"""
        
        try:
            response = self.ollama_client.chat(
                model=self.local_model,
                messages=[{'role': 'user', 'content': prioritize_prompt}]
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to prioritize responses: {e}")
            return primary_response.content

    async def _complement_responses(self, responses: List[ServiceResponse], query: str) -> str:
        """Combine complementary responses that cover different aspects"""
        
        # Group responses by content type
        type_groups = defaultdict(list)
        for response in responses:
            type_groups[response.content_type].append(response)
        
        complement_prompt = f"""Combine these complementary responses to provide a comprehensive answer to: "{query}"

"""
        
        for content_type, group_responses in type_groups.items():
            complement_prompt += f"\n{content_type.value.upper()} PERSPECTIVE:\n"
            for response in group_responses:
                complement_prompt += f"- {response.service}: {response.content[:300]}...\n"
        
        complement_prompt += """
Create a comprehensive response that:
1. Integrates different perspectives and types of information
2. Shows how different aspects complement each other
3. Provides a well-rounded, complete answer
4. Maintains logical flow between different types of content

Comprehensive Answer:"""
        
        try:
            response = self.ollama_client.chat(
                model=self.local_model,
                messages=[{'role': 'user', 'content': complement_prompt}]
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to complement responses: {e}")
            return self._fallback_merge(responses)

    async def _fact_check_synthesis(self, responses: List[ServiceResponse], query: str) -> str:
        """Synthesize responses while fact-checking conflicting information"""
        
        fact_check_prompt = f"""Analyze these responses for factual accuracy and resolve any conflicts for the query: "{query}"

"""
        
        for i, response in enumerate(responses):
            fact_check_prompt += f"Source {i+1} ({response.service}):\n{response.content}\n\n"
        
        fact_check_prompt += """
Provide a fact-checked synthesis that:
1. Identifies any conflicting information
2. Evaluates the reliability of different claims
3. Resolves conflicts based on source credibility and evidence
4. Presents the most accurate information available
5. Notes any uncertainties or areas where sources disagree

Fact-Checked Analysis:"""
        
        try:
            response = self.ollama_client.chat(
                model=self.local_model,
                messages=[{'role': 'user', 'content': fact_check_prompt}]
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to fact-check synthesis: {e}")
            return self._fallback_merge(responses)

    def _fallback_merge(self, responses: List[ServiceResponse]) -> str:
        """Simple fallback merge when AI synthesis fails"""
        merged_content = f"Combined responses from {len(responses)} services:\n\n"
        
        for response in responses:
            service_icon = self._get_service_icon(response.service)
            merged_content += f"{service_icon} **{response.service.upper()}**:\n"
            merged_content += f"{response.content}\n\n"
            
        return merged_content

    def _calculate_service_contributions(self, responses: List[ServiceResponse]) -> Dict[str, float]:
        """Calculate how much each service contributed to the final answer"""
        if not responses:
            return {}
            
        total_confidence = sum(r.confidence_score for r in responses)
        if total_confidence == 0:
            # Equal contribution if no confidence scores
            equal_contribution = 1.0 / len(responses)
            return {r.service: equal_contribution for r in responses}
            
        contributions = {}
        for response in responses:
            contributions[response.service] = response.confidence_score / total_confidence
            
        return contributions

    async def _perform_fact_checking(self, responses: List[ServiceResponse]) -> Dict[str, Any]:
        """Perform basic fact checking across responses"""
        if len(responses) < 2:
            return {'status': 'insufficient_data', 'conflicts': []}
        
        # Extract key facts from all responses
        all_facts = []
        for response in responses:
            if response.key_facts:
                all_facts.extend([(fact, response.service) for fact in response.key_facts])
        
        # Simple conflict detection
        conflicts = []
        for i, (fact1, service1) in enumerate(all_facts):
            for j, (fact2, service2) in enumerate(all_facts[i+1:], i+1):
                if service1 != service2 and self._are_conflicting_facts(fact1, fact2):
                    conflicts.append({
                        'fact1': fact1,
                        'service1': service1,
                        'fact2': fact2,
                        'service2': service2
                    })
        
        return {
            'status': 'completed',
            'total_facts': len(all_facts),
            'conflicts': conflicts,
            'conflict_ratio': len(conflicts) / max(len(all_facts), 1)
        }

    def _are_conflicting_facts(self, fact1: str, fact2: str) -> bool:
        """Simple heuristic to detect conflicting facts"""
        # Very basic implementation - could be enhanced with NLP
        fact1_lower = fact1.lower()
        fact2_lower = fact2.lower()
        
        # Look for direct contradictions
        contradictions = [
            ('increase', 'decrease'),
            ('rise', 'fall'),
            ('up', 'down'),
            ('more', 'less'),
            ('higher', 'lower'),
            ('true', 'false'),
            ('yes', 'no')
        ]
        
        for pos, neg in contradictions:
            if pos in fact1_lower and neg in fact2_lower:
                return True
            if neg in fact1_lower and pos in fact2_lower:
                return True
                
        return False

    async def _identify_contradictions(self, responses: List[ServiceResponse]) -> List[Dict[str, str]]:
        """Identify contradictions between responses"""
        contradictions = []
        
        for i, response1 in enumerate(responses):
            for j, response2 in enumerate(responses[i+1:], i+1):
                if self._responses_contradict(response1, response2):
                    contradictions.append({
                        'service1': response1.service,
                        'service2': response2.service,
                        'content1': response1.content[:200] + "...",
                        'content2': response2.content[:200] + "...",
                        'type': 'content_contradiction'
                    })
        
        return contradictions

    def _responses_contradict(self, response1: ServiceResponse, response2: ServiceResponse) -> bool:
        """Check if two responses contradict each other"""
        # Simple implementation - could be enhanced
        return self._has_conflicting_info([response1, response2])

    async def _extract_unique_insights(self, responses: List[ServiceResponse]) -> Dict[str, List[str]]:
        """Extract unique insights from each service"""
        unique_insights = {}
        
        for response in responses:
            try:
                insight_prompt = f"""Identify the unique insights or perspectives in this response that might not be found elsewhere:

{response.content}

List 2-3 unique insights or key points:"""
                
                result = self.ollama_client.chat(
                    model=self.local_model,
                    messages=[{'role': 'user', 'content': insight_prompt}]
                )
                
                insights_text = result['message']['content']
                insights = [insight.strip() for insight in insights_text.split('\n') if insight.strip()]
                unique_insights[response.service] = insights[:3]
                
            except Exception as e:
                logger.error(f"Failed to extract insights for {response.service}: {e}")
                unique_insights[response.service] = []
        
        return unique_insights

    def _calculate_overall_confidence(self, responses: List[ServiceResponse], 
                                    contradictions: List[Dict[str, str]]) -> float:
        """Calculate overall confidence score for synthesis"""
        if not responses:
            return 0.0
            
        # Average confidence of all responses
        avg_confidence = sum(r.confidence_score for r in responses) / len(responses)
        
        # Penalty for contradictions
        contradiction_penalty = len(contradictions) * 0.1
        
        # Bonus for multiple agreeing sources
        agreement_bonus = min(len(responses) * 0.05, 0.2)
        
        overall_confidence = avg_confidence + agreement_bonus - contradiction_penalty
        
        return max(0.0, min(1.0, overall_confidence))

    def _collect_sources(self, responses: List[ServiceResponse]) -> List[str]:
        """Collect all sources from responses"""
        all_sources = []
        
        for response in responses:
            # Add service as a source
            all_sources.append(response.service)
            
            # Add any embedded sources
            if response.sources:
                all_sources.extend(response.sources)
        
        return list(set(all_sources))  # Remove duplicates

    def _get_service_icon(self, service: str) -> str:
        """Get emoji icon for service"""
        icons = {
            'claude': '💎',
            'gemini': '🧠',
            'perplexity': '🔍',
            'weather': '🌤️',
            'news': '📰',
            'translate': '🌐',
            'currency': '💱',
            'maps': '🗺️',
            'stock': '📈'
        }
        return icons.get(service, '🔧')


# Example usage
async def main():
    """Test the response synthesizer"""
    synthesizer = ResponseSynthesizer()
    
    # Mock responses
    responses = [
        ServiceResponse(
            service="claude",
            content="Python is excellent for web development due to its simplicity and extensive frameworks like Django and Flask.",
            status_code=200,
            response_time=10.0,
            metadata={}
        ),
        ServiceResponse(
            service="gemini",
            content="JavaScript is the dominant language for web development, especially for frontend and full-stack development with Node.js.",
            status_code=200,
            response_time=8.0,
            metadata={}
        )
    ]
    
    result = await synthesizer.synthesize_responses(
        responses, 
        "Which is better for web development: Python or JavaScript?"
    )
    
    print(f"Strategy: {result.strategy_used}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Content: {result.synthesized_content}")


if __name__ == "__main__":
    asyncio.run(main())