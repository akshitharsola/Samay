#!/usr/bin/env python3
"""
Samay v4 - Base Desktop Automator
=================================
Abstract interface for desktop application automation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AutomationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    APP_NOT_FOUND = "app_not_found"
    ELEMENT_NOT_FOUND = "element_not_found"

@dataclass
class AutomationResult:
    status: AutomationStatus
    data: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    screenshots: Optional[list] = None

class BaseDesktopAutomator(ABC):
    """Abstract base class for desktop application automation"""
    
    def __init__(self, service_id: str, config: Dict[str, Any]):
        self.service_id = service_id
        self.config = config
        self.app_process = None
        self.automation_interface = None
    
    @abstractmethod
    def detect_app(self) -> bool:
        """Check if the desktop application is installed and accessible"""
        pass
    
    @abstractmethod
    def launch_app(self) -> AutomationResult:
        """Start the desktop application and prepare for automation"""
        pass
    
    @abstractmethod
    def wait_for_ready(self, timeout: int = 30) -> AutomationResult:
        """Wait for the application to be ready for interaction"""
        pass
    
    @abstractmethod
    def send_prompt(self, prompt: str) -> AutomationResult:
        """Submit a prompt to the application"""
        pass
    
    @abstractmethod
    def extract_response(self, timeout: int = 30) -> AutomationResult:
        """Extract the AI response from the application"""
        pass
    
    @abstractmethod
    def close_app(self) -> AutomationResult:
        """Gracefully close the application"""
        pass
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get information about the application state"""
        return {
            "service_id": self.service_id,
            "app_running": self.app_process is not None,
            "automation_ready": self.automation_interface is not None,
            "config": self.config
        }
    
    def capture_screenshot(self, name: str = "screenshot") -> Optional[str]:
        """Capture a screenshot for debugging purposes"""
        # Implementation will be added in platform-specific classes
        pass
    
    def health_check(self) -> AutomationResult:
        """Perform a basic health check of the application"""
        try:
            if not self.detect_app():
                return AutomationResult(
                    status=AutomationStatus.APP_NOT_FOUND,
                    error_message="Application not detected"
                )
            
            # Basic launch and close test
            launch_result = self.launch_app()
            if launch_result.status != AutomationStatus.SUCCESS:
                return launch_result
            
            close_result = self.close_app()
            return close_result
            
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Health check failed: {str(e)}"
            )