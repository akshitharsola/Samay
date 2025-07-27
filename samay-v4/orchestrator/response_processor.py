#!/usr/bin/env python3
"""
Samay v4 - Response Processor
============================
Handles JSON extraction and response synthesis from AI services
Fixes the core machine code template processing issue from v3
"""

import json
import re
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ResponseType(Enum):
    JSON_STRUCTURED = "json_structured"
    PLAIN_TEXT = "plain_text"
    MIXED_CONTENT = "mixed_content"
    ERROR = "error"

@dataclass
class ProcessedResponse:
    response_type: ResponseType
    main_response: str
    summary: str
    key_points: List[str]
    confidence: float
    category: str
    raw_content: str
    processing_time: float
    source_service: str
    errors: List[str] = None

class ResponseProcessor:
    """Processes and synthesizes AI service responses"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # JSON extraction patterns
        self.json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON in markdown code blocks
            r'```\s*(\{.*?\})\s*```',      # JSON in generic code blocks
            r'\{[^{}]*"response"[^{}]*"[^"]*"[^{}]*\}',  # JSON-like with "response" field
            r'\{.*?"response"\s*:\s*"[^"]*".*?\}',  # More flexible JSON matching
        ]
        
        # Required fields for machine code template
        self.required_fields = ["response", "summary", "key_points", "confidence", "category"]
        
        # Default values for missing fields
        self.default_values = {
            "summary": "AI response summary",
            "key_points": ["Main point extracted from response"],
            "confidence": 0.7,
            "category": "other"
        }
    
    def process_single_response(self, raw_response: str, service_id: str = "unknown") -> ProcessedResponse:
        """Process a single AI service response"""
        start_time = time.time()
        errors = []
        
        try:
            # First, try to extract JSON structure
            json_result = self._extract_machine_code_json(raw_response)
            
            if json_result:
                # Successfully extracted JSON
                return ProcessedResponse(
                    response_type=ResponseType.JSON_STRUCTURED,
                    main_response=json_result.get("response", raw_response),
                    summary=json_result.get("summary", self.default_values["summary"]),
                    key_points=json_result.get("key_points", self.default_values["key_points"]),
                    confidence=json_result.get("confidence", self.default_values["confidence"]),
                    category=json_result.get("category", self.default_values["category"]),
                    raw_content=raw_response,
                    processing_time=time.time() - start_time,
                    source_service=service_id
                )
            else:
                # Fallback to plain text processing
                errors.append("No valid JSON structure found, using plain text fallback")
                return self._process_plain_text_fallback(raw_response, service_id, start_time, errors)
                
        except Exception as e:
            errors.append(f"Processing error: {str(e)}")
            return self._process_plain_text_fallback(raw_response, service_id, start_time, errors)
    
    def _extract_machine_code_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from machine code template responses"""
        if not text:
            return None
        
        # Try each JSON pattern
        for pattern in self.json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # Parse JSON
                    json_data = json.loads(match)
                    
                    # Validate required fields
                    if self._validate_json_structure(json_data):
                        return json_data
                        
                except json.JSONDecodeError:
                    continue
        
        # Try to find JSON-like structure without strict formatting
        json_like = self._extract_loose_json(text)
        if json_like and self._validate_json_structure(json_like):
            return json_like
        
        return None
    
    def _extract_loose_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON-like structure with more flexible parsing"""
        try:
            # Look for response field patterns
            response_match = re.search(r'"response"\s*:\s*"([^"]*)"', text, re.DOTALL)
            summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', text, re.DOTALL)
            confidence_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
            category_match = re.search(r'"category"\s*:\s*"([^"]*)"', text)
            
            # Extract key points array
            key_points = []
            key_points_match = re.search(r'"key_points"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if key_points_match:
                points_text = key_points_match.group(1)
                point_matches = re.findall(r'"([^"]*)"', points_text)
                key_points = point_matches
            
            # Build JSON structure if we found essential fields
            if response_match:
                result = {
                    "response": response_match.group(1),
                    "summary": summary_match.group(1) if summary_match else self.default_values["summary"],
                    "key_points": key_points if key_points else self.default_values["key_points"],
                    "confidence": float(confidence_match.group(1)) if confidence_match else self.default_values["confidence"],
                    "category": category_match.group(1) if category_match else self.default_values["category"]
                }
                return result
                
        except Exception:
            pass
        
        return None
    
    def _validate_json_structure(self, json_data: Dict[str, Any]) -> bool:
        """Validate that JSON has required fields for machine code template"""
        if not isinstance(json_data, dict):
            return False
        
        # Check for response field (most important)
        if "response" not in json_data:
            return False
        
        # Other fields are optional but preferred
        return True
    
    def _process_plain_text_fallback(self, text: str, service_id: str, start_time: float, errors: List[str]) -> ProcessedResponse:
        """Process plain text response when JSON extraction fails"""
        
        # Clean up the text
        cleaned_text = self._clean_response_text(text)
        
        # Generate summary (first sentence or first 100 chars)
        summary = self._generate_summary(cleaned_text)
        
        # Extract key points (split by common patterns)
        key_points = self._extract_key_points(cleaned_text)
        
        # Estimate confidence based on response quality
        confidence = self._estimate_confidence(cleaned_text)
        
        # Categorize response
        category = self._categorize_response(cleaned_text)
        
        return ProcessedResponse(
            response_type=ResponseType.PLAIN_TEXT,
            main_response=cleaned_text,
            summary=summary,
            key_points=key_points,
            confidence=confidence,
            category=category,
            raw_content=text,
            processing_time=time.time() - start_time,
            source_service=service_id,
            errors=errors
        )
    
    def _clean_response_text(self, text: str) -> str:
        """Clean up response text removing artifacts"""
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Remove common UI artifacts
        artifacts_to_remove = [
            r"Copy to clipboard",
            r"Share this response",
            r"👍\s*👎",  # Like/dislike buttons
            r"Regenerate response",
            r"Continue this conversation",
        ]
        
        for artifact_pattern in artifacts_to_remove:
            cleaned = re.sub(artifact_pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Remove excessive line breaks
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Normalize spaces
        
        return cleaned.strip()
    
    def _generate_summary(self, text: str) -> str:
        """Generate a summary from the response text"""
        if not text:
            return self.default_values["summary"]
        
        # Try to get first sentence
        sentences = re.split(r'[.!?]+', text)
        if sentences and len(sentences[0].strip()) > 10:
            return sentences[0].strip()[:100] + ("..." if len(sentences[0]) > 100 else "")
        
        # Fallback: first 100 characters
        if len(text) > 100:
            return text[:97] + "..."
        else:
            return text
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from the response"""
        if not text:
            return self.default_values["key_points"]
        
        key_points = []
        
        # Look for numbered lists
        numbered_points = re.findall(r'\d+\.\s*([^\n]+)', text)
        if numbered_points:
            key_points.extend([point.strip() for point in numbered_points[:5]])  # Max 5 points
        
        # Look for bullet points
        if not key_points:
            bullet_points = re.findall(r'[•\-\*]\s*([^\n]+)', text)
            if bullet_points:
                key_points.extend([point.strip() for point in bullet_points[:5]])
        
        # Fallback: split by sentences and take key ones
        if not key_points:
            sentences = re.split(r'[.!?]+', text)
            important_sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) < 150]
            key_points = important_sentences[:3]  # Take up to 3 sentences
        
        return key_points if key_points else self.default_values["key_points"]
    
    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence based on response characteristics"""
        if not text:
            return 0.1
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence for longer, more detailed responses
        if len(text) > 100:
            confidence += 0.1
        if len(text) > 500:
            confidence += 0.1
        
        # Increase confidence for structured content
        if re.search(r'\d+\.', text):  # Numbered lists
            confidence += 0.1
        if re.search(r'[•\-\*]', text):  # Bullet points
            confidence += 0.05
        
        # Decrease confidence for uncertainty indicators
        uncertainty_indicators = ['maybe', 'perhaps', 'might', 'possibly', 'not sure', 'unclear']
        for indicator in uncertainty_indicators:
            if indicator.lower() in text.lower():
                confidence -= 0.1
                break
        
        # Clamp between 0.1 and 1.0
        return max(0.1, min(1.0, confidence))
    
    def _categorize_response(self, text: str) -> str:
        """Categorize the response based on content"""
        if not text:
            return "other"
        
        text_lower = text.lower()
        
        # Question patterns
        if '?' in text or any(word in text_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            return "question"
        
        # Task/instruction patterns
        if any(word in text_lower for word in ['step', 'process', 'procedure', 'method', 'approach']):
            return "task"
        
        # Information patterns
        if any(word in text_lower for word in ['information', 'fact', 'data', 'explanation', 'definition']):
            return "information"
        
        return "other"
    
    def synthesize_multi_service_responses(self, responses: List[ProcessedResponse]) -> ProcessedResponse:
        """Combine responses from multiple AI services into a unified response"""
        start_time = time.time()
        
        if not responses:
            return ProcessedResponse(
                response_type=ResponseType.ERROR,
                main_response="No responses to synthesize",
                summary="Error: No input responses",
                key_points=["No responses provided"],
                confidence=0.0,
                category="error",
                raw_content="",
                processing_time=time.time() - start_time,
                source_service="synthesizer"
            )
        
        if len(responses) == 1:
            # Single response, just return it with updated metadata
            single = responses[0]
            single.source_service = f"{single.source_service} (single)"
            return single
        
        # Multiple responses - synthesize them
        valid_responses = [r for r in responses if r.response_type != ResponseType.ERROR]
        
        if not valid_responses:
            # All responses failed
            return ProcessedResponse(
                response_type=ResponseType.ERROR,
                main_response="All services failed to provide valid responses",
                summary="Error: All services failed",
                key_points=["Multiple service failures"],
                confidence=0.0,
                category="error",
                raw_content="",
                processing_time=time.time() - start_time,
                source_service="synthesizer"
            )
        
        # Synthesize the responses
        synthesized_response = self._build_synthesized_response(valid_responses)
        synthesized_summary = self._build_synthesized_summary(valid_responses)
        synthesized_key_points = self._build_synthesized_key_points(valid_responses)
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in valid_responses) / len(valid_responses)
        
        # Use most common category
        categories = [r.category for r in valid_responses]
        most_common_category = max(set(categories), key=categories.count)
        
        # Build source list
        sources = [r.source_service for r in valid_responses]
        source_list = f"synthesized from {', '.join(sources)}"
        
        return ProcessedResponse(
            response_type=ResponseType.MIXED_CONTENT,
            main_response=synthesized_response,
            summary=synthesized_summary,
            key_points=synthesized_key_points,
            confidence=avg_confidence,
            category=most_common_category,
            raw_content=f"Combined from {len(valid_responses)} services",
            processing_time=time.time() - start_time,
            source_service=source_list
        )
    
    def _build_synthesized_response(self, responses: List[ProcessedResponse]) -> str:
        """Build a unified response from multiple services"""
        if len(responses) == 1:
            return responses[0].main_response
        
        # Find the longest, most detailed response as the base
        base_response = max(responses, key=lambda r: len(r.main_response))
        
        # Add perspectives from other services if they add value
        additional_insights = []
        for response in responses:
            if response != base_response and len(response.main_response) > 50:
                # Check if this adds new information
                if not self._is_content_similar(base_response.main_response, response.main_response):
                    additional_insights.append(f"**{response.source_service}**: {response.main_response}")
        
        if additional_insights:
            synthesized = f"{base_response.main_response}\n\n**Additional Perspectives:**\n\n"
            synthesized += "\n\n".join(additional_insights)
            return synthesized
        else:
            return base_response.main_response
    
    def _build_synthesized_summary(self, responses: List[ProcessedResponse]) -> str:
        """Build a unified summary"""
        summaries = [r.summary for r in responses if r.summary and len(r.summary) > 10]
        if not summaries:
            return "Multi-service AI response"
        
        # Use the most comprehensive summary
        best_summary = max(summaries, key=len)
        return f"{best_summary} (from {len(responses)} services)"
    
    def _build_synthesized_key_points(self, responses: List[ProcessedResponse]) -> List[str]:
        """Build unified key points list"""
        all_points = []
        for response in responses:
            all_points.extend(response.key_points)
        
        # Remove duplicates and similar points
        unique_points = []
        for point in all_points:
            if not any(self._is_content_similar(point, existing) for existing in unique_points):
                unique_points.append(point)
        
        # Return top 5 points
        return unique_points[:5]
    
    def _is_content_similar(self, text1: str, text2: str, similarity_threshold: float = 0.7) -> bool:
        """Check if two pieces of content are similar"""
        if not text1 or not text2:
            return False
        
        # Simple similarity check based on common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= similarity_threshold


def main():
    """Test the response processor"""
    print("🧪 Testing Response Processor")
    print("=" * 50)
    
    processor = ResponseProcessor()
    
    # Test 1: Machine code JSON response
    print("\n1. Testing JSON machine code response...")
    json_response = '''
    Here's my response in the requested format:
    
    ```json
    {
        "response": "This is a test response from Claude",
        "summary": "Test response demonstrating JSON format",
        "key_points": ["Point 1: JSON extraction works", "Point 2: Structured data is preserved", "Point 3: Fallback handling available"],
        "confidence": 0.95,
        "category": "information"
    }
    ```
    
    I hope this helps!
    '''
    
    result1 = processor.process_single_response(json_response, "claude")
    print(f"Result type: {result1.response_type.value}")
    print(f"Main response: {result1.main_response[:100]}...")
    print(f"Key points: {result1.key_points}")
    print(f"Confidence: {result1.confidence}")
    
    # Test 2: Plain text response
    print("\n2. Testing plain text response...")
    plain_response = '''
    Hello! I'd be happy to help you with that question. Here are the main points to consider:
    
    1. First, you need to understand the basic concepts
    2. Then, apply the methodology step by step
    3. Finally, validate your results
    
    This approach should give you good results in most cases.
    '''
    
    result2 = processor.process_single_response(plain_response, "perplexity")
    print(f"Result type: {result2.response_type.value}")
    print(f"Summary: {result2.summary}")
    print(f"Key points: {result2.key_points}")
    
    # Test 3: Multi-service synthesis
    print("\n3. Testing multi-service synthesis...")
    synthesized = processor.synthesize_multi_service_responses([result1, result2])
    print(f"Synthesized type: {synthesized.response_type.value}")
    print(f"Source: {synthesized.source_service}")
    print(f"Combined key points: {len(synthesized.key_points)}")
    
    print("\n✅ Response processor tests completed!")


if __name__ == "__main__":
    main()