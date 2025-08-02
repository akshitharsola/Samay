//
//  SynthesizedResponseView.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import SwiftUI

struct SynthesizedResponseView: View {
    let response: SynthesizedResponse
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Header
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("AI Service Synthesis")
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
                        
                        HStack {
                            Text("Sources: \(response.sources.map { $0.displayName }.joined(separator: ", "))")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            Spacer()
                            
                            Text(response.timestamp.formatted(date: .abbreviated, time: .shortened))
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Divider()
                    
                    // Analysis Summary
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Analysis Overview")
                            .font(.headline)
                        
                        if !response.analysis.consensusPoints.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Label("Consensus Points", systemImage: "checkmark.circle.fill")
                                    .font(.subheadline)
                                    .foregroundColor(.green)
                                
                                ForEach(Array(response.analysis.consensusPoints.enumerated()), id: \.offset) { index, point in
                                    HStack(alignment: .top, spacing: 8) {
                                        Text("•")
                                            .foregroundColor(.green)
                                        Text(point)
                                            .font(.body)
                                    }
                                }
                            }
                            .padding()
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(8)
                        }
                        
                        if !response.analysis.uniqueInsights.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Label("Unique Insights", systemImage: "lightbulb.fill")
                                    .font(.subheadline)
                                    .foregroundColor(.blue)
                                
                                ForEach(Array(response.analysis.uniqueInsights.enumerated()), id: \.offset) { index, insight in
                                    HStack(alignment: .top, spacing: 8) {
                                        Text("•")
                                            .foregroundColor(.blue)
                                        Text(insight)
                                            .font(.body)
                                    }
                                }
                            }
                            .padding()
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(8)
                        }
                        
                        if !response.analysis.conflictingViews.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Label("Conflicting Views", systemImage: "exclamationmark.triangle.fill")
                                    .font(.subheadline)
                                    .foregroundColor(.orange)
                                
                                ForEach(Array(response.analysis.conflictingViews.enumerated()), id: \.offset) { index, conflict in
                                    HStack(alignment: .top, spacing: 8) {
                                        Text("•")
                                            .foregroundColor(.orange)
                                        Text(conflict)
                                            .font(.body)
                                    }
                                }
                            }
                            .padding()
                            .background(Color.orange.opacity(0.1))
                            .cornerRadius(8)
                        }
                        
                        HStack {
                            Label("Quality Score", systemImage: "star.fill")
                                .font(.subheadline)
                            Text("\(Int(response.analysis.qualityScore * 100))%")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            Spacer()
                        }
                        .foregroundColor(.secondary)
                    }
                    
                    Divider()
                    
                    // Full Synthesized Content
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Complete Synthesis")
                            .font(.headline)
                        
                        Text(response.synthesizedContent)
                            .font(.body)
                            .textSelection(.enabled)
                            .padding()
                            .background(Color.secondary.opacity(0.05))
                            .cornerRadius(8)
                    }
                    
                    // Actions
                    HStack {
                        Button("Copy Synthesis") {
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
            .navigationTitle("Synthesized Response")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 700, height: 600)
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
        pasteboard.setString(response.synthesizedContent, forType: .string)
    }
    
    private func exportResponse() {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [.plainText]
        savePanel.nameFieldStringValue = "Samay_Synthesis_\(response.timestamp.formatted(date: .numeric, time: .omitted)).txt"
        
        savePanel.begin { result in
            if result == .OK, let url = savePanel.url {
                let exportContent = """
                Samay AI Synthesized Response Export
                ===================================
                
                Timestamp: \(response.timestamp.formatted(date: .complete, time: .complete))
                Sources: \(response.sources.map { $0.displayName }.joined(separator: ", "))
                Confidence: \(Int(response.confidence * 100))%
                Quality Score: \(Int(response.analysis.qualityScore * 100))%
                
                Consensus Points:
                \(response.analysis.consensusPoints.enumerated().map { "\($0.offset + 1). \($0.element)" }.joined(separator: "\n"))
                
                Unique Insights:
                \(response.analysis.uniqueInsights.enumerated().map { "\($0.offset + 1). \($0.element)" }.joined(separator: "\n"))
                
                Conflicting Views:
                \(response.analysis.conflictingViews.enumerated().map { "\($0.offset + 1). \($0.element)" }.joined(separator: "\n"))
                
                Complete Synthesis:
                \(response.synthesizedContent)
                
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
    SynthesizedResponseView(
        response: SynthesizedResponse(
            synthesizedContent: "This is a sample synthesized response combining insights from multiple AI services.",
            confidence: 0.85,
            sources: [.claude, .perplexity],
            analysis: ResponseAnalysis(
                consensusPoints: ["Both services agree on main concept", "Similar recommendations provided"],
                uniqueInsights: ["Claude: Detailed technical explanation", "Perplexity: Real-world examples"],
                conflictingViews: ["Different approaches to implementation"],
                qualityScore: 0.9
            )
        )
    )
}