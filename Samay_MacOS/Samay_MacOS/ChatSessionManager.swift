import Foundation
import SwiftUI

struct ChatSession: Codable, Identifiable {
    let id: UUID
    var title: String
    var messages: [ConversationMessage]
    let createdAt: Date
    var lastMessageAt: Date
    
    init(title: String = "New Chat") {
        self.id = UUID()
        self.title = title
        self.messages = []
        self.createdAt = Date()
        self.lastMessageAt = Date()
    }
    
    mutating func addMessage(_ message: ConversationMessage) {
        messages.append(message)
        lastMessageAt = message.timestamp
        
        // Auto-generate title from first user message if title is default
        if title == "New Chat", message.role == .user, !message.content.isEmpty {
            let words = message.content.components(separatedBy: .whitespacesAndNewlines)
            let titleWords = Array(words.prefix(5))
            title = titleWords.joined(separator: " ")
            if title.count > 50 {
                title = String(title.prefix(50)) + "..."
            }
        }
    }
    
    var preview: String {
        if let lastMessage = messages.last {
            let preview = lastMessage.content.trimmingCharacters(in: .whitespacesAndNewlines)
            return preview.count > 100 ? String(preview.prefix(100)) + "..." : preview
        }
        return "No messages"
    }
    
    var messageCount: Int {
        return messages.count
    }
}

@MainActor
class ChatSessionManager: ObservableObject {
    @Published var chatSessions: [ChatSession] = []
    @Published var currentSessionId: UUID?
    
    private let userDefaults = UserDefaults.standard
    private let sessionsKey = "ChatSessions"
    private let currentSessionKey = "CurrentSessionId"
    
    init() {
        loadChatSessions()
    }
    
    var currentSession: ChatSession? {
        get {
            guard let id = currentSessionId else { return nil }
            return chatSessions.first { $0.id == id }
        }
    }
    
    func createNewSession() {
        let newSession = ChatSession()
        chatSessions.insert(newSession, at: 0) // Add to beginning for recent-first order
        currentSessionId = newSession.id
        saveChatSessions()
    }
    
    func selectSession(_ session: ChatSession) {
        currentSessionId = session.id
        userDefaults.set(session.id.uuidString, forKey: currentSessionKey)
    }
    
    func deleteSession(_ session: ChatSession) {
        chatSessions.removeAll { $0.id == session.id }
        
        // If we deleted the current session, select another one or create new
        if currentSessionId == session.id {
            if let firstSession = chatSessions.first {
                currentSessionId = firstSession.id
            } else {
                createNewSession()
            }
        }
        
        saveChatSessions()
    }
    
    func addMessageToCurrentSession(_ message: ConversationMessage) {
        guard let sessionIndex = chatSessions.firstIndex(where: { $0.id == currentSessionId }) else {
            // Create new session if none exists
            createNewSession()
            guard let newSessionIndex = chatSessions.firstIndex(where: { $0.id == currentSessionId }) else { return }
            chatSessions[newSessionIndex].addMessage(message)
            saveChatSessions()
            return
        }
        
        chatSessions[sessionIndex].addMessage(message)
        
        // Move session to top (most recent)
        let updatedSession = chatSessions[sessionIndex]
        chatSessions.remove(at: sessionIndex)
        chatSessions.insert(updatedSession, at: 0)
        
        saveChatSessions()
    }
    
    func updateSessionTitle(_ session: ChatSession, title: String) {
        if let index = chatSessions.firstIndex(where: { $0.id == session.id }) {
            chatSessions[index].title = title
            saveChatSessions()
        }
    }
    
    func clearCurrentSession() {
        guard let sessionIndex = chatSessions.firstIndex(where: { $0.id == currentSessionId }) else { return }
        chatSessions[sessionIndex].messages.removeAll()
        saveChatSessions()
    }
    
    private func loadChatSessions() {
        // Load sessions
        if let data = userDefaults.data(forKey: sessionsKey),
           let sessions = try? JSONDecoder().decode([ChatSession].self, from: data) {
            self.chatSessions = sessions
        }
        
        // Load current session ID
        if let sessionIdString = userDefaults.string(forKey: currentSessionKey),
           let sessionId = UUID(uuidString: sessionIdString),
           chatSessions.contains(where: { $0.id == sessionId }) {
            self.currentSessionId = sessionId
        } else if let firstSession = chatSessions.first {
            self.currentSessionId = firstSession.id
        } else {
            // Create initial session if none exist
            createNewSession()
        }
    }
    
    private func saveChatSessions() {
        if let encoded = try? JSONEncoder().encode(chatSessions) {
            userDefaults.set(encoded, forKey: sessionsKey)
        }
        
        if let currentId = currentSessionId {
            userDefaults.set(currentId.uuidString, forKey: currentSessionKey)
        }
    }
    
    func exportSession(_ session: ChatSession) -> String {
        var export = "# \(session.title)\n"
        export += "Created: \(session.createdAt.formatted(date: .abbreviated, time: .shortened))\n"
        export += "Messages: \(session.messageCount)\n\n"
        
        for message in session.messages {
            let role = message.role == .user ? "**You**" : "**Assistant**"
            let timestamp = message.timestamp.formatted(date: .omitted, time: .shortened)
            export += "\(role) (\(timestamp)):\n\(message.content)\n\n"
        }
        
        return export
    }
}