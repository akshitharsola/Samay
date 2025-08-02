//
//  ChatGPTAutomator.swift
//  Samay_MacOS
//
//  Service-specific automation for ChatGPT Desktop
//

import Foundation
import ApplicationServices
import AppKit

class ChatGPTAutomator {
    static let shared = ChatGPTAutomator()
    private let bundleId = "com.openai.chat"
    private let accessibility = AccessibilityAPIAutomator.shared
    
    private init() {}
    
    // MARK: - ChatGPT-Specific Automation
    
    func automateQuery(_ query: String, isNewChat: Bool = true) async throws -> String {
        print("💬 ChatGPT Desktop automation starting...")
        
        // Launch ChatGPT if not running
        if !accessibility.isAppRunning(bundleId) {
            print("📱 Launching ChatGPT...")
            guard accessibility.launchApp(bundleId) else {
                throw AIServiceError.failedToLaunch
            }
            try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
        }
        
        guard let appElement = accessibility.getAppProcessElement(bundleId) else {
            throw AIServiceError.automationFailed("Could not access ChatGPT app")
        }
        
        // Enable accessibility for web-based app
        print("🔧 Enabling ChatGPT accessibility...")
        let accessibilityResult = AXUIElementSetAttributeValue(
            appElement,
            "AXManualAccessibility" as CFString,
            kCFBooleanTrue
        )
        print("🔧 Accessibility: \(accessibilityResult == .success ? "✅" : "❌")")
        
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Focus ChatGPT window
        _ = accessibility.focusAppWithKeyboard(bundleId)
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        // Handle new chat
        if isNewChat {
            print("🆕 Creating new ChatGPT chat...")
            _ = createNewChatGPTChat(in: appElement)
            try await Task.sleep(nanoseconds: 1_500_000_000) // 1.5 seconds
        }
        
        // Use 31first.md researched approach for ChatGPT Desktop  
        print("🎯 Using 31first.md automation approach for ChatGPT...")
        let automationSuccess = accessibility.automateTextInputWith31FirstApproach(appElement, query: query)
        
        if !automationSuccess {
            // Try alternative submit methods for ChatGPT
            print("🔄 Trying alternative ChatGPT submit methods...")
            if !accessibility.sendCmdEnterKey() {
                throw AIServiceError.automationFailed("31first.md automation approach failed for ChatGPT")
            }
        }
        
        // Wait for response
        print("⏳ Waiting for ChatGPT response...")
        return try await waitForChatGPTResponse(appElement)
    }
    
    private func findChatGPTTextInput(in appElement: AXUIElement) -> AXUIElement? {
        print("🔍 Looking for ChatGPT text input...")
        
        // Strategy 1: Look for text areas
        if let textArea = accessibility.findElementByRole(in: appElement, role: kAXTextAreaRole, maxDepth: 10) {
            return textArea
        }
        
        // Strategy 2: Look in web areas
        let webAreas = accessibility.findAllElementsByRole(in: appElement, role: "AXWebArea", maxDepth: 8)
        for webArea in webAreas {
            if let textInput = accessibility.findElementByRole(in: webArea, role: kAXTextAreaRole, maxDepth: 5) {
                return textInput
            }
        }
        
        // Strategy 3: Look for any editable element
        return accessibility.findAnyEditableElement(in: appElement, maxDepth: 10)
    }
    
    private func createNewChatGPTChat(in appElement: AXUIElement) -> Bool {
        // Try to find "New chat" or "+" button
        if let newChatButton = accessibility.findElementContainingText(in: appElement, text: "New chat", maxDepth: 8) {
            return accessibility.clickElement(newChatButton)
        }
        
        // Try Cmd+N shortcut
        let cmdNEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x2D, keyDown: true) // N key
        cmdNEvent?.flags = .maskCommand
        cmdNEvent?.post(tap: .cghidEventTap)
        let cmdNUpEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x2D, keyDown: false)
        cmdNUpEvent?.flags = .maskCommand
        cmdNUpEvent?.post(tap: .cghidEventTap)
        
        return true
    }
    
    private func waitForChatGPTResponse(_ appElement: AXUIElement) async throws -> String {
        try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds initial wait
        
        let maxWaitTime = 75.0 // 75 seconds for ChatGPT
        let checkInterval = 2.0 // Check every 2 seconds
        let startTime = Date()
        var lastLength = 0
        var stableCount = 0
        var bestResponse = ""
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let response = extractChatGPTResponse(from: appElement)
            let length = response.count
            
            print("📊 ChatGPT response: \(length) chars (was: \(lastLength))")
            
            if length > bestResponse.count {
                bestResponse = response
            }
            
            if length > lastLength && length > 70 {
                lastLength = length
                stableCount = 0
                print("📈 ChatGPT response growing...")
            } else if length == lastLength && length > 120 {
                stableCount += 1
                print("⏸️ ChatGPT response stable (\(stableCount))")
                
                if stableCount >= 2 { // 4 seconds stable
                    print("✅ ChatGPT response complete")
                    return response
                }
            }
            
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        if !bestResponse.isEmpty && bestResponse.count > 60 {
            print("⏰ ChatGPT timeout - returning best response")
            return bestResponse
        }
        
        throw AIServiceError.timeout
    }
    
    private func extractChatGPTResponse(from appElement: AXUIElement) -> String {
        print("🔍 Extracting ChatGPT response...")
        
        // Use the general response extraction but with ChatGPT-specific filtering
        var allTexts: [String] = []
        
        func collectChatGPTText(from element: AXUIElement, depth: Int = 0) {
            if depth > 8 { return }
            
            // Get text content
            var textValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &textValue) == .success,
               let text = textValue as? String,
               !text.isEmpty,
               text.count > 60 {
                
                // Filter out ChatGPT UI elements
                let lowercaseText = text.lowercased()
                if !lowercaseText.contains("send a message") &&
                   !lowercaseText.contains("chatgpt") &&
                   !lowercaseText.contains("regenerate") &&
                   !lowercaseText.contains("copy") &&
                   !allTexts.contains(text) {
                    allTexts.append(text)
                }
            }
            
            // Check children
            var children: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
               let childArray = children as? [AXUIElement] {
                for child in childArray {
                    collectChatGPTText(from: child, depth: depth + 1)
                }
            }
        }
        
        collectChatGPTText(from: appElement)
        
        // Return the longest meaningful response
        let meaningfulTexts = allTexts.filter { $0.count > 120 }
        if let longestResponse = meaningfulTexts.max(by: { $0.count < $1.count }) {
            print("✅ Found ChatGPT response: \(longestResponse.count) chars")
            return longestResponse
        }
        
        // Fallback to shorter responses
        let shortTexts = allTexts.filter { $0.count > 60 }
        if let response = shortTexts.max(by: { $0.count < $1.count }) {
            return response
        }
        
        return ""
    }
    
    // MARK: - ChatGPT-Specific Features
    
    func isChatGPTReady() -> Bool {
        return accessibility.isAppRunning(bundleId)
    }
    
    func getChatGPTStatus() -> String {
        let isRunning = accessibility.isAppRunning(bundleId)
        let canAccess = isRunning ? (accessibility.getAppProcessElement(bundleId) != nil) : false
        
        return """
        ChatGPT Desktop Status:
        • Running: \(isRunning ? "✅" : "❌")
        • Accessible: \(canAccess ? "✅" : "❌")
        • Bundle ID: \(bundleId)
        """
    }
}