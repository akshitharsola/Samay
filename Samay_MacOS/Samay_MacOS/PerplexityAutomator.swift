//
//  PerplexityAutomator.swift
//  Samay_MacOS
//
//  Service-specific automation for Perplexity
//

import Foundation
import ApplicationServices
import AppKit

class PerplexityAutomator {
    static let shared = PerplexityAutomator()
    private let bundleId = "ai.perplexity.mac"
    private let accessibility = AccessibilityAPIAutomator.shared
    
    private init() {}
    
    // MARK: - Perplexity-Specific Automation
    
    func automateQuery(_ query: String) async throws -> String {
        print("🔍 Perplexity automation starting...")
        
        // Launch Perplexity if not running
        if !accessibility.isAppRunning(bundleId) {
            print("📱 Launching Perplexity...")
            guard accessibility.launchApp(bundleId) else {
                throw AIServiceError.failedToLaunch
            }
            try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
        }
        
        guard let appElement = accessibility.getAppProcessElement(bundleId) else {
            throw AIServiceError.automationFailed("Could not access Perplexity app")
        }
        
        // Focus Perplexity window
        _ = accessibility.focusAppWithKeyboard(bundleId)
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Find search field (Perplexity uses search field, not text area)
        print("🔍 Looking for Perplexity search field...")
        var searchField = accessibility.findElementByRole(in: appElement, role: kAXTextFieldRole, maxDepth: 8)
        
        if searchField == nil {
            // Try combobox (alternative search field type)
            searchField = accessibility.findElementByRole(in: appElement, role: kAXComboBoxRole, maxDepth: 8)
        }
        
        if searchField == nil {
            // Try Tab navigation for Perplexity
            print("🔄 Direct search failed, trying Tab navigation...")
            if accessibility.focusTextInputWithTab(in: appElement, maxAttempts: 8) {
                // Send query directly via clipboard
                if !accessibility.sendTextViaClipboard(query) {
                    throw AIServiceError.automationFailed("Failed to send text to Perplexity")
                }
            } else {
                throw AIServiceError.automationFailed("Could not find Perplexity search field")
            }
        } else {
            // Focus search field and send query
            print("✅ Found Perplexity search field")
            _ = accessibility.focusElement(searchField!)
            
            try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
            
            // Clear existing content and send new query
            _ = accessibility.setElementValue(searchField!, value: "")
            try await Task.sleep(nanoseconds: 200_000_000) // 0.2 seconds
            
            if !accessibility.setElementValue(searchField!, value: query) {
                // Fallback to clipboard
                if !accessibility.sendTextViaClipboard(query) {
                    throw AIServiceError.automationFailed("Failed to send text to Perplexity")
                }
            }
        }
        
        // Submit search
        print("📤 Submitting Perplexity search...")
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        if !accessibility.sendEnterKey() {
            throw AIServiceError.automationFailed("Failed to submit search")
        }
        
        // Wait for response
        print("⏳ Waiting for Perplexity response...")
        return try await waitForPerplexityResponse(appElement)
    }
    
    private func waitForPerplexityResponse(_ appElement: AXUIElement) async throws -> String {
        try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds initial wait
        
        let maxWaitTime = 60.0 // 60 seconds for Perplexity
        let checkInterval = 2.0 // Check every 2 seconds
        let startTime = Date()
        var lastLength = 0
        var stableCount = 0
        var bestResponse = ""
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let response = extractPerplexityResponse(from: appElement)
            let length = response.count
            
            print("📊 Perplexity response: \(length) chars (was: \(lastLength))")
            
            if length > bestResponse.count {
                bestResponse = response
            }
            
            if length > lastLength && length > 100 {
                lastLength = length
                stableCount = 0
                print("📈 Perplexity response growing...")
            } else if length == lastLength && length > 200 {
                stableCount += 1
                print("⏸️ Perplexity response stable (\(stableCount))")
                
                if stableCount >= 2 { // 4 seconds stable
                    print("✅ Perplexity response complete")
                    return response
                }
            }
            
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        if !bestResponse.isEmpty && bestResponse.count > 80 {
            print("⏰ Perplexity timeout - returning best response")
            return bestResponse
        }
        
        throw AIServiceError.timeout
    }
    
    private func extractPerplexityResponse(from appElement: AXUIElement) -> String {
        print("🔍 Extracting Perplexity response...")
        
        // Strategy 1: Look for text areas with substantial content
        var allTexts: [String] = []
        
        func collectText(from element: AXUIElement, depth: Int = 0) {
            if depth > 8 { return }
            
            // Get text content
            var textValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &textValue) == .success,
               let text = textValue as? String,
               !text.isEmpty,
               text.count > 50 {
                
                // Filter out search-related UI text
                let lowercaseText = text.lowercased()
                if !lowercaseText.contains("search") &&
                   !lowercaseText.contains("ask anything") &&
                   !lowercaseText.contains("perplexity") &&
                   !allTexts.contains(text) {
                    allTexts.append(text)
                }
            }
            
            // Check children
            var children: CFTypeRef?
            if AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &children) == .success,
               let childArray = children as? [AXUIElement] {
                for child in childArray {
                    collectText(from: child, depth: depth + 1)
                }
            }
        }
        
        collectText(from: appElement)
        
        // Return the longest meaningful response
        let meaningfulTexts = allTexts.filter { $0.count > 100 }
        if let longestResponse = meaningfulTexts.max(by: { $0.count < $1.count }) {
            print("✅ Found Perplexity response: \(longestResponse.count) chars")
            return longestResponse
        }
        
        // Fallback to shorter responses
        let shortTexts = allTexts.filter { $0.count > 50 }
        if let response = shortTexts.max(by: { $0.count < $1.count }) {
            return response
        }
        
        return ""
    }
    
    // MARK: - Perplexity-Specific Features
    
    func isPerplexityReady() -> Bool {
        return accessibility.isAppRunning(bundleId)
    }
    
    func getPerplexityStatus() -> String {
        let isRunning = accessibility.isAppRunning(bundleId)
        let canAccess = isRunning ? (accessibility.getAppProcessElement(bundleId) != nil) : false
        
        return """
        Perplexity Status:
        • Running: \(isRunning ? "✅" : "❌")
        • Accessible: \(canAccess ? "✅" : "❌")
        • Bundle ID: \(bundleId)
        """
    }
}