//
//  AccessibilityAPIAutomator.swift
//  Samay_MacOS
//
//  Alternative to Apple Events using Accessibility API
//  This approach only requires Accessibility permissions, not Apple Events
//

import Foundation
import ApplicationServices
import AppKit

class AccessibilityAPIAutomator {
    static let shared = AccessibilityAPIAutomator()
    
    private init() {}
    
    // MARK: - Permission Checking
    
    func checkAccessibilityPermissions() -> Bool {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false]
        return AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    func requestAccessibilityPermissions() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        _ = AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    // MARK: - App Detection and Control
    
    func isAppRunning(_ bundleIdentifier: String) -> Bool {
        let runningApps = NSWorkspace.shared.runningApplications
        return runningApps.contains { $0.bundleIdentifier == bundleIdentifier }
    }
    
    func launchApp(_ bundleIdentifier: String) -> Bool {
        if let appURL = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleIdentifier) {
            do {
                try NSWorkspace.shared.launchApplication(at: appURL, options: [], configuration: [:])
                return true
            } catch {
                print("Failed to launch app: \(error)")
                return false
            }
        }
        return false
    }
    
    func getAppProcessElement(_ bundleIdentifier: String) -> AXUIElement? {
        guard let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == bundleIdentifier }) else {
            return nil
        }
        
        let appElement = AXUIElementCreateApplication(app.processIdentifier)
        
        // Enable manual accessibility for Electron apps (31first.md approach)
        if bundleIdentifier == "com.anthropic.claudefordesktop" || 
           bundleIdentifier == "com.openai.chat" {
            let accessibilityResult = AXUIElementSetAttributeValue(
                appElement, 
                "AXManualAccessibility" as CFString, 
                kCFBooleanTrue
            )
            print("🔧 AXManualAccessibility: \(accessibilityResult == .success ? "✅" : "❌")")
            
            // Wait for accessibility tree to be exposed
            usleep(1_000_000) // 1 second delay for Electron
        }
        
        return appElement
    }
    
    // MARK: - Window Management (31first.md approach)
    
    func raiseAndActivateWindow(_ appElement: AXUIElement) -> Bool {
        print("🪟 Raising and activating window...")
        
        // Get windows array
        var windows: CFTypeRef?
        let windowsResult = AXUIElementCopyAttributeValue(appElement, kAXWindowsAttribute as CFString, &windows)
        
        guard windowsResult == .success,
              let windowArray = windows as? [AXUIElement],
              !windowArray.isEmpty else {
            print("❌ Could not get windows")
            return false
        }
        
        let mainWindow = windowArray[0]
        
        // Perform raise action
        let raiseResult = AXUIElementPerformAction(mainWindow, kAXRaiseAction as CFString)
        print("🔼 Raise action: \(raiseResult == .success ? "✅" : "❌")")
        
        // Small delay between actions
        usleep(200_000) // 200ms
        
        // Perform main/activate action  
        let mainResult = AXUIElementPerformAction(mainWindow, "AXMain" as CFString)
        print("🎯 Main action: \(mainResult == .success ? "✅" : "❌")")
        
        return raiseResult == .success && mainResult == .success
    }
    
    // MARK: - Text Input Finding (31first.md approach)
    
    func findTextInputInWebArea(_ appElement: AXUIElement) -> AXUIElement? {
        print("🔍 Searching for text input in web areas...")
        
        // Find web areas first
        let webAreas = findAllElementsByRole(in: appElement, role: "AXWebArea", maxDepth: 6)
        print("🌐 Found \(webAreas.count) web areas")
        
        for webArea in webAreas {
            // Look for settable value elements (content-editable areas)
            if let textInput = findSettableTextElement(in: webArea, maxDepth: 8) {
                print("✅ Found settable text element in web area")
                return textInput
            }
        }
        
        return nil
    }
    
    func findSettableTextElement(in element: AXUIElement, maxDepth: Int) -> AXUIElement? {
        if maxDepth <= 0 { return nil }
        
        // Check if this element supports setting values
        var isSettable: DarwinBoolean = false
        let settableResult = AXUIElementIsAttributeSettable(element, kAXValueAttribute as CFString, &isSettable)
        
        if settableResult == .success && isSettable.boolValue {
            return element
        }
        
        // Recursively check children
        var children: CFTypeRef?
        if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
           let childArray = children as? [AXUIElement] {
            for child in childArray {
                if let found = findSettableTextElement(in: child, maxDepth: maxDepth - 1) {
                    return found
                }
            }
        }
        
        return nil
    }
    
    // MARK: - Cursor Shape Verification (31first.md fallback)
    
    func moveMouseToElementAndVerifyCursor(_ element: AXUIElement) -> Bool {
        print("🖱️ Moving mouse to element for cursor verification...")
        
        // Get element bounds
        var frame: CFTypeRef?
        let frameResult = AXUIElementCopyAttributeValue(element, "AXFrame" as CFString, &frame)
        
        guard frameResult == .success,
              let frameValue = frame as? NSValue else {
            print("❌ Could not get element frame")
            return false
        }
        
        let bounds = frameValue.rectValue
        let centerPoint = CGPoint(x: bounds.midX, y: bounds.midY)
        
        // Move mouse to center of element
        CGWarpMouseCursorPosition(centerPoint)
        print("🎯 Mouse moved to: (\(centerPoint.x), \(centerPoint.y))")
        
        // Wait and check for I-beam cursor
        let maxAttempts = 10
        for attempt in 1...maxAttempts {
            usleep(50_000) // 50ms delay
            
            if NSCursor.current == NSCursor.iBeam {
                print("✅ I-beam cursor detected (attempt \(attempt))")
                return true
            }
        }
        
        print("⚠️ I-beam cursor not detected after \(maxAttempts) attempts")
        return false
    }
    
    // MARK: - Element Focus with Press Action (31first.md approach)
    
    func focusElementWithPress(_ element: AXUIElement) -> Bool {
        print("🎯 Focusing element with AXPress action...")
        
        let pressResult = AXUIElementPerformAction(element, kAXPressAction as CFString)
        let success = pressResult == .success
        
        print("👆 Press action: \(success ? "✅" : "❌")")
        
        if success {
            usleep(300_000) // 300ms delay after press
        }
        
        return success
    }

    // MARK: - Complete 31first.md Automation Flow
    
    func automateTextInputWith31FirstApproach(_ appElement: AXUIElement, query: String) -> Bool {
        print("🚀 Starting 31first.md automation approach...")
        print("📝 Query to send: \"\(query)\"")
        
        // Step 1: Raise and activate window
        print("🪟 Step 1: Raising and activating window...")
        guard raiseAndActivateWindow(appElement) else {
            print("❌ FAILED: Could not raise and activate window")
            return false
        }
        print("✅ Window raise/activate successful")
        
        usleep(500_000) // 500ms delay after window operations
        
        // Step 2: Find text input in web area (Electron approach)
        print("🔍 Step 2: Finding text input in web area...")
        guard let textInput = findTextInputInWebArea(appElement) else {
            print("❌ FAILED: Could not find text input in web areas")
            
            // Try alternative strategies
            print("🔄 Trying alternative text input strategies...")
            if let altInput = findAnyEditableElement(in: appElement, maxDepth: 12) {
                print("✅ Found alternative editable element")
                return continueAutomationWithElement(altInput, query: query)
            }
            
            return false
        }
        print("✅ Found text input in web area")
        
        return continueAutomationWithElement(textInput, query: query)
    }
    
    private func continueAutomationWithElement(_ textInput: AXUIElement, query: String) -> Bool {
        // Step 3: Focus element with press action
        print("🎯 Step 3: Focusing element with press action...")
        if !focusElementWithPress(textInput) {
            print("❌ Initial focus failed, trying cursor verification fallback...")
            
            // Fallback: Try cursor verification approach
            if moveMouseToElementAndVerifyCursor(textInput) {
                print("✅ Cursor verification successful, retrying focus...")
                if !focusElementWithPress(textInput) {
                    print("❌ FAILED: Focus still failed after cursor verification")
                    return false
                }
            } else {
                print("❌ FAILED: Both focus and cursor verification failed")
                return false
            }
        }
        print("✅ Element focus successful")
        
        usleep(300_000) // 300ms delay after focus
        
        // Step 4: Send text directly via AX value
        print("📝 Step 4: Setting text value via AX API...")
        let setValueResult = AXUIElementSetAttributeValue(
            textInput, 
            kAXValueAttribute as CFString, 
            query as CFString
        )
        
        let textSetSuccess = setValueResult == .success
        print("✍️ Text set result: \(textSetSuccess ? "✅" : "❌") (AXError: \(setValueResult.rawValue))")
        
        if !textSetSuccess {
            // Try alternative text input methods
            print("🔄 Trying alternative text input methods...")
            if sendTextViaKeystrokes(query) {
                print("✅ Text sent via keystrokes")
            } else {
                print("❌ FAILED: All text input methods failed")
                return false
            }
        }
        
        usleep(200_000) // 200ms delay before submit
        
        // Step 5: Submit via Enter key
        print("📤 Step 5: Submitting via Enter key...")
        let submitSuccess = sendEnterKey()
        print("🚀 Submit result: \(submitSuccess ? "✅" : "❌")")
        
        return textSetSuccess || submitSuccess
    }

    // MARK: - UI Element Interaction
    
    func findTextArea(in appElement: AXUIElement, containing text: String? = nil) -> AXUIElement? {
        // Enhanced multi-strategy approach for finding text input elements
        
        // Strategy 1: Traditional roles (depth 3)
        if let textArea = findElementByRole(in: appElement, role: kAXTextAreaRole, maxDepth: 5) {
            return textArea
        }
        
        if let textField = findElementByRole(in: appElement, role: kAXTextFieldRole, maxDepth: 5) {
            return textField
        }
        
        // Strategy 2: Look for WebView containers (Electron apps)
        if let webViewElement = findWebViewContainer(in: appElement) {
            // Search within the WebView for text input elements
            if let textInput = findElementByRole(in: webViewElement, role: kAXTextAreaRole, maxDepth: 10) {
                return textInput
            }
            if let textInput = findElementByRole(in: webViewElement, role: kAXTextFieldRole, maxDepth: 10) {
                return textInput
            }
        }
        
        // Strategy 3: Search by attributes (placeholder, description)
        if let inputElement = findElementWithAttribute(in: appElement, attribute: kAXPlaceholderValueAttribute, maxDepth: 8) {
            return inputElement
        }
        
        // Strategy 4: Search for elements with specific text content (Claude-specific)
        if let messageElement = findElementContainingText(in: appElement, text: "Message Claude", maxDepth: 8) {
            return messageElement
        }
        
        // Strategy 5: Any editable element (broad search)
        if let editableElement = findEditableElement(in: appElement, maxDepth: 8) {
            return editableElement
        }
        
        // Strategy 6: Look for elements that can receive keyboard input
        if let focusableElement = findFocusableTextElement(in: appElement, maxDepth: 8) {
            return focusableElement
        }
        
        return nil
    }
    
    func findEditableElement(in parent: AXUIElement, maxDepth: Int = 5, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check if element is editable
            var editableValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXValueAttribute as CFString, &editableValue) == .success {
                // If we can get a value, try to see if we can set it (indicates editability)
                var focusedValue: CFTypeRef?
                if AXUIElementCopyAttributeValue(child, kAXFocusedAttribute as CFString, &focusedValue) == .success {
                    return child
                }
            }
            
            // Recursively search children
            if let found = findEditableElement(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findElementWithAttribute(in parent: AXUIElement, attribute: String, maxDepth: Int = 5, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check if element has the specified attribute
            var attributeValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, attribute as CFString, &attributeValue) == .success {
                return child
            }
            
            // Recursively search children
            if let found = findElementWithAttribute(in: child, attribute: attribute, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findElementByRole(in parent: AXUIElement, role: String, maxDepth: Int = 5, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            var roleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &roleValue) == .success,
               let childRole = roleValue as? String, childRole == role {
                return child
            }
            
            // Recursively search children
            if let found = findElementByRole(in: child, role: role, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    // MARK: - Advanced Detection Methods for Electron Apps
    
    func findWebViewContainer(in parent: AXUIElement, maxDepth: Int = 8, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            var roleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &roleValue) == .success,
               let childRole = roleValue as? String {
                // Look for WebView or similar container roles
                if childRole.contains("WebArea") || childRole.contains("Web") || 
                   childRole == "AXWebArea" || childRole == "AXGroup" {
                    return child
                }
            }
            
            // Recursively search children
            if let found = findWebViewContainer(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findElementContainingText(in parent: AXUIElement, text: String, maxDepth: Int = 8, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check various text attributes
            let textAttributes = [
                kAXValueAttribute,
                kAXTitleAttribute,
                kAXDescriptionAttribute,
                kAXPlaceholderValueAttribute,
                kAXHelpAttribute
            ]
            
            for attribute in textAttributes {
                var attributeValue: CFTypeRef?
                if AXUIElementCopyAttributeValue(child, attribute as CFString, &attributeValue) == .success,
                   let textValue = attributeValue as? String,
                   textValue.lowercased().contains(text.lowercased()) {
                    return child
                }
            }
            
            // Recursively search children
            if let found = findElementContainingText(in: child, text: text, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findFocusableTextElement(in parent: AXUIElement, maxDepth: Int = 8, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check if element can be focused and accepts text input
            var focusableValue: CFTypeRef?
            var editableValue: CFTypeRef?
            
            let canFocus = AXUIElementCopyAttributeValue(child, kAXFocusedAttribute as CFString, &focusableValue) == .success
            let hasValue = AXUIElementCopyAttributeValue(child, kAXValueAttribute as CFString, &editableValue) == .success
            
            if canFocus && hasValue {
                // Additional check: see if it accepts keyboard input
                var roleValue: CFTypeRef?
                if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &roleValue) == .success,
                   let role = roleValue as? String {
                    // Text-related roles that might accept input
                    if role.contains("Text") || role.contains("Edit") || role.contains("Field") {
                        return child
                    }
                }
            }
            
            // Recursively search children
            if let found = findFocusableTextElement(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func clickElement(_ element: AXUIElement) -> Bool {
        let result = AXUIElementPerformAction(element, kAXPressAction as CFString)
        return result == .success
    }
    
    func setElementValue(_ element: AXUIElement, value: String) -> Bool {
        let result = AXUIElementSetAttributeValue(element, kAXValueAttribute as CFString, value as CFString)
        return result == .success
    }
    
    func getElementValue(_ element: AXUIElement) -> String? {
        var value: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &value)
        
        guard result == .success else { return nil }
        return value as? String
    }
    
    func focusElement(_ element: AXUIElement) -> Bool {
        let result = AXUIElementSetAttributeValue(element, kAXFocusedAttribute as CFString, kCFBooleanTrue)
        return result == .success
    }
    
    // MARK: - Electron App Specific Methods (Enhanced with 31first.md solution)
    
    func findClaudeTextInput(in appElement: AXUIElement) -> AXUIElement? {
        print("🔍 Claude Electron-based text input detection (31first.md method)...")
        
        // Strategy 1: Look for AXWebArea containers first (31first.md approach)
        let webAreas = findAllElementsByRole(in: appElement, role: "AXWebArea", maxDepth: 8)
        print("🌐 Found \(webAreas.count) AXWebArea elements")
        
        for webArea in webAreas {
            if let textInput = findSettableTextElement(in: webArea, maxDepth: 8) {
                print("✅ Found settable text input in AXWebArea")
                return textInput
            }
        }
        
        // Strategy 2: Search for contentEditable elements (31first.md)
        if let contentEditable = findContentEditableElement(in: appElement, maxDepth: 10) {
            print("✅ Found contentEditable element")
            return contentEditable
        }
        
        // Strategy 3: Look for web-based roles with settable values
        let webRoles = ["AXWebArea", "AXGroup", "AXTextField", "AXTextArea"]
        for role in webRoles {
            print("🔍 Searching for role: \(role)")
            if let element = findElementByRole(in: appElement, role: role, maxDepth: 10) {
                // Verify if it's editable (contentEditable or settable value)
                var isEditable: DarwinBoolean = false
                let editableResult = AXUIElementIsAttributeSettable(
                    element,
                    kAXValueAttribute as CFString,
                    &isEditable
                )
                
                if editableResult == .success && isEditable.boolValue {
                    print("✅ Found editable element with role: \(role)")
                    return element
                }
            }
        }
        
        // Strategy 4: Search for any element that can receive text input
        if let editableElement = findAnyEditableElement(in: appElement, maxDepth: 10) {
            print("✅ Found editable element via comprehensive search")
            return editableElement
        }
        
        // Strategy 5: Look for elements with input-related attributes  
        if let inputElement = findElementWithAttribute(in: appElement, attribute: kAXPlaceholderValueAttribute, maxDepth: 10) {
            print("✅ Found element with placeholder attribute")
            return inputElement
        }
        
        print("❌ No text input element found in Claude Desktop")
        return nil
    }
    
    func findAllElementsByRole(in parent: AXUIElement, role: String, maxDepth: Int = 5, currentDepth: Int = 0) -> [AXUIElement] {
        if currentDepth >= maxDepth { return [] }
        
        var results: [AXUIElement] = []
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return results
        }
        
        for child in childArray {
            var roleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &roleValue) == .success,
               let childRole = roleValue as? String, childRole == role {
                results.append(child)
            }
            
            // Recursively search children
            results.append(contentsOf: findAllElementsByRole(in: child, role: role, maxDepth: maxDepth, currentDepth: currentDepth + 1))
        }
        
        return results
    }
    
    
    func findContentEditableElement(in parent: AXUIElement, maxDepth: Int = 5, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check for contentEditable indication via description
            var descValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXDescriptionAttribute as CFString, &descValue) == .success,
               let desc = descValue as? String,
               desc.lowercased().contains("contenteditable") || desc.lowercased().contains("editable") {
                
                // Verify it's actually settable
                var isSettable: DarwinBoolean = false
                if AXUIElementIsAttributeSettable(child, kAXValueAttribute as CFString, &isSettable) == .success && isSettable.boolValue {
                    return child
                }
            }
            
            // Recursively search children
            if let found = findContentEditableElement(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findAnyEditableElement(in parent: AXUIElement, maxDepth: Int = 5, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check if element can have its value set (indicates text input)
            var isEditable: DarwinBoolean = false
            let editableResult = AXUIElementIsAttributeSettable(
                child,
                kAXValueAttribute as CFString,
                &isEditable
            )
            
            if editableResult == .success && isEditable.boolValue {
                // Double-check by trying to get current value
                var currentValue: CFTypeRef?
                if AXUIElementCopyAttributeValue(child, kAXValueAttribute as CFString, &currentValue) == .success {
                    print("📝 Found potential text input element at depth \(currentDepth)")
                    return child
                }
            }
            
            // Recursively search children
            if let found = findAnyEditableElement(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findElementWithHTMLAttribute(in parent: AXUIElement, attribute: String, value: String, maxDepth: Int = 10, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check for HTML/DOM attributes that Electron exposes
            var descValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXDescriptionAttribute as CFString, &descValue) == .success,
               let desc = descValue as? String,
               desc.contains("\(attribute)=\"\(value)\"") {
                return child
            }
            
            // Check DOM attribute through accessibility
            var domAttributeValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, "AXDOM\(attribute.capitalized)" as CFString, &domAttributeValue) == .success,
               let domValue = domAttributeValue as? String,
               domValue == value {
                return child
            }
            
            // Recursively search children
            if let found = findElementWithHTMLAttribute(in: child, attribute: attribute, value: value, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findElementWithARIARole(in parent: AXUIElement, role: String, maxDepth: Int = 10, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check for ARIA roles
            var roleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, "AXDOMRole" as CFString, &roleValue) == .success,
               let ariaRole = roleValue as? String,
               ariaRole == role {
                return child
            }
            
            // Also check standard AX role for ARIA mappings
            var axRoleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &axRoleValue) == .success,
               let axRole = axRoleValue as? String {
                // Map common ARIA roles to AX roles
                let roleMapping = ["textbox": "AXTextField", "button": "AXButton", "link": "AXLink"]
                if roleMapping[role] == axRole {
                    return child
                }
            }
            
            // Recursively search children
            if let found = findElementWithARIARole(in: child, role: role, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findHTMLInputElement(in parent: AXUIElement, maxDepth: Int = 10, currentDepth: Int = 0) -> AXUIElement? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(parent, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check for HTML tag names that Electron might expose
            var tagValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, "AXDOMTag" as CFString, &tagValue) == .success,
               let tagName = tagValue as? String {
                if tagName.lowercased() == "input" || tagName.lowercased() == "textarea" {
                    return child
                }
            }
            
            // Check description for HTML signatures
            var descValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXDescriptionAttribute as CFString, &descValue) == .success,
               let desc = descValue as? String {
                if desc.contains("<input") || desc.contains("<textarea") || desc.contains("[object HTMLInputElement]") {
                    return child
                }
            }
            
            // Recursively search children
            if let found = findHTMLInputElement(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    // MARK: - Fallback Automation Methods
    
    func sendTextViaKeyboard(_ text: String) -> Bool {
        // Clear any existing content with Cmd+A, Delete
        let selectAllEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x00, keyDown: true) // A key
        selectAllEvent?.flags = .maskCommand
        selectAllEvent?.post(tap: .cghidEventTap)
        
        let selectAllUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x00, keyDown: false)
        selectAllUpEvent?.flags = .maskCommand
        selectAllUpEvent?.post(tap: .cghidEventTap)
        
        // Delete selected content
        let deleteEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.delete.rawValue, keyDown: true)
        deleteEvent?.post(tap: .cghidEventTap)
        let deleteUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.delete.rawValue, keyDown: false)
        deleteUpEvent?.post(tap: .cghidEventTap)
        
        // Type the text character by character
        for char in text {
            if let keyCode = virtualKeyForCharacter(char) {
                let keyDownEvent = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true)
                keyDownEvent?.post(tap: .cghidEventTap)
                let keyUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false)
                keyUpEvent?.post(tap: .cghidEventTap)
                
                // Small delay between characters
                usleep(10000) // 10ms
            }
        }
        
        return true
    }
    
    func sendTextViaClipboard(_ text: String) -> Bool {
        // Save current clipboard content
        let pasteboard = NSPasteboard.general
        let originalContent = pasteboard.string(forType: .string)
        
        // Set our text to clipboard
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
        
        // Paste the content with Cmd+V
        let pasteEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x09, keyDown: true) // V key
        pasteEvent?.flags = .maskCommand
        pasteEvent?.post(tap: .cghidEventTap)
        
        let pasteUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x09, keyDown: false)
        pasteUpEvent?.flags = .maskCommand
        pasteUpEvent?.post(tap: .cghidEventTap)
        
        // Restore original clipboard content after a delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            if let original = originalContent {
                pasteboard.clearContents()
                pasteboard.setString(original, forType: .string)
            }
        }
        
        return true
    }
    
    func focusAppWithKeyboard(_ bundleId: String) -> Bool {
        // Use Cmd+Tab to focus the application
        guard let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == bundleId }) else {
            return false
        }
        
        // Activate the application
        return app.activate(options: [.activateIgnoringOtherApps])
    }
    
    func automateWithScreenCoordinates(_ bundleId: String, inputCoordinates: CGPoint, text: String) -> Bool {
        // Activate the app first
        guard focusAppWithKeyboard(bundleId) else { return false }
        
        // Wait for app to become active
        usleep(500000) // 0.5 seconds
        
        // Click at the specified coordinates
        let clickEvent = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: inputCoordinates, mouseButton: .left)
        clickEvent?.post(tap: .cghidEventTap)
        
        let clickUpEvent = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: inputCoordinates, mouseButton: .left)
        clickUpEvent?.post(tap: .cghidEventTap)
        
        // Wait a bit for focus
        usleep(200000) // 0.2 seconds
        
        // Send the text via clipboard (more reliable than keyboard)
        return sendTextViaClipboard(text)
    }
    
    func sendEnterKey() -> Bool {
        let enterEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.enter.rawValue, keyDown: true)
        enterEvent?.post(tap: .cghidEventTap)
        let enterUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.enter.rawValue, keyDown: false)
        enterUpEvent?.post(tap: .cghidEventTap)
        return true
    }
    
    func sendBackspaceKey() -> Bool {
        let backspaceEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.delete.rawValue, keyDown: true)
        backspaceEvent?.post(tap: .cghidEventTap)
        let backspaceUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.delete.rawValue, keyDown: false)
        backspaceUpEvent?.post(tap: .cghidEventTap)
        return true
    }
    
    private func virtualKeyForCharacter(_ char: Character) -> CGKeyCode? {
        // Basic character to virtual key mapping
        switch char.lowercased().first {
        case "a": return 0x00
        case "b": return 0x0B
        case "c": return 0x08
        case "d": return 0x02
        case "e": return 0x0E
        case "f": return 0x03
        case "g": return 0x05
        case "h": return 0x04
        case "i": return 0x22
        case "j": return 0x26
        case "k": return 0x28
        case "l": return 0x25
        case "m": return 0x2E
        case "n": return 0x2D
        case "o": return 0x1F
        case "p": return 0x23
        case "q": return 0x0C
        case "r": return 0x0F
        case "s": return 0x01
        case "t": return 0x11
        case "u": return 0x20
        case "v": return 0x09
        case "w": return 0x0D
        case "x": return 0x07
        case "y": return 0x10
        case "z": return 0x06
        case " ": return VirtualKey.space.rawValue
        default: return nil
        }
    }
    
    // MARK: - Missing Automation Helper Methods
    
    func sendTextViaKeystrokes(_ text: String) -> Bool {
        print("⌨️ Sending text via keystrokes: \"\(text)\"")
        
        // Clear any existing content first
        let selectAllSuccess = sendCmdAKey() && sendDeleteKey()
        if !selectAllSuccess {
            print("⚠️ Could not clear existing content")
        }
        
        // Send each character
        for char in text {
            if !sendCharacterKey(char) {
                print("❌ Failed to send character: \(char)")
                return false
            }
            usleep(10_000) // 10ms delay between characters
        }
        
        print("✅ Text sent via keystrokes")
        return true
    }
    
    private func sendCmdAKey() -> Bool {
        let selectAllEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x00, keyDown: true) // A key
        selectAllEvent?.flags = .maskCommand
        selectAllEvent?.post(tap: .cghidEventTap)
        
        let selectAllUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x00, keyDown: false)
        selectAllUpEvent?.flags = .maskCommand
        selectAllUpEvent?.post(tap: .cghidEventTap)
        
        usleep(50_000) // 50ms delay
        return true
    }
    
    private func sendDeleteKey() -> Bool {
        let deleteEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.delete.rawValue, keyDown: true)
        deleteEvent?.post(tap: .cghidEventTap)
        let deleteUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.delete.rawValue, keyDown: false)
        deleteUpEvent?.post(tap: .cghidEventTap)
        
        usleep(50_000) // 50ms delay
        return true
    }
    
    private func sendCharacterKey(_ char: Character) -> Bool {
        let charString = String(char)
        
        // Use CGEventCreateKeyboardEvent for character input
        if let unicodeScalar = charString.unicodeScalars.first {
            let keyCode = UInt16(unicodeScalar.value)
            
            // Create unicode keyboard event
            let keyDownEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: true)
            keyDownEvent?.keyboardSetUnicodeString(stringLength: 1, unicodeString: [keyCode])
            keyDownEvent?.post(tap: .cghidEventTap)
            
            let keyUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: false)
            keyUpEvent?.keyboardSetUnicodeString(stringLength: 1, unicodeString: [keyCode])
            keyUpEvent?.post(tap: .cghidEventTap)
            
            return true
        }
        
        return false
    }
    
    
    // MARK: - Window Management (31first.md solution)
    
    func raiseAndActivateClaudeWindow(_ appElement: AXUIElement) -> Bool {
        print("🪟 Raising and activating Claude window...")
        
        var windows: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appElement, kAXWindowsAttribute as CFString, &windows)
        
        guard result == .success, let windowArray = windows as? [AXUIElement], !windowArray.isEmpty else {
            print("❌ No windows found for Claude")
            return false
        }
        
        let mainWindow = windowArray[0]
        
        // First raise the window
        let raiseResult = AXUIElementPerformAction(mainWindow, kAXRaiseAction as CFString)
        print("🔼 Window raise: \(raiseResult == .success ? "✅" : "❌")")
        
        // Then make it the main window
        let mainResult = AXUIElementPerformAction(mainWindow, "AXMain" as CFString)
        print("🎯 Window main: \(mainResult == .success ? "✅" : "❌")")
        
        return raiseResult == .success || mainResult == .success
    }
    
    func getClaudeWindowBounds(_ appElement: AXUIElement) -> CGRect? {
        var windows: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appElement, kAXWindowsAttribute as CFString, &windows)
        
        guard result == .success, let windowArray = windows as? [AXUIElement], !windowArray.isEmpty else {
            return nil
        }
        
        let mainWindow = windowArray[0]
        
        var position: CFTypeRef?
        var size: CFTypeRef?
        
        let posResult = AXUIElementCopyAttributeValue(mainWindow, kAXPositionAttribute as CFString, &position)
        let sizeResult = AXUIElementCopyAttributeValue(mainWindow, kAXSizeAttribute as CFString, &size)
        
        guard posResult == .success && sizeResult == .success,
              let posValue = position as? NSValue,
              let sizeValue = size as? NSValue else {
            return nil
        }
        
        let windowPosition = posValue.pointValue
        let windowSize = sizeValue.sizeValue
        
        return CGRect(origin: windowPosition, size: windowSize)
    }
    
    // MARK: - Claude-Specific Helper Methods
    
    func createNewClaudeChat(in appElement: AXUIElement) -> Bool {
        // Try to find and click "New Chat" button
        if let newChatButton = findElementContainingText(in: appElement, text: "New chat", maxDepth: 6) {
            return clickElement(newChatButton)
        }
        
        // Try keyboard shortcut for new chat (Cmd+N is common)
        let cmdNEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x2D, keyDown: true) // N key
        cmdNEvent?.flags = .maskCommand
        cmdNEvent?.post(tap: .cghidEventTap)
        let cmdNUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x2D, keyDown: false)
        cmdNUpEvent?.flags = .maskCommand
        cmdNUpEvent?.post(tap: .cghidEventTap)
        
        return true
    }
    
    // MARK: - Tab Key Focus Methods (Restored with window focus confirmation)
    
    func focusTextInputWithTab(in appElement: AXUIElement, maxAttempts: Int = 5) -> Bool {
        print("🎯 Focusing text input with Tab key method...")
        
        // First ensure window is properly focused
        if !confirmWindowFocus(appElement) {
            print("❌ Failed to confirm window focus")
            return false
        }
        
        // Try Tab key navigation to find text input
        for attempt in 1...maxAttempts {
            print("⌨️ Tab attempt \(attempt)...")
            
            // Send Tab key
            let tabEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.tab.rawValue, keyDown: true)
            tabEvent?.post(tap: .cghidEventTap)
            let tabUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.tab.rawValue, keyDown: false)
            tabUpEvent?.post(tap: .cghidEventTap)
            
            // Short delay to let focus change
            usleep(300_000) // 300ms
            
            // Check if we're now in text input mode
            if isMouseCursorInTextMode() {
                print("✅ Confirmed: Cursor in text input mode (I-beam)")
                return true
            }
            
            // Also check for focused editable element
            if let focusedElement = getFocusedElement(in: appElement),
               isElementEditable(focusedElement) {
                print("✅ Confirmed: Focused element is editable")
                return true
            }
        }
        
        print("❌ Tab navigation failed to find text input after \(maxAttempts) attempts")
        return false
    }
    
    func confirmWindowFocus(_ appElement: AXUIElement) -> Bool {
        print("🪟 Confirming window focus...")
        
        // Step 1: Raise and activate window
        if !raiseAndActivateClaudeWindow(appElement) {
            print("❌ Failed to raise/activate window")
            return false
        }
        
        // Step 2: Click in the window center to ensure it has focus
        if let windowBounds = getClaudeWindowBounds(appElement) {
            let centerPoint = CGPoint(
                x: windowBounds.origin.x + (windowBounds.size.width * 0.5),
                y: windowBounds.origin.y + (windowBounds.size.height * 0.5)
            )
            
            print("🖱️ Clicking window center to confirm focus: \(centerPoint)")
            _ = performMouseClick(at: centerPoint)
            
            // Wait for focus confirmation
            usleep(500_000) // 500ms
            
            return true
        }
        
        return false
    }
    
    func getFocusedElement(in appElement: AXUIElement) -> AXUIElement? {
        var focusedElement: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appElement, kAXFocusedUIElementAttribute as CFString, &focusedElement)
        
        guard result == .success, let element = focusedElement else {
            return nil
        }
        
        return (element as! AXUIElement)
    }
    
    func isElementEditable(_ element: AXUIElement) -> Bool {
        // Check if element can have its value set
        var isSettable: DarwinBoolean = false
        let result = AXUIElementIsAttributeSettable(element, kAXValueAttribute as CFString, &isSettable)
        
        return result == .success && isSettable.boolValue
    }
    
    func isMouseCursorInTextMode() -> Bool {
        // Check if mouse cursor is in text input shape (I-beam)
        let currentCursor = NSCursor.current
        
        // Compare with known text cursor types
        if currentCursor == NSCursor.iBeam || currentCursor == NSCursor.iBeamCursorForVerticalLayout {
            return true
        }
        
        return false
    }
    
    func performMouseClick(at position: CGPoint) -> Bool {
        print("🖱️ Performing mouse click at (\(position.x), \(position.y))")
        
        let clickEvent = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: position, mouseButton: .left)
        clickEvent?.post(tap: .cghidEventTap)
        
        let clickUpEvent = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: position, mouseButton: .left)
        clickUpEvent?.post(tap: .cghidEventTap)
        
        return true
    }
    
    func hoverAndCheckCursor(at position: CGPoint, maxAttempts: Int = 10) -> Bool {
        print("🔍 Hovering at (\(position.x), \(position.y)) to detect I-beam cursor...")
        
        // Move mouse to position
        CGWarpMouseCursorPosition(position)
        
        // Check cursor shape multiple times
        for attempt in 1...maxAttempts {
            usleep(50_000) // 50ms
            if isMouseCursorInTextMode() {
                print("✅ I-beam cursor detected at attempt \(attempt)")
                return true
            }
        }
        
        print("❌ No I-beam cursor detected after \(maxAttempts) attempts")
        return false
    }
    
    func clickSubmitButton(in appElement: AXUIElement) -> Bool {
        // Try to find and click the submit/send button
        let submitTexts = ["Send", "Submit", "→", "▶"]
        
        for text in submitTexts {
            if let submitButton = findElementContainingText(in: appElement, text: text, maxDepth: 8) {
                return clickElement(submitButton)
            }
        }
        
        // Try to find button by role
        if let submitButton = findElementByRole(in: appElement, role: kAXButtonRole, maxDepth: 8) {
            return clickElement(submitButton)
        }
        
        return false
    }
    
    func sendCmdEnterKey() -> Bool {
        // Send Cmd+Enter (common alternative for submitting)
        let cmdEnterEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.enter.rawValue, keyDown: true)
        cmdEnterEvent?.flags = .maskCommand
        cmdEnterEvent?.post(tap: .cghidEventTap)
        
        let cmdEnterUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: VirtualKey.enter.rawValue, keyDown: false)
        cmdEnterUpEvent?.flags = .maskCommand
        cmdEnterUpEvent?.post(tap: .cghidEventTap)
        
        return true
    }
    
    
    func extractClaudeResponse(from appElement: AXUIElement) -> String {
        print("🔍 Extracting Claude response using enhanced methods...")
        
        // Strategy 1: Look for recent response in web areas (most likely location)
        if let responseText = extractFromWebView(in: appElement) {
            print("✅ Found response via WebView extraction: \(responseText.count) chars")
            return responseText
        }
        
        // Strategy 2: Look for response container elements
        if let responseText = findResponseByContainer(in: appElement) {
            print("✅ Found response via container search: \(responseText.count) chars")
            return responseText
        }
        
        // Strategy 3: Enhanced text content search
        if let responseText = findLatestResponseText(in: appElement) {
            print("✅ Found response via latest text search: \(responseText.count) chars")
            return responseText
        }
        
        // Strategy 4: Get all visible text and filter intelligently
        if let responseText = extractVisibleText(from: appElement) {
            print("✅ Found response via visible text extraction: \(responseText.count) chars")
            return responseText
        }
        
        print("❌ No response found using any extraction method")
        return ""
    }
    
    func extractFromWebView(in appElement: AXUIElement) -> String? {
        print("🌐 Searching for response in web view areas...")
        
        // Find all web areas in the application
        let webAreas = findAllElementsByRole(in: appElement, role: "AXWebArea", maxDepth: 10)
        print("🌐 Found \(webAreas.count) web areas to search")
        
        var allResponses: [String] = []
        
        for (index, webArea) in webAreas.enumerated() {
            print("🔍 Searching web area \(index + 1)/\(webAreas.count)...")
            let responseTexts = extractTextFromWebArea(webArea)
            allResponses.append(contentsOf: responseTexts)
        }
        
        // Sort by length and filter meaningful responses
        let meaningfulResponses = allResponses
            .filter { $0.count > 100 } // Require more substantial content
            .sorted { $0.count > $1.count }
        
        if let bestResponse = meaningfulResponses.first {
            print("✅ Found best response: \(bestResponse.count) chars")
            return bestResponse
        }
        
        // Fallback to shorter responses if no long ones found
        let shortResponses = allResponses.filter { $0.count > 30 }
        if let longestShort = shortResponses.max(by: { $0.count < $1.count }) {
            print("🔄 Using shorter response: \(longestShort.count) chars")
            return longestShort
        }
        
        return nil
    }
    
    func extractTextFromWebArea(_ webArea: AXUIElement) -> [String] {
        var texts: [String] = []
        
        func collectText(from element: AXUIElement, depth: Int = 0) {
            if depth > 6 { return }
            
            // Try multiple text attributes
            let attributes = [kAXValueAttribute, kAXDescriptionAttribute, kAXTitleAttribute]
            
            for attribute in attributes {
                var textValue: CFTypeRef?
                if AXUIElementCopyAttributeValue(element, attribute as CFString, &textValue) == .success,
                   let text = textValue as? String,
                   !text.isEmpty,
                   text.count > 20 {
                    
                    // Filter out UI elements and input prompts
                    let lowercaseText = text.lowercased()
                    if !lowercaseText.contains("message claude") &&
                       !lowercaseText.contains("type a message") &&
                       !lowercaseText.contains("send message") &&
                       !lowercaseText.contains("new chat") &&
                       !texts.contains(text) {
                        texts.append(text)
                    }
                }
            }
            
            // Recursively search children
            var children: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
               let childArray = children as? [AXUIElement] {
                for child in childArray {
                    collectText(from: child, depth: depth + 1)
                }
            }
        }
        
        collectText(from: webArea)
        return texts
    }
    
    func findLatestResponseText(in appElement: AXUIElement) -> String? {
        print("🔍 Searching for latest response text...")
        
        var allTexts: [(text: String, length: Int)] = []
        
        func collectAllText(from element: AXUIElement, depth: Int = 0) {
            if depth > 8 { return }
            
            // Get text from this element
            var textValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &textValue) == .success,
               let text = textValue as? String,
               !text.isEmpty,
               text.count > 30 {
                
                // Skip input-related text
                let lowercaseText = text.lowercased()
                if !lowercaseText.contains("message claude") &&
                   !lowercaseText.contains("type") &&
                   !lowercaseText.contains("send") {
                    allTexts.append((text: text, length: text.count))
                }
            }
            
            // Recursively search children
            var children: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
               let childArray = children as? [AXUIElement] {
                for child in childArray {
                    collectAllText(from: child, depth: depth + 1)
                }
            }
        }
        
        collectAllText(from: appElement)
        
        // Sort by length and return the longest meaningful text
        let sortedTexts = allTexts.sorted { $0.length > $1.length }
        
        for textItem in sortedTexts {
            let text = textItem.text.trimmingCharacters(in: .whitespacesAndNewlines)
            if text.count >= 50 {
                print("📝 Found substantial response: \(text.count) characters")
                return text
            }
        }
        
        return nil
    }
    
    func findResponseByContainer(in appElement: AXUIElement, maxDepth: Int = 8, currentDepth: Int = 0) -> String? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appElement, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        for child in childArray {
            // Check if this element looks like a response container
            var roleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXRoleAttribute as CFString, &roleValue) == .success,
               let role = roleValue as? String {
                
                // Look for text areas, groups, or web areas that might contain responses
                if role.contains("Text") || role == "AXGroup" || role.contains("Web") {
                    var textValue: CFTypeRef?
                    if AXUIElementCopyAttributeValue(child, kAXValueAttribute as CFString, &textValue) == .success,
                       let text = textValue as? String,
                       !text.isEmpty && text.count > 20 { // Substantial content
                        return text
                    }
                }
            }
            
            // Recursively search children
            if let found = findResponseByContainer(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                return found
            }
        }
        
        return nil
    }
    
    func findResponseByTextContent(in appElement: AXUIElement, maxDepth: Int = 8, currentDepth: Int = 0) -> String? {
        if currentDepth >= maxDepth { return nil }
        
        var children: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appElement, kAXChildrenAttribute as CFString, &children)
        
        guard result == .success, let childArray = children as? [AXUIElement] else {
            return nil
        }
        
        var allTexts: [String] = []
        
        for child in childArray {
            // Get text from this element
            var textValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(child, kAXValueAttribute as CFString, &textValue) == .success,
               let text = textValue as? String,
               !text.isEmpty {
                allTexts.append(text)
            }
            
            // Recursively get text from children
            if let childText = findResponseByTextContent(in: child, maxDepth: maxDepth, currentDepth: currentDepth + 1) {
                allTexts.append(childText)
            }
        }
        
        // Join all texts and return the longest meaningful response
        let combinedText = allTexts.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        return combinedText.count > 50 ? combinedText : nil
    }
    
    func extractVisibleText(from appElement: AXUIElement, maxDepth: Int = 8) -> String? {
        var allVisibleText: [String] = []
        var seenTexts: Set<String> = []
        
        func collectVisibleText(_ element: AXUIElement, depth: Int) {
            if depth >= maxDepth { return }
            
            // Try multiple text attributes
            let attributes = [kAXValueAttribute, kAXDescriptionAttribute, kAXTitleAttribute]
            
            for attribute in attributes {
                var textValue: CFTypeRef?
                if AXUIElementCopyAttributeValue(element, attribute as CFString, &textValue) == .success,
                   let text = textValue as? String,
                   !text.isEmpty,
                   text.count > 20,
                   !seenTexts.contains(text) {
                    
                    // Filter out UI elements
                    let lowercaseText = text.lowercased()
                    if !lowercaseText.contains("message claude") &&
                       !lowercaseText.contains("search") &&
                       !lowercaseText.contains("button") &&
                       !lowercaseText.contains("menu") {
                        allVisibleText.append(text)
                        seenTexts.insert(text)
                    }
                }
            }
            
            // Get children and recurse
            var children: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
               let childArray = children as? [AXUIElement] {
                for child in childArray {
                    collectVisibleText(child, depth: depth + 1)
                }
            }
        }
        
        collectVisibleText(appElement, depth: 0)
        
        // Find the longest meaningful text (likely Claude's response)
        let meaningfulTexts = allVisibleText.filter { $0.count > 50 }
        if let longestText = meaningfulTexts.max(by: { $0.count < $1.count }) {
            return longestText
        }
        
        // Fallback: return all meaningful text combined
        let shortTexts = allVisibleText.filter { $0.count > 20 && $0.count <= 50 }
        if !shortTexts.isEmpty {
            return shortTexts.joined(separator: " ")
        }
        
        return nil
    }
    
    func parseAutomationResponse(_ response: String) -> String {
        // Extract the machine-readable part from the response
        if let range = response.range(of: "AUTOMATION_RESPONSE_END:") {
            let afterMarker = String(response[range.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines)
            return afterMarker.isEmpty ? response : afterMarker
        }
        
        return response
    }
    
    // MARK: - AI Service Specific Methods
    
    func automateClaudeQuery(_ query: String, isNewChat: Bool = true) async throws -> String {
        let bundleId = "com.anthropic.claudefordesktop"
        print("🚀 Starting Claude automation with query: '\(String(query.prefix(50)))...'")
        
        // Use the original query without extra formatting - research shows this complicates detection
        let testQuery = query
        
        // Launch Claude if not running
        if !isAppRunning(bundleId) {
            print("📱 Launching Claude...")
            guard launchApp(bundleId) else {
                throw AIServiceError.failedToLaunch
            }
            // Wait for app to launch
            try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        } else {
            print("✅ Claude is already running")
        }
        
        guard let appElement = getAppProcessElement(bundleId) else {
            print("❌ Failed to get Claude app element")
            throw AIServiceError.automationFailed("Could not access Claude app")
        }
        print("✅ Got Claude app element")
        
        // CRITICAL: Enable accessibility for Electron app (Claude Desktop) - 31first.md step 1
        print("🔧 Enabling Electron accessibility...")
        let accessibilityResult = AXUIElementSetAttributeValue(
            appElement,
            "AXManualAccessibility" as CFString,
            kCFBooleanTrue
        )
        print("🔧 Accessibility activation: \(accessibilityResult == .success ? "✅" : "❌")")
        
        // Wait for accessibility to fully activate
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second for accessibility activation
        
        // Step 2: Raise and activate Claude window (31first.md solution)
        let windowSuccess = raiseAndActivateClaudeWindow(appElement)
        print("🪟 Window raise/activate: \(windowSuccess ? "✅" : "❌")")
        
        // Wait for window activation
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 second for window activation
        
        // Handle new chat vs follow-up
        if isNewChat {
            print("🆕 Creating new chat...")
            _ = createNewClaudeChat(in: appElement)
            try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second for new chat to load
        }
        
        var sendSuccess = false
        
        // PRIMARY METHOD: Tab key navigation with window focus confirmation
        print("🎯 Trying Tab key method with window focus confirmation...")
        if focusTextInputWithTab(in: appElement) {
            print("✅ Successfully focused text input with Tab method")
            
            // Send the text via clipboard (most reliable)
            print("📋 Sending actual text via clipboard...")
            if sendTextViaClipboard(testQuery) {
                print("✅ Text sent via clipboard")
                
                // Wait for text to be pasted
                try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
                
                // Submit with Enter key
                print("📤 Submitting with Enter key...")
                sendSuccess = sendEnterKey()
                print("⌨️ Enter key result: \(sendSuccess ? "✅" : "❌")")
            } else {
                print("❌ Failed to send text via clipboard")
            }
        } else {
            print("🔄 Tab method failed, trying AXPress method...")
            
            // FALLBACK METHOD: Try to find text input element directly
            var textArea: AXUIElement?
            textArea = findClaudeTextInput(in: appElement)
            
            if textArea == nil {
                textArea = findTextArea(in: appElement)
            }
            
            if let inputElement = textArea {
                print("📝 Found text input element, using AXPress...")
                let pressResult = AXUIElementPerformAction(inputElement, kAXPressAction as CFString)
                print("🎯 AXPress result: \(pressResult == .success ? "✅" : "❌")")
                
                try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
                
                // Try setting text directly
                let setResult = AXUIElementSetAttributeValue(inputElement, kAXValueAttribute as CFString, testQuery as CFString)
                if setResult == .success {
                    print("✅ Text set via AXValue")
                    try await Task.sleep(nanoseconds: 500_000_000)
                    sendSuccess = sendEnterKey()
                } else {
                    print("🔄 AXValue failed, using clipboard...")
                    sendSuccess = sendTextViaClipboard(testQuery)
                    if sendSuccess {
                        try await Task.sleep(nanoseconds: 500_000_000)
                        sendSuccess = sendEnterKey()
                    }
                }
            } else {
                print("🔄 No text input found, trying window-based clicking...")
                
                // LAST RESORT: Window-based coordinate clicking
                if let windowBounds = getClaudeWindowBounds(appElement) {
                    let textAreaX = windowBounds.origin.x + (windowBounds.size.width * 0.5)
                    let textAreaY = windowBounds.origin.y + (windowBounds.size.height * 0.85)
                    let textAreaPosition = CGPoint(x: textAreaX, y: textAreaY)
                    
                    print("🎯 Clicking at window position: \(textAreaPosition)")
                    _ = performMouseClick(at: textAreaPosition)
                    
                    try await Task.sleep(nanoseconds: 500_000_000)
                    
                    if hoverAndCheckCursor(at: textAreaPosition) {
                        print("✅ Cursor indicates text input area")
                        sendSuccess = sendTextViaClipboard(testQuery)
                        if sendSuccess {
                            try await Task.sleep(nanoseconds: 500_000_000)
                            sendSuccess = sendEnterKey()
                        }
                    }
                }
            }
        }
        
        print("📤 Final send success: \(sendSuccess ? "✅" : "❌")")
        
        guard sendSuccess else {
            throw AIServiceError.automationFailed("Failed to submit query to Claude")
        }
        
        print("📤 Query sent to Claude, waiting for response...")
        
        // Enhanced response waiting with improved extraction
        print("📤 Query sent to Claude, waiting for response...")
        
        // Wait for Claude to start processing
        try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds initial wait
        
        let maxWaitTime = 60.0 // 60 seconds max for complex queries
        let checkInterval = 2.0 // Check every 2 seconds
        let startTime = Date()
        var lastResponseLength = 0
        var stableCount = 0
        var bestResponse = ""
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let currentResponse = extractClaudeResponse(from: appElement)
            let responseLength = currentResponse.count
            
            print("📊 Response check: \(responseLength) chars (previous: \(lastResponseLength))")
            
            // Keep the best response found
            if responseLength > bestResponse.count {
                bestResponse = currentResponse
            }
            
            if responseLength > lastResponseLength && responseLength > 50 {
                // Response is growing and substantial
                lastResponseLength = responseLength
                stableCount = 0
                print("📈 Response growing: \(String(currentResponse.prefix(100)))...")
                
            } else if responseLength == lastResponseLength && responseLength > 100 {
                // Response stable and substantial
                stableCount += 1
                print("⏳ Response stable for \(stableCount * Int(checkInterval))s")
                
                if stableCount >= 2 { // 4 seconds stable
                    print("✅ Response complete: \(String(currentResponse.prefix(100)))...")
                    return currentResponse
                }
                
            } else if responseLength > 200 && stableCount == 0 {
                // Found large response but still growing
                print("📝 Large response detected, monitoring for completion...")
            }
            
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        // Return best response found, even if timeout
        if !bestResponse.isEmpty && bestResponse.count > 50 {
            print("⚠️ Timeout - returning best response: \(bestResponse.count) chars")
            return bestResponse
        }
        
        // Final extraction attempt
        let finalResponse = extractClaudeResponse(from: appElement)
        if !finalResponse.isEmpty && finalResponse.count > 30 {
            print("🔄 Final extraction: \(finalResponse.count) chars")
            return finalResponse
        }
        
        print("❌ No response captured after \(maxWaitTime)s")
        return "Response timeout - check Claude Desktop manually for the reply."
    }
    
    
    func automatePerplexityQuery(_ query: String) async throws -> String {
        let bundleId = "ai.perplexity.mac"
        
        if !isAppRunning(bundleId) {
            guard launchApp(bundleId) else {
                throw AIServiceError.failedToLaunch
            }
            try await Task.sleep(nanoseconds: 2_000_000_000)
        }
        
        guard let appElement = getAppProcessElement(bundleId) else {
            throw AIServiceError.automationFailed("Could not access Perplexity app")
        }
        
        // Find search field (different role than text area)
        guard let searchField = findElementByRole(in: appElement, role: kAXTextFieldRole) else {
            throw AIServiceError.automationFailed("Could not find search field")
        }
        
        _ = focusElement(searchField)
        _ = setElementValue(searchField, value: query)
        
        // Submit search
        let enterKeyEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x24, keyDown: true)
        enterKeyEvent?.post(tap: .cghidEventTap)
        let enterKeyUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x24, keyDown: false)
        enterKeyUpEvent?.post(tap: .cghidEventTap)
        
        try await Task.sleep(nanoseconds: 3_000_000_000)
        
        return "Query sent to Perplexity via Accessibility API"
    }
    
    // MARK: - Debugging and Testing
    
    func debugUIStructure(for bundleId: String, maxDepth: Int = 3) -> String {
        guard let appElement = getAppProcessElement(bundleId) else {
            return "❌ Could not access app with bundle ID: \(bundleId)"
        }
        
        var debugInfo = "🔍 UI Structure for \(bundleId):\n\n"
        debugInfo += exploreUIElement(appElement, depth: 0, maxDepth: maxDepth)
        return debugInfo
    }
    
    private func exploreUIElement(_ element: AXUIElement, depth: Int, maxDepth: Int) -> String {
        if depth > maxDepth { return "" }
        
        let indent = String(repeating: "  ", count: depth)
        var info = ""
        
        // Get role
        var roleValue: CFTypeRef?
        let role = if AXUIElementCopyAttributeValue(element, kAXRoleAttribute as CFString, &roleValue) == .success,
                     let roleString = roleValue as? String {
            roleString
        } else {
            "Unknown"
        }
        
        // Get description if available
        var descValue: CFTypeRef?
        let description = if AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute as CFString, &descValue) == .success,
                            let descString = descValue as? String {
            " - \(descString)"
        } else {
            ""
        }
        
        // Get value if available
        var valueValue: CFTypeRef?
        let value = if AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &valueValue) == .success,
                      let valueString = valueValue as? String, !valueString.isEmpty {
            " (value: \(String(valueString.prefix(20))))"
        } else {
            ""
        }
        
        info += "\(indent)• \(role)\(description)\(value)\n"
        
        // Explore children
        var children: CFTypeRef?
        if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
           let childArray = children as? [AXUIElement] {
            for child in childArray.prefix(10) { // Limit to first 10 children to avoid spam
                info += exploreUIElement(child, depth: depth + 1, maxDepth: maxDepth)
            }
            if childArray.count > 10 {
                info += "\(indent)  ... (\(childArray.count - 10) more children)\n"
            }
        }
        
        return info
    }
    
    func testAccessibilityAccess() async -> String {
        guard checkAccessibilityPermissions() else {
            return "❌ Accessibility permissions not granted. Please grant access in System Preferences → Privacy & Security → Accessibility"
        }
        
        var debugInfo = "✅ Accessibility permissions granted\n\n"
        
        // List running apps that we can control
        debugInfo += "Apps available for automation:\n"
        let targetBundleIds = [
            "com.anthropic.claudefordesktop": "Claude",
            "ai.perplexity.mac": "Perplexity",
            "com.openai.chat": "ChatGPT"
        ]
        
        for (bundleId, displayName) in targetBundleIds {
            let isRunning = isAppRunning(bundleId)
            let canAccess = isRunning ? (getAppProcessElement(bundleId) != nil) : false
            debugInfo += "• \(displayName): Running=\(isRunning ? "✅" : "❌"), Accessible=\(canAccess ? "✅" : "❌")\n"
            
            // If Claude is running, show its UI structure to help debug text input finding
            if bundleId == "com.anthropic.claudefordesktop" && isRunning && canAccess {
                debugInfo += "\n" + debugUIStructure(for: bundleId, maxDepth: 2) + "\n"
            }
        }
        
        return debugInfo
    }
}

// MARK: - Extension for Key Constants

extension AccessibilityAPIAutomator {
    enum VirtualKey: UInt16 {
        case enter = 0x24
        case escape = 0x35
        case space = 0x31
        case tab = 0x30
        case delete = 0x33
    }
}