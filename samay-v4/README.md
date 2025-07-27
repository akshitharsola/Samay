# Samay v4 - Desktop-First Multi-Agent AI Assistant
*Next-generation implementation using native desktop application automation*

## 🎯 **V4 Key Improvements**

### **Strategy Shift: Desktop-First Approach**
- **Claude**: Official desktop app automation (Electron-based)
- **Perplexity**: Official desktop app automation  
- **Gemini**: PWA wrapper automation (since no native app exists)
- **Local LLM**: Continues with Ollama integration

### **Core Advantages Over V3**
1. **UI Stability**: Desktop apps update less frequently than web interfaces
2. **Better Automation**: Native system APIs vs brittle DOM selectors
3. **Stealth**: Native automation vs detectable browser automation
4. **Performance**: Direct app interaction vs browser overhead
5. **Reliability**: Fixed app versions vs changing web UIs

## 📁 **Project Structure**

```
samay-v4/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies  
├── config/
│   ├── desktop_services.yaml         # Desktop app configurations
│   ├── automation_settings.yaml      # Platform-specific automation settings
│   └── response_processing.yaml      # JSON parsing and synthesis rules
├── orchestrator/
│   ├── session_manager.py            # Main coordinator (from v3)
│   ├── desktop_service_manager.py    # Desktop app detection and lifecycle
│   ├── response_processor.py         # JSON extraction and synthesis
│   └── local_llm_client.py          # Ollama integration (from v3)
├── desktop_automation/
│   ├── __init__.py
│   ├── base_automator.py             # Abstract automation interface
│   ├── claude_desktop_automator.py   # Claude desktop app automation
│   ├── perplexity_desktop_automator.py # Perplexity desktop app automation
│   ├── gemini_pwa_automator.py       # Gemini PWA automation
│   ├── platform_handlers/
│   │   ├── windows_automation.py     # Windows UI Automation API
│   │   ├── macos_automation.py       # macOS Accessibility API  
│   │   └── electron_automation.py    # Electron/CDP automation
│   └── utils/
│       ├── app_detector.py           # Detect installed desktop apps
│       ├── process_manager.py        # Launch and monitor app processes
│       └── screen_utils.py           # Screenshot and OCR fallbacks
├── frontend/                         # React frontend (simplified from v3)
│   ├── src/
│   │   ├── components/
│   │   │   ├── DesktopServiceStatus.js # Show desktop app status
│   │   │   ├── QueryInterface.js     # Simplified query interface
│   │   │   └── ResponseDisplay.js    # Improved response rendering
│   │   └── App.js                    # Main application
│   └── package.json
├── tests/
│   ├── test_desktop_automation.py    # Desktop automation tests
│   ├── test_response_processing.py   # JSON processing tests
│   └── integration_tests.py          # End-to-end tests
├── logs/                             # Application logs
└── docs/
    ├── DESKTOP_SETUP.md              # Desktop app installation guide
    ├── AUTOMATION_GUIDE.md           # Platform-specific automation setup
    └── MIGRATION_FROM_V3.md          # Migration guide from v3
```

## 🚀 **Implementation Strategy**

### **Phase 1: Core Desktop Automation (Week 1)**
1. **Desktop Service Manager**: Detect and launch desktop apps
2. **Platform Handlers**: Windows/macOS automation APIs
3. **Claude Desktop**: First service implementation
4. **Basic Testing**: Single service end-to-end flow

### **Phase 2: Multi-Service Support (Week 2)**  
5. **Perplexity Desktop**: Second service implementation
6. **Gemini PWA**: PWA wrapper automation for Gemini
7. **Response Processing**: JSON extraction and synthesis
8. **Parallel Execution**: Multi-service coordination

### **Phase 3: Integration & Polish (Week 3)**
9. **Frontend Updates**: Desktop-aware UI components
10. **Error Handling**: Robust failure recovery
11. **Performance**: Optimization and reliability improvements
12. **Documentation**: Complete setup and usage guides

## 🔧 **Technical Architecture**

### **Service Configuration Strategy**
```yaml
# config/desktop_services.yaml
services:
  claude:
    type: "desktop_app"
    executable_paths:
      windows: "C:/Users/{user}/AppData/Local/Claude/Claude.exe"
      macos: "/Applications/Claude.app"
    automation_method: "electron_cdp"
    selectors:
      input: '[data-testid="chat-input"]'
      submit: '[data-testid="send-button"]'
      response: '[data-testid="message-content"]'
    
  perplexity:
    type: "desktop_app"  
    executable_paths:
      windows: "C:/Users/{user}/AppData/Local/Perplexity/Perplexity.exe"
      macos: "/Applications/Perplexity.app"
    automation_method: "electron_cdp"
    
  gemini:
    type: "pwa_wrapper"
    url: "https://gemini.google.com"
    automation_method: "web_automation"
    fallback_to_browser: true
```

### **Automation Interface Design**
```python
# Abstract interface for all service automators
class BaseDesktopAutomator:
    def detect_app(self) -> bool:
        """Check if desktop app is installed"""
        
    def launch_app(self) -> bool:
        """Start the desktop application"""
        
    def send_prompt(self, prompt: str) -> bool:
        """Submit prompt to the application"""
        
    def extract_response(self) -> str:
        """Get response from the application"""
        
    def close_app(self) -> bool:
        """Gracefully close the application"""
```

### **Response Processing Pipeline**
```python
# New response processing system
class ResponseProcessor:
    def extract_machine_code_json(self, raw_response: str) -> Dict:
        """Extract JSON from machine code template responses"""
        
    def create_fallback_structure(self, plain_text: str) -> Dict:
        """Generate structured response from plain text"""
        
    def synthesize_multi_service_response(self, responses: List[Dict]) -> str:
        """Combine responses from multiple services intelligently"""
```

## 🎯 **Success Criteria for V4**

### **Immediate Goals (Week 1)**
- [ ] Claude desktop app automated successfully
- [ ] Basic JSON response processing working
- [ ] Single service end-to-end query completion
- [ ] Desktop app detection and lifecycle management

### **Short-term Goals (Week 2-3)**  
- [ ] All available desktop services working (Claude + Perplexity)
- [ ] Gemini PWA automation for 3rd service
- [ ] Multi-service response synthesis
- [ ] Frontend adapted for desktop service status

### **Quality Goals**
- [ ] 90%+ success rate for prompt submission (vs 0% in v3)
- [ ] <10 second average response time per service
- [ ] Proper JSON response parsing and synthesis
- [ ] Graceful fallback when desktop apps unavailable

## 🔄 **Migration from V3**

### **What We're Keeping:**
- ✅ **Local LLM integration** (Ollama + Phi-3-Mini)
- ✅ **Session management architecture**
- ✅ **FastAPI backend structure**
- ✅ **React frontend foundation**
- ✅ **WebSocket real-time communication**

### **What We're Replacing:**
- ❌ **Browser automation** → Desktop app automation
- ❌ **SeleniumBase/UC profiles** → Native system automation APIs
- ❌ **Brittle DOM selectors** → Stable desktop app interfaces
- ❌ **Web detection avoidance** → Native system interaction

### **What We're Improving:**
- 🔧 **Response processing** - Add JSON extraction and synthesis
- 🔧 **Error handling** - Better failure recovery and diagnostics
- 🔧 **Performance** - Faster execution without browser overhead
- 🔧 **Reliability** - More stable automation methods

## 📋 **Next Steps**

1. **Review native_solution.md findings** ✅
2. **Set up development environment** for desktop automation
3. **Install Claude and Perplexity desktop apps** for testing
4. **Implement basic desktop service detection**
5. **Start with Claude desktop automation** as proof of concept

---

*Samay v4 represents a fundamental architecture shift toward sustainable, reliable multi-agent AI automation using desktop applications instead of fragile web scraping.*