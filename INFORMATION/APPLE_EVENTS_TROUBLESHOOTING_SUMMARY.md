# Apple Events Authorization Issue - Complete Summary

## Current Problem
Samay_MacOS (SwiftUI macOS app) cannot get Apple Events permission to control System Events, preventing automation of AI apps like Claude, ChatGPT, and Perplexity.

## Error Details
- **Error**: `-1743 "Not authorized to send Apple events to System Events"`
- **Current Status**: App never appears in System Preferences → Privacy & Security → Automation
- **Issue**: Permission dialog never appears, preventing user from granting access

## What We've Tried (All Failed)

### 1. Entitlements Configuration
- ✅ Added `com.apple.security.automation.apple-events` = true
- ✅ Added `com.apple.security.temporary-exception.apple-events` array with System Events
- ✅ Added proper `NSAppleEventsUsageDescription` in Info.plist
- ✅ Configured scripting-targets for Finder

### 2. Build Configurations Tested
- ❌ Debug build from Xcode
- ❌ Debug build launched from Terminal 
- ❌ Debug build with sandbox disabled
- ❌ Release build with proper signing
- ❌ Release build launched from Terminal

### 3. Permission Triggering Methods
- ❌ Direct AppleScript execution via OSAScript
- ❌ System Events initialization with launch/quit delay
- ❌ Manual TCC database manipulation attempts
- ❌ Standalone AppleScript (worked, but didn't help app)

### 4. Manual Permission Attempts
- ❌ System Preferences automation section shows no Samay_MacOS entry
- ❌ No + button to manually add applications
- ❌ tccutil reset commands (worked but permission not granted)

## Current Project Setup
- **Framework**: SwiftUI macOS app
- **Bundle ID**: com.akshitharsola.Samay-MacOS  
- **Xcode Version**: Latest
- **macOS Version**: Sequoia 15.x
- **App Sandbox**: Enabled (required for App Store)
- **Signing**: Development certificates

## Working Evidence
- ✅ Terminal has Apple Events permission (shown in System Preferences)
- ✅ Standalone AppleScript works when run via Terminal
- ✅ App successfully detects other apps and has Accessibility permissions
- ✅ Entitlements are correctly processed (visible in build logs)

## Key Observations
1. **Development vs Production Issue**: Development builds may be treated differently by TCC
2. **Sandbox Limitation**: Even with sandbox disabled, issue persists
3. **TCC Registration**: App never registers with TCC system to request permission
4. **Permission Dialog**: System never shows the "Allow?" dialog

## Technical Details
- **AppleScript Method**: Using OSAScript framework with proper initialization
- **Error Location**: `AppleScriptExecutor.swift:48` - runScript method
- **Command Working**: `osascript /path/to/script.scpt` (external)
- **Command Failing**: Internal OSAScript.executeAndReturnError()

## Next Steps Required
1. **Research alternative authorization methods**
2. **Investigate TCC database direct manipulation**
3. **Explore NSAppleScript vs OSAScript differences** 
4. **Consider App Store signing requirements**
5. **Look into macOS Sequoia-specific changes**

## Files Modified
- `Samay_MacOS.entitlements` - Complete Apple Events configuration
- `Info.plist` - Added usage description
- `AppleScriptExecutor.swift` - Permission trigger functions
- `LocalLLMManager.swift` - Command handlers

## Commands That Work
```bash
# External AppleScript execution (works)
osascript -e 'tell application "System Events" to get name of every process'

# TCC reset (works but doesn't solve issue)
tccutil reset AppleEvents com.akshitharsola.Samay-MacOS
```

## Commands That Don't Work
```swift
// Internal Swift execution (fails with -1743)
let script = OSAScript(source: scriptSource)
let result = script.executeAndReturnError(&errorInfo)
```

## Research Priority
**HIGH PRIORITY**: Find why macOS TCC system doesn't recognize the app as requesting Apple Events permission, preventing the authorization dialog from appearing.

## Detailed Context for Research
- **macOS Version**: Darwin 24.5.0 (macOS Sequoia 15.x)
- **Xcode Version**: Latest with arm64 Apple Silicon support
- **Target Architecture**: arm64-apple-macos14.0 minimum deployment
- **Development Environment**: Xcode-managed development certificates
- **Bundle Structure**: Standard SwiftUI App template with proper Info.plist and entitlements