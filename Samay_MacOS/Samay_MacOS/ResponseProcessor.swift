//
//  ResponseProcessor.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation

struct ProcessedResponse: Codable, Identifiable {
    let id = UUID()
    let content: String
    let summary: String
    let keyPoints: [String]
    let confidence: Double
    let sourceService: String
    let timestamp: Date
    let rawResponse: String
    
    init(content: String, summary: String, keyPoints: [String], confidence: Double, sourceService: String, rawResponse: String) {
        self.content = content
        self.summary = summary
        self.keyPoints = keyPoints
        self.confidence = confidence
        self.sourceService = sourceService
        self.rawResponse = rawResponse
        self.timestamp = Date()
    }
}

struct JSONCodeBlock: Codable {
    let content: String
    let summary: String?
    let keyPoints: [String]?
    let confidence: Double?
    let metadata: [String: String]?
}

class ResponseProcessor {
    static let shared = ResponseProcessor()
    
    private init() {}
    
    func processResponse(_ rawResponse: String, from service: AIServiceType) async throws -> ProcessedResponse {
        // Extract JSON code blocks from the response
        let jsonBlocks = extractJSONCodeBlocks(from: rawResponse)
        
        var processedContent = rawResponse
        var summary = ""
        var keyPoints: [String] = []
        var confidence = 0.5
        
        // Process JSON blocks if found
        if let primaryBlock = jsonBlocks.first {
            do {
                let decodedBlock = try JSONDecoder().decode(JSONCodeBlock.self, from: primaryBlock.data(using: .utf8)!)
                
                processedContent = decodedBlock.content
                summary = decodedBlock.summary ?? generateSummary(from: processedContent)
                keyPoints = decodedBlock.keyPoints ?? extractKeyPoints(from: processedContent)
                confidence = decodedBlock.confidence ?? calculateConfidence(for: processedContent, from: service)
                
            } catch {
                // If JSON parsing fails, fall back to text processing
                summary = generateSummary(from: rawResponse)
                keyPoints = extractKeyPoints(from: rawResponse)
                confidence = calculateConfidence(for: rawResponse, from: service)
            }
        } else {
            // No JSON blocks found, process as plain text
            summary = generateSummary(from: rawResponse)
            keyPoints = extractKeyPoints(from: rawResponse)
            confidence = calculateConfidence(for: rawResponse, from: service)
        }
        
        return ProcessedResponse(
            content: processedContent,
            summary: summary,
            keyPoints: keyPoints,
            confidence: confidence,
            sourceService: service.displayName,
            rawResponse: rawResponse
        )
    }
    
    private func extractJSONCodeBlocks(from text: String) -> [String] {
        let pattern = #"```(?:json)?\s*(\{.*?\})\s*```"#
        
        do {
            let regex = try NSRegularExpression(pattern: pattern, options: [.dotMatchesLineSeparators])
            let range = NSRange(text.startIndex..<text.endIndex, in: text)
            let matches = regex.matches(in: text, options: [], range: range)
            
            return matches.compactMap { match in
                guard let jsonRange = Range(match.range(at: 1), in: text) else { return nil }
                return String(text[jsonRange])
            }
        } catch {
            print("Regex error: \(error)")
            return []
        }
    }
    
    private func generateSummary(from text: String, maxLength: Int = 200) -> String {
        let cleanText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        
        if cleanText.count <= maxLength {
            return cleanText
        }
        
        // Find the last sentence that fits within the limit
        let sentences = cleanText.components(separatedBy: ". ")
        var summary = ""
        
        for sentence in sentences {
            let testSummary = summary.isEmpty ? sentence : summary + ". " + sentence
            if testSummary.count <= maxLength {
                summary = testSummary
            } else {
                break
            }
        }
        
        if summary.isEmpty {
            // If no complete sentence fits, truncate at word boundary
            let words = cleanText.components(separatedBy: " ")
            var wordSummary = ""
            
            for word in words {
                let testSummary = wordSummary.isEmpty ? word : wordSummary + " " + word
                if testSummary.count <= maxLength - 3 {
                    wordSummary = testSummary
                } else {
                    break
                }
            }
            summary = wordSummary + "..."
        } else if !summary.hasSuffix(".") {
            summary += "..."
        }
        
        return summary
    }
    
    private func extractKeyPoints(from text: String, maxPoints: Int = 5) -> [String] {
        var keyPoints: [String] = []
        
        // Look for bullet points or numbered lists
        let bulletPattern = #"(?:^|\n)\s*[•\-\*\d+\.]\s*(.+)"#
        
        do {
            let regex = try NSRegularExpression(pattern: bulletPattern, options: [.anchorsMatchLines])
            let range = NSRange(text.startIndex..<text.endIndex, in: text)
            let matches = regex.matches(in: text, options: [], range: range)
            
            for match in matches.prefix(maxPoints) {
                if let pointRange = Range(match.range(at: 1), in: text) {
                    let point = String(text[pointRange]).trimmingCharacters(in: .whitespacesAndNewlines)
                    if !point.isEmpty && point.count <= 150 {
                        keyPoints.append(point)
                    }
                }
            }
        } catch {
            print("Regex error for key points: \(error)")
        }
        
        // If no bullet points found, extract sentences
        if keyPoints.isEmpty {
            let sentences = text.components(separatedBy: ". ")
            for sentence in sentences.prefix(maxPoints) {
                let cleanSentence = sentence.trimmingCharacters(in: .whitespacesAndNewlines)
                if cleanSentence.count > 20 && cleanSentence.count <= 150 {
                    keyPoints.append(cleanSentence)
                }
            }
        }
        
        return keyPoints
    }
    
    private func calculateConfidence(for content: String, from service: AIServiceType) -> Double {
        var confidence = 0.5
        
        // Base confidence varies by service
        switch service {
        case .claude:
            confidence = 0.8
        case .perplexity:
            confidence = 0.75
        case .chatgpt:
            confidence = 0.7
        case .gemini:
            confidence = 0.75
        }
        
        // Adjust based on content characteristics
        let wordCount = content.components(separatedBy: .whitespacesAndNewlines).count
        
        if wordCount > 50 {
            confidence += 0.1
        }
        
        if content.contains("I'm not sure") || content.contains("I don't know") {
            confidence -= 0.2
        }
        
        if content.contains("definitely") || content.contains("certainly") {
            confidence += 0.1
        }
        
        return max(0.0, min(1.0, confidence))
    }
    
    func synthesizeResponses(_ responses: [ProcessedResponse]) -> ProcessedResponse? {
        guard !responses.isEmpty else { return nil }
        
        if responses.count == 1 {
            return responses.first
        }
        
        // Combine content from multiple responses
        let combinedContent = responses.map { response in
            "**\(response.sourceService):** \(response.content)"
        }.joined(separator: "\n\n---\n\n")
        
        // Create a consensus summary
        let combinedSummary = "Consensus from \(responses.count) AI services: " + 
                            responses.map { $0.summary }.joined(separator: " | ")
        
        // Merge key points
        var allKeyPoints: [String] = []
        for response in responses {
            allKeyPoints.append(contentsOf: response.keyPoints)
        }
        
        // Remove duplicates and limit to top points
        let uniqueKeyPoints = Array(Set(allKeyPoints)).prefix(7)
        
        // Calculate average confidence
        let averageConfidence = responses.reduce(0.0) { $0 + $1.confidence } / Double(responses.count)
        
        return ProcessedResponse(
            content: combinedContent,
            summary: combinedSummary,
            keyPoints: Array(uniqueKeyPoints),
            confidence: averageConfidence,
            sourceService: "Consensus",
            rawResponse: responses.map { $0.rawResponse }.joined(separator: "\n\n===\n\n")
        )
    }
}