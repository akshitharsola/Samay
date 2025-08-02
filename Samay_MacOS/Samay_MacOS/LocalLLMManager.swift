import Foundation
import Combine
import AppKit

// MARK: - Local LLM Manager
@MainActor
class LocalLLMManager: ObservableObject {
    
    // MARK: - Published Properties
    @Published var isConnected = false
    @Published var currentModel: String?
    @Published var conversationHistory: [ConversationMessage] = []
    @Published var isProcessing = false
    @Published var lastError: String?
    @Published var assistantCapabilities: [AssistantCapability] = []
    @Published var pendingUserConsent: UserConsentRequest?
    @Published var isAwaitingUserInput = false
    
    // MARK: - Private Properties
    private let ollamaBaseURL = "http://localhost:11434"
    private var urlSession = URLSession.shared
    private let defaultModel = "llama3.2:3b"
    
    // System integration manager - REMOVED for AI-focused version
    // private let systemIntegration = SystemIntegrationManager()
    
    // MARK: - Initialization
    init() {
        currentModel = defaultModel
        loadConversationHistory()
        
        // Check Ollama connection on initialization with proper main actor context
        Task { @MainActor in
            await checkOllamaConnection()
        }
        
        // Initialize assistant capabilities
        setupAssistantCapabilities()
    }
    
    // MARK: - Connection Management
    func checkOllamaConnection() async {
        print("🔍 Attempting to connect to Ollama at \(ollamaBaseURL)")
        
        guard let url = URL(string: "\(ollamaBaseURL)/api/tags") else {
            print("❌ Invalid Ollama URL")
            isConnected = false
            lastError = "Invalid Ollama URL"
            return
        }
        
        do {
            let (data, response) = try await urlSession.data(from: url)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("📡 HTTP Response Status: \(httpResponse.statusCode)")
                
                if httpResponse.statusCode == 200 {
                    // Parse available models
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let models = json["models"] as? [[String: Any]],
                       let firstModel = models.first,
                       let modelName = firstModel["name"] as? String {
                        
                        print("✅ Connected to Ollama with model: \(modelName)")
                        isConnected = true
                        currentModel = modelName
                        lastError = nil
                    } else {
                        print("✅ Connected to Ollama with fallback model: llama3.2:3b")
                        isConnected = true
                        currentModel = "llama3.2:3b" // Default fallback
                        lastError = nil
                    }
                } else {
                    print("❌ Ollama service not responding - Status: \(httpResponse.statusCode)")
                    isConnected = false
                    lastError = "Ollama service not responding"
                }
            }
        } catch {
            print("❌ Failed to connect to Ollama: \(error.localizedDescription)")
            isConnected = false
            lastError = "Failed to connect to Ollama: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Conversation Management
    func sendMessage(_ userMessage: String) async -> String {
        isProcessing = true
        
        // Handle debug commands
        if userMessage.lowercased().contains("debug ai services") || userMessage.lowercased().contains("test ai services") {
            isProcessing = false
            return await debugAIServices()
        }
        
        // Handle Apple Events permission trigger
        if userMessage.lowercased().contains("trigger apple events") || userMessage.lowercased().contains("request apple events permission") {
            isProcessing = false
            return await triggerAppleEventsPermission()
        }
        
        // Add user message to history
        let userMsg = ConversationMessage(
            id: UUID(),
            role: .user,
            content: userMessage,
            timestamp: Date()
        )
        conversationHistory.append(userMsg)
        
        var response: String
        
        if isConnected {
            // Use real Ollama API with assistant intelligence
            response = await processUserRequestWithAssistant(userMessage)
        } else {
            // Fallback to mock response
            response = "I'm currently offline. Ollama service is not available. Please ensure Ollama is running and try again."
        }
        
        // Add assistant response to history
        let assistantMsg = ConversationMessage(
            id: UUID(),
            role: .assistant,
            content: response,
            timestamp: Date()
        )
        conversationHistory.append(assistantMsg)
        
        // Save conversation history
        saveConversationHistory()
        
        isProcessing = false
        return response
    }
    
    private func queryOllama(_ message: String) async -> String {
        guard let url = URL(string: "\(ollamaBaseURL)/api/generate") else {
            return "Error: Invalid Ollama URL"
        }
        
        let requestBody: [String: Any] = [
            "model": currentModel ?? "phi3:mini",
            "prompt": message,
            "stream": false
        ]
        
        do {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
            
            let (data, response) = try await urlSession.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let responseText = json["response"] as? String {
                    return responseText
                } else {
                    return "Error: Invalid response from Ollama"
                }
            } else {
                return "Error: Ollama request failed"
            }
        } catch {
            return "Error: \(error.localizedDescription)"
        }
    }
    
    // MARK: - External AI Service Decision Making
    func analyzeQueryForExternalServices(_ query: String) async -> ExternalServiceQuery? {
        let lowercaseQuery = query.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Keywords that suggest need for external services (current info, web search, etc.)
        let externalKeywords = [
            "latest", "current", "news", "today", "recent", "2024", "2025",
            "stock price", "weather", "search", "find", "research",
            "what's happening", "breaking", "update", "trending"
        ]
        
        // Simple queries that can be handled locally
        let simplePatterns = [
            "hello", "hi", "what", "who", "how", "explain", "tell me",
            "your name", "model", "help", "thanks", "thank you"
        ]
        
        // Check if it's a simple query
        let isSimpleQuery = simplePatterns.contains { pattern in
            lowercaseQuery.contains(pattern)
        }
        
        // Check if it needs external services
        let needsExternal = externalKeywords.contains { keyword in
            lowercaseQuery.contains(keyword)
        }
        
        if isSimpleQuery && !needsExternal {
            // Handle locally for simple questions
            return ExternalServiceQuery(
                needsExternal: false,
                services: [],
                reason: "Simple query can be handled locally",
                confidence: 0.9
            )
        } else if needsExternal {
            // Use external services for current info/research
            return ExternalServiceQuery(
                needsExternal: true,
                services: ["perplexity", "claude"],
                reason: "Query requires current information or research",
                confidence: 0.8
            )
        } else {
            // Default to local for other queries
            return ExternalServiceQuery(
                needsExternal: false,
                services: [],
                reason: "Standard query handled locally",
                confidence: 0.7
            )
        }
    }
    
    func synthesizeExternalResponses(_ responses: [String: String], originalQuery: String) async -> String {
        let synthesisPrompt = """
        I consulted multiple AI services for the user's query: "\(originalQuery)"
        
        Here are their responses:
        \(responses.map { "\($0.key): \($0.value)" }.joined(separator: "\n\n"))
        
        Please synthesize these responses into a single, coherent, and helpful answer for the user.
        Evaluate the quality of each response, identify any inconsistencies, and create a comprehensive response.
        Remove any duplicate information and present the most valuable insights.
        """
        
        print("🧠 Synthesizing responses from \(responses.count) services...")
        return await queryOllama(synthesisPrompt)
    }
    
    // MARK: - Debug and Testing Methods
    
    func debugAIServices() async -> String {
        let orchestrator = AIServiceOrchestrator()
        await orchestrator.scanForServices()
        
        var debugInfo = "🔍 AI Services Debug Information:\n\n"
        
        // Check available services
        debugInfo += "Available Services: \(orchestrator.availableServices.map { $0.rawValue }.joined(separator: ", "))\n"
        debugInfo += "Running Services: \(orchestrator.runningServices.map { $0.rawValue }.joined(separator: ", "))\n\n"
        
        // Check accessibility permissions
        let automator = AccessibilityAPIAutomator.shared
        let hasAccessibility = automator.checkAccessibilityPermissions()
        debugInfo += "Accessibility Permissions: \(hasAccessibility ? "✅ Granted" : "❌ Denied")\n\n"
        
        // Check individual service detection
        debugInfo += "Individual Service Check:\n"
        for serviceType in AIServiceType.allCases {
            let detectionService = AppDetectionService.shared
            let isInstalled = await detectionService.isAppInstalled(serviceType.bundleIdentifier)
            let isRunning = await detectionService.isAppRunning(serviceType.bundleIdentifier)
            debugInfo += "• \(serviceType.rawValue): Installed=\(isInstalled ? "✅" : "❌"), Running=\(isRunning ? "✅" : "❌"), Bundle=\(serviceType.bundleIdentifier)\n"
        }
        debugInfo += "\n"
        
        // Check what apps are actually running
        debugInfo += "Currently Running Apps:\n"
        let runningApps = NSWorkspace.shared.runningApplications
        for app in runningApps {
            if let bundleId = app.bundleIdentifier, 
               let appName = app.localizedName,
               !bundleId.hasPrefix("com.apple.") && appName.count > 0 {
                debugInfo += "• \(appName): \(bundleId)\n"
            }
        }
        debugInfo += "\n"
        
        // Test a simple service query if available
        if let firstService = orchestrator.availableServices.first {
            debugInfo += "Testing \(firstService.rawValue)...\n"
            do {
                let testResponse = try await orchestrator.queryService(firstService, query: "Hello, this is a test. Please respond with 'Test successful'.")
                debugInfo += "✅ Test response: \(String(testResponse.prefix(100)))\n"
            } catch {
                debugInfo += "❌ Test failed: \(error.localizedDescription)\n"
                if let aiError = error as? AIServiceError {
                    switch aiError {
                    case .notInstalled:
                        debugInfo += "   Reason: App not installed\n"
                    case .failedToLaunch:
                        debugInfo += "   Reason: Failed to launch app\n"
                    case .automationFailed(let details):
                        if details.contains("AUTHORIZATION_REQUIRED") {
                            let instructions = details.replacingOccurrences(of: "AUTHORIZATION_REQUIRED: ", with: "")
                            debugInfo += "   Reason: 🔐 Permission Required\n"
                            debugInfo += "   📋 Instructions: \(instructions)\n"
                            debugInfo += "   💡 After granting permission, close and reopen this debug window to test again.\n"
                        } else {
                            debugInfo += "   Reason: Automation failed - \(details)\n"
                        }
                    case .responseParsingFailed:
                        debugInfo += "   Reason: Could not parse response\n"
                    case .timeout:
                        debugInfo += "   Reason: Operation timed out\n"
                    }
                }
            }
        }
        
        return debugInfo
    }
    
    func triggerAppleEventsPermission() async -> String {
        // First try the Accessibility API alternative
        let accessibilityAutomator = AccessibilityAPIAutomator.shared
        
        if !accessibilityAutomator.checkAccessibilityPermissions() {
            accessibilityAutomator.requestAccessibilityPermissions()
            return """
            🔄 Alternative Solution: Using Accessibility API instead of Apple Events
            
            ✅ Accessibility permission dialog should appear shortly.
            
            This approach works with development builds and doesn't require:
            • Apple Developer Program membership (₹9000/year)
            • Developer ID certificate
            • App notarization
            
            After granting Accessibility permission, try "debug ai services" again.
            
            Why this works: Accessibility API bypasses Apple Events TCC restrictions in Sequoia.
            """
        }
        
        // If accessibility is already granted, test it
        let testResult = await accessibilityAutomator.testAccessibilityAccess()
        return """
        ✅ Accessibility API Ready (Alternative to Apple Events)
        
        \(testResult)
        
        This solution bypasses the Apple Events TCC restriction in macOS Sequoia.
        No Developer ID certificate or notarization required!
        """
    }
    
    // MARK: - Conversation History Persistence
    private func saveConversationHistory() {
        if let encoded = try? JSONEncoder().encode(conversationHistory) {
            UserDefaults.standard.set(encoded, forKey: "ConversationHistory")
        }
    }
    
    private func loadConversationHistory() {
        if let data = UserDefaults.standard.data(forKey: "ConversationHistory"),
           let history = try? JSONDecoder().decode([ConversationMessage].self, from: data) {
            conversationHistory = history
        }
    }
    
    func clearConversationHistory() {
        conversationHistory.removeAll()
        saveConversationHistory()
    }
    
    // MARK: - Model Management
    func switchModel(to modelName: String) {
        currentModel = modelName
        UserDefaults.standard.set(modelName, forKey: "CurrentModel")
    }
    
    // MARK: - Assistant Intelligence Methods
    
    private func setupAssistantCapabilities() {
        assistantCapabilities = [
            AssistantCapability(
                name: "Email Management",
                description: "Check, read, and draft email responses",
                category: .communication,
                requiresLocalProcessing: false,
                requiresUserConsent: true
            ),
            AssistantCapability(
                name: "Document Analysis",
                description: "Analyze confidential documents locally",
                category: .research,
                requiresLocalProcessing: true,
                requiresUserConsent: false
            ),
            AssistantCapability(
                name: "Research Assistance",
                description: "Help with research using external AI services",
                category: .research,
                requiresLocalProcessing: false,
                requiresUserConsent: true
            ),
            AssistantCapability(
                name: "System Tasks",
                description: "Perform system-level operations and automation",
                category: .system,
                requiresLocalProcessing: true,
                requiresUserConsent: true
            )
        ]
    }
    
    private func processUserRequestWithAssistant(_ request: String) async -> String {
        // First check if this is a system integration request
        if isSystemIntegrationQuery(request) {
            return await handleSystemIntegrationRequest(request)
        }
        
        // Then do the standard LLM analysis for other requests
        let analysisPrompt = """
        As an intelligent personal assistant, analyze this user request and determine:
        1. What the user wants to accomplish
        2. Whether it requires confidential/local processing  
        3. Whether external AI services would be helpful
        4. What capabilities are needed
        5. Whether user consent is required
        
        User request: "\(request)"
        
        Respond in JSON format:
        {
            "intent": "description of what user wants",
            "requires_local": true/false,
            "needs_external_services": true/false,
            "suggested_services": ["service1", "service2"],
            "requires_consent": true/false,
            "confidence": 0.0-1.0,
            "reasoning": "explanation of analysis"
        }
        """
        
        let analysis = await queryOllama(analysisPrompt)
        
        // Parse the LLM analysis
        if let analysisData = parseAnalysisResponse(analysis) {
            return await handleAnalyzedRequest(request, analysis: analysisData)
        } else {
            // Fallback to direct processing
            return await queryOllama(request)
        }
    }
    
    private func parseAnalysisResponse(_ response: String) -> [String: Any]? {
        // Extract JSON from LLM response
        guard let jsonStart = response.range(of: "{"),
              let jsonEnd = response.range(of: "}", options: .backwards) else {
            return nil
        }
        
        let jsonString = String(response[jsonStart.lowerBound...jsonEnd.upperBound])
        
        do {
            if let data = jsonString.data(using: .utf8),
               let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                return json
            }
        } catch {
            print("Failed to parse LLM analysis: \(error)")
        }
        
        return nil
    }
    
    private func handleAnalyzedRequest(_ request: String, analysis: [String: Any]) async -> String {
        let requiresLocal = analysis["requires_local"] as? Bool ?? false
        let needsExternal = analysis["needs_external_services"] as? Bool ?? false
        let requiresConsent = analysis["requires_consent"] as? Bool ?? false
        let suggestedServices = analysis["suggested_services"] as? [String] ?? []
        let intent = analysis["intent"] as? String ?? "Process user request"
        
        // Handle confidential/local processing
        if requiresLocal && !needsExternal {
            return await processLocallyOnly(request, intent: intent)
        }
        
        // Handle requests requiring external services with user consent
        if needsExternal && requiresConsent {
            return await requestUserConsentAndProcess(request, services: suggestedServices, intent: intent)
        }
        
        // Handle external services without sensitive data
        if needsExternal && !requiresConsent {
            return await consultExternalServicesWithNaturalPrompts(request, services: suggestedServices)
        }
        
        // Default local processing
        return await queryOllama(request)
    }
    
    private func processLocallyOnly(_ request: String, intent: String) async -> String {
        // For confidential documents, research papers, etc.
        let localPrompt = """
        As a local AI assistant handling confidential information, please help with: \(intent)
        
        User request: "\(request)"
        
        Important: This information is confidential and should not be shared externally. 
        Provide a comprehensive response based on your knowledge without using external services.
        """
        
        return await queryOllama(localPrompt)
    }
    
    private func requestUserConsentAndProcess(_ request: String, services: [String], intent: String) async -> String {
        // Create consent request
        let consentRequest = UserConsentRequest(
            capability: intent,
            reason: "To provide the best response, I'd like to consult: \(services.joined(separator: ", "))",
            services: services,
            isConfidential: false,
            timestamp: Date()
        )
        
        // Show consent request to user
        await MainActor.run {
            pendingUserConsent = consentRequest
            isAwaitingUserInput = true
        }
        
        // For now, return a message indicating consent is needed
        return """
        I understand you want help with: \(intent)
        
        To give you the best response, I'd like to consult these AI services: \(services.joined(separator: ", "))
        
        Would you like me to proceed? I'll write natural prompts to these services and synthesize their responses for you.
        """
    }
    
    // MARK: - User Interaction Methods
    
    func approveConsentRequest() async {
        guard let consent = pendingUserConsent else { return }
        
        await MainActor.run {
            pendingUserConsent = nil
            isAwaitingUserInput = false
        }
        
        print("User approved consultation with: \(consent.services.joined(separator: ", "))")
    }
    
    func denyConsentRequest() async {
        guard let consent = pendingUserConsent else { return }
        
        await MainActor.run {
            pendingUserConsent = nil
            isAwaitingUserInput = false
        }
        
        let localResponse = await processLocallyOnly(consent.capability, intent: consent.capability)
        
        let message = ConversationMessage(
            id: UUID(),
            role: .assistant,
            content: "I'll help you with that using only my local knowledge:\n\n\(localResponse)",
            timestamp: Date()
        )
        
        await MainActor.run {
            conversationHistory.append(message)
        }
        
        saveConversationHistory()
    }
    
    private func consultExternalServicesWithNaturalPrompts(_ request: String, services: [String]) async -> String {
        // Create natural language prompts for each service
        var responses: [String: String] = [:]
        
        for service in services {
            let naturalPrompt = await createNaturalPromptForService(request, service: service)
            
            // Query the service (this would integrate with existing orchestration)
            if let response = await queryExternalService(service, prompt: naturalPrompt) {
                responses[service] = response
            }
        }
        
        // Let local LLM synthesize the responses
        if !responses.isEmpty {
            return await synthesizeResponsesIntelligently(request, responses: responses)
        }
        
        return await queryOllama(request)
    }
    
    private func createNaturalPromptForService(_ request: String, service: String) async -> String {
        let promptCreationRequest = """
        I need to ask \(service) about this user request in natural language (not API format):
        "\(request)"
        
        Create a natural prompt that \(service) would understand well, written as if a human user is asking.
        Make it clear, specific, and optimized for \(service)'s strengths.
        
        Respond with just the prompt, no explanation.
        """
        
        return await queryOllama(promptCreationRequest)
    }
    
    private func queryExternalService(_ service: String, prompt: String) async -> String? {
        // Map service string to AIServiceType and query the actual service
        let serviceType: AIServiceType?
        switch service.lowercased() {
        case "claude":
            serviceType = .claude
        case "perplexity":
            serviceType = .perplexity
        case "chatgpt":
            serviceType = .chatgpt
        case "gemini":
            serviceType = .gemini
        default:
            serviceType = nil
        }
        
        guard let type = serviceType else {
            print("⚠️ Unknown service: \(service)")
            return nil
        }
        
        // Use the AIServiceOrchestrator to query the actual service
        let orchestrator = AIServiceOrchestrator()
        await orchestrator.scanForServices()
        
        guard orchestrator.availableServices.contains(type) else {
            print("⚠️ Service \(service) not available")
            return nil
        }
        
        do {
            print("🤖 Querying \(service) with prompt: \(String(prompt.prefix(100)))...")
            let response = try await orchestrator.queryService(type, query: prompt)
            print("✅ Got response from \(service): \(String(response.prefix(100)))...")
            return response
        } catch {
            print("❌ Failed to query \(service): \(error.localizedDescription)")
            return nil
        }
    }
    
    private func synthesizeResponsesIntelligently(_ originalRequest: String, responses: [String: String]) async -> String {
        let synthesisPrompt = """
        I consulted multiple AI services for this user request: "\(originalRequest)"
        
        Here are their responses:
        \(responses.map { "\($0.key): \($0.value)" }.joined(separator: "\n\n"))
        
        Please synthesize these responses into a single, coherent, and helpful answer for the user.
        Evaluate the quality of each response, identify any inconsistencies, and create a comprehensive response.
        If any response seems inadequate, note what follow-up questions might improve it.
        """
        
        return await queryOllama(synthesisPrompt)
    }
    
    // MARK: - System Integration Methods
    
    private func isSystemIntegrationQuery(_ query: String) -> Bool {
        let lowercaseQuery = query.lowercased()
        
        let systemKeywords = [
            "weather", "temperature", "forecast", "rain", "snow", "sunny", "cloudy",
            "calendar", "schedule", "meeting", "event", "appointment", "today's schedule",
            "email", "mail", "inbox", "unread", "message", "compose", "send email",
            "notification", "reminder", "alert", "notify me", "remind me",
            "system status", "capabilities", "what can you do"
        ]
        
        return systemKeywords.contains { keyword in
            lowercaseQuery.contains(keyword)
        }
    }
    
    private func handleSystemIntegrationRequest(_ request: String) async -> String {
        let lowercaseRequest = request.lowercased()
        
        // Handle system status queries
        if lowercaseRequest.contains("system status") || lowercaseRequest.contains("status") {
            return "System integrations disabled in AI-focused mode"
        }
        
        // Handle capabilities queries
        if lowercaseRequest.contains("capabilities") || lowercaseRequest.contains("what can you do") {
            return "AI services available: Claude, Perplexity, ChatGPT, Gemini"
        }
        
        // Handle system integration queries
        let systemResponse = "System integrations disabled. Please use AI services for assistance."
        
        // Let the local LLM enhance the response with context
        let enhancementPrompt = """
        The user asked: "\(request)"
        
        I retrieved this system information:
        \(systemResponse)
        
        Please provide a natural, conversational response that includes this information but feels personal and helpful. 
        Add context, interpretation, or helpful suggestions where appropriate.
        """
        
        let enhancedResponse = await queryOllama(enhancementPrompt)
        
        // If enhancement fails, return the raw system response
        if enhancedResponse.contains("Error:") || enhancedResponse.isEmpty {
            return systemResponse
        }
        
        return enhancedResponse
    }
    
    // MARK: - System Integration Capabilities
    
    func getSystemIntegrationStatus() -> String {
        return "System integrations disabled in AI-focused mode"
    }
    
    func createSystemReminder(title: String, date: Date) async -> String {
        return "Reminder functionality disabled in AI-focused mode"
    }
    
    func composeSystemEmail(to recipient: String, subject: String, body: String) async -> String {
        return "Email functionality disabled in AI-focused mode"
    }
}

// MARK: - Data Models
struct ConversationMessage: Codable, Identifiable {
    let id: UUID
    let role: MessageRole
    let content: String
    let timestamp: Date
    
    enum MessageRole: String, Codable {
        case user = "user"
        case assistant = "assistant"
        case system = "system"
    }
}

struct ExternalServiceQuery: Codable {
    let needsExternal: Bool
    let services: [String]
    let reason: String
    let confidence: Double
}

// MARK: - Assistant Capabilities Framework
struct AssistantCapability: Codable, Identifiable {
    let id: UUID
    let name: String
    let description: String
    let category: CapabilityCategory
    let requiresLocalProcessing: Bool
    let requiresUserConsent: Bool
    
    init(name: String, description: String, category: CapabilityCategory, requiresLocalProcessing: Bool, requiresUserConsent: Bool) {
        self.id = UUID()
        self.name = name
        self.description = description
        self.category = category
        self.requiresLocalProcessing = requiresLocalProcessing
        self.requiresUserConsent = requiresUserConsent
    }
    
    enum CapabilityCategory: String, Codable, CaseIterable {
        case communication = "Communication"
        case research = "Research"
        case productivity = "Productivity"
        case system = "System"
        case creative = "Creative"
    }
}

struct UserConsentRequest: Identifiable {
    let id: UUID
    let capability: String
    let reason: String
    let services: [String]
    let isConfidential: Bool
    let timestamp: Date
    
    init(capability: String, reason: String, services: [String], isConfidential: Bool, timestamp: Date) {
        self.id = UUID()
        self.capability = capability
        self.reason = reason
        self.services = services
        self.isConfidential = isConfidential
        self.timestamp = timestamp
    }
}

struct AssistantTask: Codable, Identifiable {
    let id: UUID
    let type: TaskType
    let description: String
    let status: TaskStatus
    let result: String?
    let timestamp: Date
    
    init(type: TaskType, description: String, status: TaskStatus, result: String? = nil, timestamp: Date) {
        self.id = UUID()
        self.type = type
        self.description = description
        self.status = status
        self.result = result
        self.timestamp = timestamp
    }
    
    enum TaskType: String, Codable {
        case emailCheck = "email_check"
        case documentAnalysis = "document_analysis"  
        case researchQuery = "research_query"
        case systemTask = "system_task"
        case externalServiceQuery = "external_service_query"
    }
    
    enum TaskStatus: String, Codable {
        case pending = "pending"
        case awaitingConsent = "awaiting_consent"
        case processing = "processing"
        case completed = "completed"
        case failed = "failed"
    }
}