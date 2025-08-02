//
//  AppDetectionService.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation
import AppKit

@MainActor
class AppDetectionService: ObservableObject {
    static let shared = AppDetectionService()
    
    @Published var detectedApps: [String: URL] = [:]
    @Published var runningApps: Set<String> = []
    
    private init() {
        setupNotifications()
        Task {
            await scanForApps()
            await updateRunningApps()
        }
    }
    
    private func setupNotifications() {
        // Monitor app launches and terminations
        NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didLaunchApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            Task { @MainActor in
                await self?.updateRunningApps()
            }
        }
        
        NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didTerminateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notification in
            Task { @MainActor in
                await self?.updateRunningApps()
            }
        }
    }
    
    func scanForApps() async {
        var apps: [String: URL] = [:]
        
        // Check for each AI service
        for serviceType in AIServiceType.allCases {
            if let appURL = NSWorkspace.shared.urlForApplication(withBundleIdentifier: serviceType.bundleIdentifier) {
                apps[serviceType.bundleIdentifier] = appURL
            }
        }
        
        detectedApps = apps
    }
    
    func updateRunningApps() async {
        let runningApplications = NSWorkspace.shared.runningApplications
        var running: Set<String> = []
        
        for app in runningApplications {
            if let bundleId = app.bundleIdentifier {
                running.insert(bundleId)
            }
        }
        
        runningApps = running
    }
    
    func isAppInstalled(_ bundleIdentifier: String) async -> Bool {
        if detectedApps[bundleIdentifier] != nil {
            return true
        }
        
        // Try to find the app if not already cached
        if let _ = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleIdentifier) {
            await scanForApps() // Refresh cache
            return true
        }
        
        return false
    }
    
    func isAppRunning(_ bundleIdentifier: String) async -> Bool {
        await updateRunningApps()
        return runningApps.contains(bundleIdentifier)
    }
    
    func launchApp(_ bundleIdentifier: String) async throws {
        guard let appURL = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleIdentifier) else {
            throw AIServiceError.notInstalled
        }
        
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.activates = true
        configuration.addsToRecentItems = false
        
        do {
            _ = try await NSWorkspace.shared.openApplication(at: appURL, configuration: configuration)
        } catch {
            throw AIServiceError.failedToLaunch
        }
    }
    
    func quitApp(_ bundleIdentifier: String) async throws {
        let runningApps = NSWorkspace.shared.runningApplications
        
        for app in runningApps {
            if app.bundleIdentifier == bundleIdentifier {
                if !app.terminate() {
                    // Force quit if normal termination fails
                    _ = app.forceTerminate()
                }
                return
            }
        }
    }
    
    func getAppInfo(_ bundleIdentifier: String) async -> AppInfo? {
        guard let appURL = detectedApps[bundleIdentifier] else {
            return nil
        }
        
        guard let bundle = Bundle(url: appURL) else {
            return nil
        }
        
        let name = bundle.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String
            ?? bundle.object(forInfoDictionaryKey: "CFBundleName") as? String
            ?? "Unknown"
        
        let version = bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "Unknown"
        
        let isRunning = await isAppRunning(bundleIdentifier)
        
        return AppInfo(
            bundleIdentifier: bundleIdentifier,
            name: name,
            version: version,
            url: appURL,
            isRunning: isRunning
        )
    }
    
    func bringAppToFront(_ bundleIdentifier: String) async throws {
        let runningApps = NSWorkspace.shared.runningApplications
        
        for app in runningApps {
            if app.bundleIdentifier == bundleIdentifier {
                if app.activate(options: [.activateAllWindows, .activateIgnoringOtherApps]) {
                    return
                } else {
                    throw AIServiceError.automationFailed("Could not bring app to front")
                }
            }
        }
        
        throw AIServiceError.automationFailed("App not running")
    }
}

struct AppInfo {
    let bundleIdentifier: String
    let name: String
    let version: String
    let url: URL
    let isRunning: Bool
}
