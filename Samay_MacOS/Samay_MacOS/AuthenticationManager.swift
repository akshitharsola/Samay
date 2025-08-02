import Foundation
import AppKit

// MARK: - Authentication Manager
@MainActor
class AuthenticationManager: ObservableObject {
    
    // MARK: - Published Properties
    @Published var authenticationStates: [AIServiceType: AuthenticationState] = [:]
    @Published var lastCheckTime: Date?
    
    // MARK: - Private Properties
    private let userDefaults = UserDefaults.standard
    private let checkInterval: TimeInterval = 300 // 5 minutes
    
    // MARK: - Initialization
    init() {
        loadStoredAuthStates()
        startPeriodicCheck()
    }
    
    // MARK: - Authentication State Management
    func checkAuthenticationStatus(for service: AIServiceType) async -> AuthenticationState {
        let state = await performAuthCheck(for: service)
        authenticationStates[service] = state
        saveAuthState(for: service, state: state)
        return state
    }
    
    func checkAllServices() async {
        for service in AIServiceType.allCases {
            _ = await checkAuthenticationStatus(for: service)
        }
        lastCheckTime = Date()
    }
    
    private func performAuthCheck(for service: AIServiceType) async -> AuthenticationState {
        switch service {
        case .claude:
            return await checkClaudeAuth()
        case .perplexity:
            return await checkPerplexityAuth()
        case .chatgpt:
            return await checkChatGPTAuth()
        case .gemini:
            return await checkGeminiAuth()
        }
    }
    
    // MARK: - Service-Specific Authentication Checks
    private func checkClaudeAuth() async -> AuthenticationState {
        // Check if Claude app is installed and running
        let workspace = NSWorkspace.shared
        let bundleId = "com.anthropic.claudefordesktop"
        
        guard workspace.urlForApplication(withBundleIdentifier: bundleId) != nil else {
            return .notInstalled
        }
        
        let runningApps = workspace.runningApplications
        let isRunning = runningApps.contains { $0.bundleIdentifier == bundleId }
        
        if !isRunning {
            return .appNotRunning
        }
        
        // Basic check - if app is running, assume authenticated for now
        // In a production version, you might want to check window content or use accessibility APIs
        return .authenticated
    }
    
    private func checkPerplexityAuth() async -> AuthenticationState {
        let workspace = NSWorkspace.shared
        let bundleId = "ai.perplexity.mac"
        
        guard workspace.urlForApplication(withBundleIdentifier: bundleId) != nil else {
            return .notInstalled
        }
        
        let runningApps = workspace.runningApplications
        let isRunning = runningApps.contains { $0.bundleIdentifier == bundleId }
        
        if !isRunning {
            return .appNotRunning
        }
        
        return .authenticated
    }
    
    private func checkChatGPTAuth() async -> AuthenticationState {
        let workspace = NSWorkspace.shared
        let bundleId = "com.openai.chat"
        
        guard workspace.urlForApplication(withBundleIdentifier: bundleId) != nil else {
            return .notInstalled
        }
        
        let runningApps = workspace.runningApplications
        let isRunning = runningApps.contains { $0.bundleIdentifier == bundleId }
        
        if !isRunning {
            return .appNotRunning
        }
        
        return .authenticated
    }
    
    private func checkGeminiAuth() async -> AuthenticationState {
        // Check if Safari is running and user can access Gemini
        let workspace = NSWorkspace.shared
        let bundleId = "com.apple.Safari"
        
        guard workspace.urlForApplication(withBundleIdentifier: bundleId) != nil else {
            return .notInstalled
        }
        
        let runningApps = workspace.runningApplications
        let isRunning = runningApps.contains { $0.bundleIdentifier == bundleId }
        
        if !isRunning {
            return .requiresSetup // Safari needs to be opened
        }
        
        // For Gemini, we assume it's accessible if Safari is running
        // In production, you might want to check if user is logged into Google
        return .authenticated
    }
    
    // MARK: - Authentication Actions
    func authenticateService(_ service: AIServiceType) async {
        switch service {
        case .claude:
            await launchApp(bundleId: "com.anthropic.claudefordesktop")
        case .perplexity:
            await launchApp(bundleId: "ai.perplexity.mac")
        case .chatgpt:
            await launchApp(bundleId: "com.openai.chat")
        case .gemini:
            await openGeminiInSafari()
        }
        
        // Recheck auth status after launching
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            Task {
                await self.checkAuthenticationStatus(for: service)
            }
        }
    }
    
    private func launchApp(bundleId: String) async {
        let workspace = NSWorkspace.shared
        
        if let appURL = workspace.urlForApplication(withBundleIdentifier: bundleId) {
            let configuration = NSWorkspace.OpenConfiguration()
            configuration.activates = true
            
            do {
                try await workspace.openApplication(at: appURL, configuration: configuration)
            } catch {
                print("Failed to launch app with bundle ID \(bundleId): \(error)")
            }
        }
    }
    
    private func openGeminiInSafari() async {
        if let url = URL(string: "https://gemini.google.com/app") {
            NSWorkspace.shared.open(url)
        }
    }
    
    // MARK: - Persistence
    private func saveAuthState(for service: AIServiceType, state: AuthenticationState) {
        let key = "AuthState_\(service.rawValue)"
        let data: [String: Any] = [
            "state": state.rawValue,
            "timestamp": Date().timeIntervalSince1970
        ]
        userDefaults.set(data, forKey: key)
    }
    
    private func loadStoredAuthStates() {
        for service in AIServiceType.allCases {
            let key = "AuthState_\(service.rawValue)"
            if let data = userDefaults.dictionary(forKey: key),
               let stateRaw = data["state"] as? String,
               let timestamp = data["timestamp"] as? TimeInterval,
               let state = AuthenticationState(rawValue: stateRaw) {
                
                // Only use cached state if it's less than 30 minutes old
                if Date().timeIntervalSince1970 - timestamp < 1800 {
                    authenticationStates[service] = state
                }
            }
        }
    }
    
    // MARK: - Periodic Checking
    private func startPeriodicCheck() {
        Timer.scheduledTimer(withTimeInterval: checkInterval, repeats: true) { _ in
            Task {
                await self.checkAllServices()
            }
        }
    }
}

// MARK: - Authentication State
enum AuthenticationState: String, CaseIterable {
    case notInstalled = "not_installed"
    case appNotRunning = "app_not_running"
    case requiresSetup = "requires_setup"
    case authenticated = "authenticated"
    case authenticationFailed = "authentication_failed"
    case unknown = "unknown"
    
    var displayText: String {
        switch self {
        case .notInstalled:
            return "Not Installed"
        case .appNotRunning:
            return "App Not Running"
        case .requiresSetup:
            return "Needs Setup"
        case .authenticated:
            return "Ready"
        case .authenticationFailed:
            return "Auth Failed"
        case .unknown:
            return "Unknown"
        }
    }
    
    var color: NSColor {
        switch self {
        case .authenticated:
            return .systemGreen
        case .notInstalled, .authenticationFailed:
            return .systemRed
        case .appNotRunning, .requiresSetup:
            return .systemOrange
        case .unknown:
            return .systemGray
        }
    }
    
    var canUseService: Bool {
        return self == .authenticated
    }
}

// MARK: - Authentication Helpers
extension AuthenticationManager {
    func getReadyServices() -> [AIServiceType] {
        return authenticationStates.compactMap { (service, state) in
            state.canUseService ? service : nil
        }
    }
    
    func getServicesThatNeedSetup() -> [AIServiceType] {
        return AIServiceType.allCases.filter { service in
            let state = authenticationStates[service] ?? .unknown
            return !state.canUseService && state != .notInstalled
        }
    }
    
    func getServicesNeedingInstallation() -> [AIServiceType] {
        return authenticationStates.compactMap { (service, state) in
            state == .notInstalled ? service : nil
        }
    }
}