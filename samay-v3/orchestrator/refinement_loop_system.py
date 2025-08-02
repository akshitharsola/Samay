#!/usr/bin/env python3
"""
Samay v3 - Refinement Loop System
=================================
Phase 3: Automatic refinement loops to ensure correct outputs from web services
"""

import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum
import sqlite3
import re

from .local_llm import LocalLLMClient
from .web_agent_dispatcher import ServiceType, OutputFormat, WebResponse, RequestStatus
from .machine_language_optimizer import MachineLanguageOptimizer


class RefinementTrigger(Enum):
    FORMAT_MISMATCH = "format_mismatch"
    MISSING_FIELDS = "missing_fields"
    INVALID_DATA = "invalid_data"
    INCOMPLETE_RESPONSE = "incomplete_response"
    STRUCTURE_ERROR = "structure_error"
    CONTENT_MISMATCH = "content_mismatch"


class RefinementAction(Enum):
    CLARIFY_FORMAT = "clarify_format"
    REQUEST_MISSING_DATA = "request_missing_data"
    FIX_STRUCTURE = "fix_structure"
    PROVIDE_EXAMPLES = "provide_examples"
    SIMPLIFY_REQUEST = "simplify_request"
    SPLIT_REQUEST = "split_request"


@dataclass
class RefinementRule:
    """Defines conditions and actions for refinement"""
    rule_id: str
    trigger: RefinementTrigger
    condition: str  # Description of when to trigger
    action: RefinementAction
    priority: int  # 1-5, higher is more important
    max_attempts: int
    service_specific: Optional[ServiceType]
    success_rate: float


@dataclass
class RefinementAttempt:
    """Represents a single refinement attempt"""
    attempt_id: str
    original_request_id: str
    refinement_number: int
    trigger_reason: RefinementTrigger
    refinement_prompt: str
    expected_fix: str
    service: ServiceType
    timestamp: str


@dataclass
class RefinementSession:
    """Tracks a complete refinement session"""
    session_id: str
    original_prompt: str
    target_output: str
    service: ServiceType
    attempts: List[RefinementAttempt]
    final_success: bool
    total_attempts: int
    time_elapsed: float
    final_quality_score: float


class RefinementLoopSystem:
    """Manages automatic refinement loops for web service outputs"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "refinement_loops.db"
        self.session_id = session_id
        self.llm_client = LocalLLMClient()
        self.optimizer = MachineLanguageOptimizer(memory_dir, session_id + "_refine_opt")
        
        # Refinement rules and patterns
        self.refinement_rules = []
        self.success_patterns = {}
        self.failure_patterns = {}
        
        # Performance tracking
        self.refinement_stats = {
            "total_sessions": 0,
            "successful_refinements": 0,
            "average_attempts": 0,
            "service_performance": {}
        }
        
        self.init_database()
        self._load_default_rules()
        print(f"🔄 RefinementLoopSystem initialized for session {session_id}")
    
    def init_database(self):
        """Initialize refinement loop database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Refinement rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refinement_rules (
                rule_id TEXT PRIMARY KEY,
                trigger TEXT,
                condition_desc TEXT,
                action TEXT,
                priority INTEGER,
                max_attempts INTEGER,
                service_specific TEXT,
                success_rate REAL,
                created_at TEXT
            )
        ''')
        
        # Refinement sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refinement_sessions (
                session_id TEXT PRIMARY KEY,
                original_prompt TEXT,
                target_output TEXT,
                service TEXT,
                final_success BOOLEAN,
                total_attempts INTEGER,
                time_elapsed REAL,
                final_quality_score REAL,
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # Refinement attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refinement_attempts (
                attempt_id TEXT PRIMARY KEY,
                session_id TEXT,
                refinement_number INTEGER,
                trigger_reason TEXT,
                refinement_prompt TEXT,
                expected_fix TEXT,
                service TEXT,
                response_received TEXT,
                attempt_success BOOLEAN,
                quality_improvement REAL,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES refinement_sessions (session_id)
            )
        ''')
        
        # Success patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS success_patterns (
                pattern_id TEXT PRIMARY KEY,
                service TEXT,
                trigger_type TEXT,
                successful_prompt_pattern TEXT,
                success_count INTEGER,
                failure_count INTEGER,
                effectiveness_score REAL,
                last_updated TEXT
            )
        ''')
        
        # Quality metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                metric_id TEXT PRIMARY KEY,
                session_id TEXT,
                attempt_number INTEGER,
                format_compliance REAL,
                content_accuracy REAL,
                completeness_score REAL,
                structure_validity REAL,
                overall_quality REAL,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def execute_refinement_loop(
        self,
        original_prompt: str,
        expected_output: str,
        service: ServiceType,
        output_format: OutputFormat,
        max_refinements: int = 5,
        quality_threshold: float = 0.8
    ) -> RefinementSession:
        """Execute complete refinement loop until success or max attempts"""
        
        session_start = time.time()
        session = RefinementSession(
            session_id=str(uuid.uuid4()),
            original_prompt=original_prompt,
            target_output=expected_output,
            service=service,
            attempts=[],
            final_success=False,
            total_attempts=0,
            time_elapsed=0.0,
            final_quality_score=0.0
        )
        
        # Store initial session
        self._store_refinement_session(session)
        
        # Start with optimized prompt
        current_prompt = self.optimizer.optimize_for_service(
            original_prompt, service, expected_output, output_format
        ).optimized_prompt
        
        current_quality = 0.0
        refinement_count = 0
        
        print(f"🔄 Starting refinement loop for {service.value}")
        print(f"🎯 Target quality: {quality_threshold}")
        
        while refinement_count < max_refinements and current_quality < quality_threshold:
            refinement_count += 1
            
            print(f"🔄 Refinement attempt {refinement_count}/{max_refinements}")
            
            # Send request (mock for now - would integrate with web automation)
            response = await self._send_mock_request(current_prompt, service)
            
            # Analyze response quality and issues
            quality_score, issues = await self._analyze_response_quality(
                response, expected_output, output_format
            )
            
            print(f"📊 Quality score: {quality_score:.2f}")
            if issues:
                print(f"⚠️ Issues detected: {', '.join(issues[:2])}")
            
            # Store quality metrics
            self._store_quality_metrics(session.session_id, refinement_count, quality_score)
            
            # Check if quality is acceptable
            if quality_score >= quality_threshold:
                session.final_success = True
                session.final_quality_score = quality_score
                print(f"✅ Success! Quality threshold reached: {quality_score:.2f}")
                break
            
            # Determine refinement strategy
            refinement_trigger, refinement_action = self._determine_refinement_strategy(
                issues, service, refinement_count
            )
            
            # Generate refinement prompt
            refinement_prompt = await self._generate_refinement_prompt(
                current_prompt, response, issues, refinement_action, service, expected_output
            )
            
            # Create refinement attempt record
            attempt = RefinementAttempt(
                attempt_id=str(uuid.uuid4()),
                original_request_id=session.session_id,
                refinement_number=refinement_count,
                trigger_reason=refinement_trigger,
                refinement_prompt=refinement_prompt,
                expected_fix=self._describe_expected_fix(refinement_action, issues),
                service=service,
                timestamp=datetime.now().isoformat()
            )
            
            session.attempts.append(attempt)
            self._store_refinement_attempt(attempt, response, quality_score > current_quality)
            
            # Update current prompt for next iteration
            current_prompt = refinement_prompt
            current_quality = quality_score
            
            # Brief delay to avoid overwhelming the service
            await asyncio.sleep(1)
        
        # Finalize session
        session.total_attempts = refinement_count
        session.time_elapsed = time.time() - session_start
        session.final_quality_score = current_quality
        
        if not session.final_success:
            print(f"❌ Failed to reach quality threshold after {max_refinements} attempts")
            print(f"📊 Final quality: {current_quality:.2f}")
        
        # Update session in database
        self._update_refinement_session(session)
        
        # Update success patterns
        self._update_success_patterns(session)
        
        print(f"⏱️ Refinement loop completed in {session.time_elapsed:.2f}s")
        return session
    
    async def _send_mock_request(self, prompt: str, service: ServiceType) -> str:
        """Mock web request - would be replaced with actual web automation"""
        
        # Simulate different service response patterns
        await asyncio.sleep(2)  # Simulate network delay
        
        # Mock responses with different quality levels based on refinement
        if "JSON" in prompt and "{" in prompt:
            # Better structured prompt gets better response
            return '{"data": "example response", "status": "partial"}'
        elif "format" in prompt.lower():
            # Format-aware prompt gets semi-structured response
            return 'Data: example response\nStatus: incomplete'
        else:
            # Basic prompt gets unstructured response
            return 'Here is some information about your request. The data shows various results.'
        
    async def _analyze_response_quality(
        self,
        response: str,
        expected_output: str,
        output_format: OutputFormat
    ) -> Tuple[float, List[str]]:
        """Analyze response quality and identify issues"""
        
        issues = []
        quality_components = {}
        
        # Format compliance check
        format_score = self._check_format_compliance(response, output_format)
        quality_components['format'] = format_score
        
        if format_score < 0.5:
            if output_format == OutputFormat.JSON:
                issues.append("Response is not valid JSON format")
            else:
                issues.append(f"Response doesn't match {output_format.value} format")
        
        # Structure compliance check
        structure_score = self._check_structure_compliance(response, expected_output)
        quality_components['structure'] = structure_score
        
        if structure_score < 0.5:
            issues.append("Response missing required structure elements")
        
        # Content completeness check
        completeness_score = self._check_content_completeness(response, expected_output)
        quality_components['completeness'] = completeness_score
        
        if completeness_score < 0.5:
            issues.append("Response appears incomplete or too brief")
        
        # Content accuracy check (simplified)
        accuracy_score = self._check_content_accuracy(response)
        quality_components['accuracy'] = accuracy_score
        
        if accuracy_score < 0.5:
            issues.append("Response content may be inaccurate or irrelevant")
        
        # Calculate overall quality score
        weights = {'format': 0.3, 'structure': 0.3, 'completeness': 0.2, 'accuracy': 0.2}
        overall_quality = sum(score * weights[component] for component, score in quality_components.items())
        
        return overall_quality, issues
    
    def _check_format_compliance(self, response: str, output_format: OutputFormat) -> float:
        """Check if response complies with expected format"""
        
        if output_format == OutputFormat.JSON:
            try:
                json.loads(response.strip())
                return 1.0
            except:
                # Check if it contains JSON-like structure
                if '{' in response and '}' in response:
                    return 0.3
                return 0.0
        
        elif output_format == OutputFormat.STRUCTURED_TEXT:
            # Look for field labels and structured content
            if ':' in response and '\n' in response:
                return 0.8
            elif ':' in response:
                return 0.5
            return 0.2
        
        elif output_format == OutputFormat.MARKDOWN:
            # Look for markdown indicators
            md_indicators = ['#', '**', '*', '-', '```']
            found = sum(1 for indicator in md_indicators if indicator in response)
            return min(found * 0.2, 1.0)
        
        return 0.5  # Default for other formats
    
    def _check_structure_compliance(self, response: str, expected_output: str) -> float:
        """Check if response has expected structure"""
        
        try:
            expected_structure = json.loads(expected_output)
            if isinstance(expected_structure, dict):
                # Check for required keys
                required_keys = expected_structure.keys()
                found_keys = 0
                
                for key in required_keys:
                    if key in response:
                        found_keys += 1
                
                return found_keys / len(required_keys) if required_keys else 0.5
        except:
            # Fall back to text-based checking
            pass
        
        # Simple text-based structure checking
        expected_words = expected_output.lower().split()
        response_words = response.lower().split()
        
        matches = sum(1 for word in expected_words if word in response_words)
        return matches / len(expected_words) if expected_words else 0.0
    
    def _check_content_completeness(self, response: str, expected_output: str) -> float:
        """Check if response is complete"""
        
        # Length-based completeness check
        if len(response) < 20:
            return 0.1
        elif len(response) < 50:
            return 0.4
        elif len(response) > 200:
            return 1.0
        else:
            return len(response) / 200
    
    def _check_content_accuracy(self, response: str) -> float:
        """Check content accuracy (simplified heuristic)"""
        
        # Look for uncertainty indicators
        uncertainty_words = ['maybe', 'perhaps', 'might', 'could be', 'not sure']
        uncertainty_count = sum(1 for word in uncertainty_words if word in response.lower())
        
        # Look for confident language
        confident_words = ['is', 'are', 'will', 'must', 'definitely']
        confident_count = sum(1 for word in confident_words if word in response.lower())
        
        # Simple scoring
        if uncertainty_count > confident_count:
            return 0.3
        elif confident_count > 0:
            return 0.8
        else:
            return 0.5
    
    def _determine_refinement_strategy(
        self,
        issues: List[str],
        service: ServiceType,
        attempt_number: int
    ) -> Tuple[RefinementTrigger, RefinementAction]:
        """Determine the best refinement strategy based on issues"""
        
        # Analyze issues to determine trigger
        trigger = RefinementTrigger.CONTENT_MISMATCH  # Default
        
        for issue in issues:
            if "format" in issue.lower():
                trigger = RefinementTrigger.FORMAT_MISMATCH
                break
            elif "missing" in issue.lower() or "structure" in issue.lower():
                trigger = RefinementTrigger.MISSING_FIELDS
                break
            elif "incomplete" in issue.lower():
                trigger = RefinementTrigger.INCOMPLETE_RESPONSE
                break
            elif "invalid" in issue.lower():
                trigger = RefinementTrigger.INVALID_DATA
                break
        
        # Find matching rules
        matching_rules = [
            rule for rule in self.refinement_rules
            if rule.trigger == trigger and 
            (rule.service_specific is None or rule.service_specific == service) and
            attempt_number <= rule.max_attempts
        ]
        
        if matching_rules:
            # Use highest priority rule
            best_rule = max(matching_rules, key=lambda r: r.priority)
            return trigger, best_rule.action
        
        # Fallback strategy based on attempt number
        if attempt_number == 1:
            return trigger, RefinementAction.CLARIFY_FORMAT
        elif attempt_number == 2:
            return trigger, RefinementAction.PROVIDE_EXAMPLES
        elif attempt_number >= 3:
            return trigger, RefinementAction.SIMPLIFY_REQUEST
        
        return trigger, RefinementAction.CLARIFY_FORMAT
    
    async def _generate_refinement_prompt(
        self,
        original_prompt: str,
        failed_response: str,
        issues: List[str],
        action: RefinementAction,
        service: ServiceType,
        expected_output: str
    ) -> str:
        """Generate refinement prompt based on action and issues"""
        
        # Base refinement templates
        action_templates = {
            RefinementAction.CLARIFY_FORMAT: """
The previous response didn't match the required format. 

ISSUES DETECTED:
{issues}

ORIGINAL REQUEST:
{original_prompt}

PREVIOUS RESPONSE:
{failed_response}

REQUIRED FORMAT:
{expected_output}

Please provide a response that EXACTLY matches the required format. Pay special attention to:
1. Use the exact format specified
2. Include all required fields
3. Ensure proper data types
4. No additional text outside the format

Corrected response:
""",
            RefinementAction.REQUEST_MISSING_DATA: """
Your previous response was missing required information.

MISSING ELEMENTS:
{issues}

ORIGINAL REQUEST:
{original_prompt}

PREVIOUS INCOMPLETE RESPONSE:
{failed_response}

Please provide a COMPLETE response that includes:
{expected_output}

Make sure to address all missing elements identified above.

Complete response:
""",
            RefinementAction.PROVIDE_EXAMPLES: """
The format wasn't clear from the previous response. Here's exactly what I need:

ORIGINAL REQUEST:
{original_prompt}

EXACT FORMAT REQUIRED:
{expected_output}

EXAMPLE of correct format:
{example}

ISSUES WITH PREVIOUS RESPONSE:
{issues}

Please provide your response using EXACTLY the format shown in the example above.

Response:
""",
            RefinementAction.SIMPLIFY_REQUEST: """
Let me simplify the request to make it clearer:

SIMPLIFIED REQUEST:
{simplified_prompt}

REQUIRED OUTPUT FORMAT:
{expected_output}

ISSUES TO AVOID:
{issues}

Please provide a response that follows the format exactly.

Response:
""",
            RefinementAction.FIX_STRUCTURE: """
The structure of your previous response needs correction.

STRUCTURAL ISSUES:
{issues}

CORRECT STRUCTURE NEEDED:
{expected_output}

PREVIOUS RESPONSE (with issues):
{failed_response}

Please reformat your response to match the correct structure exactly.

Corrected response:
"""
        }
        
        # Get template for action
        template = action_templates.get(action, action_templates[RefinementAction.CLARIFY_FORMAT])
        
        # Generate example if needed
        example = ""
        if action == RefinementAction.PROVIDE_EXAMPLES:
            example = await self._generate_example_output(expected_output, service)
        
        # Simplify prompt if needed
        simplified_prompt = original_prompt
        if action == RefinementAction.SIMPLIFY_REQUEST:
            simplified_prompt = await self._simplify_prompt(original_prompt, service)
        
        # Format template
        refinement_prompt = template.format(
            issues="\n".join(f"• {issue}" for issue in issues),
            original_prompt=original_prompt,
            failed_response=failed_response[:300] + "..." if len(failed_response) > 300 else failed_response,
            expected_output=expected_output,
            example=example,
            simplified_prompt=simplified_prompt
        )
        
        return refinement_prompt
    
    async def _generate_example_output(self, expected_output: str, service: ServiceType) -> str:
        """Generate example output using local LLM"""
        
        example_prompt = f"""
Create a realistic example that matches this structure:
{expected_output}

The example should be realistic and demonstrate the exact format needed.
"""
        
        response = self.llm_client.generate_response(
            example_prompt,
            "You are an expert at creating examples. Provide only the example, no explanations."
        )
        
        return response.response if response.success else expected_output
    
    async def _simplify_prompt(self, original_prompt: str, service: ServiceType) -> str:
        """Simplify prompt using local LLM"""
        
        simplify_prompt = f"""
Simplify this prompt to make it clearer and more direct:

ORIGINAL: {original_prompt}

Make it:
1. More concise
2. Clearer in intent
3. Easier to understand
4. Direct and specific

Simplified version:
"""
        
        response = self.llm_client.generate_response(
            simplify_prompt,
            f"You are an expert at simplifying prompts for {service.value}. Be concise and clear."
        )
        
        return response.response if response.success else original_prompt
    
    def _describe_expected_fix(self, action: RefinementAction, issues: List[str]) -> str:
        """Describe what the refinement should fix"""
        
        descriptions = {
            RefinementAction.CLARIFY_FORMAT: "Correct the output format to match specifications",
            RefinementAction.REQUEST_MISSING_DATA: "Include all missing required fields and data",
            RefinementAction.FIX_STRUCTURE: "Restructure the response to match expected format",
            RefinementAction.PROVIDE_EXAMPLES: "Follow the provided example format exactly",
            RefinementAction.SIMPLIFY_REQUEST: "Address the simplified, clearer request",
            RefinementAction.SPLIT_REQUEST: "Address each part of the split request separately"
        }
        
        base_description = descriptions.get(action, "Improve response quality")
        if issues:
            return f"{base_description}. Specific issues: {', '.join(issues[:2])}"
        return base_description
    
    def _load_default_rules(self):
        """Load default refinement rules"""
        
        default_rules = [
            # Format mismatch rules
            RefinementRule(
                rule_id="format_json_fix",
                trigger=RefinementTrigger.FORMAT_MISMATCH,
                condition="Response not in JSON format when JSON expected",
                action=RefinementAction.CLARIFY_FORMAT,
                priority=5,
                max_attempts=3,
                service_specific=None,
                success_rate=0.8
            ),
            # Missing fields rules
            RefinementRule(
                rule_id="missing_fields_request",
                trigger=RefinementTrigger.MISSING_FIELDS,
                condition="Required fields missing from response",
                action=RefinementAction.REQUEST_MISSING_DATA,
                priority=4,
                max_attempts=2,
                service_specific=None,
                success_rate=0.7
            ),
            # Incomplete response rules
            RefinementRule(
                rule_id="incomplete_example",
                trigger=RefinementTrigger.INCOMPLETE_RESPONSE,
                condition="Response too brief or incomplete",
                action=RefinementAction.PROVIDE_EXAMPLES,
                priority=3,
                max_attempts=2,
                service_specific=None,
                success_rate=0.6
            ),
            # Service-specific rules
            RefinementRule(
                rule_id="claude_structure_fix",
                trigger=RefinementTrigger.STRUCTURE_ERROR,
                condition="Claude response structure issues",
                action=RefinementAction.FIX_STRUCTURE,
                priority=4,
                max_attempts=2,
                service_specific=ServiceType.CLAUDE,
                success_rate=0.75
            )
        ]
        
        self.refinement_rules = default_rules
        
        # Store rules in database
        for rule in default_rules:
            self._store_refinement_rule(rule)
    
    def get_refinement_statistics(self) -> Dict[str, Any]:
        """Get refinement loop statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN final_success = 1 THEN 1 ELSE 0 END) as successful_sessions,
                AVG(total_attempts) as avg_attempts,
                AVG(time_elapsed) as avg_time,
                AVG(final_quality_score) as avg_final_quality
            FROM refinement_sessions
        ''')
        overall_stats = dict(zip([
            'total_sessions', 'successful_sessions', 'avg_attempts', 'avg_time', 'avg_final_quality'
        ], cursor.fetchone()))
        
        # Service-specific stats
        cursor.execute('''
            SELECT 
                service,
                COUNT(*) as sessions,
                AVG(total_attempts) as avg_attempts,
                SUM(CASE WHEN final_success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM refinement_sessions
            GROUP BY service
        ''')
        service_stats = [
            dict(zip(['service', 'sessions', 'avg_attempts', 'success_rate'], row))
            for row in cursor.fetchall()
        ]
        
        # Most common issues
        cursor.execute('''
            SELECT 
                trigger_reason,
                COUNT(*) as frequency
            FROM refinement_attempts
            GROUP BY trigger_reason
            ORDER BY frequency DESC
            LIMIT 5
        ''')
        common_issues = [
            dict(zip(['issue', 'frequency'], row))
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "overall": overall_stats,
            "by_service": service_stats,
            "common_issues": common_issues,
            "success_rate": overall_stats['successful_sessions'] / overall_stats['total_sessions'] if overall_stats['total_sessions'] > 0 else 0
        }
    
    # Database operations
    def _store_refinement_session(self, session: RefinementSession):
        """Store refinement session in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO refinement_sessions 
            (session_id, original_prompt, target_output, service, final_success, 
             total_attempts, time_elapsed, final_quality_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.session_id,
            session.original_prompt,
            session.target_output,
            session.service.value,
            session.final_success,
            session.total_attempts,
            session.time_elapsed,
            session.final_quality_score,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _update_refinement_session(self, session: RefinementSession):
        """Update refinement session with final results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE refinement_sessions 
            SET final_success = ?, total_attempts = ?, time_elapsed = ?, 
                final_quality_score = ?, completed_at = ?
            WHERE session_id = ?
        ''', (
            session.final_success,
            session.total_attempts,
            session.time_elapsed,
            session.final_quality_score,
            datetime.now().isoformat(),
            session.session_id
        ))
        conn.commit()
        conn.close()
    
    def _store_refinement_attempt(self, attempt: RefinementAttempt, response: str, success: bool):
        """Store refinement attempt in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO refinement_attempts 
            (attempt_id, session_id, refinement_number, trigger_reason, refinement_prompt, 
             expected_fix, service, response_received, attempt_success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            attempt.attempt_id,
            attempt.original_request_id,
            attempt.refinement_number,
            attempt.trigger_reason.value,
            attempt.refinement_prompt,
            attempt.expected_fix,
            attempt.service.value,
            response[:1000],  # Truncate response
            success,
            attempt.timestamp
        ))
        conn.commit()
        conn.close()
    
    def _store_refinement_rule(self, rule: RefinementRule):
        """Store refinement rule in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO refinement_rules 
            (rule_id, trigger, condition_desc, action, priority, max_attempts, 
             service_specific, success_rate, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rule.rule_id,
            rule.trigger.value,
            rule.condition,
            rule.action.value,
            rule.priority,
            rule.max_attempts,
            rule.service_specific.value if rule.service_specific else None,
            rule.success_rate,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _store_quality_metrics(self, session_id: str, attempt_number: int, quality_score: float):
        """Store quality metrics for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quality_metrics 
            (metric_id, session_id, attempt_number, overall_quality, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            session_id,
            attempt_number,
            quality_score,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _update_success_patterns(self, session: RefinementSession):
        """Update success patterns based on session results"""
        # This would analyze successful refinement patterns for future use
        pass


def main():
    """Test the refinement loop system"""
    print("🔄 Testing Refinement Loop System")
    print("=" * 50)
    
    # Initialize system
    system = RefinementLoopSystem(session_id="test_refinement")
    
    # Test refinement loop
    print("\n🔄 Testing refinement loop...")
    
    async def test_loop():
        session = await system.execute_refinement_loop(
            "Extract company information from the text",
            '{"companies": [{"name": "", "description": ""}], "count": 0}',
            ServiceType.CLAUDE,
            OutputFormat.JSON,
            max_refinements=3,
            quality_threshold=0.7
        )
        
        print(f"✅ Refinement loop completed!")
        print(f"   Success: {session.final_success}")
        print(f"   Attempts: {session.total_attempts}")
        print(f"   Final quality: {session.final_quality_score:.2f}")
        print(f"   Time elapsed: {session.time_elapsed:.2f}s")
    
    # Run async test
    import asyncio
    asyncio.run(test_loop())
    
    # Test statistics
    print("\n📊 Testing statistics...")
    stats = system.get_refinement_statistics()
    print(f"✅ Statistics retrieved:")
    print(f"   Total sessions: {stats['overall']['total_sessions']}")
    print(f"   Success rate: {stats['success_rate']:.2f}")
    
    print(f"\n✅ RefinementLoopSystem test completed!")


if __name__ == "__main__":
    main()