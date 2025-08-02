import Foundation
import UserNotifications
import AppKit

@MainActor
class NotificationService: NSObject, ObservableObject {
    @Published var isAuthorized = false
    @Published var authorizationError: String?
    
    private let notificationCenter = UNUserNotificationCenter.current()
    
    override init() {
        super.init()
        requestNotificationPermission()
    }
    
    private func requestNotificationPermission() {
        notificationCenter.requestAuthorization(options: [.alert, .badge, .sound]) { [weak self] granted, error in
            DispatchQueue.main.async {
                self?.handleAuthorizationResult(granted: granted, error: error)
            }
        }
    }
    
    private func handleAuthorizationResult(granted: Bool, error: Error?) {
        if granted {
            isAuthorized = true
            authorizationError = nil
        } else {
            authorizationError = error?.localizedDescription ?? "Notification access was denied."
        }
    }
    
    // MARK: - Notification Methods
    
    func sendNotification(title: String, body: String, identifier: String = UUID().uuidString) {
        guard isAuthorized else { return }
        
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: nil)
        
        notificationCenter.add(request) { error in
            if let error = error {
                print("Failed to send notification: \(error.localizedDescription)")
            }
        }
    }
    
    func schedulNotification(title: String, body: String, date: Date, identifier: String = UUID().uuidString) {
        guard isAuthorized else { return }
        
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        
        let calendar = Calendar.current
        let components = calendar.dateComponents([.year, .month, .day, .hour, .minute], from: date)
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)
        
        notificationCenter.add(request) { error in
            if let error = error {
                print("Failed to schedule notification: \(error.localizedDescription)")
            }
        }
    }
    
    func getPendingNotifications() async -> String {
        let pendingRequests = await notificationCenter.pendingNotificationRequests()
        
        if pendingRequests.isEmpty {
            return "No pending notifications."
        }
        
        var notificationsString = "Pending Notifications:\n\n"
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateStyle = .medium
        dateFormatter.timeStyle = .short
        
        for request in pendingRequests {
            notificationsString += "• \(request.content.title)"
            
            if !request.content.body.isEmpty {
                notificationsString += ": \(request.content.body)"
            }
            
            if let trigger = request.trigger as? UNCalendarNotificationTrigger,
               let nextTriggerDate = trigger.nextTriggerDate() {
                let dateString = dateFormatter.string(from: nextTriggerDate)
                notificationsString += " (scheduled for \(dateString))"
            }
            
            notificationsString += "\n"
        }
        
        return notificationsString
    }
    
    func cancelNotification(identifier: String) {
        notificationCenter.removePendingNotificationRequests(withIdentifiers: [identifier])
    }
    
    func cancelAllNotifications() {
        notificationCenter.removeAllPendingNotificationRequests()
    }
    
    // MARK: - System Notification Monitoring
    
    func getRecentSystemNotifications() -> String {
        // Note: macOS doesn't provide direct access to other apps' notifications
        // This is a placeholder for future implementation using Accessibility APIs
        // or notification center database access (requires special permissions)
        
        return """
        System notification monitoring requires additional permissions and implementation.
        
        To access other apps' notifications, the app would need:
        1. Accessibility API permissions
        2. Full Disk Access (for notification database)
        3. Custom implementation to monitor notification center
        
        This feature will be implemented in a future update with proper user consent.
        """
    }
    
    // MARK: - Helper Methods
    
    func createReminderNotification(for event: String, minutesBefore: Int = 15) {
        guard let eventDate = parseEventTime(event) else {
            sendNotification(title: "Reminder Setup Failed", body: "Could not parse event time: \(event)")
            return
        }
        
        let reminderDate = eventDate.addingTimeInterval(-TimeInterval(minutesBefore * 60))
        
        if reminderDate > Date() {
            schedulNotification(
                title: "Upcoming Event",
                body: "You have '\(event)' in \(minutesBefore) minutes",
                date: reminderDate
            )
        }
    }
    
    private func parseEventTime(_ event: String) -> Date? {
        // Simple event time parsing - this could be enhanced with NLP
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm"
        
        // This is a placeholder - real implementation would use more sophisticated parsing
        return nil
    }
}