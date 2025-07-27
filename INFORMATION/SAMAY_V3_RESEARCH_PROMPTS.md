# Samay v3 - Research Prompts for Critical Issues
*Generated: 2025-07-27*

## 🎯 RESEARCH OBJECTIVE
These research prompts are designed to solve the 4 critical failures preventing Samay v3 from functioning: DOM selector failures, machine code processing issues, buried user questions, and missing response parsing.

---

## 🔍 RESEARCH CATEGORY 1: SERVICE INTERFACE ANALYSIS
*Priority: CRITICAL - Fixes 100% prompt submission failure*

### PROMPT 1.1: Claude.ai Current Interface Analysis
```
Research Task: Analyze Claude.ai's current chat interface (2025)

Instructions:
1. Navigate to https://claude.ai in a browser
2. Create a new conversation
3. Right-click on the chat input area and inspect element
4. Document the exact HTML structure and CSS selectors for:
   - Chat input field (contenteditable div, textarea, etc.)
   - Send/Submit button (current aria-label, data-testid, class names)
   - Message response containers (where Claude's responses appear)
   - Loading indicators (typing dots, processing states)

5. Test these specific selectors in browser console:
   - document.querySelector('[contenteditable="true"]')
   - document.querySelector('button[aria-label="Send"]')
   - document.querySelector('button[data-testid="send-button"]')
   - document.querySelector('[data-testid="chat-input"]')

6. Check for anti-automation measures:
   - Rate limiting indicators
   - CAPTCHA triggers
   - Unusual delays or blocks

7. Test keyboard alternatives:
   - Does Enter key submit messages?
   - Are there keyboard shortcuts?
   - What happens with Ctrl+Enter vs Enter?

Output: Provide working CSS selectors for input, submit, and response elements that work in 2025.
```

### PROMPT 1.2: Google Gemini Interface Analysis  
```
Research Task: Analyze Google Gemini's current chat interface (2025)

Instructions:
1. Navigate to https://gemini.google.com in a browser
2. Start a new conversation
3. Inspect the chat interface elements and document:
   - Current input field structure (textarea vs contenteditable)
   - Submit button attributes (aria-label changes from "Send Message"?)
   - Response area selectors and structure
   - Any Google-specific anti-automation measures

4. Test these selectors in browser console:
   - document.querySelector('textarea[role="textbox"]')
   - document.querySelector('button[aria-label="Send Message"]')
   - document.querySelector('button[aria-label="Send message"]') // lowercase
   - document.querySelector('[data-testid="send-button"]')

5. Check for authentication flow issues:
   - Does the interface change after login?
   - Are there different selectors for different user states?
   - How does Google handle automated interactions?

6. Document mobile vs desktop differences:
   - Do selectors change on different screen sizes?
   - Are there responsive design selector variations?

Output: Current working selectors and any special handling needed for Gemini automation.
```

### PROMPT 1.3: Perplexity.ai Interface Analysis
```
Research Task: Analyze Perplexity.ai's current interface (2025)

Instructions:
1. Navigate to https://www.perplexity.ai
2. Examine the search/query interface and document:
   - Input field type (has it changed from input to textarea?)
   - Submit button structure and attributes
   - Response/answer area selectors
   - Search result vs chat mode differences

3. Test these selectors in browser console:
   - document.querySelector('input[type="text"]')
   - document.querySelector('textarea[placeholder*="Ask anything"]')
   - document.querySelector('input[placeholder*="Ask"]')
   - document.querySelector('button[data-testid="ask-button"]')
   - document.querySelector('button[aria-label="Submit"]')

4. Analyze response extraction:
   - Where do answers appear? (specific CSS classes)
   - How are sources vs answers differentiated?
   - What's the structure of the response area?

5. Check for automation challenges:
   - Does Perplexity detect automated interactions?
   - Are there rate limits or CAPTCHA triggers?
   - How does the interface behave with rapid queries?

Output: Updated selectors and best practices for Perplexity automation.
```

---

## 🔍 RESEARCH CATEGORY 2: RESPONSE PROCESSING ARCHITECTURE
*Priority: HIGH - Fixes machine code template confusion*

### PROMPT 2.1: JSON Response Extraction Patterns
```
Research Task: Design robust JSON extraction from AI service responses

Problem Context:
- Samay sends AI services a machine code template requesting JSON responses
- Services may return JSON embedded in natural language or markdown
- Current code has no JSON extraction or validation logic
- Need fallback for when services ignore the JSON format

Research Requirements:
1. Study common patterns for JSON extraction from mixed content:
   - Regex patterns for finding JSON blocks in text
   - Handling markdown code blocks with ```json
   - Dealing with partial or malformed JSON
   - Extracting multiple JSON objects from single response

2. Design validation framework:
   - Required fields: response, summary, key_points, confidence, category
   - Type checking for each field
   - Default values for missing fields
   - Error handling for invalid JSON

3. Create fallback processing:
   - When no JSON is found, create structured response from plain text
   - Automatic key point extraction from natural language
   - Confidence scoring based on response quality
   - Category classification using keyword detection

4. Research existing libraries/approaches:
   - Python json module error handling
   - Natural language processing for structure extraction
   - Other AI aggregation tools' response processing methods

Output: Code architecture and specific implementation approach for robust response processing.
```

### PROMPT 2.2: Multi-Agent Response Synthesis Research
```
Research Task: Design intelligent aggregation of multiple AI service responses

Problem Context:
- Samay queries 3 services simultaneously (Claude, Gemini, Perplexity)
- Each service may provide different information or perspectives
- Need to synthesize responses into single, coherent answer
- Must handle conflicting information and varying quality

Research Requirements:
1. Response comparison strategies:
   - How to identify consensus vs conflicting information
   - Weighting responses based on service reliability
   - Handling partial responses vs complete failures
   - Dealing with different response styles and formats

2. Information synthesis approaches:
   - Combining complementary information from multiple sources
   - Identifying and highlighting disagreements
   - Creating unified key points from multiple perspectives
   - Maintaining source attribution for claims

3. Quality assessment metrics:
   - Scoring response relevance to original question
   - Detecting generic vs specific answers
   - Measuring response completeness and accuracy
   - Confidence aggregation from multiple sources

4. Study existing multi-source aggregation systems:
   - Academic research on multi-agent consensus
   - Commercial AI aggregation platforms
   - Search engine result synthesis methods
   - News aggregation and fact-checking approaches

Output: Design framework for intelligent response synthesis with specific algorithms and implementation strategy.
```

---

## 🔍 RESEARCH CATEGORY 3: PROMPT OPTIMIZATION
*Priority: MEDIUM - Fixes buried question problem*

### PROMPT 3.1: Effective AI Prompt Structure Research
```
Research Task: Optimize prompt structure to ensure user questions are properly addressed

Problem Context:
- Current machine code template buries user question at bottom
- AI services may focus on JSON format instructions instead of actual question
- Need to balance structured output request with question prominence

Research Requirements:
1. Study effective prompt engineering patterns:
   - Question-first vs instruction-first structures
   - How to emphasize the important parts of complex prompts
   - Balancing format requirements with content requests
   - Different approaches for different AI services

2. Test prompt variations:
   - "Answer this question in JSON format: [QUESTION]"
   - vs "Please use JSON format. Question: [QUESTION]"
   - vs current approach with template first

3. Research AI service behavior:
   - How do Claude, Gemini, Perplexity handle complex prompts?
   - Which services better follow format vs content instructions?
   - Are there service-specific prompt optimization strategies?

4. Analyze real-world implementations:
   - How do other multi-AI platforms structure prompts?
   - What prompt patterns get best compliance with format AND content?
   - Examples of successful structured response prompts

Output: Optimized prompt templates that prioritize user questions while maintaining machine-readable format.
```

---

## 🔍 RESEARCH CATEGORY 4: AUTOMATION RELIABILITY
*Priority: MEDIUM - Improves system stability*

### PROMPT 4.1: Browser Automation Anti-Detection Research
```
Research Task: Improve browser automation reliability and stealth

Problem Context:
- AI services may detect and block automated interactions
- Need human-like behavior patterns to avoid detection
- Current system has authentication success but prompt submission failures

Research Requirements:
1. Study current anti-automation measures:
   - How do Claude, Gemini, Perplexity detect bots?
   - Common indicators: timing patterns, mouse movements, etc.
   - Rate limiting and session behavior analysis

2. Research stealth automation techniques:
   - Human-like timing variations and delays
   - Mouse movement simulation patterns
   - Keyboard typing rhythm simulation
   - Browser fingerprint randomization

3. Alternative automation approaches:
   - Keyboard-only interaction (avoiding mouse detection)
   - Browser extension-based automation
   - Accessibility API usage for interactions
   - Chrome DevTools Protocol alternatives

4. Error handling and recovery:
   - Detecting when automation is blocked
   - Automatic retry strategies with different patterns
   - Fallback to manual intervention workflows
   - Session recovery after detection/blocking

Output: Improved automation strategy with stealth techniques and robust error handling.
```

### PROMPT 4.2: API Integration Feasibility Research
```
Research Task: Evaluate official API alternatives to browser automation

Problem Context:
- Browser automation is fragile and may break with UI updates
- Official APIs would be more reliable than DOM manipulation
- Need to assess cost, availability, and integration complexity

Research Requirements:
1. Official API availability:
   - Does Claude (Anthropic) offer a public API?
   - Google Gemini API access and pricing
   - Perplexity API availability and limitations
   - Rate limits, quotas, and usage restrictions

2. Cost analysis:
   - API pricing vs browser automation costs
   - Usage volume considerations for multi-agent queries
   - Free tier limitations and paid plan requirements

3. Integration complexity:
   - Authentication requirements (API keys, OAuth, etc.)
   - Request/response format differences from browser interface
   - Feature parity: do APIs support same capabilities as web interfaces?

4. Hybrid approach feasibility:
   - Using APIs where available, browser automation as fallback
   - Cost optimization: cheap APIs for simple queries, browser for complex
   - User configuration options for API vs automation preferences

Output: Feasibility assessment and integration plan for API alternatives.
```

---

## 🔍 RESEARCH CATEGORY 5: ERROR HANDLING & DIAGNOSTICS
*Priority: LOW - Improves debugging and maintenance*

### PROMPT 5.1: Comprehensive Error Handling Framework
```
Research Task: Design robust error handling and diagnostic system

Problem Context:
- Current system fails silently or with unclear error messages
- Need better debugging information for selector failures
- Users need clear feedback when services are unavailable

Research Requirements:
1. Error classification system:
   - Network/connectivity errors
   - Authentication/session errors  
   - DOM selector failures
   - Service-specific errors (rate limiting, etc.)
   - Response processing errors

2. Diagnostic information collection:
   - Screenshot capture on failures
   - HTML structure logging for selector debugging
   - Network request/response logging
   - Timing and performance metrics

3. User-friendly error reporting:
   - Clear error messages for common failures
   - Suggested solutions for different error types
   - Status indicators showing what's working vs broken
   - Graceful degradation when services are unavailable

4. Recovery and retry strategies:
   - Automatic retry with exponential backoff
   - Alternative selector attempts
   - Service health monitoring and status reporting
   - Manual intervention workflows for persistent failures

Output: Comprehensive error handling architecture with clear user communication.
```

---

## 📋 RESEARCH EXECUTION PRIORITY

### Phase 1 (Immediate - Fix Core Functionality)
1. **Execute Prompts 1.1, 1.2, 1.3** - Get current DOM selectors
2. **Execute Prompt 2.1** - Build JSON response processing
3. **Test with single service** - Verify end-to-end functionality

### Phase 2 (Short-term - Improve Reliability)  
4. **Execute Prompt 2.2** - Multi-agent response synthesis
5. **Execute Prompt 3.1** - Optimize prompt structure
6. **Execute Prompt 4.1** - Improve automation stealth

### Phase 3 (Long-term - Alternative Approaches)
7. **Execute Prompt 4.2** - Research API alternatives
8. **Execute Prompt 5.1** - Build robust error handling

---

## 🎯 SUCCESS CRITERIA

### Research Outputs Needed:
- [ ] Working CSS selectors for all 3 services (2025 current)
- [ ] Response processing code architecture
- [ ] Multi-agent synthesis algorithm design  
- [ ] Optimized prompt templates
- [ ] Automation stealth improvements
- [ ] API integration feasibility report
- [ ] Error handling framework design

### Implementation Validation:
- [ ] 1+ service completes full query cycle
- [ ] Machine code responses are properly parsed
- [ ] User questions are prominently addressed
- [ ] Multiple service responses are intelligently synthesized
- [ ] System provides clear feedback on failures

---

*These research prompts provide specific, actionable investigation tasks to fix all identified critical issues in Samay v3.*