#!/usr/bin/env python3
"""
Samay v3 - Local LLM Integration
================================
Integration with Ollama Phi-3-Mini for confidential data processing
"""

import requests
import json
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class LocalLLMResponse:
    """Structure for local LLM responses"""
    success: bool
    response: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    model_name: str = ""
    tokens_generated: int = 0


class LocalLLMClient:
    """Client for communicating with local Ollama Phi-3-Mini model"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "phi3:mini"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api"
        
        print(f"🤖 Local LLM Client initialized")
        print(f"📍 Ollama URL: {base_url}")
        print(f"🧠 Model: {model}")
        
        # Test connection
        if self.is_available():
            print("✅ Local LLM connection successful")
        else:
            print("⚠️  Local LLM not available - check if Ollama is running")
    
    def is_available(self) -> bool:
        """Check if Ollama service is running and model is available"""
        try:
            # Check if service is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            return any(self.model in name for name in model_names)
        
        except Exception as e:
            print(f"❌ Local LLM availability check failed: {e}")
            return False
    
    def generate_response(self, prompt: str, system_prompt: str = None, 
                         max_tokens: int = 1000, temperature: float = 0.7) -> LocalLLMResponse:
        """
        Generate response from local Phi-3-Mini model
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
        """
        start_time = time.time()
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make request to Ollama API
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=60,
                headers={"Content-Type": "application/json"}
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                return LocalLLMResponse(
                    success=True,
                    response=result.get("response", "").strip(),
                    execution_time=execution_time,
                    model_name=self.model,
                    tokens_generated=result.get("eval_count", 0)
                )
            else:
                return LocalLLMResponse(
                    success=False,
                    error_message=f"HTTP {response.status_code}: {response.text}",
                    execution_time=execution_time,
                    model_name=self.model
                )
        
        except requests.exceptions.Timeout:
            return LocalLLMResponse(
                success=False,
                error_message="Request timeout (60s)",
                execution_time=time.time() - start_time,
                model_name=self.model
            )
        
        except Exception as e:
            return LocalLLMResponse(
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                model_name=self.model
            )
    
    def process_confidential_data(self, prompt: str, data_type: str = "general") -> LocalLLMResponse:
        """
        Process confidential data with appropriate system prompts
        
        Args:
            prompt: The confidential prompt to process
            data_type: Type of confidential processing needed
        """
        system_prompts = {
            "grammar": "You are an expert English grammar checker and editor. Correct grammar, spelling, and style while preserving the original meaning. Be concise and accurate.",
            "summarization": "You are a professional summarizer. Create clear, concise summaries that capture key points while maintaining confidentiality. Be objective and thorough.",
            "analysis": "You are a data analyst. Analyze the provided information objectively and provide insights while respecting confidentiality. Be analytical and precise.",
            "refinement": "You are an expert editor. Refine and improve the provided text for clarity, coherence, and impact while maintaining the original intent.",
            "general": "You are a helpful AI assistant focused on providing accurate, thoughtful responses while respecting privacy and confidentiality."
        }
        
        system_prompt = system_prompts.get(data_type, system_prompts["general"])
        
        print(f"🔒 Processing confidential {data_type} data locally")
        return self.generate_response(prompt, system_prompt)
    
    def validate_cloud_response(self, cloud_response: str, original_prompt: str) -> LocalLLMResponse:
        """
        Use local LLM to validate and potentially improve cloud service responses
        
        Args:
            cloud_response: Response from cloud AI service
            original_prompt: Original user prompt
        """
        validation_prompt = f"""
Please review this AI response for accuracy, completeness, and relevance to the original question.

Original Question: {original_prompt}

AI Response to Review: {cloud_response}

Provide feedback on:
1. Accuracy and factual correctness
2. Completeness of the answer
3. Relevance to the question
4. Any improvements or corrections needed

Keep your review concise but thorough.
"""
        
        system_prompt = "You are an expert AI response validator. Analyze AI responses critically and provide constructive feedback for improvement."
        
        print("🔍 Validating cloud response with local LLM")
        return self.generate_response(validation_prompt, system_prompt)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if self.model in model.get("name", ""):
                        return {
                            "name": model.get("name", ""),
                            "size": model.get("size", 0),
                            "modified": model.get("modified_at", ""),
                            "family": model.get("details", {}).get("family", ""),
                            "format": model.get("details", {}).get("format", "")
                        }
            return {}
        except Exception as e:
            print(f"❌ Failed to get model info: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on local LLM"""
        print("🏥 Local LLM Health Check")
        
        # Basic availability check
        available = self.is_available()
        
        # Test generation with simple prompt
        test_response = None
        if available:
            test_response = self.generate_response("Hello, please respond with 'OK' if you're working properly.")
        
        # Get model information
        model_info = self.get_model_info()
        
        return {
            "available": available,
            "model": self.model,
            "base_url": self.base_url,
            "test_response_success": test_response.success if test_response else False,
            "test_response_time": test_response.execution_time if test_response else 0,
            "model_info": model_info
        }


def main():
    """Test the local LLM client"""
    print("🚀 Samay v3 - Local LLM Client Test")
    print("=" * 50)
    
    # Initialize client
    client = LocalLLMClient()
    
    # Health check
    health = client.health_check()
    print(f"\n📊 Health Check Results:")
    print(f"   Available: {'✅' if health['available'] else '❌'}")
    print(f"   Model: {health['model']}")
    print(f"   Test Response: {'✅' if health['test_response_success'] else '❌'}")
    
    if health['test_response_time'] > 0:
        print(f"   Response Time: {health['test_response_time']:.2f}s")
    
    # Model info
    if health['model_info']:
        print(f"\n🧠 Model Information:")
        for key, value in health['model_info'].items():
            print(f"   {key.title()}: {value}")
    
    if not health['available']:
        print("\n❌ Local LLM not available. Make sure Ollama is running with phi3:mini model.")
        return
    
    # Interactive test
    print(f"\n🎛️  Test Options:")
    print("1. Basic chat test")
    print("2. Grammar correction test")
    print("3. Confidential data processing test")
    print("4. Cloud response validation test")
    
    choice = input("\nSelect test (1-4, or Enter to skip): ").strip()
    
    if choice == "1":
        prompt = input("Enter a question: ").strip()
        if prompt:
            response = client.generate_response(prompt)
            print(f"\n🤖 Response ({response.execution_time:.2f}s):")
            print(response.response if response.success else f"Error: {response.error_message}")
    
    elif choice == "2":
        text = input("Enter text to correct: ").strip()
        if text:
            response = client.process_confidential_data(text, "grammar")
            print(f"\n✏️  Grammar Correction ({response.execution_time:.2f}s):")
            print(response.response if response.success else f"Error: {response.error_message}")
    
    elif choice == "3":
        data = input("Enter confidential data to process: ").strip()
        if data:
            response = client.process_confidential_data(data, "analysis")
            print(f"\n🔒 Confidential Analysis ({response.execution_time:.2f}s):")
            print(response.response if response.success else f"Error: {response.error_message}")
    
    elif choice == "4":
        original = input("Enter original question: ").strip()
        cloud_resp = input("Enter cloud AI response to validate: ").strip()
        if original and cloud_resp:
            response = client.validate_cloud_response(cloud_resp, original)
            print(f"\n🔍 Validation Result ({response.execution_time:.2f}s):")
            print(response.response if response.success else f"Error: {response.error_message}")


if __name__ == "__main__":
    main()