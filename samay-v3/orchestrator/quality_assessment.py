#!/usr/bin/env python3
"""
Samay v3 - Quality Assessment Module
===================================
Phase 2: Advanced quality evaluation for prompt refinement
"""

import json
import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum
import statistics

from .local_llm import LocalLLMClient


class QualityDimension(Enum):
    CLARITY = "clarity"
    SPECIFICITY = "specificity"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    EFFECTIVENESS = "effectiveness"
    CREATIVITY = "creativity"


class AssessmentMethod(Enum):
    HEURISTIC = "heuristic"
    LLM_BASED = "llm_based"
    HYBRID = "hybrid"
    COMPARATIVE = "comparative"


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for a prompt"""
    clarity_score: float  # How clear and understandable
    specificity_score: float  # How specific and detailed
    completeness_score: float  # How complete and comprehensive
    coherence_score: float  # How well-structured and logical
    effectiveness_score: float  # How likely to achieve goals
    creativity_score: float  # How creative and innovative
    overall_score: float  # Weighted average
    confidence_level: float  # Assessment confidence


@dataclass
class QualityAssessment:
    """Complete quality assessment record"""
    assessment_id: str
    version_id: str
    metrics: QualityMetrics
    method_used: AssessmentMethod
    detailed_feedback: Dict[str, str]
    improvement_suggestions: List[str]
    benchmark_comparison: Dict[str, float]
    timestamp: str


class QualityAssessor:
    """Advanced quality assessment for prompt refinement"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "quality_assessments.db"
        self.session_id = session_id
        self.llm_client = LocalLLMClient()
        
        # Quality benchmarks and weights
        self.dimension_weights = {
            QualityDimension.CLARITY: 0.25,
            QualityDimension.SPECIFICITY: 0.20,
            QualityDimension.COMPLETENESS: 0.20,
            QualityDimension.COHERENCE: 0.15,
            QualityDimension.EFFECTIVENESS: 0.15,
            QualityDimension.CREATIVITY: 0.05
        }
        
        # Assessment cache
        self.assessment_cache = {}
        self.benchmark_standards = {}
        
        self.init_database()
        self._load_benchmark_standards()
        print(f"📊 QualityAssessor initialized for session {session_id}")
    
    def init_database(self):
        """Initialize quality assessment database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Quality assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_assessments (
                assessment_id TEXT PRIMARY KEY,
                session_id TEXT,
                version_id TEXT,
                clarity_score REAL,
                specificity_score REAL,
                completeness_score REAL,
                coherence_score REAL,
                effectiveness_score REAL,
                creativity_score REAL,
                overall_score REAL,
                confidence_level REAL,
                method_used TEXT,
                detailed_feedback TEXT,
                improvement_suggestions TEXT,
                benchmark_comparison TEXT,
                timestamp TEXT
            )
        ''')
        
        # Quality benchmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_benchmarks (
                benchmark_id TEXT PRIMARY KEY,
                benchmark_name TEXT,
                dimension TEXT,
                score_threshold REAL,
                description TEXT,
                example_content TEXT,
                created_at TEXT
            )
        ''')
        
        # Comparative assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparative_assessments (
                comparison_id TEXT PRIMARY KEY,
                session_id TEXT,
                version_ids TEXT,
                relative_scores TEXT,
                winner_version TEXT,
                comparison_notes TEXT,
                timestamp TEXT
            )
        ''')
        
        # Assessment history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_history (
                history_id TEXT PRIMARY KEY,
                version_id TEXT,
                assessment_ids TEXT,
                quality_trend TEXT,
                improvement_rate REAL,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def assess_prompt_quality(
        self, 
        prompt: str, 
        version_id: str,
        method: AssessmentMethod = AssessmentMethod.HYBRID,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityAssessment:
        """Perform comprehensive quality assessment"""
        
        # Check cache first
        cache_key = f"{version_id}_{method.value}"
        if cache_key in self.assessment_cache:
            print(f"📋 Using cached assessment for {version_id[:8]}")
            return self.assessment_cache[cache_key]
        
        print(f"🔍 Assessing quality using {method.value} method...")
        
        # Execute assessment based on method
        if method == AssessmentMethod.HEURISTIC:
            metrics = self._heuristic_assessment(prompt, context)
        elif method == AssessmentMethod.LLM_BASED:
            metrics = self._llm_based_assessment(prompt, context)
        elif method == AssessmentMethod.HYBRID:
            metrics = self._hybrid_assessment(prompt, context)
        else:  # COMPARATIVE
            metrics = self._comparative_assessment(prompt, version_id, context)
        
        # Generate detailed feedback
        detailed_feedback = self._generate_detailed_feedback(prompt, metrics)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(prompt, metrics)
        
        # Benchmark comparison
        benchmark_comparison = self._compare_against_benchmarks(metrics)
        
        # Create assessment record
        assessment = QualityAssessment(
            assessment_id=str(uuid.uuid4()),
            version_id=version_id,
            metrics=metrics,
            method_used=method,
            detailed_feedback=detailed_feedback,
            improvement_suggestions=improvement_suggestions,
            benchmark_comparison=benchmark_comparison,
            timestamp=datetime.now().isoformat()
        )
        
        # Store assessment
        self._store_assessment(assessment)
        
        # Cache result
        self.assessment_cache[cache_key] = assessment
        
        print(f"✅ Quality assessment completed")
        print(f"📊 Overall score: {metrics.overall_score:.2f}")
        print(f"🎯 Confidence: {metrics.confidence_level:.2f}")
        
        return assessment
    
    def compare_prompt_versions(self, version_ids: List[str], prompts: List[str]) -> Dict[str, Any]:
        """Compare quality across multiple prompt versions"""
        
        if len(version_ids) != len(prompts):
            raise ValueError("Version IDs and prompts lists must have same length")
        
        assessments = []
        for version_id, prompt in zip(version_ids, prompts):
            assessment = self.assess_prompt_quality(prompt, version_id, AssessmentMethod.HYBRID)
            assessments.append(assessment)
        
        # Comparative analysis
        comparison_data = {
            "versions": len(version_ids),
            "assessments": [],
            "quality_ranking": [],
            "dimension_analysis": {},
            "improvement_trajectory": {},
            "best_practices": []
        }
        
        # Collect assessment data
        for i, assessment in enumerate(assessments):
            comparison_data["assessments"].append({
                "version_id": version_ids[i],
                "overall_score": assessment.metrics.overall_score,
                "dimension_scores": {
                    "clarity": assessment.metrics.clarity_score,
                    "specificity": assessment.metrics.specificity_score,
                    "completeness": assessment.metrics.completeness_score,
                    "coherence": assessment.metrics.coherence_score,
                    "effectiveness": assessment.metrics.effectiveness_score,
                    "creativity": assessment.metrics.creativity_score
                },
                "confidence": assessment.metrics.confidence_level
            })
        
        # Quality ranking
        ranked_assessments = sorted(assessments, key=lambda a: a.metrics.overall_score, reverse=True)
        comparison_data["quality_ranking"] = [
            {
                "rank": i + 1,
                "version_id": assessment.version_id,
                "score": assessment.metrics.overall_score
            }
            for i, assessment in enumerate(ranked_assessments)
        ]
        
        # Dimension analysis
        for dimension in QualityDimension:
            scores = [getattr(a.metrics, f"{dimension.value}_score") for a in assessments]
            comparison_data["dimension_analysis"][dimension.value] = {
                "average": statistics.mean(scores),
                "max": max(scores),
                "min": min(scores),
                "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
                "best_version": version_ids[scores.index(max(scores))]
            }
        
        # Store comparative assessment
        self._store_comparative_assessment(version_ids, comparison_data)
        
        return comparison_data
    
    def track_quality_evolution(self, version_lineage: List[str]) -> Dict[str, Any]:
        """Track quality evolution across version lineage"""
        
        evolution_data = {
            "version_count": len(version_lineage),
            "quality_trajectory": [],
            "improvement_rate": 0,
            "quality_trend": "stable",
            "dimension_trends": {},
            "peak_quality": 0,
            "regression_points": []
        }
        
        # Get assessments for all versions
        assessments = []
        for version_id in version_lineage:
            # Try to get existing assessment
            assessment = self._get_stored_assessment(version_id)
            if assessment:
                assessments.append(assessment)
        
        if len(assessments) < 2:
            return evolution_data
        
        # Quality trajectory
        for assessment in assessments:
            evolution_data["quality_trajectory"].append({
                "version_id": assessment.version_id,
                "overall_score": assessment.metrics.overall_score,
                "timestamp": assessment.timestamp
            })
        
        # Calculate improvement rate
        first_score = assessments[0].metrics.overall_score
        last_score = assessments[-1].metrics.overall_score
        evolution_data["improvement_rate"] = last_score - first_score
        
        # Determine trend
        scores = [a.metrics.overall_score for a in assessments]
        if len(scores) >= 3:
            recent_trend = scores[-3:]
            if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                evolution_data["quality_trend"] = "improving"
            elif all(recent_trend[i] >= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                evolution_data["quality_trend"] = "declining"
            else:
                evolution_data["quality_trend"] = "fluctuating"
        
        # Peak quality
        evolution_data["peak_quality"] = max(scores)
        
        # Dimension trends
        for dimension in QualityDimension:
            dimension_scores = [getattr(a.metrics, f"{dimension.value}_score") for a in assessments]
            evolution_data["dimension_trends"][dimension.value] = {
                "start": dimension_scores[0],
                "end": dimension_scores[-1],
                "peak": max(dimension_scores),
                "improvement": dimension_scores[-1] - dimension_scores[0]
            }
        
        return evolution_data
    
    def generate_quality_report(self, version_id: str) -> str:
        """Generate comprehensive quality report"""
        
        assessment = self._get_stored_assessment(version_id)
        if not assessment:
            return "No quality assessment found for this version."
        
        report_lines = [
            f"# Quality Assessment Report",
            f"**Version ID**: {version_id}",
            f"**Assessment Date**: {assessment.timestamp}",
            f"**Method**: {assessment.method_used.value}",
            "",
            "## Overall Quality Score",
            f"**{assessment.metrics.overall_score:.2f}/1.00** (Confidence: {assessment.metrics.confidence_level:.2f})",
            "",
            "## Dimension Breakdown",
            ""
        ]
        
        # Dimension scores
        dimensions = [
            ("Clarity", assessment.metrics.clarity_score),
            ("Specificity", assessment.metrics.specificity_score),
            ("Completeness", assessment.metrics.completeness_score),
            ("Coherence", assessment.metrics.coherence_score),
            ("Effectiveness", assessment.metrics.effectiveness_score),
            ("Creativity", assessment.metrics.creativity_score)
        ]
        
        for name, score in dimensions:
            status = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"
            report_lines.append(f"- **{name}**: {score:.2f} {status}")
        
        report_lines.extend([
            "",
            "## Detailed Feedback",
            ""
        ])
        
        # Add detailed feedback
        for dimension, feedback in assessment.detailed_feedback.items():
            report_lines.extend([
                f"### {dimension.replace('_', ' ').title()}",
                feedback,
                ""
            ])
        
        # Improvement suggestions
        if assessment.improvement_suggestions:
            report_lines.extend([
                "## Improvement Suggestions",
                ""
            ])
            for i, suggestion in enumerate(assessment.improvement_suggestions, 1):
                report_lines.append(f"{i}. {suggestion}")
        
        # Benchmark comparison
        if assessment.benchmark_comparison:
            report_lines.extend([
                "",
                "## Benchmark Comparison",
                ""
            ])
            for benchmark, score in assessment.benchmark_comparison.items():
                status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
                report_lines.append(f"- **{benchmark}**: {score:.2f} {status}")
        
        return "\n".join(report_lines)
    
    # Private assessment methods
    def _heuristic_assessment(self, prompt: str, context: Optional[Dict[str, Any]]) -> QualityMetrics:
        """Heuristic-based quality assessment"""
        
        if not prompt.strip():
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0, 1.0)
        
        # Clarity assessment
        clarity_score = self._assess_clarity_heuristic(prompt)
        
        # Specificity assessment
        specificity_score = self._assess_specificity_heuristic(prompt)
        
        # Completeness assessment
        completeness_score = self._assess_completeness_heuristic(prompt)
        
        # Coherence assessment
        coherence_score = self._assess_coherence_heuristic(prompt)
        
        # Effectiveness assessment
        effectiveness_score = self._assess_effectiveness_heuristic(prompt)
        
        # Creativity assessment
        creativity_score = self._assess_creativity_heuristic(prompt)
        
        # Calculate overall score
        overall_score = (
            clarity_score * self.dimension_weights[QualityDimension.CLARITY] +
            specificity_score * self.dimension_weights[QualityDimension.SPECIFICITY] +
            completeness_score * self.dimension_weights[QualityDimension.COMPLETENESS] +
            coherence_score * self.dimension_weights[QualityDimension.COHERENCE] +
            effectiveness_score * self.dimension_weights[QualityDimension.EFFECTIVENESS] +
            creativity_score * self.dimension_weights[QualityDimension.CREATIVITY]
        )
        
        return QualityMetrics(
            clarity_score=clarity_score,
            specificity_score=specificity_score,
            completeness_score=completeness_score,
            coherence_score=coherence_score,
            effectiveness_score=effectiveness_score,
            creativity_score=creativity_score,
            overall_score=overall_score,
            confidence_level=0.8  # Heuristic confidence
        )
    
    def _llm_based_assessment(self, prompt: str, context: Optional[Dict[str, Any]]) -> QualityMetrics:
        """LLM-based quality assessment"""
        
        assessment_prompt = f"""
        Evaluate this prompt across multiple quality dimensions. Provide scores from 0.0 to 1.0 for each dimension.
        
        PROMPT TO EVALUATE:
        {prompt}
        
        Please assess the following dimensions:
        1. CLARITY: How clear and understandable is the prompt?
        2. SPECIFICITY: How specific and detailed are the instructions?
        3. COMPLETENESS: How complete and comprehensive is the request?
        4. COHERENCE: How well-structured and logical is the prompt?
        5. EFFECTIVENESS: How likely is this prompt to achieve its intended goal?
        6. CREATIVITY: How creative and innovative is the approach?
        
        Provide your assessment in this exact format:
        CLARITY: [score]
        SPECIFICITY: [score]
        COMPLETENESS: [score]
        COHERENCE: [score]
        EFFECTIVENESS: [score]
        CREATIVITY: [score]
        
        Explain your reasoning for each score briefly.
        """
        
        system_prompt = "You are an expert prompt evaluator. Assess prompts objectively across quality dimensions."
        
        response = self.llm_client.generate_response(assessment_prompt, system_prompt)
        
        if not response.success:
            # Fallback to heuristic if LLM fails
            return self._heuristic_assessment(prompt, context)
        
        # Parse LLM response
        scores = self._parse_llm_assessment(response.response)
        
        # Calculate overall score
        overall_score = sum(
            scores[dim.value] * self.dimension_weights[dim] 
            for dim in QualityDimension
        )
        
        return QualityMetrics(
            clarity_score=scores["clarity"],
            specificity_score=scores["specificity"],
            completeness_score=scores["completeness"],
            coherence_score=scores["coherence"],
            effectiveness_score=scores["effectiveness"],
            creativity_score=scores["creativity"],
            overall_score=overall_score,
            confidence_level=0.9  # High confidence for LLM assessment
        )
    
    def _hybrid_assessment(self, prompt: str, context: Optional[Dict[str, Any]]) -> QualityMetrics:
        """Hybrid assessment combining heuristic and LLM methods"""
        
        # Get both assessments
        heuristic_metrics = self._heuristic_assessment(prompt, context)
        llm_metrics = self._llm_based_assessment(prompt, context)
        
        # Combine with weighted average (favor LLM for complex assessment)
        heuristic_weight = 0.3
        llm_weight = 0.7
        
        combined_metrics = QualityMetrics(
            clarity_score=heuristic_metrics.clarity_score * heuristic_weight + llm_metrics.clarity_score * llm_weight,
            specificity_score=heuristic_metrics.specificity_score * heuristic_weight + llm_metrics.specificity_score * llm_weight,
            completeness_score=heuristic_metrics.completeness_score * heuristic_weight + llm_metrics.completeness_score * llm_weight,
            coherence_score=heuristic_metrics.coherence_score * heuristic_weight + llm_metrics.coherence_score * llm_weight,
            effectiveness_score=heuristic_metrics.effectiveness_score * heuristic_weight + llm_metrics.effectiveness_score * llm_weight,
            creativity_score=heuristic_metrics.creativity_score * heuristic_weight + llm_metrics.creativity_score * llm_weight,
            overall_score=heuristic_metrics.overall_score * heuristic_weight + llm_metrics.overall_score * llm_weight,
            confidence_level=0.95  # High confidence for hybrid approach
        )
        
        return combined_metrics
    
    def _comparative_assessment(self, prompt: str, version_id: str, context: Optional[Dict[str, Any]]) -> QualityMetrics:
        """Comparative assessment against previous versions"""
        
        # Get baseline assessment
        base_metrics = self._hybrid_assessment(prompt, context)
        
        # Find similar versions for comparison
        similar_assessments = self._find_similar_assessments(prompt)
        
        if similar_assessments:
            # Adjust scores based on comparative performance
            avg_similar_score = statistics.mean([a.metrics.overall_score for a in similar_assessments])
            
            # Boost confidence if significantly better than similar
            if base_metrics.overall_score > avg_similar_score + 0.1:
                base_metrics.confidence_level = min(base_metrics.confidence_level + 0.05, 1.0)
            elif base_metrics.overall_score < avg_similar_score - 0.1:
                base_metrics.confidence_level = max(base_metrics.confidence_level - 0.05, 0.0)
        
        return base_metrics
    
    # Heuristic assessment methods
    def _assess_clarity_heuristic(self, prompt: str) -> float:
        """Assess clarity using heuristics"""
        score = 0.5  # Base score
        
        # Clear structure indicators
        if any(marker in prompt for marker in [':', '-', '1.', '2.', '•']):
            score += 0.1
        
        # Question clarity
        question_count = prompt.count('?')
        if 1 <= question_count <= 3:
            score += 0.1
        
        # Avoid ambiguous words
        ambiguous_words = ['maybe', 'perhaps', 'possibly', 'might', 'could be']
        ambiguous_count = sum(1 for word in ambiguous_words if word in prompt.lower())
        score -= ambiguous_count * 0.05
        
        # Sentence length (shorter is clearer)
        sentences = prompt.split('.')
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        if avg_length <= 15:
            score += 0.1
        elif avg_length > 25:
            score -= 0.1
        
        return max(0, min(1, score))
    
    def _assess_specificity_heuristic(self, prompt: str) -> float:
        """Assess specificity using heuristics"""
        score = 0.5  # Base score
        
        # Specific instruction words
        specific_words = ['specific', 'exactly', 'precisely', 'detailed', 'example', 'format']
        specific_count = sum(1 for word in specific_words if word in prompt.lower())
        score += min(specific_count * 0.05, 0.2)
        
        # Numbers and measurements
        if re.search(r'\d+', prompt):
            score += 0.1
        
        # Concrete examples
        if 'example' in prompt.lower() or 'for instance' in prompt.lower():
            score += 0.1
        
        # Vague language penalty
        vague_words = ['something', 'anything', 'some', 'general', 'basic']
        vague_count = sum(1 for word in vague_words if word in prompt.lower())
        score -= vague_count * 0.05
        
        return max(0, min(1, score))
    
    def _assess_completeness_heuristic(self, prompt: str) -> float:
        """Assess completeness using heuristics"""
        score = 0.5  # Base score
        
        # Length as completeness indicator
        word_count = len(prompt.split())
        if 50 <= word_count <= 200:
            score += 0.2
        elif 20 <= word_count <= 300:
            score += 0.1
        elif word_count < 10:
            score -= 0.2
        
        # Context indicators
        context_words = ['context', 'background', 'purpose', 'goal', 'objective']
        context_count = sum(1 for word in context_words if word in prompt.lower())
        score += min(context_count * 0.05, 0.15)
        
        # Requirements specification
        requirement_words = ['must', 'should', 'need', 'require', 'include']
        req_count = sum(1 for word in requirement_words if word in prompt.lower())
        score += min(req_count * 0.03, 0.15)
        
        return max(0, min(1, score))
    
    def _assess_coherence_heuristic(self, prompt: str) -> float:
        """Assess coherence using heuristics"""
        score = 0.5  # Base score
        
        # Logical connectors
        connectors = ['therefore', 'because', 'since', 'thus', 'consequently', 'first', 'second', 'finally']
        connector_count = sum(1 for word in connectors if word in prompt.lower())
        score += min(connector_count * 0.05, 0.2)
        
        # Paragraph structure (if multiple paragraphs)
        paragraphs = prompt.split('\n\n')
        if len(paragraphs) > 1:
            score += 0.1
        
        # Consistent tone/voice
        formal_words = ['please', 'kindly', 'would you']
        informal_words = ['hey', 'yo', 'gonna']
        formal_count = sum(1 for word in formal_words if word in prompt.lower())
        informal_count = sum(1 for word in informal_words if word in prompt.lower())
        
        # Penalty for mixed tone
        if formal_count > 0 and informal_count > 0:
            score -= 0.1
        
        return max(0, min(1, score))
    
    def _assess_effectiveness_heuristic(self, prompt: str) -> float:
        """Assess effectiveness using heuristics"""
        score = 0.5  # Base score
        
        # Action-oriented language
        action_words = ['create', 'generate', 'write', 'analyze', 'explain', 'provide']
        action_count = sum(1 for word in action_words if word in prompt.lower())
        score += min(action_count * 0.05, 0.2)
        
        # Goal clarity
        if 'goal' in prompt.lower() or 'objective' in prompt.lower():
            score += 0.1
        
        # Output specification
        output_words = ['output', 'result', 'format', 'response']
        output_count = sum(1 for word in output_words if word in prompt.lower())
        score += min(output_count * 0.05, 0.15)
        
        # Constraint specification
        constraint_words = ['limit', 'maximum', 'minimum', 'within', 'between']
        constraint_count = sum(1 for word in constraint_words if word in prompt.lower())
        score += min(constraint_count * 0.03, 0.1)
        
        return max(0, min(1, score))
    
    def _assess_creativity_heuristic(self, prompt: str) -> float:
        """Assess creativity using heuristics"""
        score = 0.5  # Base score
        
        # Creative language
        creative_words = ['creative', 'innovative', 'unique', 'original', 'imaginative', 'brainstorm']
        creative_count = sum(1 for word in creative_words if word in prompt.lower())
        score += min(creative_count * 0.1, 0.3)
        
        # Open-ended questions
        if '?' in prompt and ('how' in prompt.lower() or 'what if' in prompt.lower()):
            score += 0.1
        
        # Multiple perspectives
        perspective_words = ['alternative', 'different', 'various', 'multiple', 'diverse']
        perspective_count = sum(1 for word in perspective_words if word in prompt.lower())
        score += min(perspective_count * 0.05, 0.2)
        
        # Metaphors or analogies
        if 'like' in prompt or 'as if' in prompt or 'imagine' in prompt.lower():
            score += 0.05
        
        return max(0, min(1, score))
    
    # Helper methods
    def _parse_llm_assessment(self, response: str) -> Dict[str, float]:
        """Parse LLM assessment response"""
        
        default_scores = {
            "clarity": 0.5,
            "specificity": 0.5,
            "completeness": 0.5,
            "coherence": 0.5,
            "effectiveness": 0.5,
            "creativity": 0.5
        }
        
        # Extract scores using regex
        for dimension in default_scores.keys():
            pattern = f"{dimension.upper()}:\\s*([0-9.]+)"
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    default_scores[dimension] = max(0, min(1, score))
                except ValueError:
                    pass
        
        return default_scores
    
    def _generate_detailed_feedback(self, prompt: str, metrics: QualityMetrics) -> Dict[str, str]:
        """Generate detailed feedback for each dimension"""
        
        feedback = {}
        
        # Clarity feedback
        if metrics.clarity_score < 0.5:
            feedback["clarity"] = "Consider using clearer language and better structure to improve understandability."
        elif metrics.clarity_score < 0.7:
            feedback["clarity"] = "Good clarity, but could benefit from more explicit instructions."
        else:
            feedback["clarity"] = "Excellent clarity - the prompt is easy to understand."
        
        # Specificity feedback
        if metrics.specificity_score < 0.5:
            feedback["specificity"] = "Add more specific details, examples, or constraints to guide the response."
        elif metrics.specificity_score < 0.7:
            feedback["specificity"] = "Good level of detail, consider adding more specific examples."
        else:
            feedback["specificity"] = "Excellent specificity - clear and detailed instructions."
        
        # Completeness feedback
        if metrics.completeness_score < 0.5:
            feedback["completeness"] = "The prompt seems incomplete. Consider adding context and requirements."
        elif metrics.completeness_score < 0.7:
            feedback["completeness"] = "Fairly complete, but could benefit from additional context."
        else:
            feedback["completeness"] = "Comprehensive prompt with good context and requirements."
        
        # Coherence feedback
        if metrics.coherence_score < 0.5:
            feedback["coherence"] = "Improve logical flow and structure for better coherence."
        elif metrics.coherence_score < 0.7:
            feedback["coherence"] = "Good structure, but some parts could be better connected."
        else:
            feedback["coherence"] = "Excellent coherence - well-structured and logical."
        
        # Effectiveness feedback
        if metrics.effectiveness_score < 0.5:
            feedback["effectiveness"] = "May not achieve intended goals. Clarify objectives and expected outcomes."
        elif metrics.effectiveness_score < 0.7:
            feedback["effectiveness"] = "Likely to be effective, but could be more goal-oriented."
        else:
            feedback["effectiveness"] = "Highly effective prompt that should achieve its objectives."
        
        # Creativity feedback
        if metrics.creativity_score < 0.5:
            feedback["creativity"] = "Consider adding creative elements or encouraging innovative thinking."
        elif metrics.creativity_score < 0.7:
            feedback["creativity"] = "Some creative elements present, could encourage more innovation."
        else:
            feedback["creativity"] = "Excellent creativity - encourages innovative and original thinking."
        
        return feedback
    
    def _generate_improvement_suggestions(self, prompt: str, metrics: QualityMetrics) -> List[str]:
        """Generate specific improvement suggestions"""
        
        suggestions = []
        
        # Based on lowest scoring dimensions
        scores = {
            "clarity": metrics.clarity_score,
            "specificity": metrics.specificity_score,
            "completeness": metrics.completeness_score,
            "coherence": metrics.coherence_score,
            "effectiveness": metrics.effectiveness_score,
            "creativity": metrics.creativity_score
        }
        
        # Find areas for improvement (scores < 0.7)
        improvements_needed = {k: v for k, v in scores.items() if v < 0.7}
        
        if "clarity" in improvements_needed:
            suggestions.append("Use simpler language and break complex instructions into steps")
        
        if "specificity" in improvements_needed:
            suggestions.append("Add specific examples and detailed requirements")
        
        if "completeness" in improvements_needed:
            suggestions.append("Include more context and background information")
        
        if "coherence" in improvements_needed:
            suggestions.append("Improve logical flow with connecting words and better structure")
        
        if "effectiveness" in improvements_needed:
            suggestions.append("Clearly state the desired outcome and success criteria")
        
        if "creativity" in improvements_needed:
            suggestions.append("Encourage creative thinking with open-ended questions")
        
        # Generic suggestions if overall score is low
        if metrics.overall_score < 0.6:
            suggestions.append("Consider the target audience and adjust language accordingly")
            suggestions.append("Test the prompt with different scenarios to ensure robustness")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _compare_against_benchmarks(self, metrics: QualityMetrics) -> Dict[str, float]:
        """Compare metrics against quality benchmarks"""
        
        # Load or use default benchmarks
        benchmarks = self.benchmark_standards or {
            "high_quality_prompt": 0.8,
            "professional_standard": 0.7,
            "acceptable_quality": 0.6,
            "needs_improvement": 0.5
        }
        
        comparison = {}
        for benchmark_name, threshold in benchmarks.items():
            if metrics.overall_score >= threshold:
                comparison[benchmark_name] = 1.0
            else:
                comparison[benchmark_name] = metrics.overall_score / threshold
        
        return comparison
    
    def _load_benchmark_standards(self):
        """Load quality benchmarks from database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT benchmark_name, score_threshold FROM quality_benchmarks')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            self.benchmark_standards = {row[0]: row[1] for row in rows}
        else:
            # Set default benchmarks
            self.benchmark_standards = {
                "high_quality_prompt": 0.8,
                "professional_standard": 0.7,
                "acceptable_quality": 0.6,
                "needs_improvement": 0.5
            }
    
    def _store_assessment(self, assessment: QualityAssessment):
        """Store assessment in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quality_assessments 
            (assessment_id, session_id, version_id, clarity_score, specificity_score, completeness_score, 
             coherence_score, effectiveness_score, creativity_score, overall_score, confidence_level, 
             method_used, detailed_feedback, improvement_suggestions, benchmark_comparison, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment.assessment_id,
            self.session_id,
            assessment.version_id,
            assessment.metrics.clarity_score,
            assessment.metrics.specificity_score,
            assessment.metrics.completeness_score,
            assessment.metrics.coherence_score,
            assessment.metrics.effectiveness_score,
            assessment.metrics.creativity_score,
            assessment.metrics.overall_score,
            assessment.metrics.confidence_level,
            assessment.method_used.value,
            json.dumps(assessment.detailed_feedback),
            json.dumps(assessment.improvement_suggestions),
            json.dumps(assessment.benchmark_comparison),
            assessment.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _get_stored_assessment(self, version_id: str) -> Optional[QualityAssessment]:
        """Retrieve stored assessment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT assessment_id, clarity_score, specificity_score, completeness_score, 
                   coherence_score, effectiveness_score, creativity_score, overall_score, 
                   confidence_level, method_used, detailed_feedback, improvement_suggestions, 
                   benchmark_comparison, timestamp
            FROM quality_assessments WHERE version_id = ? ORDER BY timestamp DESC LIMIT 1
        ''', (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            metrics = QualityMetrics(
                clarity_score=row[1],
                specificity_score=row[2],
                completeness_score=row[3],
                coherence_score=row[4],
                effectiveness_score=row[5],
                creativity_score=row[6],
                overall_score=row[7],
                confidence_level=row[8]
            )
            
            return QualityAssessment(
                assessment_id=row[0],
                version_id=version_id,
                metrics=metrics,
                method_used=AssessmentMethod(row[9]),
                detailed_feedback=json.loads(row[10]) if row[10] else {},
                improvement_suggestions=json.loads(row[11]) if row[11] else [],
                benchmark_comparison=json.loads(row[12]) if row[12] else {},
                timestamp=row[13]
            )
        
        return None
    
    def _store_comparative_assessment(self, version_ids: List[str], comparison_data: Dict[str, Any]):
        """Store comparative assessment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comparative_assessments 
            (comparison_id, session_id, version_ids, relative_scores, winner_version, comparison_notes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            self.session_id,
            json.dumps(version_ids),
            json.dumps(comparison_data["quality_ranking"]),
            comparison_data["quality_ranking"][0]["version_id"] if comparison_data["quality_ranking"] else "",
            json.dumps(comparison_data),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _find_similar_assessments(self, prompt: str) -> List[QualityAssessment]:
        """Find assessments for similar prompts"""
        # Simplified - could use more sophisticated similarity matching
        return []


def main():
    """Test the quality assessment system"""
    print("📊 Testing Quality Assessment System")
    print("=" * 50)
    
    # Initialize quality assessor
    assessor = QualityAssessor(session_id="test_quality")
    
    # Test prompt assessment
    test_prompt = "Write a creative story about AI that includes dialogue and explores consciousness themes. Make it engaging and well-structured with clear character development."
    
    print(f"\n🔍 Assessing test prompt:")
    print(f"Prompt: {test_prompt[:100]}...")
    
    assessment = assessor.assess_prompt_quality(test_prompt, "test_version_1")
    
    print(f"\n📊 Assessment Results:")
    print(f"Overall Score: {assessment.metrics.overall_score:.2f}")
    print(f"Clarity: {assessment.metrics.clarity_score:.2f}")
    print(f"Specificity: {assessment.metrics.specificity_score:.2f}")
    print(f"Completeness: {assessment.metrics.completeness_score:.2f}")
    print(f"Confidence: {assessment.metrics.confidence_level:.2f}")
    
    # Test quality report
    print(f"\n📋 Quality Report:")
    report = assessor.generate_quality_report("test_version_1")
    print(report[:500] + "..." if len(report) > 500 else report)
    
    print(f"\n✅ QualityAssessor system test completed!")


if __name__ == "__main__":
    main()