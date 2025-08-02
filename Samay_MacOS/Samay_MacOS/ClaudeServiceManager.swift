//
//  ClaudeServiceManager.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation
import AppKit

class ClaudeServiceManager: BaseAIServiceManager {
    
    init() {
        super.init(serviceType: .claude)
    }
    
    override func sendQuery(_ query: String) async throws -> String {
        // Use the base implementation which uses Accessibility API
        return try await super.sendQuery(query)
    }
    
    private func bringClaudeToFrontWithBugWorkaround() async throws {
        // Bring Claude to front
        try await AppDetectionService.shared.bringAppToFront(serviceType.bundleIdentifier)
        
        // Wait a moment for the window to appear
        try await Task.sleep(nanoseconds: 500_000_000)
        
        // Workaround for Claude's blank screen bug: switch to another app and back
        let otherApp = NSWorkspace.shared.frontmostApplication
        if otherApp?.bundleIdentifier != serviceType.bundleIdentifier {
            // Switch to another app briefly
            try await AppDetectionService.shared.bringAppToFront("com.apple.finder")
            try await Task.sleep(nanoseconds: 300_000_000)
            
            // Switch back to Claude
            try await AppDetectionService.shared.bringAppToFront(serviceType.bundleIdentifier)
            try await Task.sleep(nanoseconds: 500_000_000)
        }
    }
    
    private func automateClaudeQuery(_ query: String) async throws {
        let executor = await AppleScriptExecutor.shared
        
        // Check if we have accessibility permissions
        guard await executor.checkAccessibilityPermissions() else {
            await executor.requestAccessibilityPermissions()
            throw AIServiceError.automationFailed("Accessibility permissions required")
        }
        
        // Enhanced Claude automation sequence
        try await executor.executeClaudeSpecificAutomation(query)
    }
    
    private func extractClaudeResponse() async throws -> String {
        let executor = await AppleScriptExecutor.shared
        
        // Wait for Claude to finish processing (adaptive wait)
        try await waitForClaudeCompletion()
        
        // Extract response using sophisticated text selection
        return try await executor.extractClaudeResponse()
    }
    
    private func waitForClaudeCompletion() async throws {
        let executor = await AppleScriptExecutor.shared
        let maxWaitTime: TimeInterval = 30.0
        let checkInterval: TimeInterval = 1.0
        let startTime = Date()
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let isGenerating = try await executor.isClaudeGenerating()
            if !isGenerating {
                // Wait a bit more to ensure completion
                try await Task.sleep(nanoseconds: 1_000_000_000)
                return
            }
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        // If we timeout, proceed anyway
        print("Claude response extraction timed out, proceeding...")
    }
    
    override func isAppResponding() async -> Bool {
        // Claude-specific responsiveness check
        guard await isRunning else { return false }
        
        // You could implement more sophisticated checks here
        // For example, checking if the Claude window is accessible
        return true
    }
}

class PerplexityServiceManager: BaseAIServiceManager {
    
    init() {
        super.init(serviceType: .perplexity)
    }
    
    override func sendQuery(_ query: String) async throws -> String {
        // Use the base implementation which uses Accessibility API
        return try await super.sendQuery(query)
    }
    
    private func automatePerplexityQuery(_ query: String) async throws {
        let executor = await AppleScriptExecutor.shared
        
        guard await executor.checkAccessibilityPermissions() else {
            await executor.requestAccessibilityPermissions()
            throw AIServiceError.automationFailed("Accessibility permissions required")
        }
        
        // Enhanced Perplexity automation
        try await executor.executePerplexitySpecificAutomation(query)
    }
    
    private func extractPerplexityResponse() async throws -> String {
        let executor = await AppleScriptExecutor.shared
        
        // Wait for search results to load
        try await Task.sleep(nanoseconds: 3_000_000_000)
        
        return try await executor.extractPerplexityResponse()
    }
}

class ChatGPTServiceManager: BaseAIServiceManager {
    
    init() {
        super.init(serviceType: .chatgpt)
    }
    
    override func sendQuery(_ query: String) async throws -> String {
        // Use the base implementation which uses Accessibility API
        return try await super.sendQuery(query)
    }
    
    private func automateChatGPTQuery(_ query: String) async throws {
        let executor = await AppleScriptExecutor.shared
        
        guard await executor.checkAccessibilityPermissions() else {
            await executor.requestAccessibilityPermissions()
            throw AIServiceError.automationFailed("Accessibility permissions required")
        }
        
        // Enhanced ChatGPT automation
        try await executor.executeChatGPTSpecificAutomation(query)
    }
    
    private func extractChatGPTResponse() async throws -> String {
        let executor = await AppleScriptExecutor.shared
        
        // Wait for ChatGPT to finish processing
        try await waitForChatGPTCompletion()
        
        return try await executor.extractChatGPTResponse()
    }
    
    private func waitForChatGPTCompletion() async throws {
        let maxWaitTime: TimeInterval = 45.0
        let checkInterval: TimeInterval = 2.0
        let startTime = Date()
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let executor = await AppleScriptExecutor.shared
            let isGenerating = try await executor.isChatGPTGenerating()
            if !isGenerating {
                // Wait a bit more to ensure completion
                try await Task.sleep(nanoseconds: 2_000_000_000)
                return
            }
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        print("ChatGPT response extraction timed out, proceeding...")
    }
}

class GeminiServiceManager: BaseAIServiceManager {
    
    init() {
        super.init(serviceType: .gemini)
    }
    
    override var isInstalled: Bool {
        get async {
            // Safari is always installed on macOS
            return true
        }
    }
    
    override var isRunning: Bool {
        get async {
            // Check if Safari is running
            return await AppDetectionService.shared.isAppRunning("com.apple.Safari")
        }
    }
    
    override func sendQuery(_ query: String) async throws -> String {
        // Gemini requires special handling through Safari
        // For now, throw not implemented error
        throw AIServiceError.automationFailed("Gemini automation via Accessibility API not yet implemented")
    }
    
    override func launch() async throws {
        // Launch Safari and navigate to Gemini
        try await AppDetectionService.shared.launchApp("com.apple.Safari")
        try await Task.sleep(nanoseconds: 1_000_000_000)
        
        // Navigate to Gemini
        let executor = await AppleScriptExecutor.shared
        try await executor.openGeminiInSafari()
    }
    
    private func automateGeminiQuery(_ query: String) async throws {
        let executor = await AppleScriptExecutor.shared
        
        guard await executor.checkAccessibilityPermissions() else {
            await executor.requestAccessibilityPermissions()
            throw AIServiceError.automationFailed("Accessibility permissions required")
        }
        
        // Gemini web automation
        try await executor.executeGeminiWebAutomation(query)
    }
    
    private func extractGeminiResponse() async throws -> String {
        let executor = await AppleScriptExecutor.shared
        
        // Wait for Gemini to finish processing
        try await waitForGeminiCompletion()
        
        return try await executor.extractGeminiResponse()
    }
    
    private func waitForGeminiCompletion() async throws {
        let maxWaitTime: TimeInterval = 60.0
        let checkInterval: TimeInterval = 3.0
        let startTime = Date()
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let executor = await AppleScriptExecutor.shared
            let isGenerating = try await executor.isGeminiGenerating()
            if !isGenerating {
                try await Task.sleep(nanoseconds: 2_000_000_000)
                return
            }
            try await Task.sleep(nanoseconds: UInt64(checkInterval * 1_000_000_000))
        }
        
        print("Gemini response extraction timed out, proceeding...")
    }
}