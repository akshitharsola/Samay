#!/usr/bin/env python3
"""
Samay v3 - Parallel Session Manager
==================================
Phase 3: Manage concurrent web sessions for parallel multi-service processing
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from enum import Enum
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

from .web_agent_dispatcher import ServiceType, OutputFormat, WebRequest, WebResponse
from .machine_language_optimizer import MachineLanguageOptimizer
from .refinement_loop_system import RefinementLoopSystem


class SessionState(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ExecutionMode(Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    PRIORITY_BASED = "priority_based"
    LOAD_BALANCED = "load_balanced"


@dataclass
class ServiceSession:
    """Represents a web service session"""
    session_id: str
    service: ServiceType
    state: SessionState
    last_activity: str
    total_requests: int
    successful_requests: int
    average_response_time: float
    current_load: int
    max_concurrent: int
    session_data: Dict[str, Any]


@dataclass
class ParallelExecution:
    """Represents a parallel execution request"""
    execution_id: str
    original_prompt: str
    target_services: List[ServiceType]
    execution_mode: ExecutionMode
    expected_output: str
    output_format: OutputFormat
    priority: int
    created_at: str
    completed_at: Optional[str]
    results: Dict[ServiceType, WebResponse]
    execution_time: float
    success_rate: float


@dataclass
class LoadBalancingMetrics:
    """Metrics for load balancing decisions"""
    service: ServiceType
    queue_length: int
    average_response_time: float
    success_rate: float
    current_load: float
    capacity_score: float


class ParallelSessionManager:
    """Manages parallel execution across multiple web service sessions"""
    
    def __init__(self, memory_dir: str = "memory", session_id: str = "default"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.db_path = self.memory_dir / "parallel_sessions.db"
        self.session_id = session_id
        
        # Initialize dependencies
        self.optimizer = MachineLanguageOptimizer(memory_dir, session_id + "_parallel_opt")
        self.refinement_system = RefinementLoopSystem(memory_dir, session_id + "_parallel_refine")
        
        # Session management
        self.service_sessions = {}
        self.execution_queue = asyncio.Queue()
        self.active_executions = {}
        self.session_locks = {}
        
        # Load balancing
        self.load_metrics = {}
        self.performance_history = {}
        
        # Configuration
        self.max_concurrent_per_service = 3
        self.default_timeout = 30.0
        self.retry_attempts = 2
        
        self.init_database()
        self._initialize_service_sessions()
        print(f"⚡ ParallelSessionManager initialized for session {session_id}")
    
    def init_database(self):
        """Initialize parallel session manager database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Service sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_sessions (
                session_id TEXT,
                service TEXT,
                state TEXT,
                last_activity TEXT,
                total_requests INTEGER,
                successful_requests INTEGER,
                average_response_time REAL,
                current_load INTEGER,
                max_concurrent INTEGER,
                session_data TEXT,
                PRIMARY KEY (session_id, service)
            )
        ''')
        
        # Parallel executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parallel_executions (
                execution_id TEXT PRIMARY KEY,
                session_id TEXT,
                original_prompt TEXT,
                target_services TEXT,
                execution_mode TEXT,
                expected_output TEXT,
                output_format TEXT,
                priority INTEGER,
                created_at TEXT,
                completed_at TEXT,
                execution_time REAL,
                success_rate REAL,
                results_summary TEXT
            )
        ''')
        
        # Execution results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_results (
                result_id TEXT PRIMARY KEY,
                execution_id TEXT,
                service TEXT,
                request_sent_at TEXT,
                response_received_at TEXT,
                response_time REAL,
                success BOOLEAN,
                quality_score REAL,
                refinement_attempts INTEGER,
                final_output TEXT,
                FOREIGN KEY (execution_id) REFERENCES parallel_executions (execution_id)
            )
        ''')
        
        # Load balancing metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS load_metrics (
                metric_id TEXT PRIMARY KEY,
                service TEXT,
                timestamp TEXT,
                queue_length INTEGER,
                response_time REAL,
                success_rate REAL,
                load_factor REAL,
                capacity_utilization REAL
            )
        ''')
        
        # Performance analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_analytics (
                analytics_id TEXT PRIMARY KEY,
                session_id TEXT,
                service TEXT,
                time_period TEXT,
                total_requests INTEGER,
                successful_requests INTEGER,
                average_response_time REAL,
                peak_load REAL,
                efficiency_score REAL,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_service_session(
        self,
        service: ServiceType,
        session_data: Dict[str, Any],
        max_concurrent: int = 3
    ):
        """Register a service session for parallel processing"""
        
        session = ServiceSession(
            session_id=str(uuid.uuid4()),
            service=service,
            state=SessionState.ACTIVE,
            last_activity=datetime.now().isoformat(),
            total_requests=0,
            successful_requests=0,
            average_response_time=0.0,
            current_load=0,
            max_concurrent=max_concurrent,
            session_data=session_data
        )
        
        self.service_sessions[service] = session
        self.session_locks[service] = asyncio.Lock()
        self.load_metrics[service] = LoadBalancingMetrics(
            service=service,
            queue_length=0,
            average_response_time=0.0,
            success_rate=1.0,
            current_load=0.0,
            capacity_score=1.0
        )
        
        # Store in database
        self._store_service_session(session)
        
        print(f"✅ {service.value.title()} session registered (max concurrent: {max_concurrent})")
    
    async def execute_parallel_request(
        self,
        prompt: str,
        services: List[ServiceType],
        expected_output: str,
        output_format: OutputFormat = OutputFormat.JSON,
        execution_mode: ExecutionMode = ExecutionMode.PARALLEL,
        priority: int = 3,
        quality_threshold: float = 0.8
    ) -> ParallelExecution:
        """Execute request across multiple services in parallel"""
        
        start_time = time.time()
        
        execution = ParallelExecution(
            execution_id=str(uuid.uuid4()),
            original_prompt=prompt,
            target_services=services,
            execution_mode=execution_mode,
            expected_output=expected_output,
            output_format=output_format,
            priority=priority,
            created_at=datetime.now().isoformat(),
            completed_at=None,
            results={},
            execution_time=0.0,
            success_rate=0.0
        )
        
        print(f"⚡ Starting parallel execution across {len(services)} services")
        print(f"🎯 Mode: {execution_mode.value}, Priority: {priority}")
        
        # Check service availability
        available_services = self._check_service_availability(services)
        if not available_services:
            print("❌ No available services for execution")
            return execution
        
        # Generate optimized prompts for each service
        optimized_prompts = self.optimizer.optimize_for_parallel_execution(
            prompt, available_services, expected_output, output_format
        )
        
        # Execute based on mode
        if execution_mode == ExecutionMode.PARALLEL:
            results = await self._execute_pure_parallel(
                optimized_prompts, expected_output, output_format, quality_threshold
            )
        elif execution_mode == ExecutionMode.SEQUENTIAL:
            results = await self._execute_sequential(
                optimized_prompts, expected_output, output_format, quality_threshold
            )
        elif execution_mode == ExecutionMode.PRIORITY_BASED:
            results = await self._execute_priority_based(
                optimized_prompts, expected_output, output_format, quality_threshold, priority
            )
        elif execution_mode == ExecutionMode.LOAD_BALANCED:
            results = await self._execute_load_balanced(
                optimized_prompts, expected_output, output_format, quality_threshold
            )
        else:
            results = await self._execute_pure_parallel(
                optimized_prompts, expected_output, output_format, quality_threshold
            )
        
        # Update execution results
        execution.results = results
        execution.execution_time = time.time() - start_time
        execution.completed_at = datetime.now().isoformat()
        execution.success_rate = self._calculate_success_rate(results)
        
        # Store execution
        self._store_parallel_execution(execution)
        
        print(f"✅ Parallel execution completed in {execution.execution_time:.2f}s")
        print(f"📊 Success rate: {execution.success_rate:.1%}")
        print(f"🎯 Services completed: {len(results)}/{len(services)}")
        
        return execution
    
    async def _execute_pure_parallel(
        self,
        optimized_prompts: Dict[ServiceType, str],
        expected_output: str,
        output_format: OutputFormat,
        quality_threshold: float
    ) -> Dict[ServiceType, WebResponse]:
        """Execute all services in pure parallel mode"""
        
        # Create tasks for all services
        tasks = []
        for service, prompt in optimized_prompts.items():
            task = asyncio.create_task(
                self._execute_single_service_with_refinement(
                    service, prompt, expected_output, output_format, quality_threshold
                )
            )
            tasks.append((service, task))
        
        # Wait for all tasks to complete
        results = {}
        for service, task in tasks:
            try:
                result = await task
                results[service] = result
            except Exception as e:
                print(f"❌ {service.value} failed: {e}")
                # Create error response
                results[service] = self._create_error_response(service, str(e))
        
        return results
    
    async def _execute_sequential(
        self,
        optimized_prompts: Dict[ServiceType, str],
        expected_output: str,
        output_format: OutputFormat,
        quality_threshold: float
    ) -> Dict[ServiceType, WebResponse]:
        """Execute services sequentially"""
        
        results = {}
        
        # Sort by load metrics for optimal order
        sorted_services = sorted(
            optimized_prompts.keys(),
            key=lambda s: self.load_metrics[s].average_response_time
        )
        
        for service in sorted_services:
            prompt = optimized_prompts[service]
            print(f"🔄 Processing {service.value}...")
            
            try:
                result = await self._execute_single_service_with_refinement(
                    service, prompt, expected_output, output_format, quality_threshold
                )
                results[service] = result
                print(f"✅ {service.value} completed")
            except Exception as e:
                print(f"❌ {service.value} failed: {e}")
                results[service] = self._create_error_response(service, str(e))
        
        return results
    
    async def _execute_priority_based(
        self,
        optimized_prompts: Dict[ServiceType, str],
        expected_output: str,
        output_format: OutputFormat,
        quality_threshold: float,
        priority: int
    ) -> Dict[ServiceType, WebResponse]:
        """Execute services based on priority and performance"""
        
        # Prioritize services based on historical performance
        service_priorities = self._calculate_service_priorities(
            list(optimized_prompts.keys()), priority
        )
        
        # Start with highest priority services first
        high_priority = [s for s, p in service_priorities.items() if p >= 4]
        medium_priority = [s for s, p in service_priorities.items() if 2 <= p < 4]
        low_priority = [s for s, p in service_priorities.items() if p < 2]
        
        results = {}
        
        # Execute high priority in parallel
        if high_priority:
            high_results = await self._execute_service_batch(
                {s: optimized_prompts[s] for s in high_priority},
                expected_output, output_format, quality_threshold
            )
            results.update(high_results)
        
        # Execute medium priority if high priority didn't meet quality threshold
        if medium_priority and not self._meets_quality_threshold(results, quality_threshold):
            medium_results = await self._execute_service_batch(
                {s: optimized_prompts[s] for s in medium_priority},
                expected_output, output_format, quality_threshold
            )
            results.update(medium_results)
        
        # Execute low priority if still not satisfied
        if low_priority and not self._meets_quality_threshold(results, quality_threshold):
            low_results = await self._execute_service_batch(
                {s: optimized_prompts[s] for s in low_priority},
                expected_output, output_format, quality_threshold
            )
            results.update(low_results)
        
        return results
    
    async def _execute_load_balanced(
        self,
        optimized_prompts: Dict[ServiceType, str],
        expected_output: str,
        output_format: OutputFormat,
        quality_threshold: float
    ) -> Dict[ServiceType, WebResponse]:
        """Execute services with load balancing"""
        
        results = {}
        remaining_services = list(optimized_prompts.keys())
        
        while remaining_services:
            # Select best available service based on load metrics
            best_service = self._select_best_available_service(remaining_services)
            
            if best_service:
                print(f"🔄 Load-balanced execution: {best_service.value}")
                
                try:
                    result = await self._execute_single_service_with_refinement(
                        best_service,
                        optimized_prompts[best_service],
                        expected_output,
                        output_format,
                        quality_threshold
                    )
                    results[best_service] = result
                except Exception as e:
                    print(f"❌ {best_service.value} failed: {e}")
                    results[best_service] = self._create_error_response(best_service, str(e))
                
                remaining_services.remove(best_service)
                
                # Update load metrics
                await self._update_load_metrics(best_service)
                
                # Brief delay for load balancing
                await asyncio.sleep(0.5)
            else:
                # No available services, wait briefly and try again
                await asyncio.sleep(1)
        
        return results
    
    async def _execute_single_service_with_refinement(
        self,
        service: ServiceType,
        prompt: str,
        expected_output: str,
        output_format: OutputFormat,
        quality_threshold: float
    ) -> WebResponse:
        """Execute single service with refinement loop"""
        
        async with self.session_locks[service]:
            # Update service load
            session = self.service_sessions[service]
            session.current_load += 1
            session.total_requests += 1
            
            try:
                # Execute refinement loop
                refinement_session = await self.refinement_system.execute_refinement_loop(
                    prompt,
                    expected_output,
                    service,
                    output_format,
                    max_refinements=3,
                    quality_threshold=quality_threshold
                )
                
                # Create web response from refinement session
                response = WebResponse(
                    response_id=str(uuid.uuid4()),
                    request_id=refinement_session.session_id,
                    service=service,
                    raw_output=f"Refinement completed with {refinement_session.total_attempts} attempts",
                    parsed_output={"success": refinement_session.final_success},
                    status=WebRequest.COMPLETED if refinement_session.final_success else WebRequest.FAILED,
                    refinement_count=refinement_session.total_attempts,
                    quality_score=refinement_session.final_quality_score,
                    timestamp=datetime.now().isoformat()
                )
                
                # Update session metrics
                if refinement_session.final_success:
                    session.successful_requests += 1
                
                # Update average response time
                if session.total_requests > 0:
                    session.average_response_time = (
                        (session.average_response_time * (session.total_requests - 1) + 
                         refinement_session.time_elapsed) / session.total_requests
                    )
                
                return response
                
            except Exception as e:
                print(f"❌ Service {service.value} execution failed: {e}")
                return self._create_error_response(service, str(e))
            
            finally:
                # Update service load
                session.current_load = max(0, session.current_load - 1)
                session.last_activity = datetime.now().isoformat()
                self._update_service_session(session)
    
    async def _execute_service_batch(
        self,
        prompts: Dict[ServiceType, str],
        expected_output: str,
        output_format: OutputFormat,
        quality_threshold: float
    ) -> Dict[ServiceType, WebResponse]:
        """Execute a batch of services in parallel"""
        
        tasks = []
        for service, prompt in prompts.items():
            task = asyncio.create_task(
                self._execute_single_service_with_refinement(
                    service, prompt, expected_output, output_format, quality_threshold
                )
            )
            tasks.append((service, task))
        
        results = {}
        for service, task in tasks:
            try:
                result = await task
                results[service] = result
            except Exception as e:
                results[service] = self._create_error_response(service, str(e))
        
        return results
    
    def _check_service_availability(self, services: List[ServiceType]) -> List[ServiceType]:
        """Check which services are available for execution"""
        
        available = []
        for service in services:
            if service in self.service_sessions:
                session = self.service_sessions[service]
                if (session.state == SessionState.ACTIVE and 
                    session.current_load < session.max_concurrent):
                    available.append(service)
        
        return available
    
    def _calculate_service_priorities(
        self, 
        services: List[ServiceType], 
        base_priority: int
    ) -> Dict[ServiceType, int]:
        """Calculate service priorities based on performance"""
        
        priorities = {}
        
        for service in services:
            priority = base_priority
            
            if service in self.load_metrics:
                metrics = self.load_metrics[service]
                
                # Adjust based on success rate
                if metrics.success_rate > 0.8:
                    priority += 1
                elif metrics.success_rate < 0.5:
                    priority -= 1
                
                # Adjust based on response time
                if metrics.average_response_time < 3.0:
                    priority += 1
                elif metrics.average_response_time > 10.0:
                    priority -= 1
                
                # Adjust based on current load
                if metrics.current_load < 0.5:
                    priority += 1
                elif metrics.current_load > 0.8:
                    priority -= 1
            
            priorities[service] = max(1, min(5, priority))  # Clamp to 1-5
        
        return priorities
    
    def _select_best_available_service(self, services: List[ServiceType]) -> Optional[ServiceType]:
        """Select the best available service for load balancing"""
        
        available_services = self._check_service_availability(services)
        if not available_services:
            return None
        
        # Score each service
        service_scores = {}
        for service in available_services:
            metrics = self.load_metrics[service]
            
            # Calculate composite score
            load_score = 1.0 - metrics.current_load
            speed_score = 1.0 / (1.0 + metrics.average_response_time)
            success_score = metrics.success_rate
            capacity_score = metrics.capacity_score
            
            composite_score = (
                load_score * 0.3 +
                speed_score * 0.3 +
                success_score * 0.2 +
                capacity_score * 0.2
            )
            
            service_scores[service] = composite_score
        
        # Return service with highest score
        return max(service_scores.keys(), key=lambda s: service_scores[s])
    
    def _meets_quality_threshold(
        self, 
        results: Dict[ServiceType, WebResponse], 
        threshold: float
    ) -> bool:
        """Check if any result meets the quality threshold"""
        
        return any(
            result.quality_score >= threshold 
            for result in results.values()
        )
    
    def _calculate_success_rate(self, results: Dict[ServiceType, WebResponse]) -> float:
        """Calculate overall success rate of execution"""
        
        if not results:
            return 0.0
        
        successful = sum(
            1 for result in results.values() 
            if result.status.value == "completed"
        )
        
        return successful / len(results)
    
    def _create_error_response(self, service: ServiceType, error_message: str) -> WebResponse:
        """Create error response for failed service"""
        
        return WebResponse(
            response_id=str(uuid.uuid4()),
            request_id="error",
            service=service,
            raw_output=f"Error: {error_message}",
            parsed_output=None,
            status=WebRequest.FAILED,
            refinement_count=0,
            quality_score=0.0,
            timestamp=datetime.now().isoformat()
        )
    
    async def _update_load_metrics(self, service: ServiceType):
        """Update load metrics for a service"""
        
        if service in self.service_sessions:
            session = self.service_sessions[service]
            metrics = self.load_metrics[service]
            
            # Update metrics
            metrics.current_load = session.current_load / session.max_concurrent
            metrics.average_response_time = session.average_response_time
            metrics.success_rate = (
                session.successful_requests / session.total_requests 
                if session.total_requests > 0 else 1.0
            )
            metrics.capacity_score = 1.0 - metrics.current_load
            
            # Store metrics
            self._store_load_metrics(metrics)
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics"""
        
        analytics = {
            "service_performance": {},
            "execution_summary": {},
            "load_balancing": {},
            "recommendations": []
        }
        
        # Service performance
        for service, session in self.service_sessions.items():
            analytics["service_performance"][service.value] = {
                "total_requests": session.total_requests,
                "success_rate": session.successful_requests / session.total_requests if session.total_requests > 0 else 0,
                "average_response_time": session.average_response_time,
                "current_load": session.current_load,
                "state": session.state.value
            }
        
        # Load balancing metrics
        for service, metrics in self.load_metrics.items():
            analytics["load_balancing"][service.value] = {
                "queue_length": metrics.queue_length,
                "capacity_utilization": 1.0 - metrics.capacity_score,
                "efficiency": metrics.success_rate * metrics.capacity_score
            }
        
        # Generate recommendations
        analytics["recommendations"] = self._generate_performance_recommendations()
        
        return analytics
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        for service, session in self.service_sessions.items():
            if session.total_requests > 0:
                success_rate = session.successful_requests / session.total_requests
                
                if success_rate < 0.7:
                    recommendations.append(
                        f"Consider optimizing prompts for {service.value} (success rate: {success_rate:.1%})"
                    )
                
                if session.average_response_time > 10:
                    recommendations.append(
                        f"High response time detected for {service.value} ({session.average_response_time:.1f}s)"
                    )
                
                if session.current_load / session.max_concurrent > 0.8:
                    recommendations.append(
                        f"Consider increasing concurrent capacity for {service.value}"
                    )
        
        return recommendations
    
    def _initialize_service_sessions(self):
        """Initialize service sessions from database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT service, state, last_activity, total_requests, successful_requests,
                   average_response_time, current_load, max_concurrent, session_data
            FROM service_sessions WHERE session_id = ?
        ''', (self.session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            service = ServiceType(row[0])
            session = ServiceSession(
                session_id=self.session_id,
                service=service,
                state=SessionState(row[1]),
                last_activity=row[2],
                total_requests=row[3],
                successful_requests=row[4],
                average_response_time=row[5],
                current_load=row[6],
                max_concurrent=row[7],
                session_data=json.loads(row[8]) if row[8] else {}
            )
            
            self.service_sessions[service] = session
            self.session_locks[service] = asyncio.Lock()
    
    # Database storage methods
    def _store_service_session(self, session: ServiceSession):
        """Store service session in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO service_sessions 
            (session_id, service, state, last_activity, total_requests, successful_requests,
             average_response_time, current_load, max_concurrent, session_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            session.service.value,
            session.state.value,
            session.last_activity,
            session.total_requests,
            session.successful_requests,
            session.average_response_time,
            session.current_load,
            session.max_concurrent,
            json.dumps(session.session_data)
        ))
        conn.commit()
        conn.close()
    
    def _update_service_session(self, session: ServiceSession):
        """Update service session in database"""
        self._store_service_session(session)  # Same as store with REPLACE
    
    def _store_parallel_execution(self, execution: ParallelExecution):
        """Store parallel execution in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO parallel_executions 
            (execution_id, session_id, original_prompt, target_services, execution_mode,
             expected_output, output_format, priority, created_at, completed_at,
             execution_time, success_rate, results_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            execution.execution_id,
            self.session_id,
            execution.original_prompt,
            json.dumps([s.value for s in execution.target_services]),
            execution.execution_mode.value,
            execution.expected_output,
            execution.output_format.value,
            execution.priority,
            execution.created_at,
            execution.completed_at,
            execution.execution_time,
            execution.success_rate,
            json.dumps({s.value: r.quality_score for s, r in execution.results.items()})
        ))
        
        # Store individual results
        for service, result in execution.results.items():
            cursor.execute('''
                INSERT INTO execution_results 
                (result_id, execution_id, service, response_time, success, 
                 quality_score, refinement_attempts, final_output)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                execution.execution_id,
                service.value,
                0.0,  # Would track actual response time
                result.status.value == "completed",
                result.quality_score,
                result.refinement_count,
                result.raw_output[:500]  # Truncate
            ))
        
        conn.commit()
        conn.close()
    
    def _store_load_metrics(self, metrics: LoadBalancingMetrics):
        """Store load balancing metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO load_metrics 
            (metric_id, service, timestamp, queue_length, response_time, 
             success_rate, load_factor, capacity_utilization)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            metrics.service.value,
            datetime.now().isoformat(),
            metrics.queue_length,
            metrics.average_response_time,
            metrics.success_rate,
            metrics.current_load,
            1.0 - metrics.capacity_score
        ))
        conn.commit()
        conn.close()


def main():
    """Test the parallel session manager"""
    print("⚡ Testing Parallel Session Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = ParallelSessionManager(session_id="test_parallel")
    
    # Register service sessions
    print("\n📝 Registering service sessions...")
    manager.register_service_session(ServiceType.CLAUDE, {"token": "mock_claude"}, 2)
    manager.register_service_session(ServiceType.GEMINI, {"token": "mock_gemini"}, 2)
    manager.register_service_session(ServiceType.PERPLEXITY, {"token": "mock_perplexity"}, 1)
    
    # Test parallel execution
    print("\n⚡ Testing parallel execution...")
    
    async def test_execution():
        execution = await manager.execute_parallel_request(
            "Extract information about AI trends",
            [ServiceType.CLAUDE, ServiceType.GEMINI],
            '{"trends": [], "summary": ""}',
            OutputFormat.JSON,
            ExecutionMode.PARALLEL,
            priority=3
        )
        
        print(f"✅ Execution completed!")
        print(f"   Success rate: {execution.success_rate:.1%}")
        print(f"   Execution time: {execution.execution_time:.2f}s")
        print(f"   Results: {len(execution.results)} services")
    
    # Run async test
    asyncio.run(test_execution())
    
    # Test analytics
    print("\n📊 Testing performance analytics...")
    analytics = manager.get_performance_analytics()
    print(f"✅ Analytics retrieved:")
    print(f"   Services tracked: {len(analytics['service_performance'])}")
    print(f"   Recommendations: {len(analytics['recommendations'])}")
    
    print(f"\n✅ ParallelSessionManager test completed!")


if __name__ == "__main__":
    main()