//
//  AIServiceManager.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation
import AppKit

enum AIServiceType: String, CaseIterable {
    case claude = "Claude"
    case perplexity = "Perplexity"
    case chatgpt = "ChatGPT"
    case gemini = "Gemini"
    
    var bundleIdentifier: String {
        switch self {
        case .claude:
            return "com.anthropic.claudefordesktop"
        case .perplexity:
            return "ai.perplexity.mac"
        case .chatgpt:
            return "com.openai.chat"
        case .gemini:
            return "com.apple.Safari" // Web-based via Safari
        }
    }
    
    var displayName: String {
        return self.rawValue
    }
}

enum AIServiceError: Error {
    case notInstalled
    case failedToLaunch
    case automationFailed(String)
    case responseParsingFailed
    case timeout
}

protocol AIServiceManager {
    var serviceType: AIServiceType { get }
    var isInstalled: Bool { get async }
    var isRunning: Bool { get async }
    
    func launch() async throws
    func isAppResponding() async -> Bool
    func sendQuery(_ query: String) async throws -> String
    func close() async throws
}

class BaseAIServiceManager: AIServiceManager {
    let serviceType: AIServiceType
    
    init(serviceType: AIServiceType) {
        self.serviceType = serviceType
    }
    
    var isInstalled: Bool {
        get async {
            return await AppDetectionService.shared.isAppInstalled(serviceType.bundleIdentifier)
        }
    }
    
    var isRunning: Bool {
        get async {
            return await AppDetectionService.shared.isAppRunning(serviceType.bundleIdentifier)
        }
    }
    
    func launch() async throws {
        try await AppDetectionService.shared.launchApp(serviceType.bundleIdentifier)
    }
    
    func isAppResponding() async -> Bool {
        // Default implementation - can be overridden by specific managers
        return await isRunning
    }
    
    func sendQuery(_ query: String) async throws -> String {
        // Use 31first.md researched approach with direct UI automation
        print("🔄 Using 31first.md automation approach for \(serviceType.rawValue)...")
        
        let automator = AccessibilityAPIAutomator.shared
        guard automator.checkAccessibilityPermissions() else {
            throw AIServiceError.automationFailed("AUTHORIZATION_REQUIRED: Please grant Accessibility permissions in System Preferences → Privacy & Security → Accessibility")
        }
        
        // Use service-specific automators with 31first.md approach
        switch serviceType {
        case .claude:
            return try await ClaudeAutomator.shared.automateQuery(query)
        case .perplexity:
            return try await PerplexityAutomator.shared.automateQuery(query)
        case .chatgpt:
            return try await ChatGPTAutomator.shared.automateQuery(query)
        case .gemini:
            return try await GeminiAutomator.shared.automateQuery(query)
        }
    }
    
    func close() async throws {
        // Default implementation
        try await AppDetectionService.shared.quitApp(serviceType.bundleIdentifier)
    }
}

@MainActor
class AIServiceOrchestrator: ObservableObject {
    @Published var availableServices: [AIServiceType] = []
    @Published var runningServices: [AIServiceType] = []
    @Published var isScanning = false
    
    private var serviceManagers: [AIServiceType: AIServiceManager] = [:]
    
    init() {
        setupServiceManagers()
    }
    
    private func setupServiceManagers() {
        serviceManagers[.claude] = ClaudeServiceManager()
        serviceManagers[.perplexity] = PerplexityServiceManager()
        serviceManagers[.chatgpt] = ChatGPTServiceManager()
        serviceManagers[.gemini] = GeminiServiceManager()
    }
    
    func scanForServices() async {
        isScanning = true
        defer { isScanning = false }
        
        var available: [AIServiceType] = []
        var running: [AIServiceType] = []
        
        for serviceType in AIServiceType.allCases {
            if let manager = serviceManagers[serviceType] {
                if await manager.isInstalled {
                    available.append(serviceType)
                }
                
                if await manager.isRunning {
                    running.append(serviceType)
                }
            }
        }
        
        availableServices = available
        runningServices = running
    }
    
    func queryService(_ serviceType: AIServiceType, query: String) async throws -> String {
        guard let manager = serviceManagers[serviceType] else {
            throw AIServiceError.notInstalled
        }
        
        if !(await manager.isRunning) {
            try await manager.launch()
            // Wait a moment for the app to fully load
            try await Task.sleep(nanoseconds: 2_000_000_000)
        }
        
        return try await manager.sendQuery(query)
    }
    
    func queryAllServices(_ query: String) async -> [AIServiceType: Result<String, Error>] {
        var results: [AIServiceType: Result<String, Error>] = [:]
        
        await withTaskGroup(of: (AIServiceType, Result<String, Error>).self) { group in
            for serviceType in availableServices {
                group.addTask {
                    do {
                        let response = try await self.queryService(serviceType, query: query)
                        return (serviceType, .success(response))
                    } catch {
                        return (serviceType, .failure(error))
                    }
                }
            }
            
            for await (serviceType, result) in group {
                results[serviceType] = result
            }
        }
        
        return results
    }
    
    func queryServicesWithPriority(_ query: String, primaryServices: [AIServiceType] = [.claude], fallbackServices: [AIServiceType] = [.perplexity, .chatgpt]) async -> AIServiceResult {
        // Try primary services first in parallel
        let primaryResults = await querySpecificServices(query, services: primaryServices)
        
        // If we got a successful result from primary services, return it
        for (serviceType, result) in primaryResults {
            if case .success(let response) = result {
                return AIServiceResult(
                    primaryResponse: ServiceResponse(service: serviceType, content: response),
                    allResponses: primaryResults,
                    synthesizedResponse: response
                )
            }
        }
        
        // If primary services failed, try fallback services
        let fallbackResults = await querySpecificServices(query, services: fallbackServices)
        let allResults = primaryResults.merging(fallbackResults) { (_, new) in new }
        
        // Find the best fallback result
        var bestResponse: String = "All AI services failed to respond"
        var primaryService: AIServiceType = .claude
        
        for (serviceType, result) in fallbackResults {
            if case .success(let response) = result {
                bestResponse = response
                primaryService = serviceType
                break
            }
        }
        
        return AIServiceResult(
            primaryResponse: ServiceResponse(service: primaryService, content: bestResponse),
            allResponses: allResults,
            synthesizedResponse: bestResponse
        )
    }
    
    private func querySpecificServices(_ query: String, services: [AIServiceType]) async -> [AIServiceType: Result<String, Error>] {
        var results: [AIServiceType: Result<String, Error>] = [:]
        
        await withTaskGroup(of: (AIServiceType, Result<String, Error>).self) { group in
            for serviceType in services {
                if availableServices.contains(serviceType) {
                    group.addTask {
                        do {
                            let response = try await self.queryService(serviceType, query: query)
                            return (serviceType, .success(response))
                        } catch {
                            return (serviceType, .failure(error))
                        }
                    }
                }
            }
            
            for await (serviceType, result) in group {
                results[serviceType] = result
            }
        }
        
        return results
    }
    
    // MARK: - Debug and Status Methods
    
    func getAutomationStatus() async -> String {
        var status = "🤖 AI Service Automation Status (31first.md approach)\n"
        status += "====================================================\n\n"
        
        // Check UI automation capability
        let automator = AccessibilityAPIAutomator.shared
        let hasAccessibility = automator.checkAccessibilityPermissions()
        status += "31first.md UI Automation:\n"
        status += "• Accessibility Permissions: \(hasAccessibility ? "✅" : "❌")\n"
        status += "• AXManualAccessibility Support: ✅\n"
        status += "• Window Raise/Activate: ✅\n"
        status += "• WebArea Text Input Finding: ✅\n"
        status += "• Cursor Shape Verification: ✅\n\n"
        
        // Check service availability
        status += "Service Status:\n"
        for serviceType in AIServiceType.allCases {
            if let manager = serviceManagers[serviceType] {
                let isInstalled = await manager.isInstalled
                let isRunning = await manager.isRunning
                let electronSupport = (serviceType == .claude || serviceType == .chatgpt) ? "🔧" : "📱"
                status += "• \(serviceType.rawValue): \(isInstalled ? electronSupport : "❌") \(isRunning ? "🟢" : "⚪")\n"
            }
        }
        
        status += "\n🔧 = Electron app with AXManualAccessibility support\n"
        status += "📱 = Native/Web app with standard accessibility\n"
        
        return status
    }
}

struct ServiceResponse {
    let service: AIServiceType
    let content: String
    let timestamp: Date = Date()
}

struct AIServiceResult {
    let primaryResponse: ServiceResponse
    let allResponses: [AIServiceType: Result<String, Error>]
    let synthesizedResponse: String
}