//
//  ServiceConfiguration.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation

@MainActor
class ServiceConfiguration: ObservableObject {
    
    @Published var primaryService: AIServiceType = .claude
    @Published var fallbackServices: [AIServiceType] = [.perplexity, .chatgpt, .gemini]
    @Published var enableParallelExecution: Bool = true
    @Published var synthesizeResponses: Bool = true
    @Published var maxResponseWaitTime: TimeInterval = 30.0
    @Published var autoRetryOnFailure: Bool = true
    @Published var maxRetryAttempts: Int = 2
    
    // Service-specific settings
    @Published var serviceSettings: [AIServiceType: ServiceSettings] = [:]
    
    // Response processing preferences
    @Published var preferredResponseLength: ResponseLength = .moderate
    @Published var enableSmartSummary: Bool = true
    @Published var confidenceThreshold: Double = 0.6
    
    private let userDefaults = UserDefaults.standard
    private let configKey = "SamayServiceConfiguration"
    
    init() {
        loadConfiguration()
        setupDefaultServiceSettings()
    }
    
    private func setupDefaultServiceSettings() {
        // Default settings for each service
        if serviceSettings[.claude] == nil {
            serviceSettings[.claude] = ServiceSettings(
                priority: 1,
                enabled: true,
                timeout: 30.0,
                retryAttempts: 2,
                customPromptPrefix: "",
                responseFormat: .markdown
            )
        }
        
        if serviceSettings[.perplexity] == nil {
            serviceSettings[.perplexity] = ServiceSettings(
                priority: 2,
                enabled: true,
                timeout: 25.0,
                retryAttempts: 1,
                customPromptPrefix: "",
                responseFormat: .plain
            )
        }
        
        if serviceSettings[.chatgpt] == nil {
            serviceSettings[.chatgpt] = ServiceSettings(
                priority: 3,
                enabled: true,
                timeout: 35.0,
                retryAttempts: 2,
                customPromptPrefix: "",
                responseFormat: .markdown
            )
        }
        
        if serviceSettings[.gemini] == nil {
            serviceSettings[.gemini] = ServiceSettings(
                priority: 4,
                enabled: true,
                timeout: 60.0,
                retryAttempts: 1,
                customPromptPrefix: "",
                responseFormat: .plain
            )
        }
    }
    
    func saveConfiguration() {
        let config = ConfigurationData(
            primaryService: primaryService,
            fallbackServices: fallbackServices,
            enableParallelExecution: enableParallelExecution,
            synthesizeResponses: synthesizeResponses,
            maxResponseWaitTime: maxResponseWaitTime,
            autoRetryOnFailure: autoRetryOnFailure,
            maxRetryAttempts: maxRetryAttempts,
            serviceSettings: serviceSettings,
            preferredResponseLength: preferredResponseLength,
            enableSmartSummary: enableSmartSummary,
            confidenceThreshold: confidenceThreshold
        )
        
        if let data = try? JSONEncoder().encode(config) {
            userDefaults.set(data, forKey: configKey)
        }
    }
    
    private func loadConfiguration() {
        guard let data = userDefaults.data(forKey: configKey),
              let config = try? JSONDecoder().decode(ConfigurationData.self, from: data) else {
            return
        }
        
        primaryService = config.primaryService
        fallbackServices = config.fallbackServices
        enableParallelExecution = config.enableParallelExecution
        synthesizeResponses = config.synthesizeResponses
        maxResponseWaitTime = config.maxResponseWaitTime
        autoRetryOnFailure = config.autoRetryOnFailure
        maxRetryAttempts = config.maxRetryAttempts
        serviceSettings = config.serviceSettings
        preferredResponseLength = config.preferredResponseLength
        enableSmartSummary = config.enableSmartSummary
        confidenceThreshold = config.confidenceThreshold
    }
    
    func getExecutionPlan(for query: String) -> ExecutionPlan {
        let enabledServices = AIServiceType.allCases.filter { serviceType in
            serviceSettings[serviceType]?.enabled ?? true
        }
        
        let sortedServices = enabledServices.sorted { service1, service2 in
            let priority1 = serviceSettings[service1]?.priority ?? 999
            let priority2 = serviceSettings[service2]?.priority ?? 999
            return priority1 < priority2
        }
        
        if enableParallelExecution {
            return ExecutionPlan(
                executionMode: .parallel,
                services: sortedServices,
                synthesizeResults: synthesizeResponses,
                fallbackStrategy: .nextAvailable
            )
        } else {
            return ExecutionPlan(
                executionMode: .sequential,
                services: [primaryService] + fallbackServices.filter { $0 != primaryService },
                synthesizeResults: false,
                fallbackStrategy: .stopOnFirstSuccess
            )
        }
    }
    
    func updateServicePriority(_ service: AIServiceType, priority: Int) {
        var settings = serviceSettings[service] ?? ServiceSettings.default
        settings.priority = priority
        serviceSettings[service] = settings
        saveConfiguration()
    }
    
    func toggleServiceEnabled(_ service: AIServiceType) {
        var settings = serviceSettings[service] ?? ServiceSettings.default
        settings.enabled.toggle()
        serviceSettings[service] = settings
        saveConfiguration()
    }
    
    func resetToDefaults() {
        primaryService = .claude
        fallbackServices = [.perplexity, .chatgpt, .gemini]
        enableParallelExecution = true
        synthesizeResponses = true
        maxResponseWaitTime = 30.0
        autoRetryOnFailure = true
        maxRetryAttempts = 2
        preferredResponseLength = .moderate
        enableSmartSummary = true
        confidenceThreshold = 0.6
        
        serviceSettings.removeAll()
        setupDefaultServiceSettings()
        saveConfiguration()
    }
}

struct ServiceSettings: Codable {
    var priority: Int
    var enabled: Bool
    var timeout: TimeInterval
    var retryAttempts: Int
    var customPromptPrefix: String
    var responseFormat: ResponseFormat
    
    static let `default` = ServiceSettings(
        priority: 999,
        enabled: true,
        timeout: 30.0,
        retryAttempts: 2,
        customPromptPrefix: "",
        responseFormat: .markdown
    )
}

enum ResponseFormat: String, Codable, CaseIterable {
    case plain = "Plain Text"
    case markdown = "Markdown"
    case structured = "Structured"
    
    var displayName: String {
        return self.rawValue
    }
}

enum ResponseLength: String, Codable, CaseIterable {
    case brief = "Brief"
    case moderate = "Moderate"
    case detailed = "Detailed"
    case comprehensive = "Comprehensive"
    
    var displayName: String {
        return self.rawValue
    }
    
    var targetWordCount: Int {
        switch self {
        case .brief: return 50
        case .moderate: return 150
        case .detailed: return 300
        case .comprehensive: return 500
        }
    }
}

struct ExecutionPlan {
    let executionMode: ExecutionMode
    let services: [AIServiceType]
    let synthesizeResults: Bool
    let fallbackStrategy: FallbackStrategy
}

enum ExecutionMode {
    case sequential
    case parallel
}

enum FallbackStrategy {
    case stopOnFirstSuccess
    case nextAvailable
    case tryAll
}

private struct ConfigurationData: Codable {
    let primaryService: AIServiceType
    let fallbackServices: [AIServiceType]
    let enableParallelExecution: Bool
    let synthesizeResponses: Bool
    let maxResponseWaitTime: TimeInterval
    let autoRetryOnFailure: Bool
    let maxRetryAttempts: Int
    let serviceSettings: [AIServiceType: ServiceSettings]
    let preferredResponseLength: ResponseLength
    let enableSmartSummary: Bool
    let confidenceThreshold: Double
}

// Make AIServiceType Codable
extension AIServiceType: Codable {}