import Foundation
import AppKit

@MainActor
class MailService: ObservableObject {
    private let appleScriptExecutor = AppleScriptExecutor.shared
    private let gmailService = GmailChromeService()
    
    @Published var isMailAppAvailable = false
    @Published var isGmailAvailable = false
    @Published var mailError: String?
    @Published var preferredService: EmailService = .appleMail
    
    enum EmailService: String, CaseIterable {
        case appleMail = "Apple Mail"
        case gmail = "Gmail (Chrome)"
        
        var displayName: String { rawValue }
    }
    
    init() {
        checkMailAppAvailability()
        checkGmailAvailability()
    }
    
    private func checkMailAppAvailability() {
        let mailAppURL = URL(fileURLWithPath: "/Applications/Mail.app")
        isMailAppAvailable = FileManager.default.fileExists(atPath: mailAppURL.path)
        
        if !isMailAppAvailable {
            mailError = "Mail.app not found. Please ensure Mail is installed."
        }
    }
    
    private func checkGmailAvailability() {
        isGmailAvailable = gmailService.isAvailable
        
        // Auto-select Gmail if Apple Mail is not available but Gmail is
        if !isMailAppAvailable && isGmailAvailable {
            preferredService = .gmail
        }
    }
    
    // MARK: - Mail Reading Methods
    
    func getUnreadEmailCount() async -> String {
        switch preferredService {
        case .appleMail:
            return await getAppleMailUnreadCount()
        case .gmail:
            return await gmailService.getUnreadEmailCount()
        }
    }
    
    private func getAppleMailUnreadCount() async -> String {
        guard isMailAppAvailable else {
            return "Mail.app not available."
        }
        
        let script = """
        tell application "Mail"
            set unreadCount to unread count of inbox
            return unreadCount as string
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            let count = result.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if let unreadCount = Int(count) {
                if unreadCount == 0 {
                    return "No unread emails."
                } else if unreadCount == 1 {
                    return "You have 1 unread email."
                } else {
                    return "You have \(unreadCount) unread emails."
                }
            } else {
                return "Could not determine unread email count."
            }
        } catch {
            return "Failed to check unread emails: \(error.localizedDescription)"
        }
    }
    
    func getRecentEmails(count: Int = 5) async -> String {
        switch preferredService {
        case .appleMail:
            return await getAppleMailRecentEmails(count: count)
        case .gmail:
            return await gmailService.getRecentEmails()
        }
    }
    
    private func getAppleMailRecentEmails(count: Int = 5) async -> String {
        guard isMailAppAvailable else {
            return "Apple Mail not available."
        }
        
        let script = """
        tell application "Mail"
            set recentMessages to messages 1 thru \(count) of inbox
            set emailList to ""
            
            repeat with msg in recentMessages
                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg
                set msgRead to read status of msg
                
                set readStatus to ""
                if msgRead is false then
                    set readStatus to "[UNREAD] "
                end if
                
                set emailList to emailList & readStatus & "From: " & msgSender & "\\n"
                set emailList to emailList & "Subject: " & msgSubject & "\\n"
                set emailList to emailList & "Date: " & (msgDate as string) & "\\n\\n"
            end repeat
            
            return emailList
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            
            if result.isEmpty {
                return "No recent emails found."
            } else {
                return "Recent Emails:\n\n\(result)"
            }
        } catch {
            return "Failed to get recent emails: \(error.localizedDescription)"
        }
    }
    
    func getUnreadEmails() async -> String {
        switch preferredService {
        case .appleMail:
            return await getAppleMailUnreadEmails()
        case .gmail:
            return await gmailService.getRecentEmails() // Gmail service handles unread in recent
        }
    }
    
    private func getAppleMailUnreadEmails() async -> String {
        guard isMailAppAvailable else {
            return "Apple Mail not available."
        }
        
        let script = """
        tell application "Mail"
            set unreadMessages to (every message of inbox whose read status is false)
            
            if (count of unreadMessages) is 0 then
                return "No unread emails."
            end if
            
            set emailList to "Unread Emails:\\n\\n"
            
            repeat with msg in unreadMessages
                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg
                
                set emailList to emailList & "From: " & msgSender & "\\n"
                set emailList to emailList & "Subject: " & msgSubject & "\\n"
                set emailList to emailList & "Date: " & (msgDate as string) & "\\n\\n"
            end repeat
            
            return emailList
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return result
        } catch {
            return "Failed to get unread emails: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Mail Composition Methods
    
    func composeEmail(to recipient: String, subject: String, body: String) async -> String {
        switch preferredService {
        case .appleMail:
            return await composeAppleMailEmail(to: recipient, subject: subject, body: body)
        case .gmail:
            return await gmailService.composeEmail(to: recipient, subject: subject, body: body)
        }
    }
    
    private func composeAppleMailEmail(to recipient: String, subject: String, body: String) async -> String {
        guard isMailAppAvailable else {
            return "Apple Mail not available."
        }
        
        let script = """
        tell application "Mail"
            set newMessage to make new outgoing message with properties {subject:"\(subject)", content:"\(body)"}
            tell newMessage
                make new to recipient at end of to recipients with properties {address:"\(recipient)"}
                activate
            end tell
        end tell
        """
        
        do {
            _ = try await appleScriptExecutor.executeScript(script)
            return "Email draft created and opened in Mail.app. You can review and send it."
        } catch {
            return "Failed to compose email: \(error.localizedDescription)"
        }
    }
    
    func sendEmail(to recipient: String, subject: String, body: String) async -> String {
        guard isMailAppAvailable else {
            return "Mail.app not available."
        }
        
        let script = """
        tell application "Mail"
            set newMessage to make new outgoing message with properties {subject:"\(subject)", content:"\(body)"}
            tell newMessage
                make new to recipient at end of to recipients with properties {address:"\(recipient)"}
                send
            end tell
        end tell
        """
        
        do {
            _ = try await appleScriptExecutor.executeScript(script)
            return "Email sent successfully to \(recipient)."
        } catch {
            return "Failed to send email: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Mail Management Methods
    
    func searchEmails(query: String) async -> String {
        guard isMailAppAvailable else {
            return "Mail.app not available."
        }
        
        let script = """
        tell application "Mail"
            set searchResults to (every message of inbox whose subject contains "\(query)" or content contains "\(query)")
            
            if (count of searchResults) is 0 then
                return "No emails found matching '\(query)'."
            end if
            
            set emailList to "Search Results for '\(query)':\\n\\n"
            
            repeat with msg in searchResults
                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg
                
                set emailList to emailList & "From: " & msgSender & "\\n"
                set emailList to emailList & "Subject: " & msgSubject & "\\n"
                set emailList to emailList & "Date: " & (msgDate as string) & "\\n\\n"
            end repeat
            
            return emailList
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return result
        } catch {
            return "Failed to search emails: \(error.localizedDescription)"
        }
    }
    
    func markAllAsRead() async -> String {
        guard isMailAppAvailable else {
            return "Mail.app not available."
        }
        
        let script = """
        tell application "Mail"
            set unreadMessages to (every message of inbox whose read status is false)
            set messageCount to count of unreadMessages
            
            if messageCount is 0 then
                return "No unread messages to mark as read."
            end if
            
            repeat with msg in unreadMessages
                set read status of msg to true
            end repeat
            
            return "Marked " & messageCount & " messages as read."
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return result
        } catch {
            return "Failed to mark emails as read: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Email Analysis Methods
    
    func getEmailSummary() async -> String {
        switch preferredService {
        case .appleMail:
            return await getAppleMailSummary()
        case .gmail:
            return await gmailService.getEmailSummary()
        }
    }
    
    private func getAppleMailSummary() async -> String {
        guard isMailAppAvailable else {
            return "Apple Mail not available."
        }
        
        let script = """
        tell application "Mail"
            set totalMessages to count of messages of inbox
            set unreadMessages to count of (every message of inbox whose read status is false)
            set todayMessages to count of (every message of inbox whose date received > (current date) - (1 * days))
            
            return "Total messages: " & totalMessages & "\\nUnread messages: " & unreadMessages & "\\nToday's messages: " & todayMessages
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return "Email Summary:\n\(result)"
        } catch {
            return "Failed to get email summary: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Service Management
    
    func switchToService(_ service: EmailService) {
        preferredService = service
    }
    
    func getAvailableServices() -> [EmailService] {
        var services: [EmailService] = []
        
        if isMailAppAvailable {
            services.append(.appleMail)
        }
        
        if isGmailAvailable {
            services.append(.gmail)
        }
        
        return services
    }
    
    func getServiceStatus() -> String {
        var status = "Email Service Status:\n\n"
        
        if isMailAppAvailable {
            status += "✅ Apple Mail: Available\n"
        } else {
            status += "❌ Apple Mail: Not available\n"
        }
        
        if isGmailAvailable {
            status += "✅ Gmail (Chrome): Available\n"
        } else {
            status += "❌ Gmail (Chrome): Not available\n"
        }
        
        status += "\nCurrent service: \(preferredService.displayName)"
        
        return status
    }
    
    var hasAnyService: Bool {
        return isMailAppAvailable || isGmailAvailable
    }
}