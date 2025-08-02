import SwiftUI

struct AuthenticationView: View {
    @StateObject private var authManager = AuthenticationManager()
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                Image(systemName: "shield.checkered")
                    .foregroundColor(.blue)
                
                Text("Service Authentication")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Spacer()
                
                Button(action: { isExpanded.toggle() }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                }
            }
            
            if isExpanded {
                // Service status list
                ForEach(AIServiceType.allCases, id: \.self) { service in
                    ServiceAuthStatusView(
                        service: service,
                        state: authManager.authenticationStates[service] ?? .unknown,
                        onAuthenticate: {
                            Task {
                                await authManager.authenticateService(service)
                            }
                        }
                    )
                }
                
                Divider()
                
                // Actions
                HStack {
                    Button("Refresh All") {
                        Task {
                            await authManager.checkAllServices()
                        }
                    }
                    .font(.caption)
                    
                    Spacer()
                    
                    if let lastCheck = authManager.lastCheckTime {
                        Text("Last check: \(lastCheck, style: .time)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            } else {
                // Summary when collapsed
                let readyCount = authManager.getReadyServices().count
                let totalCount = AIServiceType.allCases.count
                
                HStack {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(readyCount > 0 ? Color.green : Color.orange)
                            .frame(width: 6, height: 6)
                        
                        Text("\(readyCount) of \(totalCount) services ready")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    if readyCount < totalCount {
                        Button("Setup") {
                            isExpanded = true
                        }
                        .font(.caption2)
                    }
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(8)
        .task {
            await authManager.checkAllServices()
        }
    }
}

// MARK: - Service Auth Status View
struct ServiceAuthStatusView: View {
    let service: AIServiceType
    let state: AuthenticationState
    let onAuthenticate: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            // Service icon and name
            HStack(spacing: 6) {
                Image(systemName: serviceIcon)
                    .font(.caption)
                    .foregroundColor(.primary)
                
                Text(service.displayName)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .frame(width: 80, alignment: .leading)
            
            // Status indicator
            HStack(spacing: 4) {
                Circle()
                    .fill(Color(state.color))
                    .frame(width: 6, height: 6)
                
                Text(state.displayText)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            .frame(width: 70, alignment: .leading)
            
            Spacer()
            
            // Action button
            if !state.canUseService {
                Button(actionText) {
                    onAuthenticate()
                }
                .font(.caption2)
                .disabled(state == .notInstalled)
            } else {
                Image(systemName: "checkmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(.green)
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(state.canUseService ? Color.green.opacity(0.1) : Color.clear)
        .cornerRadius(6)
    }
    
    private var serviceIcon: String {
        switch service {
        case .claude:
            return "brain.head.profile"
        case .perplexity:
            return "magnifyingglass"
        case .chatgpt:
            return "message.circle"
        case .gemini:
            return "sparkles"
        }
    }
    
    private var actionText: String {
        switch state {
        case .notInstalled:
            return "Install"
        case .appNotRunning:
            return "Launch"
        case .requiresSetup:
            return "Setup"
        case .authenticationFailed:
            return "Retry"
        default:
            return "Fix"
        }
    }
}

// MARK: - Authentication Setup Guide
struct AuthenticationSetupGuide: View {
    let service: AIServiceType
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Image(systemName: serviceIcon)
                    .font(.title2)
                    .foregroundColor(.blue)
                
                Text("\(service.displayName) Setup")
                    .font(.headline)
            }
            
            Divider()
            
            // Instructions
            VStack(alignment: .leading, spacing: 8) {
                ForEach(setupInstructions, id: \.self) { instruction in
                    HStack(alignment: .top, spacing: 8) {
                        Text("•")
                            .foregroundColor(.blue)
                        
                        Text(instruction)
                            .font(.body)
                    }
                }
            }
            
            // Action buttons
            HStack {
                if let downloadURL = downloadURL {
                    Button("Download \(service.displayName)") {
                        NSWorkspace.shared.open(downloadURL)
                    }
                    .buttonStyle(.borderedProminent)
                }
                
                Button("Open Instructions") {
                    if let instructionsURL = instructionsURL {
                        NSWorkspace.shared.open(instructionsURL)
                    }
                }
                .buttonStyle(.bordered)
            }
            .padding(.top)
        }
        .padding()
        .frame(width: 400)
    }
    
    private var serviceIcon: String {
        switch service {
        case .claude:
            return "brain.head.profile"
        case .perplexity:
            return "magnifyingglass"
        case .chatgpt:
            return "message.circle"
        case .gemini:
            return "sparkles"
        }
    }
    
    private var setupInstructions: [String] {
        switch service {
        case .claude:
            return [
                "Download Claude for macOS from the official website",
                "Install and launch the application",
                "Sign in with your Anthropic account",
                "Grant accessibility permissions when prompted"
            ]
        case .perplexity:
            return [
                "Download Perplexity from the Mac App Store",
                "Launch the application",
                "Sign in with your Perplexity account (optional but recommended)",
                "The app should be ready to use"
            ]
        case .chatgpt:
            return [
                "Download ChatGPT Desktop from OpenAI's website",
                "Install and launch the application",
                "Sign in with your OpenAI account",
                "Ensure you have an active subscription if needed"
            ]
        case .gemini:
            return [
                "Open Safari browser",
                "Navigate to gemini.google.com/app",
                "Sign in with your Google account",
                "Bookmark the page for easy access"
            ]
        }
    }
    
    private var downloadURL: URL? {
        switch service {
        case .claude:
            return URL(string: "https://claude.ai/download")
        case .perplexity:
            return URL(string: "macappstore://apps.apple.com/app/perplexity-ask-anything/id6714467650")
        case .chatgpt:
            return URL(string: "https://openai.com/chatgpt/download/")
        case .gemini:
            return URL(string: "https://gemini.google.com/app")
        }
    }
    
    private var instructionsURL: URL? {
        switch service {
        case .claude:
            return URL(string: "https://support.anthropic.com/en/articles/10065433-installing-claude-desktop")
        case .perplexity:
            return URL(string: "https://www.perplexity.ai/hub/getting-started")
        case .chatgpt:
            return URL(string: "https://help.openai.com/en/articles/6654000-chatgpt-desktop-app")
        case .gemini:
            return URL(string: "https://support.google.com/gemini/answer/13275745")
        }
    }
}

#Preview {
    VStack {
        AuthenticationView()
        
        Divider()
        
        AuthenticationSetupGuide(service: .claude)
    }
    .padding()
}