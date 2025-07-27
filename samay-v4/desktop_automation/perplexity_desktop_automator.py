#!/usr/bin/env python3
"""
Samay v4 - Perplexity Desktop Automator
=======================================
Specialized automation for Perplexity desktop application (App Store version)
"""

import time
import platform
import subprocess
from typing import Dict, Any, Optional

from .base_automator import BaseDesktopAutomator, AutomationResult, AutomationStatus

# Import platform-specific handlers
system = platform.system().lower()
if system == "darwin":
    from .platform_handlers.macos_automation import MacOSAutomator
    PlatformAutomator = MacOSAutomator
elif system == "windows":
    # TODO: Implement Windows automation
    PlatformAutomator = None
elif system == "linux":
    # TODO: Implement Linux automation
    PlatformAutomator = None
else:
    PlatformAutomator = None

class PerplexityDesktopAutomator(BaseDesktopAutomator):
    """Specialized automator for Perplexity desktop application"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("perplexity", config)
        
        # Initialize platform-specific automator
        if PlatformAutomator is None:
            raise NotImplementedError(f"Platform {system} not supported yet")
        
        self.platform_automator = PlatformAutomator("perplexity", config)
        
        # Perplexity-specific configuration
        self.input_selectors = config.get("automation", {}).get("selectors", {}).get("input_fallback", [])
        self.submit_selectors = config.get("automation", {}).get("selectors", {}).get("submit_fallback", [])
        self.response_selectors = config.get("automation", {}).get("selectors", {}).get("response_fallback", [])
        
    def detect_app(self) -> bool:
        """Check if Perplexity desktop app is installed"""
        return self.platform_automator.detect_app()
    
    def launch_app(self) -> AutomationResult:
        """Launch Perplexity desktop application"""
        print(f"🚀 Starting Perplexity desktop automation...")
        
        result = self.platform_automator.launch_app()
        if result.status == AutomationStatus.SUCCESS:
            # Wait for Perplexity to be ready
            ready_result = self.wait_for_ready()
            if ready_result.status != AutomationStatus.SUCCESS:
                return ready_result
        
        return result
    
    def wait_for_ready(self, timeout: int = 30) -> AutomationResult:
        """Wait for Perplexity to be ready for interaction"""
        print(f"⏳ Waiting for Perplexity to be ready...")
        
        # Use platform automator first
        result = self.platform_automator.wait_for_ready(timeout)
        
        if result.status == AutomationStatus.SUCCESS:
            # Perplexity-specific readiness - just add delay for UI stabilization
            time.sleep(3)
            print(f"✅ Perplexity is ready for interaction")
        
        return result
    
    def send_prompt(self, prompt: str) -> AutomationResult:
        """Send a prompt to Perplexity with Perplexity-specific optimizations"""
        print(f"📝 Sending prompt to Perplexity: {prompt[:50]}...")
        
        # Add Perplexity-specific prompt processing if needed
        processed_prompt = self._process_prompt_for_perplexity(prompt)
        
        result = self.platform_automator.send_prompt(processed_prompt)
        
        if result.status == AutomationStatus.SUCCESS:
            print(f"✅ Prompt sent to Perplexity successfully")
        else:
            print(f"❌ Failed to send prompt to Perplexity: {result.error_message}")
        
        return result
    
    def extract_response(self, timeout: int = 30) -> AutomationResult:
        """Extract Perplexity's response with Perplexity-specific parsing"""
        print(f"📥 Waiting for Perplexity's response...")
        
        result = self.platform_automator.extract_response(timeout)
        
        if result.status == AutomationStatus.SUCCESS and result.data:
            # Apply Perplexity-specific response processing
            processed_response = self._process_perplexity_response(result.data)
            result.data = processed_response
            print(f"✅ Received response from Perplexity ({len(processed_response)} chars)")
        else:
            print(f"❌ Failed to get response from Perplexity: {result.error_message}")
        
        return result
    
    def close_app(self) -> AutomationResult:
        """Close Perplexity desktop application"""
        print(f"🔒 Closing Perplexity desktop...")
        
        result = self.platform_automator.close_app()
        
        if result.status == AutomationStatus.SUCCESS:
            print(f"✅ Perplexity closed successfully")
        else:
            print(f"⚠️  Issues closing Perplexity: {result.error_message}")
        
        return result
    
    def _process_prompt_for_perplexity(self, prompt: str) -> str:
        """Apply Perplexity-specific prompt processing"""
        # Add any Perplexity-specific prompt formatting
        # Perplexity works well with direct questions
        
        # For now, just return the prompt as-is
        # TODO: Add machine code template integration here if needed
        return prompt
    
    def _process_perplexity_response(self, response: str) -> str:
        """Apply Perplexity-specific response processing"""
        # Clean up response text
        cleaned_response = response.strip()
        
        # Remove common Perplexity UI artifacts if present
        artifacts_to_remove = [
            "Perplexity",
            "Copy to clipboard",
            "Share",
            "Sources:",
            "Related questions"
        ]
        
        for artifact in artifacts_to_remove:
            if cleaned_response.startswith(artifact):
                # Remove artifact if it's at the beginning
                lines = cleaned_response.split('\n')
                if lines[0].strip() == artifact:
                    cleaned_response = '\n'.join(lines[1:]).strip()
        
        return cleaned_response
    
    def perform_query(self, prompt: str, timeout: int = 60) -> AutomationResult:
        """Perform a complete query cycle: send prompt and get response"""
        start_time = time.time()
        
        try:
            print(f"🔄 Starting complete Perplexity query cycle...")
            
            # Step 1: Ensure app is running
            if not self.platform_automator._is_app_running():
                launch_result = self.launch_app()
                if launch_result.status != AutomationStatus.SUCCESS:
                    return launch_result
            
            # Step 2: Send prompt
            send_result = self.send_prompt(prompt)
            if send_result.status != AutomationStatus.SUCCESS:
                return send_result
            
            # Step 3: Extract response
            response_result = self.extract_response(timeout)
            if response_result.status != AutomationStatus.SUCCESS:
                return response_result
            
            execution_time = time.time() - start_time
            print(f"✅ Perplexity query completed in {execution_time:.1f}s")
            
            return AutomationResult(
                status=AutomationStatus.SUCCESS,
                data=response_result.data,
                execution_time=execution_time
            )
            
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Query cycle failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def health_check(self) -> AutomationResult:
        """Perform Perplexity-specific health check"""
        print(f"🏥 Running Perplexity health check...")
        
        try:
            # Basic detection
            if not self.detect_app():
                return AutomationResult(
                    status=AutomationStatus.APP_NOT_FOUND,
                    error_message="Perplexity desktop app not found"
                )
            
            # Test launch and close
            launch_result = self.launch_app()
            if launch_result.status != AutomationStatus.SUCCESS:
                return launch_result
            
            # Wait a moment
            time.sleep(2)
            
            # Test close
            close_result = self.close_app()
            
            print(f"✅ Perplexity health check completed")
            return close_result
            
        except Exception as e:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                error_message=f"Health check failed: {str(e)}"
            )


def main():
    """Test Perplexity desktop automation"""
    print("🧪 Testing Perplexity Desktop Automation")
    print("=" * 50)
    
    # Load config (simplified for testing)
    config = {
        "executable_paths": {
            "darwin": ["/Applications/Perplexity.app"]
        },
        "automation": {
            "selectors": {
                "input_fallback": [],
                "submit_fallback": [],
                "response_fallback": []
            }
        },
        "lifecycle": {
            "startup_timeout": 10,
            "shutdown_timeout": 5
        }
    }
    
    try:
        # Initialize automator
        automator = PerplexityDesktopAutomator(config)
        
        # Test detection
        print("\n1. Testing app detection...")
        if automator.detect_app():
            print("✅ Perplexity detected successfully")
        else:
            print("❌ Perplexity not detected")
            return
        
        # Test health check
        print("\n2. Running health check...")
        health_result = automator.health_check()
        print(f"Health check result: {health_result.status.value}")
        if health_result.error_message:
            print(f"Error: {health_result.error_message}")
        
        # Test basic query (if user wants to test)
        print("\n3. Test query available - run manually if desired")
        print("To test a query, modify the main() function to include:")
        print('query_result = automator.perform_query("What is artificial intelligence?")')
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()