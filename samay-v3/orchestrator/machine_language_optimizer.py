#!/usr/bin/env python3
"""
Samay v3 - Machine Language Optimizer
====================================
Phase 3: Optimize prompts for machine-readable outputs from web interfaces
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum
import sqlite3

from .local_llm import LocalLLMClient
from .web_agent_dispatcher import ServiceType, OutputFormat


class PromptCategory(Enum):
    INFORMATION_EXTRACTION = "information_extraction"
    DATA_ANALYSIS = "data_analysis"
    CREATIVE_GENERATION = "creative_generation"
    PROBLEM_SOLVING = "problem_solving"
    RESEARCH = "research"
    COMPARISON = "comparison"


class OptimizationStrategy(Enum):
    TOKEN_MINIMIZATION = "token_minimization"
    CLARITY_MAXIMIZATION = "clarity_maximization"
    STRUCTURE_ENFORCEMENT = "structure_enforcement"
    PRECISION_TARGETING = "precision_targeting"


@dataclass
class PromptOptimization:
    """Represents an optimized prompt"""
    optimization_id: str
    original_prompt: str
    optimized_prompt: str
    target_service: ServiceType
    output_format: OutputFormat
    category: PromptCategory
    strategy: OptimizationStrategy
    token_reduction: int
    clarity_score: float
    structure_compliance: float
    created_at: str


@dataclass
class MachineLanguageTemplate:
    """Template for machine-readable communication"""
    template_id: str
    name: str
    category: PromptCategory
    service_compatibility: List[ServiceType]
    template_structure: str
    output_schema: Dict[str, Any]
    validation_rules: List[str]
    example_usage: Dict[str, str]


class MachineLanguageOptimizer:
    """Optimizes prompts for machine-readable outputs"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "ml_optimizer.db"
        self.session_id = session_id
        self.llm_client = LocalLLMClient()
        
        # Optimization templates and patterns
        self.service_patterns = self._load_service_patterns()
        self.optimization_templates = self._load_optimization_templates()
        self.validation_schemas = self._load_validation_schemas()
        
        self.init_database()
        self._load_predefined_templates()
        print(f"🔧 MachineLanguageOptimizer initialized for session {session_id}")
    
    def init_database(self):
        """Initialize machine language optimizer database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prompt optimizations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_optimizations (
                optimization_id TEXT PRIMARY KEY,
                session_id TEXT,
                original_prompt TEXT,
                optimized_prompt TEXT,
                target_service TEXT,
                output_format TEXT,
                category TEXT,
                strategy TEXT,
                token_reduction INTEGER,
                clarity_score REAL,
                structure_compliance REAL,
                created_at TEXT
            )
        ''')
        
        # Machine language templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_templates (
                template_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                service_compatibility TEXT,
                template_structure TEXT,
                output_schema TEXT,
                validation_rules TEXT,
                example_usage TEXT,
                created_at TEXT
            )
        ''')
        
        # Optimization patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_patterns (
                pattern_id TEXT PRIMARY KEY,
                service TEXT,
                pattern_type TEXT,
                pattern_regex TEXT,
                replacement_template TEXT,
                effectiveness_score REAL,
                usage_count INTEGER,
                last_used TEXT
            )
        ''')
        
        # Token efficiency table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_efficiency (
                efficiency_id TEXT PRIMARY KEY,
                original_tokens INTEGER,
                optimized_tokens INTEGER,
                token_savings INTEGER,
                optimization_type TEXT,
                service TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def optimize_for_service(
        self,
        prompt: str,
        target_service: ServiceType,
        expected_output: str,
        output_format: OutputFormat = OutputFormat.JSON,
        strategy: OptimizationStrategy = OptimizationStrategy.STRUCTURE_ENFORCEMENT
    ) -> PromptOptimization:
        """Optimize prompt for specific service with machine-readable output"""
        
        # Analyze prompt category
        category = self._classify_prompt_category(prompt)
        
        # Apply service-specific optimizations
        optimized_prompt = self._apply_service_optimization(
            prompt, target_service, strategy, output_format
        )
        
        # Add machine language structure
        structured_prompt = self._add_machine_language_structure(
            optimized_prompt, expected_output, output_format, target_service
        )
        
        # Add validation instructions
        final_prompt = self._add_validation_instructions(
            structured_prompt, expected_output, target_service
        )
        
        # Calculate metrics
        token_reduction = self._calculate_token_reduction(prompt, final_prompt)
        clarity_score = self._assess_clarity(final_prompt)
        structure_compliance = self._assess_structure_compliance(final_prompt, output_format)
        
        # Create optimization record
        optimization = PromptOptimization(
            optimization_id=str(uuid.uuid4()),
            original_prompt=prompt,
            optimized_prompt=final_prompt,
            target_service=target_service,
            output_format=output_format,
            category=category,
            strategy=strategy,
            token_reduction=token_reduction,
            clarity_score=clarity_score,
            structure_compliance=structure_compliance,
            created_at=datetime.now().isoformat()
        )
        
        # Store optimization
        self._store_optimization(optimization)
        
        print(f"🔧 Optimized for {target_service.value}: {token_reduction} tokens saved")
        print(f"📊 Clarity: {clarity_score:.2f}, Structure: {structure_compliance:.2f}")
        
        return optimization
    
    def create_machine_language_template(
        self,
        name: str,
        category: PromptCategory,
        services: List[ServiceType],
        base_structure: str,
        output_schema: Dict[str, Any],
        validation_rules: List[str]
    ) -> MachineLanguageTemplate:
        """Create reusable machine language template"""
        
        template = MachineLanguageTemplate(
            template_id=str(uuid.uuid4()),
            name=name,
            category=category,
            service_compatibility=services,
            template_structure=base_structure,
            output_schema=output_schema,
            validation_rules=validation_rules,
            example_usage=self._generate_example_usage(base_structure, services)
        )
        
        # Store template
        self._store_template(template)
        
        print(f"📝 Created template '{name}' for {len(services)} services")
        return template
    
    def apply_template(
        self,
        template_id: str,
        variables: Dict[str, str],
        target_service: ServiceType
    ) -> str:
        """Apply template with variables for specific service"""
        
        template = self._get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        if target_service not in template.service_compatibility:
            print(f"⚠️ Template not optimized for {target_service.value}")
        
        # Apply variables to template
        prompt = template.template_structure
        for var, value in variables.items():
            prompt = prompt.replace(f"{{{var}}}", value)
        
        # Add service-specific optimizations
        optimized = self._apply_service_specific_template_mods(prompt, target_service)
        
        return optimized
    
    def optimize_for_parallel_execution(
        self,
        base_prompt: str,
        services: List[ServiceType],
        expected_output: str,
        output_format: OutputFormat = OutputFormat.JSON
    ) -> Dict[ServiceType, str]:
        """Optimize prompt for parallel execution across multiple services"""
        
        optimized_prompts = {}
        
        # Generate base optimization
        base_optimization = self._create_base_parallel_structure(
            base_prompt, expected_output, output_format
        )
        
        # Service-specific adaptations
        for service in services:
            service_prompt = self._adapt_for_service_parallel(
                base_optimization, service, output_format
            )
            
            # Add cross-service consistency instructions
            service_prompt = self._add_consistency_instructions(
                service_prompt, services, service
            )
            
            optimized_prompts[service] = service_prompt
        
        print(f"⚡ Optimized for parallel execution across {len(services)} services")
        return optimized_prompts
    
    def generate_refinement_prompt(
        self,
        original_prompt: str,
        failed_output: str,
        expected_structure: Dict[str, Any],
        target_service: ServiceType,
        issues: List[str]
    ) -> str:
        """Generate optimized refinement prompt"""
        
        # Analyze failure patterns
        failure_analysis = self._analyze_failure_patterns(failed_output, expected_structure)
        
        # Create targeted refinement
        refinement_template = self._get_refinement_template(target_service, failure_analysis)
        
        # Generate refinement prompt
        refinement_prompt = refinement_template.format(
            original_prompt=original_prompt,
            failed_output=failed_output[:500],  # Truncate for brevity
            issues="\n".join(f"- {issue}" for issue in issues),
            expected_structure=json.dumps(expected_structure, indent=2),
            service_instructions=self._get_service_refinement_instructions(target_service)
        )
        
        return refinement_prompt
    
    def analyze_optimization_effectiveness(self) -> Dict[str, Any]:
        """Analyze the effectiveness of optimizations"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Token savings analysis
        cursor.execute('''
            SELECT AVG(token_reduction), SUM(token_reduction), COUNT(*)
            FROM prompt_optimizations WHERE session_id = ?
        ''', (self.session_id,))
        token_stats = cursor.fetchone()
        
        # Strategy effectiveness
        cursor.execute('''
            SELECT strategy, AVG(clarity_score), AVG(structure_compliance), COUNT(*)
            FROM prompt_optimizations WHERE session_id = ?
            GROUP BY strategy
        ''', (self.session_id,))
        strategy_stats = cursor.fetchall()
        
        # Service performance
        cursor.execute('''
            SELECT target_service, AVG(clarity_score), AVG(structure_compliance), COUNT(*)
            FROM prompt_optimizations WHERE session_id = ?
            GROUP BY target_service
        ''', (self.session_id,))
        service_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "token_savings": {
                "average_reduction": token_stats[0] or 0,
                "total_saved": token_stats[1] or 0,
                "optimizations_count": token_stats[2] or 0
            },
            "strategy_performance": [
                {
                    "strategy": row[0],
                    "avg_clarity": row[1],
                    "avg_structure": row[2],
                    "usage_count": row[3]
                }
                for row in strategy_stats
            ],
            "service_performance": [
                {
                    "service": row[0],
                    "avg_clarity": row[1],
                    "avg_structure": row[2],
                    "usage_count": row[3]
                }
                for row in service_stats
            ]
        }
    
    # Private optimization methods
    def _classify_prompt_category(self, prompt: str) -> PromptCategory:
        """Classify prompt into category"""
        
        prompt_lower = prompt.lower()
        
        # Category indicators
        if any(word in prompt_lower for word in ['extract', 'find', 'identify', 'locate']):
            return PromptCategory.INFORMATION_EXTRACTION
        elif any(word in prompt_lower for word in ['analyze', 'examine', 'evaluate', 'assess']):
            return PromptCategory.DATA_ANALYSIS
        elif any(word in prompt_lower for word in ['create', 'generate', 'write', 'compose']):
            return PromptCategory.CREATIVE_GENERATION
        elif any(word in prompt_lower for word in ['solve', 'fix', 'resolve', 'troubleshoot']):
            return PromptCategory.PROBLEM_SOLVING
        elif any(word in prompt_lower for word in ['research', 'investigate', 'explore', 'discover']):
            return PromptCategory.RESEARCH
        elif any(word in prompt_lower for word in ['compare', 'contrast', 'versus', 'difference']):
            return PromptCategory.COMPARISON
        
        return PromptCategory.INFORMATION_EXTRACTION  # Default
    
    def _apply_service_optimization(
        self,
        prompt: str,
        service: ServiceType,
        strategy: OptimizationStrategy,
        output_format: OutputFormat
    ) -> str:
        """Apply service-specific optimizations"""
        
        # Get service patterns
        patterns = self.service_patterns.get(service, {})
        
        optimized = prompt
        
        # Apply strategy-specific optimizations
        if strategy == OptimizationStrategy.TOKEN_MINIMIZATION:
            optimized = self._minimize_tokens(optimized, service)
        elif strategy == OptimizationStrategy.CLARITY_MAXIMIZATION:
            optimized = self._maximize_clarity(optimized, service)
        elif strategy == OptimizationStrategy.STRUCTURE_ENFORCEMENT:
            optimized = self._enforce_structure(optimized, output_format, service)
        elif strategy == OptimizationStrategy.PRECISION_TARGETING:
            optimized = self._target_precision(optimized, service)
        
        # Apply service-specific patterns
        for pattern, replacement in patterns.get('optimizations', {}).items():
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
        
        return optimized
    
    def _add_machine_language_structure(
        self,
        prompt: str,
        expected_output: str,
        output_format: OutputFormat,
        service: ServiceType
    ) -> str:
        """Add machine-readable structure to prompt"""
        
        # Format-specific structure
        format_instructions = {
            OutputFormat.JSON: f"""
CRITICAL: Your response must be valid JSON with this exact structure:
{expected_output}

Do not include any text before or after the JSON. Start with {{ and end with }}.
""",
            OutputFormat.STRUCTURED_TEXT: f"""
CRITICAL: Format your response exactly as follows:
{expected_output}

Use the exact field names and structure shown above.
""",
            OutputFormat.MARKDOWN: f"""
CRITICAL: Use markdown format with this structure:
{expected_output}

Follow markdown syntax precisely.
""",
            OutputFormat.XML: f"""
CRITICAL: Provide XML output with this structure:
{expected_output}

Ensure proper XML syntax with opening and closing tags.
"""
        }
        
        instruction = format_instructions.get(output_format, "")
        
        # Service-specific additions
        service_additions = {
            ServiceType.CLAUDE: "\n\nBe precise and follow the format exactly. Do not add explanations or extra text.",
            ServiceType.GEMINI: "\n\nPlease ensure the output is machine-readable and parseable.",
            ServiceType.PERPLEXITY: "\n\nProvide structured, factual information in the specified format."
        }
        
        return f"{prompt}\n\n{instruction}{service_additions.get(service, '')}"
    
    def _add_validation_instructions(
        self,
        prompt: str,
        expected_output: str,
        service: ServiceType
    ) -> str:
        """Add validation instructions to ensure correct output"""
        
        validation_instruction = f"""

VALIDATION CHECKLIST before responding:
1. ✓ Response matches the exact format specified
2. ✓ All required fields are included
3. ✓ Data types are correct (strings, numbers, arrays, etc.)
4. ✓ No extra text or explanations outside the specified format
5. ✓ Output is machine-parseable

If any validation fails, correct it before responding.
"""
        
        return prompt + validation_instruction
    
    def _minimize_tokens(self, prompt: str, service: ServiceType) -> str:
        """Minimize token usage while preserving meaning"""
        
        # Common token reduction patterns
        reductions = [
            (r'\bplease\b', ''),
            (r'\bkindly\b', ''),
            (r'\bwould you\b', ''),
            (r'\bi would like you to\b', ''),
            (r'\bcan you\b', ''),
            (r'\s+', ' '),  # Multiple spaces to single space
        ]
        
        optimized = prompt
        for pattern, replacement in reductions:
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
        
        return optimized.strip()
    
    def _maximize_clarity(self, prompt: str, service: ServiceType) -> str:
        """Maximize clarity for better comprehension"""
        
        # Add clarity improvements
        if not prompt.endswith('.'):
            prompt += '.'
        
        # Ensure imperative voice
        if prompt.lower().startswith(('can you', 'could you', 'would you')):
            # Convert to imperative
            prompt = re.sub(r'^(can|could|would) you\s+', '', prompt, flags=re.IGNORECASE)
            prompt = prompt[0].upper() + prompt[1:] if prompt else prompt
        
        return prompt
    
    def _enforce_structure(self, prompt: str, output_format: OutputFormat, service: ServiceType) -> str:
        """Enforce structural requirements"""
        
        structure_enforcements = {
            OutputFormat.JSON: "Return only valid JSON format.",
            OutputFormat.STRUCTURED_TEXT: "Use structured text with clear field labels.",
            OutputFormat.MARKDOWN: "Use proper markdown formatting.",
            OutputFormat.XML: "Return valid XML with proper tags."
        }
        
        enforcement = structure_enforcements.get(output_format, "")
        if enforcement and enforcement not in prompt:
            prompt = f"{prompt} {enforcement}"
        
        return prompt
    
    def _target_precision(self, prompt: str, service: ServiceType) -> str:
        """Target precision for the specific service"""
        
        precision_additions = {
            ServiceType.CLAUDE: "Be precise and analytical.",
            ServiceType.GEMINI: "Provide accurate, factual information.",
            ServiceType.PERPLEXITY: "Focus on relevant, current information."
        }
        
        addition = precision_additions.get(service, "")
        if addition and addition not in prompt:
            prompt = f"{prompt} {addition}"
        
        return prompt
    
    def _calculate_token_reduction(self, original: str, optimized: str) -> int:
        """Calculate approximate token reduction"""
        
        # Simple token estimation (words + punctuation)
        original_tokens = len(original.split()) + len(re.findall(r'[^\w\s]', original))
        optimized_tokens = len(optimized.split()) + len(re.findall(r'[^\w\s]', optimized))
        
        return max(0, original_tokens - optimized_tokens)
    
    def _assess_clarity(self, prompt: str) -> float:
        """Assess prompt clarity"""
        
        score = 0.5  # Base score
        
        # Clear structure indicators
        if any(marker in prompt for marker in [':', '-', '1.', '2.', '•']):
            score += 0.2
        
        # Imperative voice
        if not prompt.lower().startswith(('can you', 'could you', 'would you')):
            score += 0.1
        
        # Specific instructions
        if any(word in prompt.lower() for word in ['exact', 'specific', 'precise', 'must']):
            score += 0.1
        
        # Length optimization
        word_count = len(prompt.split())
        if 20 <= word_count <= 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_structure_compliance(self, prompt: str, output_format: OutputFormat) -> float:
        """Assess structure compliance"""
        
        score = 0.5  # Base score
        
        format_indicators = {
            OutputFormat.JSON: ['json', '{', '}', 'format'],
            OutputFormat.STRUCTURED_TEXT: ['structure', 'format', 'field'],
            OutputFormat.MARKDOWN: ['markdown', '#', '##', '**'],
            OutputFormat.XML: ['xml', '<', '>', 'tag']
        }
        
        indicators = format_indicators.get(output_format, [])
        found = sum(1 for indicator in indicators if indicator in prompt.lower())
        
        if found > 0:
            score += min(found * 0.1, 0.4)
        
        # Validation instructions
        if 'validation' in prompt.lower() or 'checklist' in prompt.lower():
            score += 0.1
        
        return min(score, 1.0)
    
    def _load_service_patterns(self) -> Dict[ServiceType, Dict]:
        """Load service-specific optimization patterns"""
        return {
            ServiceType.CLAUDE: {
                'optimizations': {
                    r'\bI need you to\b': '',
                    r'\bCould you please\b': '',
                }
            },
            ServiceType.GEMINI: {
                'optimizations': {
                    r'\bHelp me\b': '',
                    r'\bI want you to\b': '',
                }
            },
            ServiceType.PERPLEXITY: {
                'optimizations': {
                    r'\bSearch for\b': 'Find',
                    r'\bLook up\b': 'Find',
                }
            }
        }
    
    def _load_optimization_templates(self) -> Dict[str, str]:
        """Load optimization templates"""
        return {
            "information_extraction": "{task}. Return JSON: {structure}",
            "data_analysis": "Analyze: {data}. Output: {format}",
            "creative_generation": "Generate: {content}. Format: {structure}",
            "research": "Research: {topic}. Structure: {format}"
        }
    
    def _load_validation_schemas(self) -> Dict[OutputFormat, Dict]:
        """Load validation schemas for different formats"""
        return {
            OutputFormat.JSON: {
                "validation": "Must be valid JSON",
                "schema": {"type": "object", "required": []}
            },
            OutputFormat.STRUCTURED_TEXT: {
                "validation": "Must have labeled fields",
                "schema": {"fields": []}
            }
        }
    
    def _load_predefined_templates(self):
        """Load predefined templates into database"""
        
        templates = [
            {
                "name": "JSON Information Extraction",
                "category": PromptCategory.INFORMATION_EXTRACTION,
                "services": [ServiceType.CLAUDE, ServiceType.GEMINI],
                "structure": "Extract information from: {source}\n\nReturn JSON: {schema}",
                "schema": {"extracted_data": {}, "confidence": 0.0},
                "rules": ["Must be valid JSON", "Include confidence score"]
            },
            {
                "name": "Structured Research Query",
                "category": PromptCategory.RESEARCH,
                "services": [ServiceType.PERPLEXITY],
                "structure": "Research: {query}\n\nProvide structured results: {format}",
                "schema": {"results": [], "sources": [], "summary": ""},
                "rules": ["Include sources", "Provide summary"]
            }
        ]
        
        for template_data in templates:
            # Check if template already exists
            existing = self._get_template_by_name(template_data["name"])
            if not existing:
                template = MachineLanguageTemplate(
                    template_id=str(uuid.uuid4()),
                    name=template_data["name"],
                    category=template_data["category"],
                    service_compatibility=template_data["services"],
                    template_structure=template_data["structure"],
                    output_schema=template_data["schema"],
                    validation_rules=template_data["rules"],
                    example_usage={}
                )
                self._store_template(template)
    
    # Database methods
    def _store_optimization(self, optimization: PromptOptimization):
        """Store optimization in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prompt_optimizations 
            (optimization_id, session_id, original_prompt, optimized_prompt, target_service, 
             output_format, category, strategy, token_reduction, clarity_score, structure_compliance, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            optimization.optimization_id,
            self.session_id,
            optimization.original_prompt,
            optimization.optimized_prompt,
            optimization.target_service.value,
            optimization.output_format.value,
            optimization.category.value,
            optimization.strategy.value,
            optimization.token_reduction,
            optimization.clarity_score,
            optimization.structure_compliance,
            optimization.created_at
        ))
        conn.commit()
        conn.close()
    
    def _store_template(self, template: MachineLanguageTemplate):
        """Store template in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ml_templates 
            (template_id, name, category, service_compatibility, template_structure, 
             output_schema, validation_rules, example_usage, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template.template_id,
            template.name,
            template.category.value,
            json.dumps([s.value for s in template.service_compatibility]),
            template.template_structure,
            json.dumps(template.output_schema),
            json.dumps(template.validation_rules),
            json.dumps(template.example_usage),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _get_template(self, template_id: str) -> Optional[MachineLanguageTemplate]:
        """Get template by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT template_id, name, category, service_compatibility, template_structure, 
                   output_schema, validation_rules, example_usage
            FROM ml_templates WHERE template_id = ?
        ''', (template_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MachineLanguageTemplate(
                template_id=row[0],
                name=row[1],
                category=PromptCategory(row[2]),
                service_compatibility=[ServiceType(s) for s in json.loads(row[3])],
                template_structure=row[4],
                output_schema=json.loads(row[5]),
                validation_rules=json.loads(row[6]),
                example_usage=json.loads(row[7])
            )
        return None
    
    def _get_template_by_name(self, name: str) -> Optional[MachineLanguageTemplate]:
        """Get template by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT template_id FROM ml_templates WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._get_template(row[0])
        return None
    
    # Additional helper methods (simplified for space)
    def _create_base_parallel_structure(self, prompt: str, expected_output: str, output_format: OutputFormat) -> str:
        """Create base structure for parallel execution"""
        return f"{prompt}\n\nIMPORTANT: Provide {output_format.value} output matching: {expected_output}"
    
    def _adapt_for_service_parallel(self, base: str, service: ServiceType, output_format: OutputFormat) -> str:
        """Adapt prompt for service in parallel context"""
        service_note = f"\n\n[{service.value.upper()} SPECIFIC]: Ensure output is consistent with other services."
        return base + service_note
    
    def _add_consistency_instructions(self, prompt: str, all_services: List[ServiceType], current_service: ServiceType) -> str:
        """Add consistency instructions for parallel execution"""
        other_services = [s.value for s in all_services if s != current_service]
        if other_services:
            consistency_note = f"\n\nCONSISTENCY: Ensure results are comparable with {', '.join(other_services)}."
            return prompt + consistency_note
        return prompt
    
    def _analyze_failure_patterns(self, failed_output: str, expected_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in failed outputs"""
        return {
            "missing_structure": len(expected_structure) > 0 and not any(key in failed_output for key in expected_structure.keys()),
            "format_issues": "json" in str(expected_structure).lower() and not failed_output.strip().startswith('{'),
            "incomplete_response": len(failed_output) < 50
        }
    
    def _get_refinement_template(self, service: ServiceType, failure_analysis: Dict[str, Any]) -> str:
        """Get refinement template based on service and failure analysis"""
        base_template = """
Previous response had issues: {issues}

Original request: {original_prompt}
Failed output: {failed_output}
Expected structure: {expected_structure}

{service_instructions}

Provide corrected response:
"""
        return base_template
    
    def _get_service_refinement_instructions(self, service: ServiceType) -> str:
        """Get service-specific refinement instructions"""
        instructions = {
            ServiceType.CLAUDE: "Focus on precise formatting and complete structure.",
            ServiceType.GEMINI: "Ensure all fields are included with correct data types.",
            ServiceType.PERPLEXITY: "Provide factual, structured information as specified."
        }
        return instructions.get(service, "Follow the format exactly as specified.")
    
    def _apply_service_specific_template_mods(self, prompt: str, service: ServiceType) -> str:
        """Apply service-specific template modifications"""
        mods = {
            ServiceType.CLAUDE: lambda p: p + "\n\nBe analytical and precise.",
            ServiceType.GEMINI: lambda p: p + "\n\nProvide comprehensive information.",
            ServiceType.PERPLEXITY: lambda p: p + "\n\nInclude relevant sources."
        }
        return mods.get(service, lambda p: p)(prompt)
    
    def _generate_example_usage(self, structure: str, services: List[ServiceType]) -> Dict[str, str]:
        """Generate example usage for template"""
        return {
            "basic_usage": f"Example: {structure}",
            "supported_services": ", ".join(s.value for s in services)
        }


def main():
    """Test the machine language optimizer"""
    print("🔧 Testing Machine Language Optimizer")
    print("=" * 50)
    
    # Initialize optimizer
    optimizer = MachineLanguageOptimizer(session_id="test_ml_optimizer")
    
    # Test optimization
    print("\n🔧 Testing prompt optimization...")
    test_prompt = "Can you please help me extract information about AI companies from this text and provide it in a structured format"
    expected_output = '{"companies": [{"name": "", "description": "", "founded": ""}], "count": 0}'
    
    optimization = optimizer.optimize_for_service(
        test_prompt,
        ServiceType.CLAUDE,
        expected_output,
        OutputFormat.JSON,
        OptimizationStrategy.STRUCTURE_ENFORCEMENT
    )
    
    print(f"✅ Optimization completed!")
    print(f"   Token reduction: {optimization.token_reduction}")
    print(f"   Clarity score: {optimization.clarity_score:.2f}")
    print(f"   Structure compliance: {optimization.structure_compliance:.2f}")
    print(f"   Optimized: {optimization.optimized_prompt[:100]}...")
    
    # Test parallel optimization
    print("\n⚡ Testing parallel optimization...")
    parallel_prompts = optimizer.optimize_for_parallel_execution(
        "Research current AI trends and provide analysis",
        [ServiceType.CLAUDE, ServiceType.GEMINI, ServiceType.PERPLEXITY],
        '{"trends": [], "analysis": "", "sources": []}',
        OutputFormat.JSON
    )
    
    print(f"✅ Parallel optimization completed for {len(parallel_prompts)} services")
    
    # Test effectiveness analysis
    print("\n📊 Testing effectiveness analysis...")
    effectiveness = optimizer.analyze_optimization_effectiveness()
    print(f"✅ Analysis completed:")
    print(f"   Total token savings: {effectiveness['token_savings']['total_saved']}")
    print(f"   Optimizations count: {effectiveness['token_savings']['optimizations_count']}")
    
    print(f"\n✅ MachineLanguageOptimizer system test completed!")


if __name__ == "__main__":
    main()