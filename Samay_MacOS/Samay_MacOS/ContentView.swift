//
//  ContentView.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var items: [Item]
    @StateObject private var orchestrator = AIServiceOrchestrator()
    @State private var debugOutput = ""
    @State private var testQuery = "Hello, this is a test message from Samay."
    @State private var selectedService: AIServiceType = .claude
    @State private var isLoading = false

    var body: some View {
        NavigationSplitView {
            List {
                // AI Services Section
                Section("🤖 AI Services") {
                    NavigationLink {
                        AIServiceDebugView()
                    } label: {
                        Label("Debug AI Services", systemImage: "wrench.and.screwdriver")
                    }
                    
                    NavigationLink {
                        AIServiceTestView()
                    } label: {
                        Label("Test AI Services", systemImage: "play.circle")
                    }
                    
                    NavigationLink {
                        AutomationInfoView()
                    } label: {
                        Label("Automation Info", systemImage: "info.circle")
                    }
                }
                
                // Original Items Section
                Section("📝 Items") {
                    ForEach(items) { item in
                        NavigationLink {
                            Text("Item at \(item.timestamp, format: Date.FormatStyle(date: .numeric, time: .standard))")
                        } label: {
                            Text(item.timestamp, format: Date.FormatStyle(date: .numeric, time: .standard))
                        }
                    }
                    .onDelete(perform: deleteItems)
                }
            }
            .navigationSplitViewColumnWidth(min: 180, ideal: 200)
            .toolbar {
                ToolbarItem {
                    Button(action: addItem) {
                        Label("Add Item", systemImage: "plus")
                    }
                }
            }
        } detail: {
            VStack {
                Text("🤖 Samay AI Service Manager")
                    .font(.largeTitle)
                    .padding()
                
                Text("Select an option from the sidebar to get started")
                    .foregroundColor(.secondary)
                
                Spacer()
            }
        }
        .task {
            await orchestrator.scanForServices()
        }
    }

    private func addItem() {
        withAnimation {
            let newItem = Item(timestamp: Date())
            modelContext.insert(newItem)
        }
    }

    private func deleteItems(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                modelContext.delete(items[index])
            }
        }
    }
}

// MARK: - AI Service Debug View

struct AIServiceDebugView: View {
    @StateObject private var orchestrator = AIServiceOrchestrator()
    @State private var debugOutput = ""
    @State private var isLoading = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("🔧 AI Service Debug")
                .font(.title)
                .padding(.bottom)
            
            HStack {
                Button("Refresh Status") {
                    Task {
                        await refreshStatus()
                    }
                }
                .disabled(isLoading)
                
                Button("Scan Services") {
                    Task {
                        await orchestrator.scanForServices()
                        await refreshStatus()
                    }
                }
                .disabled(isLoading)
                
                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }
            
            ScrollView {
                Text(debugOutput.isEmpty ? "Click 'Refresh Status' to see debug information" : debugOutput)
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(8)
            }
            
            Spacer()
        }
        .padding()
        .task {
            await refreshStatus()
        }
    }
    
    private func refreshStatus() async {
        isLoading = true
        debugOutput = await orchestrator.getAutomationStatus()
        isLoading = false
    }
}

// MARK: - AI Service Test View

struct AIServiceTestView: View {
    @StateObject private var orchestrator = AIServiceOrchestrator()
    @State private var testQuery = "Hello, this is a test message from Samay."
    @State private var selectedService: AIServiceType = .claude
    @State private var testResult = ""
    @State private var isLoading = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("🧪 AI Service Testing")
                .font(.title)
                .padding(.bottom)
            
            VStack(alignment: .leading, spacing: 10) {
                Text("Test Query:")
                    .font(.headline)
                
                TextEditor(text: $testQuery)
                    .frame(height: 100)
                    .border(Color.gray, width: 1)
            }
            
            HStack {
                Text("Service:")
                    .font(.headline)
                
                Picker("Service", selection: $selectedService) {
                    ForEach(AIServiceType.allCases, id: \.self) { service in
                        Text(service.rawValue).tag(service)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                
                Spacer()
                
                Button("Test Service") {
                    Task {
                        await testService()
                    }
                }
                .disabled(isLoading || testQuery.isEmpty)
                
                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }
            
            ScrollView {
                Text(testResult.isEmpty ? "Run a test to see results" : testResult)
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(8)
            }
            
            Spacer()
        }
        .padding()
        .task {
            await orchestrator.scanForServices()
        }
    }
    
    private func testService() async {
        isLoading = true
        testResult = "🔄 Testing \(selectedService.rawValue) with query: \"\(testQuery)\"\n\n"
        
        do {
            let response = try await orchestrator.queryService(selectedService, query: testQuery)
            testResult += "✅ Success!\n\n"
            testResult += "Response:\n"
            testResult += response
        } catch {
            testResult += "❌ Error: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
}

// MARK: - Automation Info View

struct AutomationInfoView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("🔧 31first.md Automation Approach")
                .font(.title)
                .padding(.bottom)
            
            Text("Samay uses the researched 31first.md approach for reliable AI service automation:")
                .foregroundColor(.secondary)
            
            VStack(alignment: .leading, spacing: 12) {
                AutomationFeatureRow(
                    icon: "gear.circle.fill",
                    title: "AXManualAccessibility",
                    description: "Enables Electron app accessibility tree exposure"
                )
                
                AutomationFeatureRow(
                    icon: "arrow.up.circle.fill", 
                    title: "Window Raise & Activate",
                    description: "Properly brings windows to front and focus"
                )
                
                AutomationFeatureRow(
                    icon: "magnifyingglass.circle.fill",
                    title: "WebArea Text Input Finding", 
                    description: "Locates content-editable areas in web-based apps"
                )
                
                AutomationFeatureRow(
                    icon: "hand.point.up.left.fill",
                    title: "AXPress Action Focus",
                    description: "Simulates clicks to focus input elements"
                )
                
                AutomationFeatureRow(
                    icon: "cursorarrow.click.badge.clock.fill",
                    title: "Cursor Shape Verification",
                    description: "I-beam cursor detection as fallback verification"
                )
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(12)
            
            Divider()
            
            Text("📋 Key Benefits")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 8) {
                BenefitRow(icon: "checkmark.circle.fill", text: "95%+ reliability for Electron apps like Claude Desktop")
                BenefitRow(icon: "checkmark.circle.fill", text: "Direct accessibility API usage (no shortcuts dependency)")
                BenefitRow(icon: "checkmark.circle.fill", text: "Robust fallback mechanisms with cursor detection")  
                BenefitRow(icon: "checkmark.circle.fill", text: "Works with content-editable web elements")
                BenefitRow(icon: "checkmark.circle.fill", text: "Researched and tested approach")
            }
            
            Divider()
            
            HStack {
                Button("Open 31first.md Research") {
                    let url = URL(fileURLWithPath: "/Users/akshitharsola/Documents/Samay/31first.md")
                    NSWorkspace.shared.open(url)
                }
                
                Button("Test AI Services") {
                    // Navigate to test view - handled by parent navigation
                }
                .disabled(true) // Placeholder - navigation handled elsewhere
            }
            .padding(.top)
            
            Spacer()
        }
        .padding()
    }
}

struct AutomationFeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .font(.title2)
                .frame(width: 24)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
    }
}

struct BenefitRow: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: icon)
                .foregroundColor(.green)
                .font(.caption)
            Text(text)
                .font(.caption)
            Spacer()
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: Item.self, inMemory: true)
}
