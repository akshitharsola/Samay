//
//  AppleScriptExecutor.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation
import OSAKit
import ApplicationServices
import AppKit

@MainActor
class AppleScriptExecutor {
    static let shared = AppleScriptExecutor()
    
    private init() {}
    
    func executeScript(_ scriptSource: String, timeout: TimeInterval = 30.0) async throws -> String {
        // Try NSAppleScript first for better TCC compatibility
        do {
            return try await executeWithNSAppleScript(scriptSource)
        } catch {
            // Fall back to OSAScript if NSAppleScript fails
            print("NSAppleScript failed, falling back to OSAScript: \(error)")
            try await initializeSystemEvents()
            return try runScript(scriptSource, timeout: timeout)
        }
    }
    
    // Enhanced NSAppleScript execution method
    private func executeWithNSAppleScript(_ scriptSource: String) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.main.async {
                guard let script = NSAppleScript(source: scriptSource) else {
                    continuation.resume(throwing: AIServiceError.automationFailed("Failed to create NSAppleScript"))
                    return
                }
                
                var errorInfo: NSDictionary?
                let result = script.executeAndReturnError(&errorInfo)
                
                if let error = errorInfo {
                    let errorMessage = error.description
                    continuation.resume(throwing: AIServiceError.automationFailed("NSAppleScript error: \(errorMessage)"))
                } else {
                    continuation.resume(returning: result.stringValue ?? "")
                }
            }
        }
    }
    
    private func initializeSystemEvents() async throws {
        let initScript = """
        tell application id "com.apple.systemevents"
            launch
            set quit delay to 0
        end tell
        delay 0.3
        
        -- Wait for System Events to be fully ready
        repeat 10 times
            try
                tell application "System Events"
                    set processNames to name of every process
                end tell
                exit repeat
            on error
                delay 0.2
            end try
        end repeat
        """
        
        _ = try runScript(initScript, timeout: 10.0)
    }
    
    private func runScript(_ scriptSource: String, timeout: TimeInterval) throws -> String {
        let script = OSAScript(source: scriptSource)
        
        var errorInfo: NSDictionary?
        let result = script.executeAndReturnError(&errorInfo)
        
        if let error = errorInfo {
            let errorMessage = error.description
            throw AIServiceError.automationFailed("AppleScript error: \(errorMessage)")
        }
        
        return result?.stringValue ?? ""
    }
    
    func checkAccessibilityPermissions() -> Bool {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false]
        return AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    func requestAccessibilityPermissions() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        _ = AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    func triggerAppleEventsPermissionRequest() async throws {
        // Use the enhanced NSAppleScript method for better TCC compatibility
        try await requestAppleEventsPermissionDialog()
    }
    
    // New method using NSAppleScript for better TCC compatibility
    func requestAppleEventsPermissionDialog() async throws {
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.main.async {
                // Use NSAppleScript instead of OSAScript for better TCC dialog triggering
                let scriptSource = """
                tell application "System Events"
                    activate
                    -- Simple request that should trigger TCC dialog
                    try
                        get name of every process
                        return "Apple Events permission granted"
                    on error errorMessage
                        return "Apple Events permission denied: " & errorMessage
                    end try
                end tell
                """
                
                guard let script = NSAppleScript(source: scriptSource) else {
                    continuation.resume(throwing: AIServiceError.automationFailed("Failed to create NSAppleScript"))
                    return
                }
                
                var errorInfo: NSDictionary?
                let result = script.executeAndReturnError(&errorInfo)
                
                if let error = errorInfo {
                    let errorMessage = error.description
                    print("NSAppleScript error: \(errorMessage)")
                    // Don't throw error for -1743, as this is expected during permission request
                    if errorMessage.contains("-1743") {
                        print("Apple Events permission required - this is expected on first run")
                    }
                    continuation.resume(returning: ())
                } else {
                    print("NSAppleScript executed successfully: \(result.stringValue ?? "No result")")
                    continuation.resume(returning: ())
                }
            }
        }
    }
    
    func simpleSystemEventsTest() async throws -> String {
        // Bypass our initialization and try direct access
        let simpleScript = """
        tell application "System Events"
            return "test"
        end tell
        """
        
        return try runScript(simpleScript, timeout: 5.0)
    }
    
    // Test method to verify TCC permissions are working
    func testAppleEventsPermission() async -> Bool {
        do {
            let testScript = """
            tell application "System Events"
                set processCount to count of processes
                return "Found " & processCount & " processes"
            end tell
            """
            
            let result = try await executeScript(testScript)
            print("Apple Events test successful: \(result)")
            return true
        } catch {
            print("Apple Events test failed: \(error)")
            return false
        }
    }
}

// MARK: - Common AppleScript Templates

extension AppleScriptExecutor {
    
    func getAppWindowInfo(_ bundleIdentifier: String) async throws -> [WindowInfo] {
        let script = """
        tell application "System Events"
            set appProcess to first application process whose bundle identifier is "\(bundleIdentifier)"
            set windowList to windows of appProcess
            set windowInfo to {}
            repeat with w in windowList
                set windowTitle to name of w
                set windowPosition to position of w
                set windowSize to size of w
                set end of windowInfo to {title:windowTitle, position:windowPosition, size:windowSize}
            end repeat
            return windowInfo
        end tell
        """
        
        let result = try await executeScript(script)
        return parseWindowInfo(result)
    }
    
    func clickElement(appName: String, elementDescription: String) async throws {
        let script = """
        tell application "System Events"
            tell process "\(appName)"
                click \(elementDescription)
            end tell
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func typeText(_ text: String) async throws {
        let escapedText = text.replacingOccurrences(of: "\"", with: "\\\"")
        let script = """
        tell application "System Events"
            keystroke "\(escapedText)"
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func pressKey(_ key: String, modifiers: [String] = []) async throws {
        let modifierString = modifiers.isEmpty ? "" : "using {\(modifiers.joined(separator: ", "))}"
        let script = """
        tell application "System Events"
            key code \(key) \(modifierString)
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func getClipboardContent() async throws -> String {
        let script = """
        set the clipboard to the clipboard as string
        return the clipboard
        """
        
        return try await executeScript(script)
    }
    
    func setClipboardContent(_ content: String) async throws {
        let escapedContent = content.replacingOccurrences(of: "\"", with: "\\\"")
        let script = """
        set the clipboard to "\(escapedContent)"
        """
        
        _ = try await executeScript(script)
    }
    
    private func parseWindowInfo(_ scriptResult: String) -> [WindowInfo] {
        // Basic parsing - in a real implementation, you'd want more robust parsing
        // This is a simplified version for demonstration
        return []
    }
}

// MARK: - AI Service Specific Automation

extension AppleScriptExecutor {
    
    func executeClaudeSpecificAutomation(_ query: String) async throws {
        let script = """
        tell application "Claude"
            activate
            -- Wait for Claude to be frontmost
            repeat until frontmost
                delay 0.1
            end repeat
        end tell
        
        delay 1.0
        
        tell application "System Events"
            tell process "Claude"
                -- Focus on the input area
                try
                    set inputField to first text area whose value is not ""
                    set focused of inputField to true
                on error
                    -- Fallback: click in the input area
                    try
                        click (first text area)
                    on error
                        -- Secondary fallback: use keyboard navigation
                        key code 48 -- Tab key to navigate to input
                    end try
                end try
                
                delay 0.2
                
                -- Clear existing content
                key code 0 using command down -- Cmd+A
                
                -- Type the query
                keystroke "\(escapeForAppleScript(query))"
                
                delay 0.1
                
                -- Send the query
                key code 36 -- Enter key
            end tell
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func isClaudeGenerating() async throws -> Bool {
        let script = """
        tell application "System Events"
            tell process "Claude"
                try
                    -- Look for generating indicators
                    set generatingElements to buttons whose name contains "Stop"
                    if (count of generatingElements) > 0 then
                        return true
                    end if
                    
                    -- Check for typing indicators or loading states
                    set loadingElements to static text whose value contains "..."
                    if (count of loadingElements) > 0 then
                        return true
                    end if
                    
                    return false
                on error
                    return false
                end try
            end tell
        end tell
        """
        
        let result = try await executeScript(script)
        return result.lowercased().contains("true")
    }
    
    func extractClaudeResponse() async throws -> String {
        let script = """
        tell application "System Events"
            tell process "Claude"
                try
                    -- Find the latest response area
                    set responseElements to static text whose value is not ""
                    if (count of responseElements) > 0 then
                        set latestResponse to value of last item of responseElements
                        
                        -- Copy to clipboard for extraction
                        set the clipboard to latestResponse
                        return latestResponse
                    else
                        return "No response found"
                    end if
                on error errorMessage
                    return "Error extracting response: " & errorMessage
                end try
            end tell
        end tell
        """
        
        return try await executeScript(script)
    }
    
    func executePerplexitySpecificAutomation(_ query: String) async throws {
        let script = """
        tell application "Perplexity- Ask Anything"
            activate
            -- Wait for Perplexity to be frontmost
            repeat until frontmost
                delay 0.1
            end repeat
        end tell
        
        delay 1.0
        
        tell application "System Events"
            tell process "Perplexity- Ask Anything"
                -- Focus on search input
                try
                    set searchField to first text field
                    set focused of searchField to true
                on error
                    key code 48 -- Tab to navigate to input
                end try
                
                delay 0.2
                
                -- Clear and enter query
                key code 0 using command down -- Cmd+A
                keystroke "\(escapeForAppleScript(query))"
                
                delay 0.1
                
                -- Submit search
                key code 36 -- Enter
            end tell
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func extractPerplexityResponse() async throws -> String {
        let script = """
        tell application "System Events"
            tell process "Perplexity- Ask Anything"
                try
                    -- Wait for results to load
                    delay 2
                    
                    -- Find response content
                    set responseText to ""
                    set textElements to static text
                    
                    repeat with textElement in textElements
                        set elementValue to value of textElement
                        if length of elementValue > 50 then
                            set responseText to responseText & elementValue & " "
                        end if
                    end repeat
                    
                    return responseText
                on error errorMessage
                    return "Error extracting Perplexity response: " & errorMessage
                end try
            end tell
        end tell
        """
        
        return try await executeScript(script)
    }
    
    func executeChatGPTSpecificAutomation(_ query: String) async throws {
        let script = """
        tell application "ChatGPT"
            activate
            -- Wait for ChatGPT to be frontmost
            repeat until frontmost
                delay 0.1
            end repeat
        end tell
        
        delay 1.0
        
        tell application "System Events"
            tell process "ChatGPT"
                -- Focus on the input area
                try
                    set inputField to first text area
                    set focused of inputField to true
                on error
                    -- Fallback: click in the message input area
                    try
                        click (first text area)
                    on error
                        -- Try to find input by placeholder or accessibility
                        key code 48 -- Tab to navigate
                    end try
                end try
                
                delay 0.3
                
                -- Clear existing content
                key code 0 using command down -- Cmd+A
                
                -- Type the query
                keystroke "\(escapeForAppleScript(query))"
                
                delay 0.2
                
                -- Send the message (Enter or Send button)
                key code 36 -- Enter key
            end tell
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func isChatGPTGenerating() async throws -> Bool {
        let script = """
        tell application "System Events"
            tell process "ChatGPT"
                try
                    -- Look for stop generation button or loading indicators
                    set stopButtons to buttons whose name contains "Stop" or name contains "stop"
                    if (count of stopButtons) > 0 then
                        return true
                    end if
                    
                    -- Check for thinking/generating indicators
                    set thinkingElements to static text whose value contains "thinking" or value contains "..."
                    if (count of thinkingElements) > 0 then
                        return true
                    end if
                    
                    -- Check for progress indicators
                    set progressElements to progress indicators
                    if (count of progressElements) > 0 then
                        return true
                    end if
                    
                    return false
                on error
                    return false
                end try
            end tell
        end tell
        """
        
        let result = try await executeScript(script)
        return result.lowercased().contains("true")
    }
    
    func extractChatGPTResponse() async throws -> String {
        let script = """
        tell application "System Events"
            tell process "ChatGPT"
                try
                    -- Find the conversation area and get the latest response
                    set conversationArea to first scroll area
                    set responseElements to static text of conversationArea
                    
                    if (count of responseElements) > 0 then
                        -- Get the latest non-empty response
                        set latestResponse to ""
                        repeat with responseElement in reverse of responseElements
                            set elementValue to value of responseElement
                            if length of elementValue > 20 then
                                set latestResponse to elementValue
                                exit repeat
                            end if
                        end repeat
                        
                        if latestResponse is not "" then
                            -- Copy to clipboard for extraction
                            set the clipboard to latestResponse
                            return latestResponse
                        else
                            return "No substantial response found"
                        end if
                    else
                        return "No response elements found"
                    end if
                on error errorMessage
                    return "Error extracting ChatGPT response: " & errorMessage
                end try
            end tell
        end tell
        """
        
        return try await executeScript(script)
    }
    
    func openGeminiInSafari() async throws {
        let script = """
        tell application "Safari"
            activate
            
            -- Check if Gemini is already open in a tab
            set geminiFound to false
            repeat with theWindow in windows
                repeat with theTab in tabs of theWindow
                    if URL of theTab contains "gemini.google.com" then
                        set current tab of theWindow to theTab
                        set index of theWindow to 1
                        set geminiFound to true
                        exit repeat
                    end if
                end repeat
                if geminiFound then exit repeat
            end repeat
            
            -- If not found, open new tab with Gemini
            if not geminiFound then
                tell front window
                    set current tab to (make new tab with properties {URL:"https://gemini.google.com/app"})
                end tell
            end if
        end tell
        
        delay 2
        """
        
        _ = try await executeScript(script)
    }
    
    func executeGeminiWebAutomation(_ query: String) async throws {
        let script = """
        tell application "Safari"
            activate
        end tell
        
        delay 1
        
        tell application "System Events"
            tell process "Safari"
                -- Look for the text input area on Gemini web page
                try
                    -- Try to find the prompt input field
                    set inputField to first text area whose description contains "prompt" or description contains "message" or description contains "Enter"
                    set focused of inputField to true
                on error
                    -- Fallback: click in the main content area and use keyboard navigation
                    try
                        key code 48 -- Tab to navigate to input
                        delay 0.5
                    end try
                end try
                
                delay 0.5
                
                -- Clear any existing content
                key code 0 using command down -- Cmd+A
                
                -- Type the query
                keystroke "\(escapeForAppleScript(query))"
                
                delay 0.3
                
                -- Submit the query (Enter key)
                key code 36 -- Enter
            end tell
        end tell
        """
        
        _ = try await executeScript(script)
    }
    
    func isGeminiGenerating() async throws -> Bool {
        let script = """
        tell application "System Events"
            tell process "Safari"
                try
                    -- Look for generating indicators in Gemini web interface
                    set loadingElements to static text whose value contains "Thinking" or value contains "Generating" or value contains "..."
                    if (count of loadingElements) > 0 then
                        return true
                    end if
                    
                    -- Check for progress indicators or spinning elements
                    set progressElements to progress indicators
                    if (count of progressElements) > 0 then
                        return true
                    end if
                    
                    -- Look for stop button which indicates generation in progress
                    set stopButtons to buttons whose name contains "Stop" or description contains "stop"
                    if (count of stopButtons) > 0 then
                        return true
                    end if
                    
                    return false
                on error
                    return false
                end try
            end tell
        end tell
        """
        
        let result = try await executeScript(script)
        return result.lowercased().contains("true")
    }
    
    func extractGeminiResponse() async throws -> String {
        let script = """
        tell application "System Events"
            tell process "Safari"
                try
                    -- Wait a moment for content to fully load
                    delay 1
                    
                    -- Try to find the response content in Gemini's web interface
                    set responseText to ""
                    
                    -- Look for text elements that contain substantial content
                    set allTextElements to static text
                    repeat with textElement in allTextElements
                        set elementValue to value of textElement
                        if length of elementValue > 50 then
                            -- Skip navigation and UI elements, focus on response content
                            if elementValue does not contain "Gemini" and elementValue does not contain "Google" and elementValue does not contain "Sign in" then
                                if responseText is "" then
                                    set responseText to elementValue
                                else
                                    set responseText to responseText & " " & elementValue
                                end if
                            end if
                        end if
                    end repeat
                    
                    if responseText is not "" then
                        -- Copy to clipboard for backup
                        set the clipboard to responseText
                        return responseText
                    else
                        return "No response content found in Gemini interface"
                    end if
                    
                on error errorMessage
                    return "Error extracting Gemini response: " & errorMessage
                end try
            end tell
        end tell
        """
        
        return try await executeScript(script)
    }
    
    private func escapeForAppleScript(_ text: String) -> String {
        return text
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\n", with: "\\n")
            .replacingOccurrences(of: "\r", with: "\\r")
    }
}

struct WindowInfo {
    let title: String
    let position: CGPoint
    let size: CGSize
}

// MARK: - Key Code Constants

extension AppleScriptExecutor {
    enum KeyCode {
        static let enter = "36"
        static let escape = "53"
        static let space = "49"
        static let tab = "48"
        static let delete = "51"
        static let returnKey = "36"
        static let commandV = "9" // V key, use with command modifier
        static let commandC = "8" // C key, use with command modifier
        static let commandA = "0" // A key, use with command modifier
    }
    
    enum Modifier {
        static let command = "command down"
        static let shift = "shift down"
        static let option = "option down"
        static let control = "control down"
    }
}