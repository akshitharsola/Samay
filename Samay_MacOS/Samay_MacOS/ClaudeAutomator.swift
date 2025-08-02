//
//  ClaudeAutomator.swift
//  Samay_MacOS
//
//  Service-specific automation for Claude Desktop
//

import Foundation
import ApplicationServices
import AppKit

class ClaudeAutomator {
    static let shared = ClaudeAutomator()
    private let bundleId = "com.anthropic.claudefordesktop"
    private let accessibility = AccessibilityAPIAutomator.shared
    
    private init() {}
    
    // MARK: - Claude-Specific Automation
    
    func automateQuery(_ query: String, isNewChat: Bool = true) async throws -> String {
        print("🤖 Claude Desktop automation starting...")
        
        // Launch Claude if not running
        if !accessibility.isAppRunning(bundleId) {
            print("📱 Launching Claude Desktop...")
            guard accessibility.launchApp(bundleId) else {
                throw AIServiceError.failedToLaunch
            }
            try await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
        }
        
        guard let appElement = accessibility.getAppProcessElement(bundleId) else {
            throw AIServiceError.automationFailed("Could not access Claude app")
        }
        
        // Enable Electron accessibility
        print("🔧 Enabling Claude Desktop accessibility...")
        let accessibilityResult = AXUIElementSetAttributeValue(
            appElement,
            "AXManualAccessibility" as CFString,
            kCFBooleanTrue
        )
        print("🔧 Accessibility: \(accessibilityResult == .success ? "✅" : "❌")")
        
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Raise and activate window
        let windowSuccess = accessibility.raiseAndActivateClaudeWindow(appElement)
        print("🪟 Window focus: \(windowSuccess ? "✅" : "❌")")
        
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        // Handle new chat
        if isNewChat {
            print("🆕 Creating new Claude chat...")
            _ = accessibility.createNewClaudeChat(in: appElement)
            try await Task.sleep(nanoseconds: 1_500_000_000) // 1.5 seconds
        }
        
        // Use 31first.md researched approach for Claude Desktop
        print("🎯 Using 31first.md automation approach for Claude...")
        let automationSuccess = accessibility.automateTextInputWith31FirstApproach(appElement, query: query)
        
        if !automationSuccess {
            throw AIServiceError.automationFailed("31first.md automation approach failed for Claude")
        }
        
        // Wait for response
        print("⏳ Waiting for Claude response...")
        return try await waitForClaudeResponse(appElement)
    }
    
    private func waitForClaudeResponse(_ appElement: AXUIElement) async throws -> String {
        try await Task.sleep(nanoseconds: 4_000_000_000) // 4 seconds initial wait
        
        let maxWaitTime = 90.0 // 90 seconds for Claude (can be slow)
        let checkInterval = 2.5 // Check every 2.5 seconds
        let startTime = Date()
        var lastLength = 0
        var stableCount = 0
        var bestResponse = ""
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let response = accessibility.extractClaudeResponse(from: appElement)
            let length = response.count
            
            print("📊 Claude response: \(length) chars (was: \(lastLength))")
            
            if length > bestResponse.count {
                bestResponse = response
            }
            
            if length > lastLength && length > 80 {
                lastLength = length
                stableCount = 0
                print("📈 Claude response growing...")
            } else if length == lastLength && length > 150 {
                stableCount += 1
                print("⏸️ Claude response stable (\(stableCount))")
                
                if stableCount >= 2 { // 5 seconds stable
                    print("✅ Claude response complete")
                    return response
                }
            }
            
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        if !bestResponse.isEmpty && bestResponse.count > 50 {
            print("⏰ Claude timeout - returning best response")
            return bestResponse
        }
        
        throw AIServiceError.timeout
    }
    
    // MARK: - Claude-Specific Features
    
    func createNewChat() async throws -> Bool {
        guard let appElement = accessibility.getAppProcessElement(bundleId) else {
            return false
        }
        
        return accessibility.createNewClaudeChat(in: appElement)
    }
    
    func isClaudeReady() -> Bool {
        return accessibility.isAppRunning(bundleId)
    }
    
    func getClaudeStatus() -> String {
        let isRunning = accessibility.isAppRunning(bundleId)
        let canAccess = isRunning ? (accessibility.getAppProcessElement(bundleId) != nil) : false
        
        return """
        Claude Desktop Status:
        • Running: \(isRunning ? "✅" : "❌")
        • Accessible: \(canAccess ? "✅" : "❌")
        • Bundle ID: \(bundleId)
        """
    }
}