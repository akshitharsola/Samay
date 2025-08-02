# Samay v3 Manual Testing Guide

## 🎯 Frontend UI Testing

### Tab 1: Smart Dashboard
- ✅ View real-time productivity metrics
- ✅ See today's schedule with time blocks  
- ✅ Check proactive suggestions panel
- ✅ Use quick action buttons

### Tab 2: Enhanced Chat
- ✅ Start conversation with companion
- ✅ Test memory: "What did I just ask about?"
- ✅ See proactive suggestions appear
- ✅ Watch personality adaptation

### Tab 3: Web Services Panel  
- ✅ Submit query to multiple services
- ✅ Select output format (JSON/Text/Markdown)
- ✅ See parallel processing status
- ✅ Review response quality scores

### Tab 4: Workflow Builder
- ✅ Create new workflow
- ✅ Add triggers and steps
- ✅ Execute workflow and see status
- ✅ View execution history

### Tab 5: Knowledge Panel
- ✅ Add knowledge item
- ✅ Test different search modes
- ✅ View AI-generated insights
- ✅ See relationship mapping

## 🔄 Service Modality Testing

### Local LLM Mode
1. Go to Enhanced Chat
2. Type: "Use local mode only"
3. Ask: "What are good productivity tips?"
4. ✅ Should process locally with Phi-3-Mini

### Confidential Mode  
1. In Web Services panel
2. Enable "Confidential Mode"
3. Submit sensitive query
4. ✅ Should process locally without external calls

### Web Services Mode
1. In Web Services panel
2. Select all services: Claude, Gemini, Perplexity
3. Submit: "Latest AI development trends"
4. ✅ Should show parallel processing to all services

## 📊 Visual Flow Demonstration

1. **Input**: Type message in Enhanced Chat
2. **Processing**: See "Thinking..." indicator
3. **Memory**: Previous context retrieved and displayed
4. **Suggestions**: Proactive suggestions appear in sidebar
5. **Output**: Formatted response with metadata
6. **Analytics**: Dashboard updates with new interaction

## 🔍 API Inspection

1. Open browser dev tools (F12)
2. Go to Network tab
3. Interact with UI
4. ✅ See actual API calls being made
5. ✅ Inspect request/response data
6. ✅ Verify WebSocket connections for real-time updates

## 🧪 Error Testing

1. Try invalid inputs
2. Test with no internet (web services)
3. Submit extremely long messages
4. ✅ Should show graceful error handling
5. ✅ Should fallback to local processing when needed
