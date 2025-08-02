import Foundation
import EventKit

@MainActor
class CalendarService: ObservableObject {
    private let eventStore = EKEventStore()
    
    @Published var isAuthorized = false
    @Published var authorizationError: String?
    
    init() {
        requestCalendarAccess()
    }
    
    private func requestCalendarAccess() {
        switch EKEventStore.authorizationStatus(for: .event) {
        case .notDetermined:
            eventStore.requestAccess(to: .event) { [weak self] granted, error in
                DispatchQueue.main.async {
                    self?.handleAuthorizationResult(granted: granted, error: error)
                }
            }
        case .authorized:
            isAuthorized = true
        case .denied, .restricted:
            authorizationError = "Calendar access denied. Please enable calendar access in System Preferences."
        @unknown default:
            authorizationError = "Unknown calendar authorization status."
        }
    }
    
    private func handleAuthorizationResult(granted: Bool, error: Error?) {
        if granted {
            isAuthorized = true
            authorizationError = nil
        } else {
            authorizationError = error?.localizedDescription ?? "Calendar access was denied."
        }
    }
    
    // MARK: - Calendar Methods
    
    func getTodaysEvents() async -> String {
        guard isAuthorized else {
            return "Calendar access not authorized. Please enable calendar access in System Preferences."
        }
        
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let tomorrow = calendar.date(byAdding: .day, value: 1, to: today)!
        
        let predicate = eventStore.predicateForEvents(withStart: today, end: tomorrow, calendars: nil)
        let events = eventStore.events(matching: predicate)
        
        if events.isEmpty {
            return "No events scheduled for today."
        }
        
        var eventsString = "Today's Schedule:\n\n"
        
        let dateFormatter = DateFormatter()
        dateFormatter.timeStyle = .short
        
        for event in events.sorted(by: { $0.startDate < $1.startDate }) {
            let startTime = dateFormatter.string(from: event.startDate)
            let endTime = dateFormatter.string(from: event.endDate)
            
            eventsString += "• \(startTime) - \(endTime): \(event.title ?? "Untitled Event")"
            
            if let location = event.location, !location.isEmpty {
                eventsString += " (at \(location))"
            }
            
            eventsString += "\n"
        }
        
        return eventsString
    }
    
    func getUpcomingEvents(days: Int = 7) async -> String {
        guard isAuthorized else {
            return "Calendar access not authorized. Please enable calendar access in System Preferences."
        }
        
        let calendar = Calendar.current
        let startDate = Date()
        let endDate = calendar.date(byAdding: .day, value: days, to: startDate)!
        
        let predicate = eventStore.predicateForEvents(withStart: startDate, end: endDate, calendars: nil)
        let events = eventStore.events(matching: predicate)
        
        if events.isEmpty {
            return "No upcoming events in the next \(days) days."
        }
        
        var eventsString = "Upcoming Events (Next \(days) Days):\n\n"
        
        let dateFormatter = DateFormatter()
        let dayFormatter = DateFormatter()
        dayFormatter.dateFormat = "EEEE, MMM d"
        dateFormatter.timeStyle = .short
        
        let groupedEvents = Dictionary(grouping: events) { event in
            calendar.startOfDay(for: event.startDate)
        }
        
        let sortedDays = groupedEvents.keys.sorted()
        
        for day in sortedDays {
            let dayEvents = groupedEvents[day]!.sorted { $0.startDate < $1.startDate }
            let dayString = dayFormatter.string(from: day)
            
            eventsString += "\(dayString):\n"
            
            for event in dayEvents {
                let startTime = dateFormatter.string(from: event.startDate)
                let endTime = dateFormatter.string(from: event.endDate)
                
                eventsString += "  • \(startTime) - \(endTime): \(event.title ?? "Untitled Event")"
                
                if let location = event.location, !location.isEmpty {
                    eventsString += " (at \(location))"
                }
                
                eventsString += "\n"
            }
            
            eventsString += "\n"
        }
        
        return eventsString
    }
    
    func getNextEvent() async -> String {
        guard isAuthorized else {
            return "Calendar access not authorized. Please enable calendar access in System Preferences."
        }
        
        let calendar = Calendar.current
        let now = Date()
        let nextWeek = calendar.date(byAdding: .weekOfYear, value: 1, to: now)!
        
        let predicate = eventStore.predicateForEvents(withStart: now, end: nextWeek, calendars: nil)
        let events = eventStore.events(matching: predicate)
        
        guard let nextEvent = events.sorted(by: { $0.startDate < $1.startDate }).first else {
            return "No upcoming events found."
        }
        
        let dateFormatter = DateFormatter()
        let timeFormatter = DateFormatter()
        dateFormatter.dateFormat = "EEEE, MMM d"
        timeFormatter.timeStyle = .short
        
        let eventDate = dateFormatter.string(from: nextEvent.startDate)
        let startTime = timeFormatter.string(from: nextEvent.startDate)
        let endTime = timeFormatter.string(from: nextEvent.endDate)
        
        var eventString = "Next Event:\n"
        eventString += "• \(nextEvent.title ?? "Untitled Event")\n"
        eventString += "• \(eventDate) at \(startTime) - \(endTime)\n"
        
        if let location = nextEvent.location, !location.isEmpty {
            eventString += "• Location: \(location)\n"
        }
        
        let timeUntil = nextEvent.startDate.timeIntervalSince(now)
        if timeUntil > 0 {
            let hours = Int(timeUntil) / 3600
            let minutes = (Int(timeUntil) % 3600) / 60
            
            if hours > 0 {
                eventString += "• Starts in \(hours) hours and \(minutes) minutes"
            } else {
                eventString += "• Starts in \(minutes) minutes"
            }
        }
        
        return eventString
    }
    
    func createEvent(title: String, startDate: Date, endDate: Date, location: String? = nil, notes: String? = nil) async -> String {
        guard isAuthorized else {
            return "Calendar access not authorized. Cannot create events."
        }
        
        let event = EKEvent(eventStore: eventStore)
        event.title = title
        event.startDate = startDate
        event.endDate = endDate
        event.location = location
        event.notes = notes
        event.calendar = eventStore.defaultCalendarForNewEvents
        
        do {
            try eventStore.save(event, span: .thisEvent)
            return "Event '\(title)' created successfully."
        } catch {
            return "Failed to create event: \(error.localizedDescription)"
        }
    }
}