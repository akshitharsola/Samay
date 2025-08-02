#!/usr/bin/env python3
"""
Samay v3 - Companion Interface System
====================================
Enhanced chat interface with companion AI integration
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from .conversation_memory import ConversationMemory
from .personality_profile import PersonalityProfile
from .task_scheduler import TaskScheduler
from .local_llm import LocalLLMClient
from .brainstorm_engine import BrainstormEngine
from .version_control import VersionControl
from .quality_assessment import QualityAssessor
from .web_agent_dispatcher import WebAgentDispatcher, ServiceType, OutputFormat
from .machine_language_optimizer import MachineLanguageOptimizer
from .parallel_session_manager import ParallelSessionManager, ExecutionMode
from .enhanced_task_scheduler import EnhancedTaskScheduler, TaskPriority, TaskStatus
from .proactive_assistant import ProactiveAssistant, UserContext, SuggestionType
from .workflow_automation import WorkflowAutomation, WorkflowStatus
from .personal_knowledge_base import PersonalKnowledgeBase, KnowledgeType


@dataclass
class CompanionResponse:
    """Enhanced response with companion context"""
    content: str
    response_type: str  # companion, task_suggestion, reminder, clarification
    personality_context: Dict[str, Any]
    memory_references: List[str]
    suggested_actions: List[str]
    proactive_suggestions: List[str]
    emotional_tone: str
    confidence_score: float


class CompanionInterface:
    """Enhanced chat interface with companion AI capabilities"""
    
    def __init__(self, user_id: str = "default", memory_dir: str = "memory"):
        self.user_id = user_id
        self.memory_dir = memory_dir
        
        # Initialize companion components
        self.memory = ConversationMemory(memory_dir, user_id)
        self.personality = PersonalityProfile(memory_dir, user_id)
        self.scheduler = TaskScheduler(memory_dir, user_id)
        self.llm_client = LocalLLMClient()
        
        # Initialize Phase 2 components
        self.brainstorm_engine = BrainstormEngine(memory_dir, user_id + "_brainstorm")
        self.version_control = VersionControl(memory_dir, user_id + "_vc")
        self.quality_assessor = QualityAssessor(memory_dir, user_id + "_quality")
        
        # Initialize Phase 3 components
        self.web_dispatcher = WebAgentDispatcher(memory_dir, user_id + "_web")
        self.ml_optimizer = MachineLanguageOptimizer(memory_dir, user_id + "_ml_opt")
        self.parallel_manager = ParallelSessionManager(memory_dir, user_id + "_parallel")
        
        # Initialize Phase 4 components
        self.enhanced_scheduler = EnhancedTaskScheduler(f"{memory_dir}/enhanced_tasks.db")
        self.proactive_assistant = ProactiveAssistant(f"{memory_dir}/proactive_assistant.db")
        self.workflow_automation = WorkflowAutomation(f"{memory_dir}/workflow_automation.db")
        self.knowledge_base = PersonalKnowledgeBase(f"{memory_dir}/knowledge_base.db")
        
        # Session state
        self.current_session_id = f"session_{int(datetime.now().timestamp())}"
        self.context_window = []
        self.conversation_mode = "companion"  # companion, assistant, task_focused, brainstorming
        
        print(f"🤖 CompanionInterface initialized for {user_id}")
        print(f"🧠 Phase 1: Memory, Personality, Scheduler, LLM")
        print(f"⚡ Phase 2: Brainstorming, Version Control, Quality Assessment")
        print(f"🌐 Phase 3: Web Dispatcher, ML Optimizer, Parallel Manager")
        print(f"🚀 Phase 4: Enhanced Scheduler, Proactive Assistant, Workflow Automation, Knowledge Base")
        print(f"🎭 Mode: {self.conversation_mode}")
    
    def process_companion_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> CompanionResponse:
        """Process user input with full companion capabilities"""
        
        # Analyze input intent and context
        input_analysis = self._analyze_user_input(user_input, context)
        
        # Get relevant memory context
        memory_context = self.memory.get_relevant_context(user_input)
        
        # Generate adaptive system prompt
        system_prompt = self._generate_enhanced_system_prompt(input_analysis, memory_context)
        
        # Create enhanced prompt with companion context
        enhanced_prompt = self._build_companion_prompt(user_input, input_analysis, memory_context)
        
        # Generate response using local LLM
        llm_response = self.llm_client.generate_response(enhanced_prompt, system_prompt)
        
        if not llm_response.success:
            return self._create_fallback_response(user_input, llm_response.error_message)
        
        # Process and enhance the response
        companion_response = self._enhance_response(llm_response.response, input_analysis, memory_context)
        
        # Store conversation in memory
        conversation_id = self.memory.store_conversation(user_input, companion_response.content)
        
        # Adapt personality based on interaction
        self.personality.adapt_to_interaction(user_input, context=input_analysis)
        
        # Check for task-related actions
        self._process_task_actions(user_input, companion_response)
        
        return companion_response
    
    def get_proactive_suggestions(self) -> List[str]:
        """Generate proactive suggestions based on current context"""
        suggestions = []
        
        # Check for due reminders
        due_reminders = self.scheduler.get_due_reminders()
        if due_reminders:
            suggestions.append(f"You have {len(due_reminders)} reminders due")
        
        # Check for overdue tasks
        stats = self.scheduler.get_task_statistics()
        if stats['overdue_tasks'] > 0:
            suggestions.append(f"You have {stats['overdue_tasks']} overdue tasks")
        
        # Memory-based suggestions
        memory_stats = self.memory.get_memory_stats()
        if memory_stats['recent_activity'] == 0:
            suggestions.append("Welcome back! What would you like to work on today?")
        
        # Personality-driven suggestions
        if self.personality.personality_traits.curiosity > 0.7:
            suggestions.append("I noticed an interesting pattern in your recent work. Would you like to explore it?")
        
        return suggestions
    
    def switch_conversation_mode(self, mode: str) -> str:
        """Switch between conversation modes"""
        valid_modes = ["companion", "assistant", "task_focused", "brainstorming"]
        
        if mode not in valid_modes:
            return f"Invalid mode. Choose from: {', '.join(valid_modes)}"
        
        old_mode = self.conversation_mode
        self.conversation_mode = mode
        
        mode_descriptions = {
            "companion": "Personal AI companion with memory and personality",
            "assistant": "Focused task assistance and information",
            "task_focused": "Task management and productivity features",
            "brainstorming": "Creative ideation and iterative refinement"
        }
        
        return f"Switched from {old_mode} to {mode} mode: {mode_descriptions[mode]}"
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get comprehensive conversation summary"""
        
        # Memory statistics
        memory_stats = self.memory.get_memory_stats()
        
        # Personality profile
        personality_summary = self.personality.get_personality_summary()
        
        # Task statistics
        task_stats = self.scheduler.get_task_statistics()
        
        # Recent context
        recent_conversations = self.memory.get_conversation_history(limit=5)
        
        return {
            "session_id": self.current_session_id,
            "user_id": self.user_id,
            "conversation_mode": self.conversation_mode,
            "memory_stats": memory_stats,
            "personality": {
                "communication_style": personality_summary['communication_style']['tone_preference'],
                "adaptation_count": personality_summary['adaptation_count']
            },
            "tasks": {
                "total": task_stats['total_tasks'],
                "completed_today": task_stats['completed_today'],
                "overdue": task_stats['overdue_tasks']
            },
            "recent_topics": memory_stats.get('top_topics', [])[:5],
            "last_interaction": memory_stats.get('last_interaction'),
            "companion_readiness": self._assess_companion_readiness()
        }
    
    def handle_follow_up_questions(self, original_response: str, follow_up: str) -> CompanionResponse:
        """Handle follow-up questions with conversation continuity"""
        
        # Add conversation continuity context
        continuity_context = {
            "previous_response": original_response,
            "conversation_flow": "follow_up",
            "maintain_context": True
        }
        
        # Process with enhanced context
        return self.process_companion_input(follow_up, continuity_context)
    
    def get_daily_briefing(self) -> str:
        """Generate personalized daily briefing"""
        
        # Get today's schedule
        daily_schedule = self.scheduler.get_daily_schedule()
        
        # Get proactive suggestions
        suggestions = self.get_proactive_suggestions()
        
        # Get personality-appropriate greeting
        greeting_template = self.personality.get_response_template("greeting")
        
        # Build briefing
        briefing_parts = [
            greeting_template["opening"],
            f"Today's overview: {daily_schedule['summary']}",
        ]
        
        if suggestions:
            briefing_parts.append(f"I noticed: {suggestions[0]}")
        
        briefing_parts.append(greeting_template["follow_up"])
        
        return " ".join(briefing_parts)
    
    def start_brainstorming_session(
        self, 
        initial_prompt: str, 
        refinement_goal: str = "general_improvement"
    ) -> str:
        """Start an iterative brainstorming session"""
        
        # Switch to brainstorming mode
        self.switch_conversation_mode("brainstorming")
        
        # Start brainstorming engine session
        session_id = self.brainstorm_engine.start_brainstorming_session(
            initial_prompt, 
            refinement_goal
        )
        
        # Store in memory
        self.memory.store_conversation(
            f"Started brainstorming session: {initial_prompt}",
            f"Brainstorming session {session_id} initiated with goal: {refinement_goal}",
            {"session_id": session_id, "session_type": "brainstorming"}
        )
        
        print(f"🧠 Started brainstorming session: {session_id}")
        return session_id
    
    def refine_current_prompt(self, feedback: str, refinement_type: str = "improvement") -> Dict[str, Any]:
        """Refine the current prompt in brainstorming session"""
        
        if not self.brainstorm_engine.current_prompt_id:
            return {"error": "No active brainstorming session"}
        
        # Refine using brainstorming engine
        refined_version = self.brainstorm_engine.refine_prompt(feedback, refinement_type)
        
        # Track version change
        if refined_version.parent_version:
            self.version_control.track_version_change(
                refined_version.parent_version,
                refined_version.version_id,
                self.version_control.ChangeType.MODIFY,
                f"Refined based on feedback: {feedback[:50]}..."
            )
        
        # Assess quality
        quality_assessment = self.quality_assessor.assess_prompt_quality(
            refined_version.content,
            refined_version.version_id
        )
        
        # Store in memory
        self.memory.store_conversation(
            f"Refine prompt: {feedback}",
            f"Refined to version {refined_version.version_id[:8]} with quality {quality_assessment.metrics.overall_score:.2f}",
            {
                "version_id": refined_version.version_id,
                "quality_score": quality_assessment.metrics.overall_score,
                "refinement_type": refinement_type
            }
        )
        
        return {
            "refined_version": refined_version,
            "quality_assessment": quality_assessment,
            "version_id": refined_version.version_id
        }
    
    def create_prompt_branch(
        self, 
        branch_focus: str, 
        alternative_prompt: Optional[str] = None
    ) -> str:
        """Create alternative branch for exploring different approaches"""
        
        from brainstorm_engine import BranchType
        
        branch_id = self.brainstorm_engine.create_conversation_branch(
            BranchType.ALTERNATIVE,
            branch_focus,
            alternative_prompt
        )
        
        # Create branch snapshot in version control
        self.version_control.create_branch_snapshot(
            branch_id,
            f"Branch: {branch_focus}",
            f"Exploring alternative approach: {branch_focus}"
        )
        
        print(f"🌟 Created branch for: {branch_focus}")
        return branch_id
    
    def compare_prompt_versions(self, version_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple prompt versions comprehensively"""
        
        # Get prompt content for each version
        prompts = []
        for version_id in version_ids:
            version_info = self._get_version_content(version_id)
            prompts.append(version_info.get("content", "") if version_info else "")
        
        # Quality comparison
        quality_comparison = self.quality_assessor.compare_prompt_versions(version_ids, prompts)
        
        # Version control comparison if applicable
        if len(version_ids) == 2:
            vc_comparison = self.version_control.compare_branches(
                self._get_version_branch(version_ids[0]),
                self._get_version_branch(version_ids[1])
            )
            quality_comparison["version_control"] = vc_comparison
        
        return quality_comparison
    
    def get_brainstorming_suggestions(self, current_prompt: str) -> List[str]:
        """Get AI-powered suggestions for prompt improvement"""
        
        # Get refinement suggestions from brainstorming engine
        brainstorm_suggestions = self.brainstorm_engine.get_refinement_suggestions(current_prompt)
        
        # Get quality-based suggestions
        if self.brainstorm_engine.current_prompt_id:
            assessment = self.quality_assessor.assess_prompt_quality(
                current_prompt,
                self.brainstorm_engine.current_prompt_id
            )
            quality_suggestions = assessment.improvement_suggestions
        else:
            quality_suggestions = []
        
        # Combine and deduplicate
        all_suggestions = brainstorm_suggestions + quality_suggestions
        unique_suggestions = list(dict.fromkeys(all_suggestions))  # Preserve order, remove duplicates
        
        return unique_suggestions[:7]  # Limit to top 7 suggestions
    
    def finalize_brainstorming_session(self) -> Dict[str, Any]:
        """Finalize current brainstorming session"""
        
        if not self.brainstorm_engine.current_prompt_id:
            return {"error": "No active brainstorming session"}
        
        # Finalize session
        summary = self.brainstorm_engine.finalize_session()
        
        # Generate quality report for final prompt
        if summary.get("final_prompt"):
            quality_report = self.quality_assessor.generate_quality_report(
                self.brainstorm_engine.current_prompt_id
            )
            summary["quality_report"] = quality_report
        
        # Store completion in memory
        self.memory.store_conversation(
            "Finalize brainstorming session",
            f"Session completed with {summary['total_iterations']} iterations. Final quality: {summary['final_quality_score']:.2f}",
            summary
        )
        
        # Switch back to companion mode
        self.switch_conversation_mode("companion")
        
        return summary
    
    def get_quality_evolution(self) -> Dict[str, Any]:
        """Get quality evolution for current brainstorming session"""
        
        if not self.brainstorm_engine.current_branch_id:
            return {"error": "No active brainstorming session"}
        
        # Get version lineage
        branch_info = self.brainstorm_engine._get_conversation_branch(
            self.brainstorm_engine.current_branch_id
        )
        
        if not branch_info:
            return {"error": "Branch information not found"}
        
        version_lineage = branch_info.prompt_versions
        
        # Track quality evolution
        evolution = self.quality_assessor.track_quality_evolution(version_lineage)
        
        return evolution
    
    def register_web_service(self, service: ServiceType, session_data: Dict[str, Any]):
        """Register a web service session for companion use"""
        
        # Register with web dispatcher
        self.web_dispatcher.register_service_session(service, session_data)
        
        # Register with parallel manager
        self.parallel_manager.register_service_session(service, session_data, max_concurrent=2)
        
        # Store in memory
        self.memory.store_conversation(
            f"Register {service.value} service",
            f"Web service {service.value} registered and ready for companion use",
            {"service": service.value, "status": "registered"}
        )
        
        print(f"🌐 {service.value.title()} web service registered for companion use")
    
    def execute_web_assisted_request(
        self,
        prompt: str,
        services: List[ServiceType],
        expected_output: str,
        output_format: OutputFormat = OutputFormat.JSON,
        execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    ) -> Dict[str, Any]:
        """Execute request with web service assistance"""
        
        import asyncio
        
        # Optimize prompt for web services
        optimized_prompts = {}
        for service in services:
            optimization = self.ml_optimizer.optimize_for_service(
                prompt, service, expected_output, output_format
            )
            optimized_prompts[service] = optimization.optimized_prompt
        
        # Execute through parallel manager
        async def execute():
            return await self.parallel_manager.execute_parallel_request(
                prompt, services, expected_output, output_format, execution_mode
            )
        
        execution_result = asyncio.run(execute())
        
        # Store in memory
        self.memory.store_conversation(
            f"Web-assisted request: {prompt[:50]}...",
            f"Executed across {len(services)} services with {execution_result.success_rate:.1%} success rate",
            {
                "services": [s.value for s in services],
                "execution_mode": execution_mode.value,
                "success_rate": execution_result.success_rate,
                "execution_time": execution_result.execution_time
            }
        )
        
        # Return structured results
        return {
            "execution_id": execution_result.execution_id,
            "success_rate": execution_result.success_rate,
            "execution_time": execution_result.execution_time,
            "results": {
                service.value: {
                    "quality_score": result.quality_score,
                    "refinement_count": result.refinement_count,
                    "content": result.raw_output,
                    "success": result.status.value == "completed"
                }
                for service, result in execution_result.results.items()
            },
            "best_result": self._select_best_web_result(execution_result.results)
        }
    
    def optimize_prompt_for_web_services(
        self,
        prompt: str,
        target_services: List[ServiceType],
        expected_output: str,
        output_format: OutputFormat = OutputFormat.JSON
    ) -> Dict[str, str]:
        """Optimize prompt for multiple web services"""
        
        optimized = {}
        
        for service in target_services:
            optimization = self.ml_optimizer.optimize_for_service(
                prompt, service, expected_output, output_format
            )
            optimized[service.value] = optimization.optimized_prompt
        
        # Store optimization in memory
        self.memory.store_conversation(
            f"Optimize prompt for web services: {prompt[:50]}...",
            f"Generated optimized prompts for {len(target_services)} services",
            {
                "original_prompt": prompt,
                "services": [s.value for s in target_services],
                "optimization_count": len(optimized)
            }
        )
        
        return optimized
    
    def get_web_service_analytics(self) -> Dict[str, Any]:
        """Get analytics for web service usage"""
        
        # Get dispatcher stats
        dispatcher_stats = self.web_dispatcher.get_communication_stats()
        
        # Get parallel manager analytics
        parallel_analytics = self.parallel_manager.get_performance_analytics()
        
        # Get ML optimizer effectiveness
        ml_effectiveness = self.ml_optimizer.analyze_optimization_effectiveness()
        
        return {
            "communication": dispatcher_stats,
            "parallel_performance": parallel_analytics,
            "optimization": ml_effectiveness,
            "summary": {
                "total_requests": dispatcher_stats.get("total_requests", 0),
                "success_rate": dispatcher_stats.get("success_rate", 0),
                "active_services": dispatcher_stats.get("active_services", []),
                "average_refinements": dispatcher_stats.get("average_refinements", 0)
            }
        }
    
    def execute_intelligent_web_query(
        self,
        query: str,
        preferred_services: Optional[List[ServiceType]] = None,
        quality_threshold: float = 0.8,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """Execute intelligent web query with automatic service selection and refinement"""
        
        # Default to all available services if none specified
        if not preferred_services:
            preferred_services = [ServiceType.CLAUDE, ServiceType.GEMINI, ServiceType.PERPLEXITY]
        
        # Determine optimal output format based on query
        output_format = self._determine_optimal_output_format(query)
        
        # Generate expected output structure
        expected_output = self._generate_expected_output_structure(query, output_format)
        
        # Execute with web assistance
        result = self.execute_web_assisted_request(
            query,
            preferred_services,
            expected_output,
            output_format,
            ExecutionMode.LOAD_BALANCED
        )
        
        # If quality threshold not met, try refinement
        if result["success_rate"] < quality_threshold and max_attempts > 1:
            print(f"🔄 Quality below threshold ({result['success_rate']:.1%}), attempting refinement...")
            
            # Try with different execution mode
            refined_result = self.execute_web_assisted_request(
                query,
                preferred_services,
                expected_output,
                output_format,
                ExecutionMode.PRIORITY_BASED
            )
            
            # Use better result
            if refined_result["success_rate"] > result["success_rate"]:
                result = refined_result
        
        return result
    
    def switch_to_web_mode(self) -> str:
        """Switch companion to web-assisted mode"""
        
        old_mode = self.conversation_mode
        self.conversation_mode = "web_assisted"
        
        # Store mode change
        self.memory.store_conversation(
            f"Switch to web-assisted mode",
            f"Companion now using web services for enhanced capabilities",
            {"old_mode": old_mode, "new_mode": "web_assisted"}
        )
        
        return f"Switched from {old_mode} to web-assisted mode. Now using Claude, Gemini, and Perplexity for enhanced responses."
    
    def get_web_service_recommendations(self) -> List[str]:
        """Get recommendations for web service usage"""
        
        analytics = self.get_web_service_analytics()
        recommendations = []
        
        # Check service performance
        if analytics["communication"]["success_rate"] < 0.7:
            recommendations.append("Consider optimizing prompts for better web service success rates")
        
        if analytics["communication"]["average_refinements"] > 2:
            recommendations.append("High refinement count detected - review prompt clarity")
        
        # Check parallel performance
        parallel_perf = analytics["parallel_performance"]
        for service_data in parallel_perf.get("service_performance", {}).values():
            if service_data["success_rate"] < 0.6:
                recommendations.append(f"Service showing low success rate - check connectivity")
        
        # Check optimization effectiveness
        opt_data = analytics["optimization"]
        if opt_data["token_savings"]["average_reduction"] < 5:
            recommendations.append("Token optimization showing minimal savings - review optimization strategies")
        
        if not recommendations:
            recommendations.append("Web services performing well - no immediate optimizations needed")
        
        return recommendations
    
    # Phase 4 Advanced Companion Features
    
    def get_smart_schedule(self, date: str = None) -> Dict[str, Any]:
        """Get AI-optimized daily schedule"""
        
        if date:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date).date()
        else:
            from datetime import date
            date_obj = date.today()
        
        schedule = self.enhanced_scheduler.get_smart_schedule(date_obj)
        
        # Store schedule access in memory
        self.memory.store_conversation(
            f"Requested smart schedule for {date_obj}",
            f"Generated optimized schedule with {len(schedule.get('time_blocks', []))} time blocks",
            {"date": date_obj.isoformat(), "productivity_estimate": schedule.get("estimated_productivity")}
        )
        
        return schedule
    
    def create_smart_task(self, title: str, description: str = "", 
                         priority: str = "medium", due_date: str = None,
                         estimated_duration: int = None, category: str = "general",
                         tags: List[str] = None) -> Dict[str, Any]:
        """Create a smart task with enhanced features"""
        
        # Convert priority string to enum
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        priority_enum = priority_map.get(priority.lower(), TaskPriority.MEDIUM)
        
        # Parse due date if provided
        due_date_obj = None
        if due_date:
            from datetime import datetime
            try:
                due_date_obj = datetime.fromisoformat(due_date)
            except ValueError:
                pass
        
        # Create the task
        task_id = self.enhanced_scheduler.create_smart_task(
            title=title,
            description=description,
            priority=priority_enum,
            due_date=due_date_obj,
            estimated_duration=estimated_duration,
            category=category,
            tags=tags or []
        )
        
        # Store in memory
        self.memory.store_conversation(
            f"Created smart task: {title}",
            f"Task created with ID {task_id}, priority {priority}, category {category}",
            {
                "task_id": task_id,
                "title": title,
                "priority": priority,
                "category": category,
                "estimated_duration": estimated_duration
            }
        )
        
        return {
            "task_id": task_id,
            "title": title,
            "priority": priority,
            "category": category,
            "success": True
        }
    
    def get_proactive_suggestions_enhanced(self) -> List[Dict[str, Any]]:
        """Get enhanced proactive suggestions based on current context"""
        
        # Get current user context
        context = self._build_current_user_context()
        
        # Get suggestions from proactive assistant
        suggestions = self.proactive_assistant.generate_proactive_suggestions(context)
        
        # Convert to simplified format
        simple_suggestions = []
        for suggestion in suggestions:
            simple_suggestions.append({
                "id": suggestion.id,
                "type": suggestion.type.value,
                "title": suggestion.title,
                "message": suggestion.message,
                "priority": suggestion.priority.name,
                "action_required": suggestion.action_required,
                "relevance_score": suggestion.relevance_score
            })
        
        # Store in memory
        self.memory.store_conversation(
            "Generated proactive suggestions",
            f"Created {len(simple_suggestions)} personalized suggestions",
            {"suggestion_count": len(simple_suggestions), "context": context.__dict__}
        )
        
        return simple_suggestions
    
    def acknowledge_suggestion(self, suggestion_id: int, feedback: str = "helpful") -> bool:
        """Acknowledge a proactive suggestion with feedback"""
        
        success = self.proactive_assistant.acknowledge_suggestion(suggestion_id, feedback)
        
        if success:
            self.memory.store_conversation(
                f"Acknowledged suggestion {suggestion_id}",
                f"Provided feedback: {feedback}",
                {"suggestion_id": suggestion_id, "feedback": feedback}
            )
        
        return success
    
    def create_workflow(self, name: str, description: str, category: str = "personal") -> int:
        """Create a new automation workflow"""
        
        workflow_id = self.workflow_automation.create_workflow(name, description, category)
        
        # Store in memory
        self.memory.store_conversation(
            f"Created workflow: {name}",
            f"New automation workflow created with ID {workflow_id}",
            {"workflow_id": workflow_id, "name": name, "category": category}
        )
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: int, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an automation workflow"""
        
        import asyncio
        
        # Execute workflow asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.workflow_automation.execute_workflow(workflow_id, context or {})
            )
        finally:
            loop.close()
        
        # Store execution in memory
        self.memory.store_conversation(
            f"Executed workflow {workflow_id}",
            f"Workflow completed with status: {result.get('status')}",
            {
                "workflow_id": workflow_id,
                "status": result.get("status"),
                "steps_completed": result.get("steps_completed"),
                "duration_minutes": result.get("duration_minutes")
            }
        )
        
        return result
    
    def get_workflow_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for workflow automation"""
        
        # Create common workflow suggestions
        suggestions = [
            {
                "name": "Daily Standup Automation",
                "description": "Automate daily standup preparation and follow-up",
                "category": "productivity",
                "benefits": ["Saves 15 minutes daily", "Consistent meeting prep", "Automatic action items"]
            },
            {
                "name": "Project Deadline Management",
                "description": "Automated deadline tracking and preparation",
                "category": "project_management",
                "benefits": ["Proactive deadline alerts", "Auto-scheduling prep time", "Progress tracking"]
            },
            {
                "name": "Meeting Automation",
                "description": "Automate meeting preparation and follow-up",
                "category": "meetings",
                "benefits": ["Agenda preparation", "Action item creation", "Follow-up reminders"]
            }
        ]
        
        return suggestions
    
    def add_to_knowledge_base(self, title: str, content: str, knowledge_type: str = "document",
                             category: str = "general", tags: List[str] = None) -> int:
        """Add item to personal knowledge base"""
        
        # Convert knowledge type string to enum
        type_map = {
            "document": KnowledgeType.DOCUMENT,
            "conversation": KnowledgeType.CONVERSATION,
            "project": KnowledgeType.PROJECT,
            "contact": KnowledgeType.CONTACT,
            "insight": KnowledgeType.INSIGHT,
            "template": KnowledgeType.TEMPLATE,
            "reference": KnowledgeType.REFERENCE
        }
        knowledge_type_enum = type_map.get(knowledge_type.lower(), KnowledgeType.DOCUMENT)
        
        # Add to knowledge base
        item_id = self.knowledge_base.add_knowledge_item(
            title=title,
            content=content,
            knowledge_type=knowledge_type_enum,
            category=category,
            tags=tags or []
        )
        
        # Store in memory
        self.memory.store_conversation(
            f"Added to knowledge base: {title}",
            f"Knowledge item {item_id} created in {category} category",
            {
                "item_id": item_id,
                "title": title,
                "type": knowledge_type,
                "category": category,
                "tags": tags or []
            }
        )
        
        return item_id
    
    def search_knowledge(self, query: str, search_type: str = "hybrid",
                        categories: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search the personal knowledge base"""
        
        results = self.knowledge_base.search_knowledge(
            query=query,
            search_type=search_type,
            categories=categories,
            limit=limit
        )
        
        # Convert to simplified format
        simple_results = []
        for result in results:
            simple_results.append({
                "id": result.item.id,
                "title": result.item.title,
                "content_snippet": result.matched_content,
                "category": result.item.category,
                "type": result.item.knowledge_type.value,
                "relevance_score": result.relevance_score,
                "match_type": result.match_type,
                "tags": result.item.tags
            })
        
        # Store search in memory
        self.memory.store_conversation(
            f"Searched knowledge base: {query}",
            f"Found {len(simple_results)} relevant items",
            {
                "query": query,
                "search_type": search_type,
                "results_count": len(simple_results),
                "categories": categories
            }
        )
        
        return simple_results
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """Get comprehensive productivity insights"""
        
        # Get enhanced scheduler insights
        task_insights = self.enhanced_scheduler.get_productivity_insights()
        
        # Get proactive assistant analytics
        suggestion_analytics = self.proactive_assistant.get_suggestion_analytics()
        
        # Get workflow analytics
        workflow_analytics = self.workflow_automation.get_workflow_analytics()
        
        # Get knowledge base analytics
        knowledge_analytics = self.knowledge_base.get_knowledge_analytics()
        
        # Combine insights
        insights = {
            "task_management": task_insights,
            "proactive_assistance": suggestion_analytics,
            "automation": workflow_analytics,
            "knowledge_base": knowledge_analytics,
            "overall_score": self._calculate_overall_productivity_score(
                task_insights, suggestion_analytics, workflow_analytics, knowledge_analytics
            )
        }
        
        # Store in memory
        self.memory.store_conversation(
            "Generated productivity insights",
            f"Comprehensive analysis across {len(insights)} areas",
            {"overall_score": insights["overall_score"]}
        )
        
        return insights
    
    def _build_current_user_context(self) -> UserContext:
        """Build current user context for proactive suggestions"""
        
        from datetime import datetime
        
        # Get recent activity from memory
        recent_conversations = self.memory.get_conversation_history(limit=5)
        
        # Analyze current activity
        current_activity = "general"
        if recent_conversations:
            last_conv = recent_conversations[0]
            if "task" in last_conv["user_input"].lower():
                current_activity = "task_management"
            elif "schedule" in last_conv["user_input"].lower():
                current_activity = "scheduling"
            elif any(word in last_conv["user_input"].lower() for word in ["help", "problem", "stuck"]):
                current_activity = "problem_solving"
        
        # Get task statistics
        task_stats = self.scheduler.get_task_statistics()
        
        # Determine workload status
        workload_status = "moderate"
        if task_stats["total_tasks"] > 15:
            workload_status = "heavy"
        elif task_stats["total_tasks"] > 25:
            workload_status = "overloaded"
        elif task_stats["total_tasks"] < 5:
            workload_status = "light"
        
        # Get upcoming deadlines
        upcoming_deadlines = []
        # This would be populated from task scheduler in real implementation
        
        # Determine time of day
        hour = datetime.now().hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        return UserContext(
            current_activity=current_activity,
            focus_state="focused",  # Default - could be enhanced with actual monitoring
            energy_level=7,  # Default - could be enhanced with user input
            mood="productive",  # Default - could be enhanced with sentiment analysis
            location="office",  # Default - could be enhanced with location detection
            time_of_day=time_of_day,
            workload_status=workload_status,
            upcoming_deadlines=upcoming_deadlines,
            recent_productivity=0.75  # Default - could be calculated from actual data
        )
    
    def _calculate_overall_productivity_score(self, task_insights: Dict, suggestion_analytics: Dict,
                                            workflow_analytics: Dict, knowledge_analytics: Dict) -> float:
        """Calculate overall productivity score"""
        
        scores = []
        
        # Task management score
        if "average_productivity" in task_insights:
            scores.append(task_insights["average_productivity"])
        
        # Suggestion effectiveness score
        if "acknowledgment_rate" in suggestion_analytics:
            scores.append(suggestion_analytics["acknowledgment_rate"] / 100.0)
        
        # Workflow automation score
        if "success_rate" in workflow_analytics:
            scores.append(workflow_analytics["success_rate"] / 100.0)
        
        # Knowledge utilization score (based on recent searches)
        if "recent_searches" in knowledge_analytics:
            knowledge_score = min(knowledge_analytics["recent_searches"] / 10.0, 1.0)
            scores.append(knowledge_score)
        
        # Return average score
        return sum(scores) / len(scores) if scores else 0.7
    
    # Private helper methods
    def _analyze_user_input(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user input for intent and context"""
        
        analysis = {
            "intent": "general",
            "urgency": "normal",
            "emotional_tone": "neutral",
            "task_related": False,
            "requires_memory": False,
            "conversation_type": "informational"
        }
        
        input_lower = user_input.lower()
        
        # Intent detection
        if any(word in input_lower for word in ['help', 'assist', 'can you']):
            analysis["intent"] = "assistance_request"
        elif any(word in input_lower for word in ['remind', 'schedule', 'task', 'todo']):
            analysis["intent"] = "task_management"
            analysis["task_related"] = True
        elif any(word in input_lower for word in ['remember', 'recall', 'what did', 'last time']):
            analysis["intent"] = "memory_query"
            analysis["requires_memory"] = True
        elif any(word in input_lower for word in ['brainstorm', 'ideas', 'think about']):
            analysis["intent"] = "brainstorming"
            analysis["conversation_type"] = "creative"
        
        # Urgency detection
        if any(word in input_lower for word in ['urgent', 'asap', 'immediately', 'now']):
            analysis["urgency"] = "high"
        elif any(word in input_lower for word in ['when possible', 'later', 'eventually']):
            analysis["urgency"] = "low"
        
        # Emotional tone detection
        if any(word in input_lower for word in ['frustrated', 'stuck', 'confused', 'difficult']):
            analysis["emotional_tone"] = "challenged"
        elif any(word in input_lower for word in ['excited', 'great', 'awesome', 'love']):
            analysis["emotional_tone"] = "positive"
        elif any(word in input_lower for word in ['worried', 'concerned', 'anxious']):
            analysis["emotional_tone"] = "concerned"
        
        # Add context if provided
        if context:
            analysis.update(context)
        
        return analysis
    
    def _generate_enhanced_system_prompt(self, input_analysis: Dict, memory_context: Dict) -> str:
        """Generate enhanced system prompt with companion context"""
        
        # Base personality system prompt
        base_prompt = self.personality.generate_system_prompt(input_analysis)
        
        # Add memory context
        memory_additions = []
        if memory_context.get("recent_conversations"):
            memory_additions.append("Use previous conversation context to provide continuity.")
        
        if memory_context.get("user_context"):
            user_prefs = memory_context["user_context"]
            if user_prefs:
                memory_additions.append(f"User preferences: {user_prefs}")
        
        # Add task context if relevant
        task_additions = []
        if input_analysis.get("task_related"):
            task_stats = self.scheduler.get_task_statistics()
            task_additions.append(f"User has {task_stats['total_tasks']} active tasks.")
        
        # Add mode-specific instructions
        mode_instructions = {
            "companion": "Be proactive, empathetic, and remember personal context.",
            "assistant": "Focus on providing helpful, accurate information.",
            "task_focused": "Prioritize task management and productivity guidance.",
            "brainstorming": "Encourage creative thinking and exploration of ideas."
        }
        
        mode_instruction = mode_instructions.get(self.conversation_mode, "")
        
        # Combine all elements
        enhanced_parts = [base_prompt]
        
        if memory_additions:
            enhanced_parts.extend(memory_additions)
        
        if task_additions:
            enhanced_parts.extend(task_additions)
        
        if mode_instruction:
            enhanced_parts.append(mode_instruction)
        
        return " ".join(enhanced_parts)
    
    def _build_companion_prompt(self, user_input: str, analysis: Dict, memory_context: Dict) -> str:
        """Build enhanced prompt with companion context"""
        
        prompt_parts = []
        
        # Add memory context if relevant
        if memory_context.get("recent_conversations"):
            prompt_parts.append("Recent conversation context:")
            for conv in memory_context["recent_conversations"][:2]:
                prompt_parts.append(f"- {conv['user_input'][:100]}...")
        
        # Add current user input
        prompt_parts.append(f"Current user input: {user_input}")
        
        # Add analysis context for complex intents
        if analysis["intent"] != "general":
            prompt_parts.append(f"User intent: {analysis['intent']}")
        
        if analysis["emotional_tone"] != "neutral":
            prompt_parts.append(f"User's emotional tone: {analysis['emotional_tone']}")
        
        return "\n".join(prompt_parts)
    
    def _enhance_response(self, raw_response: str, analysis: Dict, memory_context: Dict) -> CompanionResponse:
        """Enhance raw LLM response with companion features"""
        
        # Determine response type
        response_type = "companion"
        if analysis.get("task_related"):
            response_type = "task_suggestion"
        elif analysis.get("requires_memory"):
            response_type = "memory_reference"
        
        # Extract suggested actions (simplified)
        suggested_actions = []
        if "should" in raw_response.lower() or "recommend" in raw_response.lower():
            suggested_actions.append("Consider the recommendation provided")
        
        # Generate proactive suggestions
        proactive_suggestions = []
        if self.personality.communication_style.proactive_suggestions:
            if analysis["intent"] == "task_management":
                proactive_suggestions.append("Would you like me to help prioritize your tasks?")
            elif analysis["emotional_tone"] == "challenged":
                proactive_suggestions.append("I can break this down into smaller steps if that would help.")
        
        # Determine emotional tone of response
        emotional_tone = "supportive"
        if analysis["emotional_tone"] == "positive":
            emotional_tone = "enthusiastic"
        elif analysis["emotional_tone"] == "challenged":
            emotional_tone = "encouraging"
        
        # Get memory references
        memory_references = []
        if memory_context.get("related_conversations"):
            memory_references = [conv["user_input"][:50] + "..." 
                               for conv in memory_context["related_conversations"][:2]]
        
        return CompanionResponse(
            content=raw_response,
            response_type=response_type,
            personality_context={
                "warmth": self.personality.personality_traits.warmth,
                "communication_style": self.personality.communication_style.tone_preference
            },
            memory_references=memory_references,
            suggested_actions=suggested_actions,
            proactive_suggestions=proactive_suggestions,
            emotional_tone=emotional_tone,
            confidence_score=0.8  # Simplified confidence calculation
        )
    
    def _create_fallback_response(self, user_input: str, error_message: str) -> CompanionResponse:
        """Create fallback response when LLM fails"""
        
        fallback_content = "I apologize, but I'm having trouble processing that right now. Could you try rephrasing your request?"
        
        return CompanionResponse(
            content=fallback_content,
            response_type="error_fallback",
            personality_context={},
            memory_references=[],
            suggested_actions=["Try rephrasing the request"],
            proactive_suggestions=[],
            emotional_tone="apologetic",
            confidence_score=0.3
        )
    
    def _process_task_actions(self, user_input: str, response: CompanionResponse):
        """Process any task-related actions from the conversation"""
        
        # Simple task extraction (could be enhanced with NLP)
        if "remind me" in user_input.lower():
            # Extract reminder from user input
            task_info = self.scheduler.parse_natural_language_task(user_input)
            if task_info["title"]:
                reminder_id = self.scheduler.add_reminder(
                    title=task_info["title"],
                    message=f"Reminder: {task_info['title']}",
                    remind_at=task_info.get("due_date") or datetime.now().isoformat()
                )
                response.suggested_actions.append(f"Created reminder: {task_info['title']}")
        
        elif "add task" in user_input.lower() or "create task" in user_input.lower():
            # Extract task from user input
            task_info = self.scheduler.parse_natural_language_task(user_input)
            if task_info["title"]:
                task_id = self.scheduler.create_task(
                    title=task_info["title"],
                    description=task_info["description"],
                    priority=task_info["priority"],
                    due_date=task_info["due_date"],
                    tags=task_info["tags"]
                )
                response.suggested_actions.append(f"Created task: {task_info['title']}")
    
    def _assess_companion_readiness(self) -> float:
        """Assess how well the companion is configured for the user"""
        
        readiness_factors = {
            "memory_context": len(self.memory.get_conversation_history(limit=10)) / 10.0,
            "personality_adaptation": min(self.personality._get_adaptation_count() / 5.0, 1.0),
            "task_integration": min(self.scheduler.get_task_statistics()["total_tasks"] / 5.0, 1.0),
            "llm_availability": 1.0 if self.llm_client.is_available() else 0.0
        }
        
        return sum(readiness_factors.values()) / len(readiness_factors)
    
    def _get_version_content(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get content for a specific version"""
        
        # Check brainstorming engine database
        brainstorm_db = self.memory_dir / "brainstorming.db"
        if not brainstorm_db.exists():
            return None
        
        import sqlite3
        conn = sqlite3.connect(brainstorm_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content, stage, quality_score, created_at
            FROM prompt_versions WHERE version_id = ?
        ''', (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "content": row[0],
                "stage": row[1],
                "quality_score": row[2],
                "created_at": row[3]
            }
        
        return None
    
    def _get_version_branch(self, version_id: str) -> Optional[str]:
        """Get branch ID for a version"""
        
        brainstorm_db = self.memory_dir / "brainstorming.db"
        if not brainstorm_db.exists():
            return None
        
        import sqlite3
        conn = sqlite3.connect(brainstorm_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT branch_id FROM conversation_branches 
            WHERE prompt_versions LIKE ?
        ''', (f'%"{version_id}"%',))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def _select_best_web_result(self, results: Dict[ServiceType, Any]) -> Dict[str, Any]:
        """Select the best result from web service responses"""
        
        if not results:
            return {"service": "none", "quality_score": 0.0, "content": "No results available"}
        
        # Find result with highest quality score
        best_service = None
        best_score = 0.0
        best_result = None
        
        for service, result in results.items():
            if hasattr(result, 'quality_score') and result.quality_score > best_score:
                best_score = result.quality_score
                best_service = service
                best_result = result
        
        if best_result:
            return {
                "service": best_service.value,
                "quality_score": best_score,
                "content": best_result.raw_output,
                "refinement_count": getattr(best_result, 'refinement_count', 0)
            }
        
        # Fallback to first result
        first_service, first_result = next(iter(results.items()))
        return {
            "service": first_service.value,
            "quality_score": getattr(first_result, 'quality_score', 0.0),
            "content": getattr(first_result, 'raw_output', str(first_result)),
            "refinement_count": getattr(first_result, 'refinement_count', 0)
        }
    
    def _determine_optimal_output_format(self, query: str) -> OutputFormat:
        """Determine optimal output format based on query"""
        
        query_lower = query.lower()
        
        # JSON for structured data requests
        if any(word in query_lower for word in ['data', 'information', 'extract', 'structure', 'json']):
            return OutputFormat.JSON
        
        # Markdown for documentation or formatted text
        if any(word in query_lower for word in ['document', 'format', 'write', 'create', 'markdown']):
            return OutputFormat.MARKDOWN
        
        # Structured text for lists and organized information
        if any(word in query_lower for word in ['list', 'steps', 'process', 'instructions']):
            return OutputFormat.STRUCTURED_TEXT
        
        # Default to JSON for machine processing
        return OutputFormat.JSON
    
    def _generate_expected_output_structure(self, query: str, output_format: OutputFormat) -> str:
        """Generate expected output structure based on query and format"""
        
        if output_format == OutputFormat.JSON:
            # Analyze query to determine JSON structure
            query_lower = query.lower()
            
            if 'list' in query_lower or 'items' in query_lower:
                return '{"items": [], "count": 0, "summary": ""}'
            elif 'information' in query_lower or 'data' in query_lower:
                return '{"data": {}, "source": "", "confidence": 0.0}'
            elif 'analysis' in query_lower or 'compare' in query_lower:
                return '{"analysis": "", "findings": [], "conclusion": ""}'
            else:
                return '{"result": "", "details": {}, "metadata": {}}'
        
        elif output_format == OutputFormat.MARKDOWN:
            return """# Title
## Summary
Content here
## Details
- Point 1
- Point 2
## Conclusion
Final thoughts"""
        
        elif output_format == OutputFormat.STRUCTURED_TEXT:
            return """Result: [main result]
Details: [detailed information]
Source: [information source]
Confidence: [confidence level]"""
        
        else:
            return "Structured response matching the request"


def main():
    """Test the companion interface system"""
    print("🤖 Testing Companion Interface System")
    print("=" * 50)
    
    # Initialize companion interface
    companion = CompanionInterface(user_id="test_user")
    
    # Test basic companion interaction
    print("\n💬 Testing companion interaction:")
    response = companion.process_companion_input(
        "Hi, I'm feeling a bit overwhelmed with my tasks today"
    )
    print(f"Response: {response.content[:200]}...")
    print(f"Type: {response.response_type}")
    print(f"Emotional tone: {response.emotional_tone}")
    print(f"Suggestions: {len(response.proactive_suggestions)}")
    
    # Test proactive suggestions
    print("\n💡 Testing proactive suggestions:")
    suggestions = companion.get_proactive_suggestions()
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"{i}. {suggestion}")
    
    # Test mode switching
    print("\n🔄 Testing mode switching:")
    mode_result = companion.switch_conversation_mode("task_focused")
    print(f"Mode switch: {mode_result}")
    
    # Test daily briefing
    print("\n📋 Testing daily briefing:")
    briefing = companion.get_daily_briefing()
    print(f"Briefing: {briefing}")
    
    # Test conversation summary
    print("\n📊 Testing conversation summary:")
    summary = companion.get_conversation_summary()
    print(f"Session: {summary['session_id']}")
    print(f"Mode: {summary['conversation_mode']}")
    print(f"Companion readiness: {summary['companion_readiness']:.1%}")
    print(f"Memory stats: {summary['memory_stats']['total_conversations']} conversations")
    
    # Test task integration
    print("\n📋 Testing task integration:")
    task_response = companion.process_companion_input(
        "remind me to call John tomorrow at 2 PM"
    )
    print(f"Task response: {task_response.content[:150]}...")
    print(f"Actions: {task_response.suggested_actions}")
    
    print(f"\n✅ CompanionInterface system test completed!")


if __name__ == "__main__":
    main()