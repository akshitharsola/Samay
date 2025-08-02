//
//  ResponseSynthesizer.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation

@MainActor
class ResponseSynthesizer: ObservableObject {
    
    func synthesizeResponses(_ responses: [AIServiceType: Result<String, Error>]) async -> SynthesizedResponse {
        let successfulResponses = extractSuccessfulResponses(responses)
        
        if successfulResponses.isEmpty {
            return SynthesizedResponse(
                synthesizedContent: "All AI services failed to provide a response.",
                confidence: 0.0,
                sources: [],
                analysis: ResponseAnalysis(
                    consensusPoints: [],
                    uniqueInsights: [],
                    conflictingViews: [],
                    qualityScore: 0.0
                )
            )
        }
        
        if successfulResponses.count == 1 {
            let (service, content) = successfulResponses.first!
            return SynthesizedResponse(
                synthesizedContent: content,
                confidence: 0.7, // Single source has moderate confidence
                sources: [service],
                analysis: analyzeSingleResponse(content, from: service)
            )
        }
        
        // Multiple responses - perform synthesis
        return await performMultiResponseSynthesis(successfulResponses)
    }
    
    private func extractSuccessfulResponses(_ responses: [AIServiceType: Result<String, Error>]) -> [(AIServiceType, String)] {
        return responses.compactMap { (service, result) in
            if case .success(let content) = result {
                return (service, content)
            }
            return nil
        }
    }
    
    private func analyzeSingleResponse(_ content: String, from service: AIServiceType) -> ResponseAnalysis {
        let keyPoints = extractKeyPoints(from: content)
        
        return ResponseAnalysis(
            consensusPoints: keyPoints.prefix(3).map { $0 },
            uniqueInsights: keyPoints.suffix(2).map { $0 },
            conflictingViews: [],
            qualityScore: calculateQualityScore(content, from: service)
        )
    }
    
    private func performMultiResponseSynthesis(_ responses: [(AIServiceType, String)]) async -> SynthesizedResponse {
        let allContent = responses.map { $0.1 }
        let services = responses.map { $0.0 }
        
        // Extract key themes from all responses
        let allKeyPoints = allContent.flatMap { extractKeyPoints(from: $0) }
        let consensusPoints = findConsensusPoints(allKeyPoints)
        let uniqueInsights = findUniqueInsights(responses)
        let conflictingViews = findConflictingViews(responses)
        
        // Create synthesized content
        let synthesizedContent = createSynthesizedContent(
            consensusPoints: consensusPoints,
            uniqueInsights: uniqueInsights,
            conflictingViews: conflictingViews,
            originalResponses: responses
        )
        
        // Calculate confidence based on consensus and quality
        let confidence = calculateSynthesisConfidence(
            consensusLevel: consensusPoints.count,
            totalServices: responses.count,
            qualityScores: responses.map { calculateQualityScore($0.1, from: $0.0) }
        )
        
        return SynthesizedResponse(
            synthesizedContent: synthesizedContent,
            confidence: confidence,
            sources: services,
            analysis: ResponseAnalysis(
                consensusPoints: consensusPoints,
                uniqueInsights: uniqueInsights,
                conflictingViews: conflictingViews,
                qualityScore: responses.map { calculateQualityScore($0.1, from: $0.0) }.average()
            )
        )
    }
    
    private func extractKeyPoints(from content: String) -> [String] {
        // Simple key point extraction based on sentence structure
        let sentences = content.components(separatedBy: .newlines)
            .flatMap { $0.components(separatedBy: ". ") }
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty && $0.count > 20 }
        
        // Filter for sentences that look like key points
        return sentences.filter { sentence in
            let lowercased = sentence.lowercased()
            return lowercased.contains("key") ||
                   lowercased.contains("important") ||
                   lowercased.contains("main") ||
                   lowercased.contains("primary") ||
                   sentence.hasPrefix("1.") ||
                   sentence.hasPrefix("2.") ||
                   sentence.hasPrefix("3.") ||
                   sentence.hasPrefix("-") ||
                   sentence.hasPrefix("•")
        }.prefix(5).map { String($0) }
    }
    
    private func findConsensusPoints(_ allKeyPoints: [String]) -> [String] {
        // Find points mentioned across multiple responses
        var pointCounts: [String: Int] = [:]
        
        for point in allKeyPoints {
            let normalized = normalizeText(point)
            pointCounts[normalized, default: 0] += 1
        }
        
        return pointCounts
            .filter { $0.value > 1 }
            .sorted { $0.value > $1.value }
            .prefix(3)
            .map { $0.key }
    }
    
    private func findUniqueInsights(_ responses: [(AIServiceType, String)]) -> [String] {
        // Find insights unique to each service
        var uniqueInsights: [String] = []
        
        for (service, content) in responses {
            let servicePoints = extractKeyPoints(from: content)
            let otherContent = responses.filter { $0.0 != service }.map { $0.1 }.joined(separator: " ")
            
            for point in servicePoints {
                if !otherContent.localizedCaseInsensitiveContains(normalizeText(point)) {
                    uniqueInsights.append("\(service.displayName): \(point)")
                }
            }
        }
        
        return Array(uniqueInsights.prefix(3))
    }
    
    private func findConflictingViews(_ responses: [(AIServiceType, String)]) -> [String] {
        // Simple conflict detection based on opposing keywords
        let conflictKeywords = [
            ("yes", "no"),
            ("true", "false"),
            ("recommend", "avoid"),
            ("should", "shouldn't"),
            ("good", "bad"),
            ("positive", "negative")
        ]
        
        var conflicts: [String] = []
        
        for (keyword1, keyword2) in conflictKeywords {
            let services1 = responses.filter { $0.1.localizedCaseInsensitiveContains(keyword1) }.map { $0.0 }
            let services2 = responses.filter { $0.1.localizedCaseInsensitiveContains(keyword2) }.map { $0.0 }
            
            if !services1.isEmpty && !services2.isEmpty {
                conflicts.append("Conflicting views on \(keyword1) vs \(keyword2): \(services1.map { $0.displayName }.joined(separator: ", ")) vs \(services2.map { $0.displayName }.joined(separator: ", "))")
            }
        }
        
        return Array(conflicts.prefix(2))
    }
    
    private func createSynthesizedContent(consensusPoints: [String], uniqueInsights: [String], conflictingViews: [String], originalResponses: [(AIServiceType, String)]) -> String {
        var content = "## AI Service Synthesis\n\n"
        
        if !consensusPoints.isEmpty {
            content += "### Consensus Points\n"
            for point in consensusPoints {
                content += "• \(point)\n"
            }
            content += "\n"
        }
        
        if !uniqueInsights.isEmpty {
            content += "### Unique Insights\n"
            for insight in uniqueInsights {
                content += "• \(insight)\n"
            }
            content += "\n"
        }
        
        if !conflictingViews.isEmpty {
            content += "### Areas of Disagreement\n"
            for conflict in conflictingViews {
                content += "• \(conflict)\n"
            }
            content += "\n"
        }
        
        content += "### Individual Service Responses\n"
        for (service, response) in originalResponses {
            content += "**\(service.displayName):** \(response.prefix(200))...\n\n"
        }
        
        return content
    }
    
    private func calculateQualityScore(_ content: String, from service: AIServiceType) -> Double {
        var score = 0.5 // Base score
        
        // Length factor
        let wordCount = content.components(separatedBy: .whitespacesAndNewlines).count
        if wordCount > 50 { score += 0.1 }
        if wordCount > 100 { score += 0.1 }
        
        // Structure factor
        if content.contains("```") { score += 0.1 } // Code blocks
        if content.contains("1.") || content.contains("•") { score += 0.1 } // Lists
        
        // Service-specific bias
        switch service {
        case .claude:
            score += 0.1 // Claude tends to be comprehensive
        case .perplexity:
            if content.localizedCaseInsensitiveContains("source") { score += 0.1 } // Perplexity provides sources
        case .chatgpt:
            if content.contains("\n\n") { score += 0.05 } // ChatGPT structures well
        case .gemini:
            if content.localizedCaseInsensitiveContains("google") { score += 0.05 } // Gemini has Google knowledge
        }
        
        return min(score, 1.0)
    }
    
    private func calculateSynthesisConfidence(consensusLevel: Int, totalServices: Int, qualityScores: [Double]) -> Double {
        let consensusRatio = Double(consensusLevel) / Double(totalServices)
        let averageQuality = qualityScores.average()
        let serviceCount = Double(totalServices)
        
        // Formula: consensus importance + quality + service diversity
        let confidence = (consensusRatio * 0.4) + (averageQuality * 0.4) + (min(serviceCount / 3.0, 1.0) * 0.2)
        
        return min(confidence, 1.0)
    }
    
    private func normalizeText(_ text: String) -> String {
        return text.lowercased()
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "  ", with: " ")
    }
}

struct SynthesizedResponse {
    let synthesizedContent: String
    let confidence: Double
    let sources: [AIServiceType]
    let analysis: ResponseAnalysis
    let timestamp: Date = Date()
}

struct ResponseAnalysis {
    let consensusPoints: [String]
    let uniqueInsights: [String]
    let conflictingViews: [String]
    let qualityScore: Double
}

extension Array where Element == Double {
    func average() -> Double {
        guard !isEmpty else { return 0.0 }
        return reduce(0, +) / Double(count)
    }
}