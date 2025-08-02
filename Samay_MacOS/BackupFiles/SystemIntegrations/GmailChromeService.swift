import Foundation
import AppKit

@MainActor
class GmailChromeService: ObservableObject {
    @Published var isAvailable = false
    @Published var isGmailLoggedIn = false
    @Published var lastError: String?
    
    private let appleScriptExecutor = AppleScriptExecutor.shared
    
    init() {
        checkChromeAvailability()
    }
    
    private func checkChromeAvailability() {
        let chromeAppPath = "/Applications/Google Chrome.app"
        isAvailable = FileManager.default.fileExists(atPath: chromeAppPath)
        
        if isAvailable {
            Task {
                await checkGmailLogin()
            }
        }
    }
    
    private func checkGmailLogin() async {
        let script = """
        tell application "Google Chrome"
            set gmail_logged_in to false
            repeat with w in every window
                repeat with t in every tab of w
                    if URL of t contains "mail.google.com" then
                        tell t to execute javascript "document.querySelector('[data-ogsr-up]') !== null"
                        set gmail_logged_in to true
                        exit repeat
                    end if
                end repeat
                if gmail_logged_in then exit repeat
            end repeat
            return gmail_logged_in
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            isGmailLoggedIn = result.contains("true")
        } catch {
            lastError = "Failed to check Gmail login status: \(error.localizedDescription)"
            isGmailLoggedIn = false
        }
    }
    
    func openGmail() async {
        let script = """
        tell application "Google Chrome"
            activate
            set gmail_tab_found to false
            
            -- Check if Gmail is already open in any tab
            repeat with w in every window
                repeat with t in every tab of w
                    if URL of t contains "mail.google.com" then
                        set active tab index of w to (index of t)
                        set index of w to 1
                        set gmail_tab_found to true
                        exit repeat
                    end if
                end repeat
                if gmail_tab_found then exit repeat
            end repeat
            
            -- If not found, open Gmail in a new tab
            if not gmail_tab_found then
                tell front window to make new tab with properties {URL:"https://mail.google.com"}
            end if
        end tell
        """
        
        do {
            _ = try await appleScriptExecutor.executeScript(script)
            await checkGmailLogin()
        } catch {
            lastError = "Failed to open Gmail: \(error.localizedDescription)"
        }
    }
    
    func getUnreadEmailCount() async -> String {
        guard isAvailable else {
            return "Google Chrome not available. Please install Chrome to use Gmail integration."
        }
        
        let script = """
        tell application "Google Chrome"
            set gmail_tab_found to false
            set unread_count to "0"
            
            repeat with w in every window
                repeat with t in every tab of w
                    if URL of t contains "mail.google.com" then
                        tell t to execute javascript "
                            var countElement = document.querySelector('a[href*=\"#inbox\"] .aim');
                            var count = countElement ? countElement.textContent.replace(/[()]/g, '') : '0';
                            count;
                        "
                        set unread_count to the result as string
                        set gmail_tab_found to true
                        exit repeat
                    end if
                end repeat
                if gmail_tab_found then exit repeat
            end repeat
            
            if not gmail_tab_found then
                return "Gmail not open in Chrome. Please open Gmail first."
            else
                return "You have " & unread_count & " unread emails."
            end if
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return result
        } catch {
            lastError = "Failed to get unread email count: \(error.localizedDescription)"
            return "Could not retrieve unread email count. Error: \(error.localizedDescription)"
        }
    }
    
    func getRecentEmails() async -> String {
        guard isAvailable else {
            return "Google Chrome not available. Please install Chrome to use Gmail integration."
        }
        
        let script = """
        tell application "Google Chrome"
            set gmail_tab_found to false
            set recent_emails to "No emails found"
            
            repeat with w in every window
                repeat with t in every tab of w
                    if URL of t contains "mail.google.com" then
                        tell t to execute javascript "
                            var emails = [];
                            var emailRows = document.querySelectorAll('tr[id]');
                            
                            for (var i = 0; i < Math.min(5, emailRows.length); i++) {
                                var row = emailRows[i];
                                var senderElement = row.querySelector('span[email]');
                                var subjectElement = row.querySelector('span[id] > span:not([class])');
                                var timeElement = row.querySelector('span[title]');
                                
                                if (senderElement && subjectElement) {
                                    var sender = senderElement.getAttribute('email') || senderElement.textContent;
                                    var subject = subjectElement.textContent || 'No subject';
                                    var time = timeElement ? timeElement.getAttribute('title') : 'Unknown time';
                                    
                                    emails.push('From: ' + sender + '\\\\nSubject: ' + subject + '\\\\nTime: ' + time);
                                }
                            }
                            
                            emails.length > 0 ? emails.join('\\\\n\\\\n') : 'No recent emails found';
                        "
                        set recent_emails to the result as string
                        set gmail_tab_found to true
                        exit repeat
                    end if
                end repeat
                if gmail_tab_found then exit repeat
            end repeat
            
            if not gmail_tab_found then
                return "Gmail not open in Chrome. Please open Gmail first."
            else
                return recent_emails
            end if
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return result.replacingOccurrences(of: "\\\\n", with: "\n")
        } catch {
            lastError = "Failed to get recent emails: \(error.localizedDescription)"
            return "Could not retrieve recent emails. Error: \(error.localizedDescription)"
        }
    }
    
    func composeEmail(to recipient: String, subject: String, body: String) async -> String {
        guard isAvailable else {
            return "Google Chrome not available. Please install Chrome to use Gmail integration."
        }
        
        await openGmail() // Ensure Gmail is open first
        
        let script = """
        tell application "Google Chrome"
            set gmail_tab_found to false
            
            repeat with w in every window
                repeat with t in every tab of w
                    if URL of t contains "mail.google.com" then
                        tell t to execute javascript "
                            // Click compose button
                            var composeButton = document.querySelector('div[gh=\"cm\"]');
                            if (composeButton) {
                                composeButton.click();
                                
                                // Wait a moment for compose window to appear
                                setTimeout(function() {
                                    // Fill recipient
                                    var toField = document.querySelector('textarea[name=\"to\"]');
                                    if (toField) {
                                        toField.value = '\(recipient)';
                                        toField.dispatchEvent(new Event('input', { bubbles: true }));
                                    }
                                    
                                    // Fill subject
                                    var subjectField = document.querySelector('input[name=\"subjectbox\"]');
                                    if (subjectField) {
                                        subjectField.value = '\(subject)';
                                        subjectField.dispatchEvent(new Event('input', { bubbles: true }));
                                    }
                                    
                                    // Fill body
                                    var bodyField = document.querySelector('div[contenteditable=\"true\"][aria-label*=\"Message\"]');
                                    if (bodyField) {
                                        bodyField.innerHTML = '\(body.replacingOccurrences(of: "'", with: "\\'"))';
                                        bodyField.dispatchEvent(new Event('input', { bubbles: true }));
                                    }
                                }, 1000);
                                
                                'compose_initiated';
                            } else {
                                'compose_button_not_found';
                            }
                        "
                        set gmail_tab_found to true
                        exit repeat
                    end if
                end repeat
                if gmail_tab_found then exit repeat
            end repeat
            
            if not gmail_tab_found then
                return "Gmail not open in Chrome. Please open Gmail first."
            else
                return "Email composition initiated. Please review and send from Gmail."
            end if
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            return result
        } catch {
            lastError = "Failed to compose email: \(error.localizedDescription)"
            return "Could not compose email. Error: \(error.localizedDescription)"
        }
    }
    
    func searchEmails(query: String) async -> String {
        guard isAvailable else {
            return "Google Chrome not available. Please install Chrome to use Gmail integration."
        }
        
        let script = """
        tell application "Google Chrome"
            set gmail_tab_found to false
            
            repeat with w in every window
                repeat with t in every tab of w
                    if URL of t contains "mail.google.com" then
                        tell t to execute javascript "
                            var searchBox = document.querySelector('input[aria-label=\"Search mail\"]');
                            if (searchBox) {
                                searchBox.value = '\(query)';
                                searchBox.dispatchEvent(new Event('input', { bubbles: true }));
                                
                                // Press Enter to search
                                var enterEvent = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
                                searchBox.dispatchEvent(enterEvent);
                                
                                'search_initiated';
                            } else {
                                'search_box_not_found';
                            }
                        "
                        set gmail_tab_found to true
                        exit repeat
                    end if
                end repeat
                if gmail_tab_found then exit repeat
            end repeat
            
            if not gmail_tab_found then
                return "Gmail not open in Chrome. Please open Gmail first."
            else
                return "Search initiated for: \(query). Results will appear in Gmail."
            end if
        end tell
        """
        
        do {
            let result = try await appleScriptExecutor.executeScript(script)
            await openGmail() // Bring Gmail to front
            return result
        } catch {
            lastError = "Failed to search emails: \(error.localizedDescription)"
            return "Could not search emails. Error: \(error.localizedDescription)"
        }
    }
    
    func getEmailSummary() async -> String {
        let unreadCount = await getUnreadEmailCount()
        let recentEmails = await getRecentEmails()
        
        return """
        Gmail Summary:
        
        \(unreadCount)
        
        Recent Emails:
        \(recentEmails)
        """
    }
}