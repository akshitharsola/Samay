# 🏗️ Samay v6 Architecture Documentation

## System Overview

Samay v6 implements a **Browser Extension + Web App hybrid architecture** to achieve cross-domain AI service automation while maintaining zero API costs.

## Component Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web App       │◄──►│ Browser Extension │◄──►│ AI Services     │
│                 │    │                  │    │                 │
│ • React UI      │    │ • Tab Management │    │ • ChatGPT       │
│ • FastAPI       │    │ • Script Inject  │    │ • Claude        │
│ • Local LLM     │    │ • Response Monitor│   │ • Gemini        │
│ • Synthesis     │    │ • Content Extract │    │ • Perplexity    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Data Flow

### 1. Query Initiation
```
User Input → React UI → FastAPI Backend → Extension Message
```

### 2. Automation Execution  
```
Extension → Open Tabs → Inject Scripts → Monitor Responses → Extract Content
```

### 3. Intelligence Processing
```
Raw Responses → Local LLM Analysis → Follow-up Decision → Synthesis Engine
```

### 4. Result Delivery
```
Synthesized Response → React UI → User Display
```

## Component Details

### Web Application Layer

#### Frontend (React)
- **Location**: `web-app/frontend/`
- **Purpose**: User interface and interaction
- **Key Components**:
  - `QueryInput.js`: Clean query input interface
  - `AutomationStatus.js`: Real-time progress tracking
  - `ResponseViewer.js`: Multi-service response display
  - `ExtensionConnector.js`: Extension communication handler

#### Backend (FastAPI)
- **Location**: `web-app/backend/`
- **Purpose**: Local processing and orchestration
- **Key Modules**:
  - `main.py`: Server entry point and routing
  - `core/local_assistant.py`: Ollama integration
  - `core/synthesis_engine.py`: Response combination
  - `core/followup_analyzer.py`: Intelligence analysis

### Browser Extension Layer

#### Extension Core
- **Location**: `extension/`
- **Purpose**: Cross-domain automation engine
- **Architecture**: Manifest V3 service worker pattern

#### Key Components
```javascript
// background.js - Main orchestrator
class AutomationOrchestrator {
  async handleAutomationRequest(query, options) {
    // 1. Open AI service tabs
    const tabs = await this.openAllServiceTabs();
    
    // 2. Inject automation scripts  
    await this.injectScriptsToAllTabs(tabs, query);
    
    // 3. Monitor for responses
    const responses = await this.monitorAllResponses(tabs);
    
    // 4. Send back to web app
    return this.sendResponsesToWebApp(responses);
  }
}
```

### Communication Protocol

#### Message Types
```javascript
// Web App → Extension
{
  action: "startAutomation",
  query: "user query text", 
  sessionId: "unique_session_id",
  options: {
    followUps: true,
    services: ["chatgpt", "claude", "gemini", "perplexity"]
  }
}

// Extension → Web App  
{
  action: "automationProgress",
  sessionId: "unique_session_id",
  status: "injecting|monitoring|extracting|complete",
  progress: {
    chatgpt: "complete",
    claude: "monitoring", 
    gemini: "injecting",
    perplexity: "pending"
  }
}
```

#### API Endpoints
```python
# FastAPI Backend Routes
@app.post("/api/automation/start")
async def start_automation(request: AutomationRequest)

@app.get("/api/automation/status/{session_id}")  
async def get_automation_status(session_id: str)

@app.post("/api/synthesis/generate")
async def generate_synthesis(responses: List[ServiceResponse])

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str)
```

## Service Integration Architecture

### Service Configuration System
```javascript
const serviceConfigs = {
  chatgpt: {
    url: "https://chat.openai.com/",
    selectors: {
      input: "textarea[data-id='root']",
      send_button: "button[data-testid='send-button']", 
      response_area: "div[data-message-author-role='assistant']",
      loading_indicator: ".result-thinking"
    },
    timing: {
      injection_delay: 2000,
      typing_speed: 15, // chars/sec
      response_timeout: 60000
    }
  },
  // ... other service configs
};
```

### Automation Script Injection
```javascript
// Universal injection pattern
async function injectScript(tabId, serviceName, query) {
  await chrome.scripting.executeScript({
    target: { tabId },
    func: (query, config) => {
      // Find input element
      const input = document.querySelector(config.selectors.input);
      
      // Simulate human typing
      let index = 0;
      function typeChar() {
        if (index < query.length) {
          input.value += query[index++];
          input.dispatchEvent(new Event('input', {bubbles: true}));
          setTimeout(typeChar, 1000 / config.timing.typing_speed);
        } else {
          // Submit query
          document.querySelector(config.selectors.send_button).click();
        }
      }
      
      setTimeout(typeChar, config.timing.injection_delay);
    },
    args: [query, serviceConfigs[serviceName]]
  });
}
```

## Intelligence Layer Architecture

### Local LLM Integration
```python
# core/local_assistant.py
class LocalAssistant:
    def __init__(self):
        self.ollama_client = ollama.Client()
        self.model = "phi3:mini"
    
    async def analyze_responses(self, responses: Dict[str, str]) -> AnalysisResult:
        prompt = f"""
        Analyze these AI service responses:
        ChatGPT: {responses['chatgpt']}
        Claude: {responses['claude']}
        Gemini: {responses['gemini']}
        Perplexity: {responses['perplexity']}
        
        Determine if follow-up questions would improve response quality.
        """
        
        result = await self.ollama_client.generate(
            model=self.model,
            prompt=prompt
        )
        
        return self.parse_analysis(result.response)
```

### Follow-up Question Generation
```python
# core/followup_analyzer.py
class FollowupAnalyzer:
    async def generate_followups(self, responses: Dict) -> Dict[str, str]:
        analysis = await self.analyze_completeness(responses)
        
        if analysis.needs_followup:
            return {
                "chatgpt": self.generate_general_followup(analysis),
                "claude": self.generate_analytical_followup(analysis),
                "gemini": self.generate_technical_followup(analysis), 
                "perplexity": self.generate_research_followup(analysis)
            }
        
        return {}
```

### Response Synthesis
```python
# core/synthesis_engine.py  
class SynthesisEngine:
    async def synthesize_responses(self, original: Dict, followups: Dict = None) -> str:
        synthesis_prompt = self.build_synthesis_prompt(original, followups)
        
        synthesis = await self.local_llm.generate(synthesis_prompt)
        
        return self.format_final_response(synthesis, original, followups)
    
    def format_final_response(self, synthesis: str, original: Dict, followups: Dict) -> str:
        return f"""
        🎯 COMPREHENSIVE AI ANALYSIS
        
        {synthesis}
        
        📊 SOURCE ATTRIBUTION:
        💎 ChatGPT: {len(original['chatgpt'].split())} words
        🧠 Claude: {len(original['claude'].split())} words  
        🔍 Gemini: {len(original['gemini'].split())} words
        📡 Perplexity: {len(original['perplexity'].split())} words
        
        {self.format_followups(followups) if followups else ""}
        """
```

## Security Architecture

### Extension Permissions Model
```json
// manifest.json security configuration
{
  "permissions": [
    "scripting",     // Required for script injection
    "tabs",          // Required for tab management  
    "storage",       // Required for preferences
    "activeTab"      // Required for current tab access
  ],
  "host_permissions": [
    "https://chat.openai.com/*",
    "https://claude.ai/*",
    "https://gemini.google.com/*", 
    "https://www.perplexity.ai/*"
  ],
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### Data Privacy Architecture
- **No External APIs**: All processing happens locally
- **No Data Persistence**: Conversations deleted after synthesis
- **Local LLM**: All analysis done on user's machine
- **Extension Isolation**: Scripts run in isolated contexts

## Performance Architecture

### Optimization Strategies
```javascript
// Concurrent automation execution
class ConcurrentAutomation {
  async automateAllServices(query) {
    const tasks = [
      this.automateService('chatgpt', query),
      this.automateService('claude', query),
      this.automateService('gemini', query), 
      this.automateService('perplexity', query)
    ];
    
    // Execute in parallel for maximum speed
    const responses = await Promise.allSettled(tasks);
    
    return this.processResponses(responses);
  }
}
```

### Resource Management
- **Memory Optimization**: Cleanup tabs after automation
- **CPU Efficiency**: Throttled automation to prevent browser overload
- **Network Minimal**: Only local communication between components

## Error Handling Architecture

### Resilience Patterns
```javascript
// Graceful degradation
class ErrorHandler {
  async handleServiceFailure(serviceName, error) {
    console.error(`${serviceName} automation failed:`, error);
    
    // Try alternative approach
    if (error.type === 'injection_failed') {
      return await this.retryWithAlternativeSelectors(serviceName);
    }
    
    if (error.type === 'response_timeout') {
      return await this.handlePartialResponse(serviceName);
    }
    
    // Ultimate fallback
    return {
      service: serviceName,
      status: 'failed',
      content: `${serviceName} automation failed: ${error.message}`,
      fallback: true
    };
  }
}
```

## Deployment Architecture

### Development Environment
```bash
# Multi-process development setup
Process 1: FastAPI Backend (port 8000)
Process 2: React Frontend (port 3000)  
Process 3: Ollama Service (port 11434)
Process 4: Chrome Extension (loaded unpacked)
```

### Production Considerations
- **Extension Distribution**: Chrome Web Store or manual installation
- **Local Deployment**: All components run on user's machine
- **No Server Dependencies**: Completely self-contained system
- **Cross-Platform**: Works on macOS, Windows, Linux (with Chrome)

## Monitoring & Observability

### Logging Architecture
```python
# Structured logging system
import logging
import json

class StructuredLogger:
    def log_automation_event(self, event_type: str, data: Dict):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "session_id": data.get("session_id"),
            "service": data.get("service"),
            "status": data.get("status"),
            "duration": data.get("duration"),
            "error": data.get("error")
        }
        
        logging.info(json.dumps(log_entry))
```

### Performance Metrics
- **Automation Success Rate**: Per-service tracking
- **Response Time Distribution**: Latency analysis  
- **Error Rate Monitoring**: Failure pattern detection
- **Resource Usage Tracking**: Memory and CPU utilization

This architecture enables true multi-AI automation while maintaining security, performance, and reliability standards.