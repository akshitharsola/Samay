#!/usr/bin/env python3
"""
Samay v4 - Desktop Service Manager
==================================
Manages lifecycle and coordination of desktop AI applications
"""

import os
import sys
import time
import subprocess
import platform
import yaml

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - some process monitoring features disabled")
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class ServiceStatus(Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    RUNNING = "running"
    READY = "ready"
    ERROR = "error"

@dataclass
class ServiceInfo:
    name: str
    type: str
    status: ServiceStatus
    pid: Optional[int] = None
    executable_path: Optional[str] = None
    error_message: Optional[str] = None
    last_health_check: Optional[float] = None

class DesktopServiceManager:
    """Manages desktop AI service applications lifecycle and health"""
    
    def __init__(self, config_path: str = "config/desktop_services.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.platform = platform.system().lower()
        self.services: Dict[str, ServiceInfo] = {}
        
        # Initialize service status
        self._initialize_services()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load desktop services configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback configuration if config file is missing"""
        return {
            "services": {
                "claude": {
                    "name": "Claude Desktop",
                    "type": "desktop_app",
                    "enabled": True,
                    "executable_paths": {
                        "windows": ["C:/Users/{user}/AppData/Local/Claude/Claude.exe"],
                        "darwin": ["/Applications/Claude.app"],  # macOS
                        "linux": ["/opt/claude/claude"]
                    }
                },
                "perplexity": {
                    "name": "Perplexity Desktop", 
                    "type": "desktop_app",
                    "enabled": True,
                    "executable_paths": {
                        "windows": ["C:/Users/{user}/AppData/Local/Perplexity/Perplexity.exe"],
                        "darwin": ["/Applications/Perplexity.app"],
                        "linux": ["/opt/perplexity/perplexity"]
                    }
                }
            }
        }
    
    def _initialize_services(self):
        """Initialize service status tracking"""
        for service_id, service_config in self.config.get("services", {}).items():
            if not service_config.get("enabled", True):
                continue
                
            self.services[service_id] = ServiceInfo(
                name=service_config.get("name", service_id),
                type=service_config.get("type", "desktop_app"),
                status=ServiceStatus.NOT_INSTALLED
            )
    
    def detect_installed_apps(self) -> Dict[str, bool]:
        """Check which AI service desktop apps are installed"""
        detection_results = {}
        
        for service_id, service_info in self.services.items():
            try:
                executable_path = self._find_executable(service_id)
                if executable_path:
                    service_info.status = ServiceStatus.INSTALLED
                    service_info.executable_path = executable_path
                    detection_results[service_id] = True
                    print(f"✅ {service_info.name} found at: {executable_path}")
                else:
                    service_info.status = ServiceStatus.NOT_INSTALLED
                    detection_results[service_id] = False
                    print(f"❌ {service_info.name} not found")
                    
            except Exception as e:
                service_info.status = ServiceStatus.ERROR
                service_info.error_message = str(e)
                detection_results[service_id] = False
                print(f"❌ Error detecting {service_info.name}: {e}")
        
        return detection_results
    
    def _find_executable(self, service_id: str) -> Optional[str]:
        """Find the executable path for a service"""
        service_config = self.config["services"].get(service_id, {})
        executable_paths = service_config.get("executable_paths", {})
        
        # Get platform-specific paths
        platform_paths = executable_paths.get(self.platform, [])
        if not platform_paths:
            return None
        
        # Expand user placeholders
        username = os.getenv("USER") or os.getenv("USERNAME") or "user"
        
        for path_template in platform_paths:
            path = path_template.format(user=username)
            path_obj = Path(path)
            
            # Check if executable exists
            if path_obj.exists():
                # For macOS apps, check if it's actually executable
                if self.platform == "darwin" and path.endswith(".app"):
                    # For .app bundles, look for the actual executable inside
                    app_name = path_obj.stem
                    executable = path_obj / "Contents" / "MacOS" / app_name
                    if executable.exists():
                        return str(executable)
                    else:
                        return str(path_obj)  # Return .app path anyway
                else:
                    return str(path_obj)
        
        return None
    
    def launch_app(self, service_id: str) -> bool:
        """Start a desktop application"""
        if service_id not in self.services:
            print(f"❌ Unknown service: {service_id}")
            return False
        
        service_info = self.services[service_id]
        
        # Check if already running
        if self.is_app_running(service_id):
            print(f"✅ {service_info.name} is already running")
            return True
        
        # Check if installed
        if service_info.status == ServiceStatus.NOT_INSTALLED:
            print(f"❌ {service_info.name} is not installed")
            return False
        
        try:
            executable_path = service_info.executable_path
            if not executable_path:
                print(f"❌ No executable path for {service_info.name}")
                return False
            
            print(f"🚀 Launching {service_info.name}...")
            
            # Launch the application
            if self.platform == "darwin":  # macOS
                # Use 'open' command for .app bundles
                if executable_path.endswith(".app"):
                    process = subprocess.Popen(["open", executable_path])
                else:
                    process = subprocess.Popen([executable_path])
            else:  # Windows/Linux
                process = subprocess.Popen([executable_path])
            
            # Wait a moment for the app to start
            time.sleep(2)
            
            # Check if process is running
            if self.is_app_running(service_id):
                service_info.status = ServiceStatus.RUNNING
                print(f"✅ {service_info.name} launched successfully")
                return True
            else:
                print(f"❌ Failed to launch {service_info.name}")
                return False
                
        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            print(f"❌ Error launching {service_info.name}: {e}")
            return False
    
    def is_app_running(self, service_id: str) -> bool:
        """Check if a desktop app is currently running"""
        if service_id not in self.services:
            return False
        
        service_config = self.config["services"].get(service_id, {})
        process_names = service_config.get("process_names", {})
        platform_processes = process_names.get(self.platform, [])
        
        if not platform_processes:
            # Fallback: use executable name
            executable_path = self.services[service_id].executable_path
            if executable_path:
                platform_processes = [Path(executable_path).name]
        
        # Check running processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name']
                for target_name in platform_processes:
                    if proc_name.lower() == target_name.lower():
                        self.services[service_id].pid = proc.info['pid']
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
    
    def close_app(self, service_id: str) -> bool:
        """Gracefully close a desktop application"""
        if service_id not in self.services:
            return False
        
        service_info = self.services[service_id]
        
        if not self.is_app_running(service_id):
            print(f"✅ {service_info.name} is not running")
            return True
        
        try:
            if service_info.pid:
                # Try graceful shutdown first
                process = psutil.Process(service_info.pid)
                process.terminate()
                
                # Wait for graceful shutdown
                timeout = self.config.get("automation_settings", {}).get("delays", {}).get("shutdown_timeout", 5)
                process.wait(timeout=timeout)
                
                print(f"✅ {service_info.name} closed gracefully")
            
            service_info.status = ServiceStatus.INSTALLED
            service_info.pid = None
            return True
            
        except psutil.TimeoutExpired:
            # Force kill if graceful shutdown fails
            try:
                process.kill()
                print(f"⚠️  {service_info.name} force-killed")
                return True
            except:
                pass
        except Exception as e:
            print(f"❌ Error closing {service_info.name}: {e}")
        
        return False
    
    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get detailed status information for a service"""
        if service_id not in self.services:
            return {"error": f"Unknown service: {service_id}"}
        
        service_info = self.services[service_id]
        
        return {
            "name": service_info.name,
            "type": service_info.type,
            "status": service_info.status.value,
            "installed": service_info.status != ServiceStatus.NOT_INSTALLED,
            "running": self.is_app_running(service_id),
            "pid": service_info.pid,
            "executable_path": service_info.executable_path,
            "error_message": service_info.error_message,
            "last_health_check": service_info.last_health_check
        }
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all configured services"""
        return {
            service_id: self.get_service_status(service_id)
            for service_id in self.services.keys()
        }
    
    def health_check(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform health check on services"""
        if service_id:
            services_to_check = [service_id] if service_id in self.services else []
        else:
            services_to_check = list(self.services.keys())
        
        results = {}
        
        for svc_id in services_to_check:
            try:
                # Update installation status
                executable_path = self._find_executable(svc_id)
                if executable_path:
                    self.services[svc_id].executable_path = executable_path
                    self.services[svc_id].status = ServiceStatus.INSTALLED
                else:
                    self.services[svc_id].status = ServiceStatus.NOT_INSTALLED
                
                # Update running status
                if self.is_app_running(svc_id):
                    self.services[svc_id].status = ServiceStatus.RUNNING
                
                # Record health check time
                self.services[svc_id].last_health_check = time.time()
                
                results[svc_id] = self.get_service_status(svc_id)
                
            except Exception as e:
                self.services[svc_id].status = ServiceStatus.ERROR
                self.services[svc_id].error_message = str(e)
                results[svc_id] = self.get_service_status(svc_id)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all services"""
        all_status = self.get_all_services_status()
        
        total_services = len(all_status)
        installed_services = sum(1 for s in all_status.values() if s["installed"])
        running_services = sum(1 for s in all_status.values() if s["running"])
        
        return {
            "total_services": total_services,
            "installed_services": installed_services,
            "running_services": running_services,
            "services": all_status,
            "platform": self.platform,
            "config_loaded": bool(self.config)
        }


def main():
    """Test the desktop service manager"""
    print("🔍 Testing Samay v4 Desktop Service Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = DesktopServiceManager()
    
    # Detect installed apps
    print("\n1. Detecting installed applications...")
    installed = manager.detect_installed_apps()
    
    # Show summary
    print("\n2. Service summary:")
    summary = manager.get_summary()
    print(f"Platform: {summary['platform']}")
    print(f"Total services: {summary['total_services']}")
    print(f"Installed: {summary['installed_services']}")
    print(f"Running: {summary['running_services']}")
    
    # Show detailed status
    print("\n3. Detailed service status:")
    for service_id, status in summary["services"].items():
        print(f"   {status['name']}: {status['status']}")
        if status.get("executable_path"):
            print(f"      Path: {status['executable_path']}")
        if status.get("error_message"):
            print(f"      Error: {status['error_message']}")
    
    # Test launching the first available service
    print("\n4. Testing service launch...")
    for service_id, status in summary["services"].items():
        if status["installed"] and not status["running"]:
            print(f"Attempting to launch {status['name']}...")
            success = manager.launch_app(service_id)
            if success:
                print(f"✅ Successfully launched {status['name']}")
                time.sleep(3)  # Let it run briefly
                manager.close_app(service_id)
                print(f"✅ Successfully closed {status['name']}")
            break
    else:
        print("No available services to test launch")


if __name__ == "__main__":
    main()