//
//  GeminiAutomator.swift
//  Samay_MacOS
//
//  Service-specific automation for Gemini (via Safari)
//

import Foundation
import ApplicationServices
import AppKit

class GeminiAutomator {
    static let shared = GeminiAutomator()
    private let bundleId = "com.apple.Safari"
    private let geminiURL = "https://gemini.google.com"
    private let accessibility = AccessibilityAPIAutomator.shared
    
    private init() {}
    
    // MARK: - Gemini-Specific Automation (Safari-based)
    
    func automateQuery(_ query: String) async throws -> String {
        print("🤖 Gemini (Safari) automation starting...")
        
        // Launch Safari if not running
        if !accessibility.isAppRunning(bundleId) {
            print("📱 Launching Safari...")
            guard accessibility.launchApp(bundleId) else {
                throw AIServiceError.failedToLaunch
            }
            try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
        }
        
        // Navigate to Gemini if needed
        try await navigateToGemini()
        
        guard let appElement = accessibility.getAppProcessElement(bundleId) else {
            throw AIServiceError.automationFailed("Could not access Safari")
        }
        
        // Focus Safari window
        _ = accessibility.focusAppWithKeyboard(bundleId)
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Wait for Gemini to load
        try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        
        // Focus text input
        print("🎯 Focusing Gemini text input...")
        let focusSuccess = accessibility.focusTextInputWithTab(in: appElement, maxAttempts: 10)
        
        if !focusSuccess {
            // Try direct web area search
            print("🔄 Tab method failed, searching web areas...")
            if let textInput = findGeminiTextInput(in: appElement) {
                let pressResult = AXUIElementPerformAction(textInput, kAXPressAction as CFString)
                if pressResult != .success {
                    // Try clicking if press fails
                    var frameValue: CFTypeRef?
                    if AXUIElementCopyAttributeValue(textInput, "AXFrame" as CFString, &frameValue) == .success,
                       let frameData = frameValue as? NSValue {
                        let bounds = frameData.rectValue
                        let center = CGPoint(x: bounds.midX, y: bounds.midY)
                        _ = accessibility.performMouseClick(at: center)
                    }
                }
            } else {
                // Try clicking in approximate text area location
                if let windowBounds = getSafariWindowBounds(appElement) {
                    let textAreaX = windowBounds.origin.x + (windowBounds.size.width * 0.5)
                    let textAreaY = windowBounds.origin.y + (windowBounds.size.height * 0.8)
                    let textAreaPosition = CGPoint(x: textAreaX, y: textAreaY)
                    
                    print("🎯 Clicking estimated Gemini input area...")
                    _ = accessibility.performMouseClick(at: textAreaPosition)
                    try await Task.sleep(nanoseconds: 500_000_000)
                }
            }
        }
        
        // Send text
        print("📝 Sending query to Gemini...")
        if !accessibility.sendTextViaClipboard(query) {
            throw AIServiceError.automationFailed("Failed to send text to Gemini")
        }
        
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        // Submit
        print("📤 Submitting query...")
        if !accessibility.sendEnterKey() {
            throw AIServiceError.automationFailed("Failed to submit query")
        }
        
        // Wait for response
        print("⏳ Waiting for Gemini response...")
        return try await waitForGeminiResponse(appElement)
    }
    
    private func navigateToGemini() async throws {
        // Open new tab and navigate to Gemini
        let cmdTEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x11, keyDown: true) // T key
        cmdTEvent?.flags = .maskCommand
        cmdTEvent?.post(tap: .cghidEventTap)
        let cmdTUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x11, keyDown: false)
        cmdTUpEvent?.flags = .maskCommand
        cmdTUpEvent?.post(tap: .cghidEventTap)
        
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Type Gemini URL
        if !accessibility.sendTextViaClipboard(geminiURL) {
            throw AIServiceError.automationFailed("Failed to navigate to Gemini")
        }
        
        // Press Enter to navigate
        _ = accessibility.sendEnterKey()
        
        // Wait for navigation
        try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
    }
    
    private func findGeminiTextInput(in appElement: AXUIElement) -> AXUIElement? {
        print("🔍 Looking for Gemini text input in Safari...")
        
        // Look in web areas for text input
        let webAreas = accessibility.findAllElementsByRole(in: appElement, role: "AXWebArea", maxDepth: 6)
        print("🌐 Found \(webAreas.count) web areas in Safari")
        
        for webArea in webAreas {
            // Look for text areas in web content
            if let textArea = accessibility.findElementByRole(in: webArea, role: kAXTextAreaRole, maxDepth: 8) {
                return textArea
            }
            
            // Look for any editable element
            if let editableElement = accessibility.findAnyEditableElement(in: webArea, maxDepth: 8) {
                return editableElement
            }
        }
        
        return nil
    }
    
    private func getSafariWindowBounds(_ appElement: AXUIElement) -> CGRect? {
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
    
    private func waitForGeminiResponse(_ appElement: AXUIElement) async throws -> String {
        try await Task.sleep(nanoseconds: 4_000_000_000) // 4 seconds initial wait
        
        let maxWaitTime = 60.0 // 60 seconds for Gemini
        let checkInterval = 2.5 // Check every 2.5 seconds
        let startTime = Date()
        var lastLength = 0
        var stableCount = 0
        var bestResponse = ""
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let response = extractGeminiResponse(from: appElement)
            let length = response.count
            
            print("📊 Gemini response: \(length) chars (was: \(lastLength))")
            
            if length > bestResponse.count {
                bestResponse = response
            }
            
            if length > lastLength && length > 80 {
                lastLength = length
                stableCount = 0
                print("📈 Gemini response growing...")
            } else if length == lastLength && length > 150 {
                stableCount += 1
                print("⏸️ Gemini response stable (\(stableCount))")
                
                if stableCount >= 2 { // 5 seconds stable
                    print("✅ Gemini response complete")
                    return response
                }
            }
            
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        if !bestResponse.isEmpty && bestResponse.count > 60 {
            print("⏰ Gemini timeout - returning best response")
            return bestResponse
        }
        
        throw AIServiceError.timeout
    }
    
    private func extractGeminiResponse(from appElement: AXUIElement) -> String {
        print("🔍 Extracting Gemini response from Safari...")
        
        var allTexts: [String] = []
        
        func collectGeminiText(from element: AXUIElement, depth: Int = 0) {
            if depth > 8 { return }
            
            // Get text content
            var textValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &textValue) == .success,
               let text = textValue as? String,
               !text.isEmpty,
               text.count > 80 {
                
                // Filter out Gemini UI elements
                let lowercaseText = text.lowercased()
                if !lowercaseText.contains("ask gemini") &&
                   !lowercaseText.contains("google") &&
                   !lowercaseText.contains("search") &&
                   !lowercaseText.contains("sign in") &&
                   !allTexts.contains(text) {
                    allTexts.append(text)
                }
            }
            
            // Check children
            var children: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
               let childArray = children as? [AXUIElement] {
                for child in childArray {
                    collectGeminiText(from: child, depth: depth + 1)
                }
            }
        }
        
        collectGeminiText(from: appElement)
        
        // Return the longest meaningful response
        let meaningfulTexts = allTexts.filter { $0.count > 150 }
        if let longestResponse = meaningfulTexts.max(by: { $0.count < $1.count }) {
            print("✅ Found Gemini response: \(longestResponse.count) chars")
            return longestResponse
        }
        
        // Fallback to shorter responses
        let shortTexts = allTexts.filter { $0.count > 80 }
        if let response = shortTexts.max(by: { $0.count < $1.count }) {
            return response
        }
        
        return ""
    }
    
    // MARK: - Gemini-Specific Features
    
    func isGeminiReady() -> Bool {
        return accessibility.isAppRunning(bundleId)
    }
    
    func getGeminiStatus() -> String {
        let isRunning = accessibility.isAppRunning(bundleId)
        let canAccess = isRunning ? (accessibility.getAppProcessElement(bundleId) != nil) : false
        
        return """
        Gemini (Safari) Status:
        • Safari Running: \(isRunning ? "✅" : "❌")
        • Safari Accessible: \(canAccess ? "✅" : "❌")
        • Bundle ID: \(bundleId)
        • Gemini URL: \(geminiURL)
        """
    }
}