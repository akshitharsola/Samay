import Foundation
import SwiftUI

@MainActor
class SystemIntegrationManager: ObservableObject {
    // Service instances
    let weatherService = WeatherService()
    let calendarService = CalendarService()
    let notificationService = NotificationService()
    let mailService = MailService()
    
    @Published var isInitialized = false
    @Published var initializationStatus: String = "Initializing system integrations..."
    
    init() {
        Task {
            await initializeServices()
        }
    }
    
    private func initializeServices() async {
        initializationStatus = "Setting up weather service..."
        try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        initializationStatus = "Setting up calendar service..."
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        initializationStatus = "Setting up notification service..."
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        initializationStatus = "Setting up mail service..."
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        initializationStatus = "System integrations ready!"
        isInitialized = true
    }
    
    // MARK: - Unified Query Interface
    
    func handleSystemQuery(_ query: String) async -> String {
        let lowercaseQuery = query.lowercased()
        
        // Weather queries
        if lowercaseQuery.contains("weather") || lowercaseQuery.contains("temperature") || lowercaseQuery.contains("forecast") {
            return await handleWeatherQuery(query)
        }
        
        // Calendar queries
        if lowercaseQuery.contains("calendar") || lowercaseQuery.contains("schedule") || lowercaseQuery.contains("event") || lowercaseQuery.contains("meeting") {
            return await handleCalendarQuery(query)
        }
        
        // Email queries
        if lowercaseQuery.contains("email") || lowercaseQuery.contains("mail") || lowercaseQuery.contains("inbox") {
            return await handleEmailQuery(query)
        }
        
        // Notification queries
        if lowercaseQuery.contains("notification") || lowercaseQuery.contains("reminder") || lowercaseQuery.contains("alert") {
            return await handleNotificationQuery(query)
        }
        
        return "I can help you with weather, calendar, email, and notifications. What would you like to know?"
    }
    
    // MARK: - Weather Query Handler
    
    private func handleWeatherQuery(_ query: String) async -> String {
        let lowercaseQuery = query.lowercased()
        
        do {
            if lowercaseQuery.contains("forecast") || lowercaseQuery.contains("next few days") {
                return try await weatherService.getWeatherForecast()
            } else if lowercaseQuery.contains("alert") || lowercaseQuery.contains("warning") {
                return try await weatherService.getWeatherAlerts()
            } else {
                return try await weatherService.getCurrentWeather()
            }
        } catch {
            return "Weather information unavailable: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Calendar Query Handler
    
    private func handleCalendarQuery(_ query: String) async -> String {
        let lowercaseQuery = query.lowercased()
        
        if lowercaseQuery.contains("today") || lowercaseQuery.contains("today's") {
            return await calendarService.getTodaysEvents()
        } else if lowercaseQuery.contains("next") || lowercaseQuery.contains("upcoming") {
            if lowercaseQuery.contains("event") {
                return await calendarService.getNextEvent()
            } else {
                return await calendarService.getUpcomingEvents()
            }
        } else if lowercaseQuery.contains("week") || lowercaseQuery.contains("7 days") {
            return await calendarService.getUpcomingEvents(days: 7)
        } else {
            return await calendarService.getTodaysEvents()
        }
    }
    
    // MARK: - Email Query Handler
    
    private func handleEmailQuery(_ query: String) async -> String {
        let lowercaseQuery = query.lowercased()
        
        if lowercaseQuery.contains("unread") {
            return await mailService.getUnreadEmails()
        } else if lowercaseQuery.contains("recent") {
            return await mailService.getRecentEmails()
        } else if lowercaseQuery.contains("count") || lowercaseQuery.contains("how many") {
            return await mailService.getUnreadEmailCount()
        } else if lowercaseQuery.contains("summary") {
            return await mailService.getEmailSummary()
        } else if lowercaseQuery.contains("search") {
            // Extract search term (this could be enhanced with better NLP)
            return "To search emails, please specify what you're looking for. For example: 'Search emails for meeting notes'"
        } else {
            return await mailService.getUnreadEmailCount()
        }
    }
    
    // MARK: - Notification Query Handler
    
    private func handleNotificationQuery(_ query: String) async -> String {
        let lowercaseQuery = query.lowercased()
        
        if lowercaseQuery.contains("pending") || lowercaseQuery.contains("scheduled") {
            return await notificationService.getPendingNotifications()
        } else if lowercaseQuery.contains("system") {
            return notificationService.getRecentSystemNotifications()
        } else {
            return await notificationService.getPendingNotifications()
        }
    }
    
    // MARK: - Action Methods
    
    func createReminder(title: String, date: Date) async -> String {
        notificationService.schedulNotification(
            title: "Reminder",
            body: title,
            date: date
        )
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateStyle = .medium
        dateFormatter.timeStyle = .short
        let dateString = dateFormatter.string(from: date)
        
        return "Reminder '\(title)' scheduled for \(dateString)."
    }
    
    func composeEmail(to recipient: String, subject: String, body: String) async -> String {
        return await mailService.composeEmail(to: recipient, subject: subject, body: body)
    }
    
    func sendNotification(title: String, body: String) {
        notificationService.sendNotification(title: title, body: body)
    }
    
    // MARK: - Status Methods
    
    func getSystemStatus() -> String {
        var status = "System Integration Status:\n\n"
        
        // Weather status
        if weatherService.isLocationAuthorized {
            status += "✅ Weather: Ready\n"
        } else {
            status += "⚠️ Weather: Location access needed\n"
        }
        
        // Calendar status
        if calendarService.isAuthorized {
            status += "✅ Calendar: Ready\n"
        } else {
            status += "⚠️ Calendar: Access needed\n"
        }
        
        // Notification status
        if notificationService.isAuthorized {
            status += "✅ Notifications: Ready\n"
        } else {
            status += "⚠️ Notifications: Permission needed\n"
        }
        
        // Mail status
        if mailService.hasAnyService {
            status += "✅ Mail: Ready (\(mailService.preferredService.displayName))\n"
        } else {
            status += "⚠️ Mail: No email service available\n"
        }
        
        return status
    }
    
    func getAvailableCapabilities() -> String {
        return """
        Available System Capabilities:
        
        🌤️ Weather:
        • Current weather conditions
        • Weather forecasts
        • Weather alerts and warnings
        
        📅 Calendar:
        • Today's schedule
        • Upcoming events
        • Next event details
        • Create new events
        
        📧 Email:
        • Unread email count
        • Recent emails
        • Email summaries
        • Compose emails
        
        🔔 Notifications:
        • Scheduled reminders
        • Pending notifications
        • Create new reminders
        
        Just ask me about any of these topics and I'll help you access the information!
        """
    }
}