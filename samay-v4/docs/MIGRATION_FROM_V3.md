# Migration Guide: Samay v3 → v4
*Transitioning from browser automation to desktop-first approach*

## 🎯 **Migration Overview**

Samay v4 represents a **fundamental architecture shift** from brittle web browser automation to stable desktop application automation. This guide helps you migrate from v3 while preserving your data and settings.

## 📊 **Key Changes Summary**

| Component | V3 Approach | V4 Approach | Migration Required |
|-----------|-------------|-------------|-------------------|
| **Service Access** | Browser automation | Desktop app automation | ✅ **Yes** - Install desktop apps |
| **DOM Selectors** | Web CSS selectors | Desktop UI automation | ✅ **Yes** - New automation methods |
| **Authentication** | Browser profiles | Desktop app sessions | ⚠️ **Partial** - May need re-authentication |
| **Local LLM** | Ollama integration | Same Ollama integration | ❌ **No** - Direct port |
| **Frontend** | React interface | Enhanced React interface | ⚠️ **Partial** - Some UI changes |
| **API Structure** | FastAPI backend | Same FastAPI backend | ❌ **No** - Compatible |
| **Configuration** | Python configs | YAML configurations | ✅ **Yes** - New format |

## 🔄 **Migration Process**

### **Phase 1: Environment Setup (30 minutes)**

#### **1.1 Install Desktop Applications**
Based on the native solution research, install these desktop apps:

```bash
# Claude Desktop (Official)
# Download from: https://claude.ai/download
# - Windows: Claude Desktop installer
# - macOS: Claude.app from App Store or direct download
# - Linux: Available for some distributions

# Perplexity Desktop (Official)  
# Download from: https://www.perplexity.ai
# - Windows: Perplexity Desktop installer
# - macOS: Perplexity.app from App Store
# - Linux: Check official Perplexity site

# Gemini PWA (Since no native app exists)
# Install as Progressive Web App:
# 1. Open Chrome/Edge
# 2. Go to https://gemini.google.com
# 3. Click install app icon in address bar
# OR use WebCatalog: https://webcatalog.io/apps/google-bard
```

#### **1.2 Setup V4 Environment**
```bash
# Navigate to Samay directory
cd /Users/akshitharsola/Documents/Samay

# Verify v4 folder exists (already created)
ls samay-v4/

# Create Python virtual environment for v4
python3 -m venv samay-v4/venv
source samay-v4/venv/bin/activate  # macOS/Linux
# OR: samay-v4\venv\Scripts\activate  # Windows

# Install v4 dependencies
cd samay-v4
pip install -r requirements.txt
```

### **Phase 2: Configuration Migration (20 minutes)**

#### **2.1 Migrate Authentication Data**
Your v3 browser profiles contain authentication cookies that we can reference:

```bash
# V3 authentication is stored in:
# samay-v3/profiles/claude/
# samay-v3/profiles/gemini/  
# samay-v3/profiles/perplexity/

# For V4, you'll need to authenticate in desktop apps manually:
# 1. Launch each desktop app
# 2. Sign in with your credentials
# 3. Verify authentication works
# 4. Desktop apps will remember your login
```

#### **2.2 Update Service Configuration**
```bash
# Review and customize desktop service config:
vi config/desktop_services.yaml

# Key settings to verify:
# - executable_paths match your installations
# - automation methods are supported on your platform
# - selectors are appropriate for your app versions
```

#### **2.3 Migrate Local LLM Settings**
```bash
# Copy Ollama configuration from v3:
# The local LLM (Phi-3-Mini) setup should work unchanged
# Just verify Ollama is still running:

ollama list
# Should show: phi3:mini or similar model

# If not installed, re-setup:
# ollama pull phi3:mini
```

### **Phase 3: Data Migration (15 minutes)**

#### **3.1 Copy Conversation History** 
```bash
# V3 conversation data is in SQLite databases:
# samay-v3/memory/*.db

# For V4, you can copy relevant databases:
mkdir -p samay-v4/memory
cp samay-v3/memory/conversations.db samay-v4/memory/
cp samay-v3/memory/personality.db samay-v4/memory/
cp samay-v3/memory/tasks.db samay-v4/memory/

# Note: V4 will create new databases for desktop-specific features
```

#### **3.2 Migrate Custom Configurations**
```bash
# Copy any custom prompt templates or settings:
# (Review what's worth migrating from v3)

# Example: Custom prompt templates
if [ -f "samay-v3/custom_prompts.json" ]; then
    cp samay-v3/custom_prompts.json samay-v4/config/
fi

# Example: User preferences  
if [ -f "samay-v3/user_preferences.json" ]; then
    cp samay-v3/user_preferences.json samay-v4/config/
fi
```

### **Phase 4: Testing and Validation (30 minutes)**

#### **4.1 Test Desktop Service Detection**
```bash
# Test the desktop service manager:
cd samay-v4
python orchestrator/desktop_service_manager.py

# Expected output:
# ✅ Claude Desktop found at: /Applications/Claude.app
# ✅ Perplexity Desktop found at: /Applications/Perplexity.app
# ❌ Gemini (will use PWA fallback)
```

#### **4.2 Test Service Launching**
```bash
# Test launching services individually:
python -c "
from orchestrator.desktop_service_manager import DesktopServiceManager
manager = DesktopServiceManager()
manager.detect_installed_apps()
print('Testing Claude launch...')
success = manager.launch_app('claude')
print(f'Claude launch: {success}')
if success:
    manager.close_app('claude')
"
```

#### **4.3 Test Basic Query Flow**
```bash
# Once basic automation is working, test a simple query:
# (This will be implemented in the next development phase)

# For now, verify the infrastructure is working:
python -c "
from orchestrator.desktop_service_manager import DesktopServiceManager
manager = DesktopServiceManager()
summary = manager.get_summary()
print(f'Services ready: {summary[\"installed_services\"]}/{summary[\"total_services\"]}')
"
```

## 🔧 **Troubleshooting Common Migration Issues**

### **Issue 1: Desktop Apps Not Detected**
```bash
# Problem: Apps installed but not detected
# Solution: Check executable paths in config

# Edit desktop_services.yaml:
# - Verify paths match your actual installation
# - Check platform-specific paths (Windows/macOS/Linux)
# - Add custom paths if needed

# Test detection manually:
ls "/Applications/Claude.app"  # macOS
ls "C:\Users\{username}\AppData\Local\Claude\Claude.exe"  # Windows
```

### **Issue 2: Authentication Required**
```bash
# Problem: Desktop apps require login
# Solution: Manual authentication in each app

# 1. Launch each desktop app manually
# 2. Sign in with your credentials  
# 3. Verify you can use the app normally
# 4. Close app and test v4 automation

# Desktop apps should remember your login session
```

### **Issue 3: Platform-Specific Automation Issues**
```bash
# Problem: Automation not working on your platform
# Solution: Install platform-specific dependencies

# macOS:
pip install pyobjc-framework-Quartz pyobjc-framework-ApplicationServices

# Windows:  
pip install pywinauto comtypes

# Linux:
pip install pyatspi python-xlib

# Test platform detection:
python -c "import platform; print(f'Platform: {platform.system().lower()}')"
```

### **Issue 4: Gemini Service Unavailable**
```bash
# Problem: No official Gemini desktop app
# Solution: Use PWA or browser fallback

# Option 1: Install Gemini as PWA
# 1. Open Chrome/Edge
# 2. Go to https://gemini.google.com  
# 3. Click "Install app" in address bar

# Option 2: Use WebCatalog wrapper
# Download from: https://webcatalog.io/apps/google-bard

# Option 3: Fallback to v3 browser automation for Gemini only
# Edit desktop_services.yaml:
# gemini:
#   fallback_browser: true
#   browser_profile: "../samay-v3/profiles/gemini"
```

## 🎯 **Migration Validation Checklist**

### **✅ Environment Setup**
- [ ] Desktop apps installed (Claude, Perplexity)
- [ ] V4 Python environment created and activated
- [ ] V4 dependencies installed successfully
- [ ] Platform-specific automation libraries installed

### **✅ Service Detection**
- [ ] Desktop service manager detects installed apps
- [ ] Executable paths correctly configured
- [ ] Service status shows "installed" for available apps
- [ ] Platform detection working correctly

### **✅ Authentication**
- [ ] Claude desktop app authentication working
- [ ] Perplexity desktop app authentication working
- [ ] Gemini PWA/fallback authentication working
- [ ] Local LLM (Ollama) still accessible

### **✅ Data Migration**
- [ ] Conversation history copied from v3
- [ ] Custom configurations migrated
- [ ] User preferences preserved
- [ ] Local LLM models still available

### **✅ Basic Functionality**
- [ ] Desktop apps can be launched programmatically
- [ ] Apps can be closed gracefully
- [ ] Service health checks working
- [ ] Error handling functional

## 🚀 **Next Steps After Migration**

### **Phase 5: Development Continuation**
Once migration is complete, continue with v4 development:

1. **Implement Desktop Automation** - Build actual automation interfaces
2. **Add Response Processing** - Fix the machine code JSON parsing issue
3. **Test End-to-End Flow** - Verify complete query → response cycle
4. **Enhance Frontend** - Update UI for desktop service status
5. **Performance Optimization** - Tune automation timing and reliability

### **Phase 6: Validation and Rollback Plan**
- **Success Criteria**: V4 achieves >90% query success rate (vs 0% in v3)
- **Rollback Plan**: If v4 fails, v3 is preserved and can continue to be used
- **Hybrid Approach**: Run both v3 and v4 in parallel during transition

## 📚 **Additional Resources**

### **Desktop App Documentation**
- **Claude Desktop**: https://support.anthropic.com/en/articles/10065433-installing-claude-desktop
- **Perplexity Desktop**: https://www.perplexity.ai (check download section)
- **Gemini PWA**: https://gemini.google.com (install as web app)

### **Platform Automation Guides**
- **Windows UI Automation**: https://docs.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32
- **macOS Accessibility**: https://developer.apple.com/documentation/applicationservices/accessibility
- **Linux AT-SPI**: https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/

### **Troubleshooting Resources**
- **V4 Issues**: Create issues in the project repository
- **Desktop App Issues**: Refer to official app documentation
- **Platform Issues**: Check platform-specific automation documentation

---

*This migration preserves your v3 investment while moving to a more reliable desktop-first architecture. The parallel folder structure ensures you can always fall back to v3 if needed.*