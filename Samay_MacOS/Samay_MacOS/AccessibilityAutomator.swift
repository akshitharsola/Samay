//
//  AccessibilityAutomator.swift
//  Samay_MacOS
//
//  Created by Claude on 29/07/25.
//

import Foundation
import ApplicationServices
import AppKit
import CoreGraphics

@MainActor
class AccessibilityAutomator {
    static let shared = AccessibilityAutomator()
    
    private init() {}
    
    func checkPermissions() -> Bool {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false]
        return AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    func requestPermissions() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        _ = AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    func automateClaudeApp(_ query: String) async throws {
        guard checkPermissions() else {
            throw AIServiceError.automationFailed("Accessibility permissions not granted")
        }
        
        // Launch Claude app
        let workspace = NSWorkspace.shared
        guard let claudeURL = workspace.urlForApplication(withBundleIdentifier: "com.anthropic.claudefordesktop") else {
            throw AIServiceError.notInstalled
        }
        
        try await workspace.openApplication(at: claudeURL, configuration: NSWorkspace.OpenConfiguration())
        
        // Wait for app to launch
        try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        
        // Get the Claude application
        let runningApps = workspace.runningApplications
        guard let claudeApp = runningApps.first(where: { $0.bundleIdentifier == "com.anthropic.claudefordesktop" }) else {
            throw AIServiceError.failedToLaunch
        }
        
        // Activate the app
        claudeApp.activate(options: [.activateIgnoringOtherApps])
        
        // Wait for activation
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Get accessibility element for the app
        let appElement = AXUIElementCreateApplication(claudeApp.processIdentifier)
        
        // Find the text input field
        try await findAndFocusInputField(appElement)
        
        // Type the query using CGEventPost (if available) or pasteboard
        try await typeText(query)
        
        // Press Enter
        try await pressEnterKey()
    }
    
    private func findAndFocusInputField(_ appElement: AXUIElement) async throws {
        // Look for text areas or text fields using a more compatible approach
        var children: CFTypeRef?
        let childrenResult = AXUIElementCopyAttributeValue(appElement, kAXChildrenAttribute, &children)
        
        if childrenResult == .success, let childElements = children as? [AXUIElement] {
            // Look for text fields recursively
            for child in childElements {
                var role: CFTypeRef?
                if AXUIElementCopyAttributeValue(child, kAXRoleAttribute, &role) == .success,
                   let roleString = role as? String,
                   (roleString == kAXTextAreaRole || roleString == kAXTextFieldRole) {
                    
                    // Try to focus this element
                    let focusResult = AXUIElementSetAttributeValue(child, kAXFocusedAttribute, kCFBooleanTrue)
                    if focusResult == .success {
                        return
                    }
                }
            }
        }
        
        // If no text field found, just continue - we'll use global keyboard events
        print("⚠️ Could not find specific input field, using global keyboard events")
    }
    
    private func clickElement(_ element: AXUIElement) async throws {
        var position: CFTypeRef?
        let positionResult = AXUIElementCopyAttributeValue(element, kAXPositionAttribute, &position)
        
        guard positionResult == .success,
              let positionValue = position,
              CFGetTypeID(positionValue) == AXValueGetTypeID() else {
            throw AIServiceError.automationFailed("Could not get element position")
        }
        
        var point = CGPoint.zero
        guard AXValueGetValue(positionValue as! AXValue, .cgPoint, &point) else {
            throw AIServiceError.automationFailed("Could not extract point from position")
        }
        
        // Create and post a mouse click event
        guard let clickDown = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left),
              let clickUp = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left) else {
            throw AIServiceError.automationFailed("Could not create mouse events")
        }
        
        clickDown.post(tap: .cghidEventTap)
        clickUp.post(tap: .cghidEventTap)
    }
    
    private func typeText(_ text: String) async throws {
        // Use pasteboard approach as it's more reliable in sandboxed apps
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
        
        // Simulate Cmd+V
        guard let cmdV = CGEvent(keyboardEventSource: nil, virtualKey: 9, keyDown: true) else { // V key
            throw AIServiceError.automationFailed("Could not create paste event")
        }
        
        cmdV.flags = .maskCommand
        cmdV.post(tap: .cghidEventTap)
        
        // Key up
        guard let cmdVUp = CGEvent(keyboardEventSource: nil, virtualKey: 9, keyDown: false) else {
            throw AIServiceError.automationFailed("Could not create paste up event")
        }
        
        cmdVUp.flags = .maskCommand
        cmdVUp.post(tap: .cghidEventTap)
    }
    
    private func pressEnterKey() async throws {
        // Press Enter key (key code 36)
        guard let enterDown = CGEvent(keyboardEventSource: nil, virtualKey: 36, keyDown: true),
              let enterUp = CGEvent(keyboardEventSource: nil, virtualKey: 36, keyDown: false) else {
            throw AIServiceError.automationFailed("Could not create Enter key events")
        }
        
        enterDown.post(tap: .cghidEventTap)
        enterUp.post(tap: .cghidEventTap)
    }
    
    func extractClaudeResponse() async throws -> String {
        guard checkPermissions() else {
            throw AIServiceError.automationFailed("Accessibility permissions not granted")
        }
        
        // Get Claude app
        let workspace = NSWorkspace.shared
        let runningApps = workspace.runningApplications
        guard let claudeApp = runningApps.first(where: { $0.bundleIdentifier == "com.anthropic.claudefordesktop" }) else {
            throw AIServiceError.automationFailed("Claude app not running")
        }
        
        let appElement = AXUIElementCreateApplication(claudeApp.processIdentifier)
        
        // Look for static text elements by searching children recursively
        var responseText = ""
        try await extractTextFromElement(appElement, into: &responseText)
        
        if !responseText.isEmpty {
            return responseText.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        
        return "Could not extract response using Accessibility API"
    }
    
    private func extractTextFromElement(_ element: AXUIElement, into responseText: inout String) async throws {
        // Check if this element has text content
        var value: CFTypeRef?
        if AXUIElementCopyAttributeValue(element, kAXValueAttribute, &value) == .success,
           let stringValue = value as? String,
           stringValue.count > 50 { // Only consider substantial text
            responseText += stringValue + " "
        }
        
        // Recursively check children
        var children: CFTypeRef?
        if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, &children) == .success,
           let childElements = children as? [AXUIElement] {
            for child in childElements {
                try await extractTextFromElement(child, into: &responseText)
            }
        }
    }
}