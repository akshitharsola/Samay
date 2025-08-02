//
//  ResponseDetailView.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import SwiftUI

struct ResponseDetailView: View {
    let response: ProcessedResponse
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Header
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(response.sourceService)
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Spacer()
                            
                            HStack(spacing: 4) {
                                Text("Confidence:")
                                    .font(.caption)
                                Text("\(Int(response.confidence * 100))%")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                    .foregroundColor(confidenceColor)
                            }
                        }
                        
                        Text(response.timestamp.formatted(date: .abbreviated, time: .shortened))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Divider()
                    
                    // Summary
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Summary")
                            .font(.headline)
                        
                        Text(response.summary)
                            .padding()
                            .background(Color.secondary.opacity(0.1))
                            .cornerRadius(8)
                    }
                    
                    // Key Points
                    if !response.keyPoints.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Key Points")
                                .font(.headline)
                            
                            ForEach(Array(response.keyPoints.enumerated()), id: \.offset) { index, point in
                                HStack(alignment: .top, spacing: 8) {
                                    Text("\(index + 1).")
                                        .font(.caption)
                                        .fontWeight(.medium)
                                        .foregroundColor(.accentColor)
                                    
                                    Text(point)
                                        .font(.body)
                                }
                            }
                        }
                    }
                    
                    Divider()
                    
                    // Full Content
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Full Response")
                            .font(.headline)
                        
                        Text(response.content)
                            .font(.body)
                            .textSelection(.enabled)
                            .padding()
                            .background(Color.secondary.opacity(0.05))
                            .cornerRadius(8)
                    }
                    
                    // Actions
                    HStack {
                        Button("Copy to Clipboard") {
                            copyToClipboard()
                        }
                        
                        Spacer()
                        
                        Button("Export") {
                            exportResponse()
                        }
                    }
                    .padding(.top)
                }
                .padding()
            }
            .navigationTitle("AI Response")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 600, height: 500)
    }
    
    private var confidenceColor: Color {
        if response.confidence >= 0.8 {
            return .green
        } else if response.confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }
    
    private func copyToClipboard() {
        let pasteboard = NSPasteboard.general
        pasteboard.declareTypes([.string], owner: nil)
        pasteboard.setString(response.content, forType: .string)
    }
    
    private func exportResponse() {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [.plainText]
        savePanel.nameFieldStringValue = "Samay_Response_\(response.timestamp.formatted(date: .numeric, time: .omitted)).txt"
        
        savePanel.begin { result in
            if result == .OK, let url = savePanel.url {
                let exportContent = """
                Samay AI Response Export
                ========================
                
                Service: \(response.sourceService)
                Timestamp: \(response.timestamp.formatted(date: .complete, time: .complete))
                Confidence: \(Int(response.confidence * 100))%
                
                Summary:
                \(response.summary)
                
                Key Points:
                \(response.keyPoints.enumerated().map { "\($0.offset + 1). \($0.element)" }.joined(separator: "\n"))
                
                Full Response:
                \(response.content)
                
                ---
                Generated by Samay AI Assistant
                """
                
                do {
                    try exportContent.write(to: url, atomically: true, encoding: .utf8)
                } catch {
                    print("Export failed: \(error)")
                }
            }
        }
    }
}

#Preview {
    ResponseDetailView(
        response: ProcessedResponse(
            content: "This is a sample response content for preview purposes.",
            summary: "Sample response summary",
            keyPoints: ["First key point", "Second key point", "Third key point"],
            confidence: 0.85,
            sourceService: "Claude",
            rawResponse: "Raw response content"
        )
    )
}