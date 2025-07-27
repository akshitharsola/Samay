#!/usr/bin/env python3
"""
Samay v4 - macOS Automation Handler
===================================
macOS-specific automation using AppleScript and Accessibility APIs
"""

import time
import subprocess
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import AppKit
    import Quartz
    from AppKit import NSWorkspace, NSRunningApplication
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID
    MACOS_AVAILABLE = True
except ImportError:
    print("⚠️  macOS automation libraries not available. Install with: pip install pyobjc-framework-Quartz pyobjc-framework-ApplicationServices")
    MACOS_AVAILABLE = False

from ..base_automator import BaseDesktopAutomator, AutomationResult, AutomationStatus

class MacOSAutomator(BaseDesktopAutomator):
    """macOS-specific desktop automation using native APIs"""
    
    def __init__(self, service_id: str, config: Dict[str, Any]):
        super().__init__(service_id, config)
        self.app_bundle_path = None
        self.app_executable_path = None
        self.running_app = None
        
    def detect_app(self) -> bool:
        """Check if the desktop application is installed on macOS"""
        if not MACOS_AVAILABLE:
            return False
            
        executable_paths = self.config.get("executable_paths", {}).get("darwin", [])
        
        for path in executable_paths:
            path_obj = Path(path)
            if path_obj.exists():
                if path.endswith(".app"):
                    self.app_bundle_path = str(path_obj)
                    # Find the actual executable
                    app_name = path_obj.stem
                    executable = path_obj / "Contents" / "MacOS" / app_name
                    if executable.exists():
                        self.app_executable_path = str(executable)
                    else:
                        # Some apps might have different executable names
                        macos_dir = path_obj / "Contents" / "MacOS"
                        if macos_dir.exists():
                            executables = list(macos_dir.glob("*"))
                            if executables:
                                self.app_executable_path = str(executables[0])
                else:
                    self.app_executable_path = str(path_obj)
                    
                return True
        
        return False
    
    def launch_app(self) -> AutomationResult:
        """Launch the application using macOS methods"""
        start_time = time.time()
        
        try:
            if not self.detect_app():
                return AutomationResult(
                    status=AutomationStatus.APP_NOT_FOUND,
                    error_message="Application not found",
                    execution_time=time.time() - start_time
                )
            
            # Check if already running
            if self._is_app_running():
                print(f"✅ {self.service_id} is already running")
                return AutomationResult(
                    status=AutomationStatus.SUCCESS,
                    data="App already running",
                    execution_time=time.time() - start_time
                )
            
            print(f"🚀 Launching {self.service_id} using macOS APIs...")
            
            # Use NSWorkspace to launch the app
            workspace = NSWorkspace.sharedWorkspace()
            if self.app_bundle_path:
                # Launch .app bundle
                success = workspace.launchApplication_(self.app_bundle_path)
            else:
                # Launch executable directly
                success = workspace.launchApplication_(self.app_executable_path)
            
            if not success:
                return AutomationResult(
                    status=AutomationStatus.FAILED,
                    error_message="Failed to launch application via NSWorkspace",
                    execution_time=time.time() - start_time
                )
            
            # Wait for app to start
            timeout = self.config.get("lifecycle", {}).get("startup_timeout", 10)
            for _ in range(timeout):
                if self._is_app_running():
                    print(f"✅ {self.service_id} launched successfully")
                    return AutomationResult(
                        status=AutomationStatus.SUCCESS,
                        data="App launched successfully",
                        execution_time=time.time() - start_time
                    )
                time.sleep(1)
            
            return AutomationResult(
                status=AutomationStatus.TIMEOUT,
                error_message=f"App did not start within {timeout} seconds",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Launch failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _is_app_running(self) -> bool:
        """Check if the app is currently running"""
        if not MACOS_AVAILABLE:
            return False
            
        # Get app name from bundle path or executable
        if self.app_bundle_path:
            app_name = Path(self.app_bundle_path).stem
        else:
            app_name = Path(self.app_executable_path).name
        
        # Check running applications
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        for app in running_apps:
            if app.localizedName() == app_name or app.bundleIdentifier() and app_name.lower() in app.bundleIdentifier().lower():
                self.running_app = app
                return True
        
        return False
    
    def wait_for_ready(self, timeout: int = 30) -> AutomationResult:
        """Wait for the application to be ready for interaction"""
        start_time = time.time()
        
        try:
            for _ in range(timeout):
                if self._is_app_running():
                    # Additional checks can be added here
                    # For now, just verify the app is running
                    time.sleep(2)  # Give app time to fully load UI
                    return AutomationResult(
                        status=AutomationStatus.SUCCESS,
                        data="App is ready",
                        execution_time=time.time() - start_time
                    )
                time.sleep(1)
            
            return AutomationResult(
                status=AutomationStatus.TIMEOUT,
                error_message=f"App not ready within {timeout} seconds",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Wait for ready failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def send_prompt(self, prompt: str) -> AutomationResult:
        """Send prompt using AppleScript and accessibility"""
        start_time = time.time()
        
        try:
            if not self._is_app_running():
                return AutomationResult(
                    status=AutomationStatus.APP_NOT_FOUND,
                    error_message="App is not running",
                    execution_time=time.time() - start_time
                )
            
            # For now, use a simple AppleScript approach
            # This will be enhanced with proper accessibility APIs
            app_name = Path(self.app_bundle_path).stem if self.app_bundle_path else self.service_id
            
            # AppleScript to activate app and send text
            script = f'''
            tell application "{app_name}"
                activate
                delay 1
            end tell
            
            tell application "System Events"
                tell process "{app_name}"
                    -- Try to find and click the input field
                    try
                        -- Look for text field or text area
                        set inputField to first text field whose value is ""
                        click inputField
                        delay 0.5
                        keystroke "{prompt}"
                        delay 1
                        -- Try to find send button or use Enter
                        try
                            click button "Send"
                        on error
                            key code 36  -- Enter key
                        end try
                    on error
                        -- Fallback: just type and press enter
                        keystroke "{prompt}"
                        delay 1
                        key code 36  -- Enter key
                    end try
                end tell
            end tell
            '''
            
            # Execute AppleScript
            process = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if process.returncode == 0:
                return AutomationResult(
                    status=AutomationStatus.SUCCESS,
                    data="Prompt sent successfully",
                    execution_time=time.time() - start_time
                )
            else:
                return AutomationResult(
                    status=AutomationStatus.FAILED,
                    error_message=f"AppleScript failed: {process.stderr}",
                    execution_time=time.time() - start_time
                )
                
        except subprocess.TimeoutExpired:
            return AutomationResult(
                status=AutomationStatus.TIMEOUT,
                error_message="Prompt sending timed out",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Send prompt failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def extract_response(self, timeout: int = 30) -> AutomationResult:
        """Extract AI response using accessibility APIs"""
        start_time = time.time()
        
        try:
            if not self._is_app_running():
                return AutomationResult(
                    status=AutomationStatus.APP_NOT_FOUND,
                    error_message="App is not running",
                    execution_time=time.time() - start_time
                )
            
            # Wait for response to appear
            app_name = Path(self.app_bundle_path).stem if self.app_bundle_path else self.service_id
            
            # AppleScript to extract response text
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    try
                        -- Look for response text in various common containers
                        set responseText to ""
                        
                        -- Try to find text in static text elements
                        try
                            set staticTexts to every static text
                            repeat with staticText in staticTexts
                                set textValue to value of staticText
                                if length of textValue > 50 then
                                    set responseText to responseText & textValue & "\\n"
                                end if
                            end repeat
                        end try
                        
                        -- Try to find text in text areas
                        try
                            set textAreas to every text area
                            repeat with textArea in textAreas
                                set textValue to value of textArea
                                if length of textValue > 50 then
                                    set responseText to responseText & textValue & "\\n"
                                end if
                            end repeat
                        end try
                        
                        return responseText
                    on error
                        return "Error: Could not extract response"
                    end try
                end tell
            end tell
            '''
            
            # Poll for response with timeout
            for attempt in range(timeout):
                time.sleep(1)
                
                process = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if process.returncode == 0 and process.stdout.strip():
                    response_text = process.stdout.strip()
                    if len(response_text) > 10:  # Minimum response length
                        return AutomationResult(
                            status=AutomationStatus.SUCCESS,
                            data=response_text,
                            execution_time=time.time() - start_time
                        )
            
            return AutomationResult(
                status=AutomationStatus.TIMEOUT,
                error_message=f"No response extracted within {timeout} seconds",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Extract response failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def close_app(self) -> AutomationResult:
        """Gracefully close the application"""
        start_time = time.time()
        
        try:
            if not self._is_app_running():
                return AutomationResult(
                    status=AutomationStatus.SUCCESS,
                    data="App was not running",
                    execution_time=time.time() - start_time
                )
            
            if self.running_app:
                # Use NSRunningApplication to terminate
                success = self.running_app.terminate()
                
                if success:
                    # Wait for app to close
                    timeout = self.config.get("lifecycle", {}).get("shutdown_timeout", 5)
                    for _ in range(timeout):
                        if not self._is_app_running():
                            return AutomationResult(
                                status=AutomationStatus.SUCCESS,
                                data="App closed successfully",
                                execution_time=time.time() - start_time
                            )
                        time.sleep(1)
                    
                    # Force kill if needed
                    self.running_app.forceTerminate()
                    
                return AutomationResult(
                    status=AutomationStatus.SUCCESS,
                    data="App closed (forced)",
                    execution_time=time.time() - start_time
                )
            else:
                return AutomationResult(
                    status=AutomationStatus.FAILED,
                    error_message="No running app reference",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Close app failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def capture_screenshot(self, name: str = "screenshot") -> Optional[str]:
        """Capture a screenshot for debugging"""
        try:
            timestamp = int(time.time())
            screenshot_path = f"logs/screenshots/{self.service_id}_{name}_{timestamp}.png"
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            
            # Use macOS screencapture command
            subprocess.run(["screencapture", screenshot_path], check=True)
            
            return screenshot_path
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return None