//
//  MenuBarContentView.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//  Updated for Local LLM Integration - Phase 3
//

import SwiftUI
import SwiftData

struct MenuBarContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var items: [Item]
    @State private var showingLegacyInterface = false
    
    var body: some View {
        TabView {
            // Main conversation interface
            ConversationView()
                .tabItem {
                    Image(systemName: "message")
                    Text("Chat")
                }
            
            // Legacy interface for reference/settings
            LegacyView()
                .tabItem {
                    Image(systemName: "gearshape")
                    Text("Services")
                }
        }
        .frame(width: 400, height: 550)
    }
}

// MARK: - Legacy Interface (for service management and settings)
struct LegacyView: View {
    @StateObject private var orchestrator = AIServiceOrchestrator()
    @StateObject private var appDetector = AppDetectionService.shared
    @StateObject private var configuration = ServiceConfiguration()
    @State private var hasAccessibilityPermission = false
    @State private var hasAppleEventsPermission = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
            Text("Service Management")
                .font(.headline)
                .padding(.top)
            
            // Show available services
            if !orchestrator.availableServices.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Available AI Services:")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    ForEach(orchestrator.availableServices, id: \.self) { service in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(orchestrator.runningServices.contains(service) ? .green : .orange)
                                .frame(width: 8, height: 8)
                            
                            Text(service.displayName)
                                .font(.body)
                            
                            Spacer()
                            
                            Text(orchestrator.runningServices.contains(service) ? "Running" : "Available")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(8)
                    }
                }
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.title2)
                        .foregroundColor(.orange)
                    
                    Text("No AI Services Found")
                        .font(.headline)
                    
                    Text("Make sure Claude, Perplexity, ChatGPT, or Gemini are installed")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding()
            }
            
            Divider()
            
            // Permission Status
            VStack(alignment: .leading, spacing: 8) {
                Text("Permissions")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack(spacing: 8) {
                    Circle()
                        .fill(hasAccessibilityPermission ? .green : .red)
                        .frame(width: 8, height: 8)
                    
                    Text("Accessibility")
                        .font(.body)
                    
                    Spacer()
                    
                    if !hasAccessibilityPermission {
                        Button("Grant") {
                            AccessibilityAPIAutomator.shared.requestAccessibilityPermissions()
                        }
                        .font(.caption)
                    }
                }
                
                HStack(spacing: 8) {
                    Circle()
                        .fill(hasAppleEventsPermission ? .green : .red)
                        .frame(width: 8, height: 8)
                    
                    Text("Apple Events")
                        .font(.body)
                    
                    Spacer()
                    
                    if !hasAppleEventsPermission {
                        Button("Test") {
                            Task { @MainActor in
                                // Use Accessibility API test instead of Apple Events
                                let automator = AccessibilityAPIAutomator.shared
                                hasAppleEventsPermission = automator.checkAccessibilityPermissions()
                            }
                        }
                        .font(.caption)
                        .disabled(false)
                    }
                }
            }
            .padding(.horizontal)
            
            Divider()
            
            // Configuration options
            VStack(alignment: .leading, spacing: 12) {
                Text("Configuration")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Toggle("Enable Parallel Execution", isOn: $configuration.enableParallelExecution)
                Toggle("Synthesize Responses", isOn: $configuration.synthesizeResponses)
                
                HStack {
                    Text("Primary Service:")
                        .font(.body)
                    
                    Spacer()
                    
                    Picker("Primary Service", selection: $configuration.primaryService) {
                        ForEach(orchestrator.availableServices, id: \.self) { service in
                            Text(service.displayName).tag(service)
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                }
            }
            .padding(.horizontal)
            
            Spacer()
            
            Divider()
            
            // Footer actions
            HStack {
                Button("Refresh Services") {
                    Task {
                        await orchestrator.scanForServices()
                    }
                }
                .font(.caption)
                
                Spacer()
                
                Button("Quit Samay") {
                    NSApplication.shared.terminate(nil)
                }
                .font(.caption)
            }
            .padding(.horizontal)
            .padding(.bottom)
        }
        .task {
            await orchestrator.scanForServices()
            
            // Check permissions status (non-blocking)
            await MainActor.run {
                hasAccessibilityPermission = AccessibilityAPIAutomator.shared.checkAccessibilityPermissions()
            }
            
            // Don't check Apple Events permission on startup to avoid UI blocking
            // User can test it manually with the Test button
        }
        }
    }
}

#Preview {
    MenuBarContentView()
        .modelContainer(for: Item.self, inMemory: true)
}