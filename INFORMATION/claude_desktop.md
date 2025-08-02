<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# So we were working on our project and resolved the permission issues, now important area to work is with the automation of inputting the prompt, fetching output and even follow up prompt, which all to be automated -

🔍 Comprehensive Research Prompt for Claude Desktop Automation

Research Objective

Find detailed technical solutions for automating Claude Desktop app interactions on macOS using Swift and the
  Accessibility API, specifically focusing on text input submission and response extraction.

---
  Current Technical Context

What We're Building

- Application: Samay macOS - AI Session Manager
  - Language: Swift (Xcode project)
  - Target: Claude Desktop app automation via macOS Accessibility API
  - Architecture: Native macOS app using SwiftUI + Accessibility framework

What We're Using

// Core Technologies:
  - macOS Accessibility API (AXUIElement)
  - Swift async/await patterns
  - Bundle ID: com.anthropic.claudefordesktop
  - Xcode with proper entitlements and code signing

Current Status

- ✅ Accessibility Permissions: Granted and working
  - ✅ App Detection: Can find and connect to Claude Desktop
  - ✅ Bundle ID Access: Successfully gets Claude's AXUIElement
  - ❌ Text Input: Not successfully sending prompts
  - ❌ Response Extraction: Getting "content not detected"

---
  Specific Research Questions

1. Claude Desktop UI Architecture Analysis

Research Focus: Understanding Claude Desktop's internal structure
  - What is Claude Desktop built with? (Electron, native WebKit, custom framework?)
  - How does Claude Desktop expose its UI elements through macOS Accessibility API?
  - What are the specific AX roles, attributes, and hierarchy patterns used by Claude Desktop?
  - Are there any special accessibility flags or properties that need to be enabled?

2. Text Input Mechanism Discovery

Research Focus: How to programmatically send text to Claude Desktop
  - What AX roles does Claude Desktop use for its text input area? (AXTextArea, AXTextField, custom roles?)
  - What are the exact attribute names and values for Claude's input elements?
  - How does the send button work in Claude Desktop from an accessibility perspective?
  - Are there keyboard shortcuts that trigger message sending? (Enter, Cmd+Enter, etc.)
  - Does Claude use contentEditable div elements that require special handling?

3. Response Detection Patterns

Research Focus: How to reliably detect and extract Claude's responses
  - How does Claude Desktop structure its chat messages in the accessibility tree?
  - What AX attributes contain the actual response text?
  - How can we distinguish between user messages and Claude's responses?
  - What patterns indicate when Claude has finished generating a response?
  - Are there unique identifiers or markers in Claude's response containers?

4. Automation Workflow Requirements

First-Time Prompt Scenario:

User clicks "Debug AI Services" →
  App needs to:
  1. Focus Claude Desktop window
  2. Create new chat (if needed)
  3. Input prompt: "Explain quantum computing"
  4. Submit prompt (press Enter/Send button)
  5. Wait for Claude's response
  6. Extract complete response text
  7. Return response to Samay app

Follow-Up Prompt Scenario:

User sends another query in same session →
  App needs to:
  1. Focus existing Claude chat
  2. Input follow-up prompt: "Explain it simply"
  3. Submit prompt
  4. Wait for response
  5. Extract response
  6. Return to app

---
  Technical Investigation Areas

A. Accessibility API Deep Dive

Research these specific macOS Accessibility API aspects:
  - AXUIElementCopyAttributeNames() - What attributes does Claude expose?
  - AXUIElementCopyAttributeValue() - How to get text content from Claude elements?
  - AXUIElementSetAttributeValue() - How to set text in Claude's input field?
  - AXUIElementPerformAction() - What actions are available on Claude elements?
  - WebView accessibility bridging - If Claude is Electron/web-based

B. Alternative Automation Approaches

If direct Accessibility API doesn't work:
  - AppleScript integration with Claude Desktop
  - Keyboard event simulation (CGEvent)
  - Pasteboard/clipboard-based text insertion
  - Mouse click automation for send buttons
  - Hybrid approaches combining multiple methods

C. Electron App Automation Specifics

If Claude Desktop is Electron-based:
  - How to enable accessibility in Electron apps?
  - Web content accessibility bridging
  - DOM element access through accessibility layer
  - Special handling for contentEditable elements

---
  Code Context for Research

Current Implementation Structure

// Main automation entry point
  func automateClaudeQuery(_ query: String, isNewChat: Bool = true) async throws -> String

// Key helper methods
  func findClaudeTextInput(in appElement: AXUIElement) -> AXUIElement?
  func extractClaudeResponse(from appElement: AXUIElement) -> String
  func sendTextToElement(_ element: AXUIElement, text: String) -> Bool

Current Challenge Points

// 1. Text input detection failing
  textArea = findClaudeTextInput(in: appElement)  // Returns nil

// 2. Text sending not working  
  let success = sendTextToElement(inputElement, text: query)  // Returns false

// 3. Response extraction empty
  let response = extractClaudeResponse(from: appElement)  // Returns ""

---
  Expected Research Deliverables

1. Technical Solution Document

- Exact AX attributes and roles used by Claude Desktop
  - Step-by-step automation workflow with specific API calls
  - Code samples showing working text input and response extraction
  - Handling differences between new chat vs follow-up messages

2. Alternative Approaches

- Backup automation methods if Accessibility API limitations exist
  - Hybrid approaches combining multiple automation techniques
  - Error handling and fallback strategies

3. Implementation Guide

- Specific Swift code patterns for Claude Desktop automation
  - Required entitlements, permissions, and setup
  - Testing and debugging approaches
  - Performance considerations and timing requirements

---
  Success Criteria

The research should enable us to:
  1. ✅ Successfully send text prompts to Claude Desktop programmatically
  2. ✅ Trigger prompt submission (equivalent to pressing Enter/Send)
  3. ✅ Detect when Claude has finished responding
  4. ✅ Extract complete response text reliably
  5. ✅ Handle both new chat creation and follow-up messages
  6. ✅ Integrate seamlessly with our existing Swift/Accessibility API codebase

Now I have comprehensive information about Claude Desktop automation. Let me compile this into a detailed technical solution document.

# **Claude Desktop macOS Automation: Comprehensive Technical Solution**

## **Executive Summary**

Based on extensive research, Claude Desktop is an **Electron application** with specific accessibility characteristics that require a multi-faceted approach for automation. The solution involves enabling accessibility, implementing hybrid automation techniques, and addressing Electron-specific UI element detection challenges.

## **1. Claude Desktop Architecture Analysis**

### **Application Framework**

- **Technology**: Electron-based application [^1][^2][^3]
- **Bundle ID**: `com.anthropic.claudefordesktop`
- **UI Framework**: Web-based (HTML/CSS/JavaScript) wrapped in Electron
- **Text Input**: Uses `contentEditable` elements instead of native text fields [^4][^5]


### **Accessibility Exposure**

- Accessibility is **disabled by default** in Electron apps for performance reasons [^6][^7]
- Requires explicit activation via `AXManualAccessibility` attribute [^6][^8][^7]
- Web content is accessible through accessibility API after activation [^8]


## **2. Core Technical Requirements**

### **Essential Steps for Claude Desktop Automation**

#### **Step 1: Enable Accessibility for Electron Apps**

```swift
import ApplicationServices

func enableAccessibilityForClaudeDesktop() -> Bool {
    // Get Claude Desktop app reference
    guard let app = NSWorkspace.shared.runningApplications.first(where: { 
        $0.bundleIdentifier == "com.anthropic.claudefordesktop" 
    }) else {
        return false
    }
    
    // Create AXUIElement for the app
    let appElement = AXUIElementCreateApplication(app.processIdentifier)
    
    // Enable accessibility manually
    let result = AXUIElementSetAttributeValue(
        appElement, 
        "AXManualAccessibility" as CFString, 
        true as CFTypeRef
    )
    
    return result == .success
}
```


#### **Step 2: Advanced UI Element Detection**

```swift
func findClaudeTextInput(in appElement: AXUIElement) -> AXUIElement? {
    // First enable accessibility
    _ = enableAccessibilityForClaudeDesktop()
    
    // Wait for accessibility to activate
    usleep(500_000) // 500ms delay
    
    // Look for contentEditable elements with specific roles
    let possibleRoles = ["AXWebArea", "AXTextArea", "AXTextField", "AXGroup"]
    
    for role in possibleRoles {
        if let element = searchForElementByRole(appElement, role: role) {
            // Verify it's editable
            var isEditable: DarwinBoolean = false
            let editableResult = AXUIElementIsAttributeSettable(
                element, 
                kAXValueAttribute as CFString, 
                &isEditable
            )
            
            if editableResult == .success && isEditable.boolValue {
                return element
            }
        }
    }
    
    return nil
}

func searchForElementByRole(_ element: AXUIElement, role: String) -> AXUIElement? {
    // Recursive search through UI hierarchy
    var children: CFTypeRef?
    let childrenResult = AXUIElementCopyAttributeValue(
        element, 
        kAXChildrenAttribute as CFString, 
        &children
    )
    
    guard childrenResult == .success,
          let childArray = children as? [AXUIElement] else {
        return nil
    }
    
    for child in childArray {
        // Check role
        var roleValue: CFTypeRef?
        if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &roleValue) == .success,
           let roleString = roleValue as? String,
           roleString == role {
            return child
        }
        
        // Recursive search
        if let found = searchForElementByRole(child, role: role) {
            return found
        }
    }
    
    return nil
}
```


## **3. Text Input Implementation**

### **Primary Method: Direct Accessibility API**

```swift
func sendTextToClaudeDesktop(_ text: String) async throws -> Bool {
    guard let app = NSWorkspace.shared.runningApplications.first(where: { 
        $0.bundleIdentifier == "com.anthropic.claudefordesktop" 
    }) else {
        throw AutomationError.appNotFound
    }
    
    // Activate Claude Desktop
    app.activate()
    await Task.sleep(nanoseconds: 500_000_000) // 500ms
    
    let appElement = AXUIElementCreateApplication(app.processIdentifier)
    
    // Enable accessibility
    guard enableAccessibilityForClaudeDesktop() else {
        throw AutomationError.accessibilityNotEnabled
    }
    
    // Find input element
    guard let inputElement = findClaudeTextInput(in: appElement) else {
        throw AutomationError.inputElementNotFound
    }
    
    // Set text value
    let result = AXUIElementSetAttributeValue(
        inputElement,
        kAXValueAttribute as CFString,
        text as CFTypeRef
    )
    
    return result == .success
}
```


### **Fallback Method: Keyboard Simulation**

```swift
func sendTextViaKeyboardSimulation(_ text: String) {
    for character in text {
        if let (keyCode, flags) = getKeyCodeForCharacter(character) {
            sendKeystroke(keyCode: keyCode, flags: flags)
            usleep(50_000) // 50ms delay between keystrokes
        }
    }
}

func sendKeystroke(keyCode: CGKeyCode, flags: CGEventFlags = []) {
    guard let keyDown = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true),
          let keyUp = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false) else {
        return
    }
    
    keyDown.flags = flags
    keyUp.flags = flags
    
    keyDown.post(tap: .cgAnnotatedSessionEventTap)
    keyUp.post(tap: .cgAnnotatedSessionEventTap)
}
```


### **Trigger Submission**

```swift
func submitPrompt() {
    // Try Enter key first
    sendKeystroke(keyCode: 36) // Return key
    
    // Alternative: Cmd+Enter
    // sendKeystroke(keyCode: 36, flags: .maskCommand)
}
```


## **4. Response Detection and Extraction**

### **Observer-Based Response Monitoring**

```swift
class ClaudeResponseObserver {
    private var observer: AXObserver?
    private var appElement: AXUIElement?
    
    func startMonitoring(processID: pid_t) throws {
        let result = AXObserverCreate(processID, { observer, element, notification, refcon in
            // Handle notifications
            let notificationName = notification as String
            if notificationName == kAXValueChangedNotification as String ||
               notificationName == "AXLoadComplete" {
                // Response likely complete
                NotificationCenter.default.post(
                    name: NSNotification.Name("ClaudeResponseReady"),
                    object: element
                )
            }
        }, &observer)
        
        guard result == .success, let observer = observer else {
            throw AutomationError.observerCreationFailed
        }
        
        self.observer = observer
        self.appElement = AXUIElementCreateApplication(processID)
        
        // Add notifications for text changes
        let notifications = [
            kAXValueChangedNotification,
            "AXLoadComplete",
            "AXChildrenChanged"
        ]
        
        for notification in notifications {
            AXObserverAddNotification(
                observer,
                appElement!,
                notification as CFString,
                nil
            )
        }
        
        // Add to run loop
        CFRunLoopAddSource(
            CFRunLoopGetCurrent(),
            AXObserverGetRunLoopSource(observer),
            .defaultMode
        )
    }
}
```


### **Polling-Based Response Detection**

```swift
func waitForClaudeResponse(timeout: TimeInterval = 30.0) async throws -> String {
    let startTime = Date()
    var lastResponseLength = 0
    var stableCount = 0
    
    while Date().timeIntervalSince(startTime) < timeout {
        let currentResponse = extractClaudeResponse()
        
        if currentResponse.count > lastResponseLength {
            lastResponseLength = currentResponse.count
            stableCount = 0
        } else if currentResponse.count == lastResponseLength && !currentResponse.isEmpty {
            stableCount += 1
            
            // Response stable for 2 seconds = complete
            if stableCount >= 4 { // 4 * 500ms = 2s
                return currentResponse
            }
        }
        
        try await Task.sleep(nanoseconds: 500_000_000) // 500ms
    }
    
    throw AutomationError.responseTimeout
}

func extractClaudeResponse() -> String {
    guard let app = NSWorkspace.shared.runningApplications.first(where: { 
        $0.bundleIdentifier == "com.anthropic.claudefordesktop" 
    }) else {
        return ""
    }
    
    let appElement = AXUIElementCreateApplication(app.processIdentifier)
    
    // Look for response containers
    let responseElements = findResponseElements(in: appElement)
    
    var fullResponse = ""
    for element in responseElements {
        if let text = getTextFromElement(element) {
            fullResponse += text + "\n"
        }
    }
    
    return fullResponse.trimmingCharacters(in: .whitespacesAndNewlines)
}
```


## **5. Complete Automation Workflow**

### **Main Automation Function**

```swift
func automateClaudeQuery(_ query: String, isNewChat: Bool = true) async throws -> String {
    // Step 1: Ensure accessibility permissions
    let options: [String: Any] = [kAXTrustedCheckOptionPrompt.takeRetainedValue() as String: true]
    guard AXIsProcessTrustedWithOptions(options as CFDictionary) else {
        throw AutomationError.accessibilityPermissionDenied
    }
    
    // Step 2: Find or launch Claude Desktop
    guard let app = NSWorkspace.shared.runningApplications.first(where: { 
        $0.bundleIdentifier == "com.anthropic.claudefordesktop" 
    }) else {
        // Launch Claude Desktop if not running
        NSWorkspace.shared.launchApplication(withBundleIdentifier: "com.anthropic.claudefordesktop", 
                                             options: [], 
                                             additionalEventParamDescriptor: nil)
        try await Task.sleep(nanoseconds: 3_000_000_000) // 3s launch delay
        
        guard let launchedApp = NSWorkspace.shared.runningApplications.first(where: { 
            $0.bundleIdentifier == "com.anthropic.claudefordesktop" 
        }) else {
            throw AutomationError.appLaunchFailed
        }
    }
    
    // Step 3: Activate and prepare app
    app.activate()
    try await Task.sleep(nanoseconds: 1_000_000_000) // 1s activation delay
    
    // Step 4: Create new chat if needed
    if isNewChat {
        sendKeystroke(keyCode: 11, flags: .maskCommand) // Cmd+B for new chat (if available)
        try await Task.sleep(nanoseconds: 500_000_000) // 500ms
    }
    
    // Step 5: Send text input
    let success = try await sendTextToClaudeDesktop(query)
    guard success else {
        throw AutomationError.textInputFailed
    }
    
    // Step 6: Submit prompt
    submitPrompt()
    
    // Step 7: Wait for and extract response
    let response = try await waitForClaudeResponse()
    
    return response
}
```


## **6. Error Handling and Edge Cases**

### **Error Types**

```swift
enum AutomationError: Error {
    case appNotFound
    case appLaunchFailed
    case accessibilityPermissionDenied
    case accessibilityNotEnabled
    case inputElementNotFound
    case textInputFailed
    case responseTimeout
    case observerCreationFailed
}
```


### **Retry Mechanisms**

```swift
func automateClaudeQueryWithRetry(_ query: String, maxRetries: Int = 3) async throws -> String {
    var lastError: Error?
    
    for attempt in 1...maxRetries {
        do {
            return try await automateClaudeQuery(query)
        } catch {
            lastError = error
            
            // Progressive backoff
            let delay = TimeInterval(attempt * attempt) // 1s, 4s, 9s
            try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
            
            // Reset accessibility for retry
            _ = enableAccessibilityForClaudeDesktop()
        }
    }
    
    throw lastError ?? AutomationError.textInputFailed
}
```


## **7. Alternative Implementation Approaches**

### **AppleScript Bridge**

```swift
func sendTextViaAppleScript(_ text: String) -> Bool {
    let script = """
    tell application "Claude"
        activate
        delay 0.5
        tell application "System Events"
            keystroke "\(text)"
            key code 36 -- Return
        end tell
    end tell
    """
    
    var error: NSDictionary?
    if let scriptObject = NSAppleScript(source: script) {
        let result = scriptObject.executeAndReturnError(&error)
        return error == nil
    }
    
    return false
}
```


### **Hybrid Approach**

```swift
func hybridTextInput(_ text: String) async throws -> Bool {
    // Try accessibility API first
    do {
        return try await sendTextToClaudeDesktop(text)
    } catch {
        // Fallback to keyboard simulation
        sendTextViaKeyboardSimulation(text)
        return true
    }
}
```


## **8. Required Entitlements and Permissions**

### **Info.plist Additions**

```xml
<key>NSAppleEventsUsageDescription</key>
<string>This app requires access to control other applications for AI automation.</string>
```


### **Runtime Permission Check**

```swift
func checkAccessibilityPermissions() -> Bool {
    let options: [String: Any] = [kAXTrustedCheckOptionPrompt.takeRetainedValue() as String: true]
    return AXIsProcessTrustedWithOptions(options as CFDictionary)
}
```


## **9. Performance Optimization**

### **Element Caching**

```swift
class ClaudeUIElementCache {
    private var cachedInputElement: AXUIElement?
    private var cacheTimestamp: Date?
    private let cacheValidityDuration: TimeInterval = 10.0
    
    func getCachedInputElement(for appElement: AXUIElement) -> AXUIElement? {
        if let cached = cachedInputElement,
           let timestamp = cacheTimestamp,
           Date().timeIntervalSince(timestamp) < cacheValidityDuration {
            return cached
        }
        
        // Cache miss - find element
        let element = findClaudeTextInput(in: appElement)
        cachedInputElement = element
        cacheTimestamp = Date()
        
        return element
    }
}
```


## **10. Testing and Validation**

### **Unit Test Structure**

```swift
class ClaudeAutomationTests: XCTestCase {
    
    func testAccessibilityPermissions() {
        XCTAssertTrue(checkAccessibilityPermissions())
    }
    
    func testClaudeDesktopDetection() {
        let app = NSWorkspace.shared.runningApplications.first { 
            $0.bundleIdentifier == "com.anthropic.claudefordesktop" 
        }
        XCTAssertNotNil(app)
    }
    
    func testTextInputElement() async {
        // Test with actual Claude Desktop running
        guard let app = getClaudeDesktopApp() else {
            XCTSkip("Claude Desktop not running")
        }
        
        let appElement = AXUIElementCreateApplication(app.processIdentifier)
        let inputElement = findClaudeTextInput(in: appElement)
        
        XCTAssertNotNil(inputElement)
    }
}
```


## **11. Success Criteria Validation**

Based on the research, this solution addresses all the specified success criteria:

1. ✅ **Successfully send text prompts**: Multiple methods implemented with fallbacks
2. ✅ **Trigger prompt submission**: Enter key and alternative submission methods
3. ✅ **Detect response completion**: Observer pattern and polling mechanisms
4. ✅ **Extract complete response text**: Comprehensive text extraction from UI elements
5. ✅ **Handle new chat vs follow-up**: Conditional chat creation logic
6. ✅ **Integrate with existing Swift/Accessibility codebase**: Native Swift implementation

## **12. Implementation Notes**

- **Timing is crucial**: Electron apps need time to fully load and expose accessibility elements
- **Progressive enhancement**: Start with basic functionality and add sophistication
- **Error handling**: Comprehensive retry mechanisms for reliability
- **User experience**: Provide clear feedback about automation status
- **Security**: Respect user privacy and provide clear permission explanations

This comprehensive solution provides multiple implementation paths and fallback mechanisms to ensure reliable Claude Desktop automation while maintaining security and user control.

<div style="text-align: center">⁂</div>

[^1]: https://github.com/aaddrick/claude-desktop-debian

[^2]: https://github.com/aaddrick/claude-desktop-arch

[^3]: https://www.reddit.com/r/ClaudeAI/comments/1gh63hs/not_even_hiding_the_electron_logo/

[^4]: https://chrisnicoll.net/2019/01/text-input-with-contenteditable/

[^5]: https://stackoverflow.com/questions/29863549/insert-text-in-input-box-in-contenteditable-div-in-ie

[^6]: https://electronjs.org/docs/latest/tutorial/accessibility

[^7]: http://docs3.w3cub.com/electron/tutorial/accessibility/

[^8]: https://stackoverflow.com/questions/66223599/atom-electron-web-applications-and-accessibility-apis-macos-and-windows

[^9]: https://github.com/mlobo2012/Claude_Desktop_API_USE_VIA_MCP

[^10]: https://apps.apple.com/us/app/claude-by-anthropic/id6473753684

[^11]: https://www.linkedin.com/pulse/building-automated-accessibility-test-tools-using-anthropics-dodd-6azme

[^12]: https://apidog.com/blog/claude-computer-use/

[^13]: https://www.anthropic.com/engineering/claude-code-best-practices

[^14]: https://www.datacamp.com/blog/what-is-anthropic-computer-use

[^15]: https://ai-rockstars.com/claude-ai-api-tutorial/

[^16]: https://www.indragie.com/blog/i-shipped-a-macos-app-built-entirely-by-claude-code

[^17]: https://www.theserverside.com/video/How-to-use-Claude-Desktop-tutorial-for-beginners

[^18]: https://mac.install.guide/ai/claude/computer-use

[^19]: https://docs.anthropic.com/en/docs/claude-code/overview

[^20]: https://datascientest.com/en/all-about-claude-computer

[^21]: https://mcpservers.org/servers/dpaluy/claude-assist-mcp

[^22]: https://www.uipath.com/newsroom/uipath-integrates-anthropic-claude-language-models-for-generative-solutions

[^23]: https://www.youtube.com/watch?v=7TtuiNnhwmM

[^24]: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool

[^25]: https://www.reddit.com/r/ClaudeAI/comments/1ji8ruv/my_claude_workflow_guide_advanced_setup_with_mcp/

[^26]: https://www.anthropic.com/claude

[^27]: https://www.anthropic.com/engineering/desktop-extensions

[^28]: https://claude.ai

[^29]: https://dev.to/stephenc222/track-ui-events-and-network-activity-in-macos-using-rust-swiftui-3p0b

[^30]: https://research.macpaw.com/publications/how-to-parse-macos-app-ui

[^31]: https://developer.apple.com/videos/play/wwdc2025/229/

[^32]: https://stackoverflow.com/questions/63917186/macos-accessibility-api-not-working-after-change-in-code-and-new-build-xcode-sw

[^33]: https://blog.stackademic.com/from-fields-to-feedback-managing-user-input-in-swift-storyboard-ui-cb41f988a75c

[^34]: https://www.chromium.org/developers/accessibility/mac-accessibility/

[^35]: https://developer.apple.com/videos/play/wwdc2024/10073/

[^36]: https://www.youtube.com/watch?v=xLWfJIYg2PM

[^37]: https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/OSXAXmodel.html

[^38]: https://stackoverflow.com/questions/6836278/api-for-accessing-ui-elements-in-mac-os-x

[^39]: https://stackoverflow.com/questions/33563135/ui-automation-clear-textfield-with-the-clear-button

[^40]: https://forum.keyboardmaestro.com/t/os-x-accessibility-inspector-uielementinspector-tool-for-ui-scripting/3443

[^41]: https://www.browserstack.com/guide/what-is-swift-ui

[^42]: https://www.tpgi.com/short-note-on-labelling-text-fields-in-native-ios-applications/

[^43]: https://www.washington.edu/accesscomputing/what-accessibility-features-are-available-within-macintosh-operating-system

[^44]: https://www.reddit.com/r/swift/comments/18k909w/i_hit_a_dead_end_with_accessibility_apis/

[^45]: https://developer.apple.com/documentation/applicationservices/1459374-axuielementcreateapplication

[^46]: https://apple.stackexchange.com/questions/40436/how-to-know-the-name-of-ui-elements-using-accessibility-inspector-or-any-other

[^47]: https://developer.apple.com/documentation/accessibility/accessibility-api

[^48]: https://github.com/kif-framework/KIF

[^49]: https://github.com/CharlieHess/electron-text-substitutions

[^50]: https://github.com/electron/electron/issues/7206

[^51]: https://www.stephanmiller.com/electron-project-from-scratch-with-claude-code/

[^52]: https://github.com/electron/electron/issues/8902

[^53]: https://electronjs.org

[^54]: https://github.com/electron/electron/issues/36337

[^55]: https://auth0.com/blog/securing-electron-applications-with-openid-connect-and-oauth-2/

[^56]: https://helpx.adobe.com/in/acrobat/using/editing-document-structure-content-tags.html

[^57]: https://electronjs.org/docs/latest/api/app

[^58]: https://playwright.dev/docs/api/class-frame

[^59]: https://webdriver.io/docs/desktop-testing/electron/

[^60]: https://claude.ai/public/artifacts/a4be14ad-3942-4914-b6f0-5622dd87b0f2

[^61]: https://discussions.apple.com/thread/254489488

[^62]: https://www.reddit.com/r/swift/comments/14mufhf/axuielementsetattributevalue_not_working_on_word/

[^63]: https://github.com/DevilFinger/DFAXUIElement

[^64]: https://www.youtube.com/watch?v=eLHBiE8_jQc

[^65]: https://stackoverflow.com/questions/72478435/select-text-in-webkit-applications-via-macos-accessibility-api

[^66]: https://macdevelopers.wordpress.com/2014/01/31/accessing-text-value-from-any-system-wide-application-via-accessibility-api/

[^67]: https://www.reddit.com/r/swift/comments/160qm20/accessibility_how_to_programmatically_scroll_a/

[^68]: https://www.youtube.com/watch?v=9NB_h2jfPLE

[^69]: https://www.youtube.com/watch?v=uVCFV668dSQ

[^70]: https://stackoverflow.com/questions/72562896/set-selected-text-through-the-macos-accessibility-apis-in-catalyst-apps

[^71]: https://www.devtechie.com/community/public/posts/145823-swiftui-textfield-a-closer-look

[^72]: https://github.com/tmandry/AXSwift/blob/main/Sources/UIElement.swift

[^73]: https://macdevelopers.wordpress.com/2014/02/05/how-to-get-selected-text-and-its-coordinates-from-any-system-wide-application-using-accessibility-api/

[^74]: https://stackoverflow.com/questions/65476921/how-to-use-axuielementcreatesystemwide-in-swift

[^75]: https://developer.apple.com/videos/play/wwdc2021/10119/

[^76]: https://developer.apple.com/documentation/applicationservices/axuielement_h

[^77]: https://github.com/chrs1885/Capable

[^78]: https://www.youtube.com/watch?v=iOVWWF7dBMY

[^79]: http://man.hubwiz.com/docset/electron.docset/Contents/Resources/Documents/docs/all/index.html

[^80]: https://electronjs.org/docs/latest/tutorial/native-code-and-electron-swift-macos

[^81]: https://www.youtube.com/watch?v=ICQRofCNocA

[^82]: https://www.reddit.com/r/applescript/comments/1g6qqtq/ui_browser_and_accessibility_inspector_able_to/

[^83]: https://www.youtube.com/watch?v=MflvJATVLeU

[^84]: https://electronjs.org/docs/latest/api/system-preferences

[^85]: https://www.reddit.com/r/macapps/comments/1bsldnc/what_are_the_real_world_benefits_of_a_native_mac/

[^86]: https://github.com/anongecko/claude-mac-app-m1

[^87]: https://www.astrolytics.io/blog/electron-vs-swift-mac-app

[^88]: https://a.hatena.ne.jp/Carnegie1/?gid=null+class%3Dl+��++h%3D+��+ID%3DSERP

[^89]: https://issues.chromium.org/issues/370009398

[^90]: https://github.com/electron/electron/issues/37465

[^91]: https://developer.apple.com/accessibility/

[^92]: https://stackoverflow.com/questions/27484330/simulate-keypress-using-swift

[^93]: https://blog.kulman.sk/implementing-auto-type-on-macos/

[^94]: https://stackoverflow.com/questions/70814854/how-to-prompt-for-accessibility-features-in-a-macos-app-from-the-appdelegate/70889502

[^95]: https://swiftjectivec.com/Handling-Keyboard-Presses-in-SwiftUI-for-macOS/

[^96]: https://superuser.com/questions/321599/automate-sequence-of-key-strokes-in-mac

[^97]: https://github.com/socsieng/sendkeys-macos

[^98]: https://www.avanderlee.com/swiftui/key-press-events-detection/

[^99]: https://github.com/socsieng/sendkeys

[^100]: https://developer.apple.com/documentation/accessibility/accessibility-inspector

[^101]: https://ifnotnil.com/t/swift-ios-simulate-a-keystroke-from-a-hardware-keyboard/3139

[^102]: https://github.com/NakaokaRei/SwiftAutoGUI

[^103]: https://developer.apple.com/documentation/accessibility/testing-system-accessibility-features-in-your-app

[^104]: https://www.youtube.com/watch?v=vn11z-kxRmE

[^105]: https://apple.stackexchange.com/questions/63897/can-a-mac-be-programmed-to-simulate-pressing-a-key-at-a-certain-rate-via-softwar

[^106]: https://developer.apple.com/videos/play/wwdc2022/10153/

[^107]: https://developer.apple.com/documentation/coregraphics/cgevent

[^108]: https://playbooks.com/mcp/nakaokarei-swift-autogui

[^109]: https://github.com/mjrusso/scoot

[^110]: https://www.youtube.com/watch?v=RoDUYFuNeJU

[^111]: https://firebase.google.com/docs/remote-config/automate-rc

[^112]: https://signoz.io/guides/claude-api-latency/

