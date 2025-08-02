import SwiftUI

struct ConversationView: View {
    @StateObject private var llmManager = LocalLLMManager()
    @StateObject private var orchestrator = AIServiceOrchestrator()
    @StateObject private var sessionManager = ChatSessionManager()
    @State private var inputText = ""
    @State private var isExpanded = false
    @State private var showingSettings = false
    @State private var showingChatSessions = false
    @FocusState private var isInputFocused: Bool
    
    // Computed property for current session messages
    private var currentSessionMessages: [ConversationMessage] {
        return sessionManager.currentSession?.messages ?? []
    }
    
    var body: some View {
        HStack(spacing: 0) {
            // Chat sessions sidebar (show/hide with toggle)
            if showingChatSessions {
                ChatSessionsView(sessionManager: sessionManager)
                Divider()
            }
            
            // Main chat view
            VStack(spacing: 0) {
                // Header with status and controls
                headerView
                
                Divider()
                
                // Conversation history - show current session messages
                if isExpanded || !currentSessionMessages.isEmpty {
                    conversationHistoryView
                        .frame(maxHeight: 400)
                    
                    Divider()
                }
                
                // User consent request
                if let consentRequest = llmManager.pendingUserConsent {
                    consentRequestView(consentRequest)
                    Divider()
                }
                
                // Input area
                inputAreaView
                
                // Connection status and authentication
                VStack(spacing: 8) {
                    if !llmManager.isConnected {
                        connectionStatusView
                    }
                    
                    // AI Service Authentication status
                    AuthenticationView()
                }
            }
            .frame(width: showingChatSessions ? 420 : 420, alignment: .top)
        }
        .background(Color(.windowBackgroundColor))
        .onAppear {
            isInputFocused = true
            syncCurrentSessionWithLLM()
        }
        .task {
            await orchestrator.scanForServices()
            await llmManager.checkOllamaConnection()
        }
        .onChange(of: sessionManager.currentSessionId) {
            syncCurrentSessionWithLLM()
        }
    }
    
    // MARK: - Header View
    private var headerView: some View {
        HStack {
            // Chat sessions toggle
            Button(action: { 
                withAnimation(.easeInOut(duration: 0.15)) {
                    showingChatSessions.toggle()
                }
            }) {
                Image(systemName: "sidebar.left")
                    .font(.caption)
                    .foregroundColor(showingChatSessions ? .accentColor : .secondary)
            }
            .help("Toggle Chat Sessions")
            
            // Status indicator
            HStack(spacing: 4) {
                Circle()
                    .fill(llmManager.isConnected ? Color.green : Color.red)
                    .frame(width: 6, height: 6)
                
                Text(llmManager.isConnected ? "Connected" : "Offline")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Current session title
            if let session = sessionManager.currentSession {
                Text(session.title)
                    .font(.caption)
                    .foregroundColor(.primary)
                    .lineLimit(1)
            }
            
            // Model selector
            if llmManager.isConnected {
                Text(llmManager.currentModel ?? "Mock Assistant")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            // Controls
            HStack(spacing: 8) {
                Button(action: { 
                    sessionManager.createNewSession()
                }) {
                    Image(systemName: "plus.message")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .help("New Chat")
                
                Button(action: { isExpanded.toggle() }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Button(action: { showingSettings = true }) {
                    Image(systemName: "gearshape")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
    }
    
    // MARK: - Conversation History View
    private var conversationHistoryView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(currentSessionMessages) { message in
                        ConversationMessageView(message: message)
                            .id(message.id)
                    }
                    
                    if llmManager.isProcessing {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text("Thinking...")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 16)
                        .id("thinking")
                    }
                }
                .padding(.vertical, 12)
                .onChange(of: currentSessionMessages.count) {
                    // Auto-scroll to latest message
                    if let lastMessage = currentSessionMessages.last {
                        withAnimation(.easeOut(duration: 0.15)) {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
                .onChange(of: llmManager.isProcessing) {
                    if llmManager.isProcessing {
                        withAnimation(.easeOut(duration: 0.15)) {
                            proxy.scrollTo("thinking", anchor: .bottom)
                        }
                    }
                }
            }
        }
        .background(Color(.controlBackgroundColor).opacity(0.3))
    }
    
    // MARK: - Input Area View
    private var inputAreaView: some View {
        VStack(spacing: 8) {
            HStack {
                TextField("Ask me anything...", text: $inputText, axis: .vertical)
                    .textFieldStyle(.plain)
                    .focused($isInputFocused)
                    .disabled(llmManager.isProcessing)
                    .onSubmit {
                        Task {
                            await sendMessage()
                        }
                    }
                
                Button(action: {
                    Task {
                        await sendMessage()
                    }
                }) {
                    Image(systemName: "paperplane.fill")
                        .foregroundColor(.accentColor)
                }
                .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || llmManager.isProcessing)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            
            // Quick actions
            if inputText.isEmpty && currentSessionMessages.isEmpty {
                quickActionsView
            }
        }
    }
    
    // MARK: - Quick Actions View
    private var quickActionsView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                QuickActionButton(title: "Research", icon: "magnifyingglass") {
                    inputText = "Help me research "
                    isInputFocused = true
                }
                
                QuickActionButton(title: "Explain", icon: "lightbulb") {
                    inputText = "Please explain "
                    isInputFocused = true
                }
                
                QuickActionButton(title: "Code", icon: "chevron.left.forwardslash.chevron.right") {
                    inputText = "Help me write code for "
                    isInputFocused = true
                }
                
                QuickActionButton(title: "Summarize", icon: "doc.text") {
                    inputText = "Please summarize "
                    isInputFocused = true
                }
            }
            .padding(.horizontal, 12)
        }
        .padding(.bottom, 8)
    }
    
    // MARK: - Consent Request View
    private func consentRequestView(_ request: UserConsentRequest) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "shield.checkered")
                    .foregroundColor(.blue)
                Text("Permission Required")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text(request.reason)
                    .font(.body)
                    .foregroundColor(.secondary)
                
                if !request.services.isEmpty {
                    Text("Services: \(request.services.joined(separator: ", "))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(6)
                }
            }
            
            HStack(spacing: 12) {
                Button("Allow") {
                    Task {
                        await llmManager.approveConsentRequest()
                    }
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                
                Button("Deny") {
                    Task {
                        await llmManager.denyConsentRequest()
                    }
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                
                Spacer()
                
                Text("Local processing only")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(12)
        .background(Color.blue.opacity(0.05))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.blue.opacity(0.2), lineWidth: 1)
        )
        .padding(.horizontal, 12)
    }
    
    // MARK: - Connection Status View
    private var connectionStatusView: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: "exclamationmark.triangle")
                    .foregroundColor(.orange)
                Text("Local LLM not connected")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Button("Install Ollama") {
                if let url = URL(string: "https://ollama.ai") {
                    NSWorkspace.shared.open(url)
                }
            }
            .font(.caption)
        }
        .padding(.horizontal, 12)
        .padding(.bottom, 8)
    }
    
    // MARK: - Session Management
    private func syncCurrentSessionWithLLM() {
        llmManager.conversationHistory = currentSessionMessages
    }
    
    // MARK: - Actions
    private func sendMessage() async {
        let userInput = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userInput.isEmpty else { return }
        
        inputText = ""
        
        // Create user message and add to session
        let userMessage = ConversationMessage(
            id: UUID(),
            role: .user,
            content: userInput,
            timestamp: Date()
        )
        
        sessionManager.addMessageToCurrentSession(userMessage)
        syncCurrentSessionWithLLM()
        
        // First, check if we need external AI services
        if let serviceQuery = await llmManager.analyzeQueryForExternalServices(userInput) {
            if serviceQuery.needsExternal && serviceQuery.confidence > 0.7 {
                // Query external services
                await queryExternalServicesAndSynthesize(userInput, services: serviceQuery.services)
                return
            }
        }
        
        // Use local LLM only
        let response = await llmManager.sendMessage(userInput)
        let assistantMessage = ConversationMessage(
            id: UUID(),
            role: .assistant,
            content: response,
            timestamp: Date()
        )
        sessionManager.addMessageToCurrentSession(assistantMessage)
        syncCurrentSessionWithLLM()
    }
    
    private func queryExternalServicesAndSynthesize(_ query: String, services: [String]) async {
        let thinkingMsg = ConversationMessage(
            id: UUID(),
            role: .assistant,
            content: "Let me consult some external AI services to give you the most comprehensive answer...",
            timestamp: Date()
        )
        sessionManager.addMessageToCurrentSession(thinkingMsg)
        syncCurrentSessionWithLLM()
        
        // Query selected external services in parallel
        var responses: [String: String] = [:]
        
        await withTaskGroup(of: (String, String?).self) { group in
            for serviceString in services {
                // Map service strings to AIServiceType
                let serviceType: AIServiceType?
                switch serviceString.lowercased() {
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
                
                if let service = serviceType, orchestrator.availableServices.contains(service) {
                    group.addTask {
                        do {
                            let response = try await orchestrator.queryService(service, query: query)
                            return (serviceString, response)
                        } catch {
                            return (serviceString, nil)
                        }
                    }
                }
            }
            
            for await (service, response) in group {
                if let response = response {
                    responses[service] = response
                }
            }
        }
        
        // Synthesize responses using local LLM
        if !responses.isEmpty {
            let synthesized = await llmManager.synthesizeExternalResponses(responses, originalQuery: query)
            
            // Remove the "thinking" message and add synthesized response
            if let session = sessionManager.currentSession,
               let index = session.messages.firstIndex(where: { $0.id == thinkingMsg.id }) {
                sessionManager.chatSessions[sessionManager.chatSessions.firstIndex(where: { $0.id == session.id })!].messages.remove(at: index)
            }
            
            let finalMsg = ConversationMessage(
                id: UUID(),
                role: .assistant,
                content: synthesized,
                timestamp: Date()
            )
            sessionManager.addMessageToCurrentSession(finalMsg)
            syncCurrentSessionWithLLM()
        } else {
            // Fall back to local LLM only
            let response = await llmManager.sendMessage(query)
            // Remove thinking message and add real response
            if let session = sessionManager.currentSession,
               let index = session.messages.firstIndex(where: { $0.id == thinkingMsg.id }) {
                sessionManager.chatSessions[sessionManager.chatSessions.firstIndex(where: { $0.id == session.id })!].messages.remove(at: index)
            }
            
            let finalMsg = ConversationMessage(
                id: UUID(),
                role: .assistant,
                content: response,
                timestamp: Date()
            )
            sessionManager.addMessageToCurrentSession(finalMsg)
            syncCurrentSessionWithLLM()
        }
    }
}

// MARK: - Conversation Message View
struct ConversationMessageView: View {
    let message: ConversationMessage
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Avatar
            Circle()
                .fill(message.role == .user ? Color.blue : Color.green)
                .frame(width: 28, height: 28)
                .overlay {
                    Image(systemName: message.role == .user ? "person.fill" : "brain.head.profile")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.white)
                }
            
            // Message content
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(message.role == .user ? "You" : "Assistant")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    Text(message.timestamp, style: .time)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
                
                Text(message.content)
                    .font(.system(size: 14, design: .default))
                    .foregroundColor(.primary)
                    .textSelection(.enabled)
                    .padding(.vertical, 10)
                    .padding(.horizontal, 12)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(message.role == .user ? 
                                  Color.blue.opacity(0.08) : 
                                  Color(.controlBackgroundColor))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.secondary.opacity(0.1), lineWidth: 1)
                            )
                    )
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 16)
    }
}

// MARK: - Quick Action Button
struct QuickActionButton: View {
    let title: String
    let icon: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.caption)
                Text(title)
                    .font(.caption)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color.secondary.opacity(0.1))
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview
#Preview {
    ConversationView()
}