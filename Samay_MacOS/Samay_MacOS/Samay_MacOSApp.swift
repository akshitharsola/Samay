//
//  Samay_MacOSApp.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import SwiftUI
import SwiftData
import AppKit

// AppDelegate to handle Apple Events TCC properly
class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Delay Apple Events initialization to ensure TCC system is ready
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.initializeAppleEventsPermissions()
        }
    }
    
    private func initializeAppleEventsPermissions() {
        Task {
            do {
                // Trigger Apple Events permission request using NSAppleScript
                try await AppleScriptExecutor.shared.requestAppleEventsPermissionDialog()
            } catch {
                print("Failed to initialize Apple Events permissions: \(error)")
            }
        }
    }
}

@main
struct Samay_MacOSApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @State private var isMenuPresented = false
    
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            Item.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        MenuBarExtra("Samay AI", systemImage: "brain.head.profile") {
            MenuBarContentView()
                .modelContainer(sharedModelContainer)
        }
        .menuBarExtraStyle(.window)
    }
}
