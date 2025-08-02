# TCC Apple Events Permission Solution - Implementation Summary

## Problem Solved
macOS Sequoia's TCC system requires **notarized Developer ID builds** for Apple Events permission dialogs to appear. Development builds are silently denied with error -1743.

## Implementation Details

### 1. NSApplicationDelegateAdaptor Integration
**File**: `Samay_MacOSApp.swift`
- Added `AppDelegate` class with `NSApplicationDelegate` protocol
- Integrated with SwiftUI app using `@NSApplicationDelegateAdaptor`
- Delays Apple Events initialization until after app launch to ensure TCC system is ready

### 2. Enhanced AppleScript Execution
**File**: `AppleScriptExecutor.swift`
- **Hybrid Approach**: Try NSAppleScript first, fall back to OSAScript
- **NSAppleScript Priority**: Better TCC dialog triggering than OSAScript
- **Permission Request Method**: `requestAppleEventsPermissionDialog()` using NSAppleScript
- **Test Method**: `testAppleEventsPermission()` to verify permissions

### 3. User Interface Integration  
**File**: `MenuBarContentView.swift`
- Added permission status indicators for Accessibility and Apple Events
- Real-time permission checking and testing buttons
- Visual feedback with green/red status indicators

## Key Changes Made

### App Delegate Integration
```swift
class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.initializeAppleEventsPermissions()
        }
    }
}
```

### NSAppleScript Implementation
```swift
func requestAppleEventsPermissionDialog() async throws {
    // Uses NSAppleScript instead of OSAScript for better TCC compatibility
    let script = NSAppleScript(source: scriptSource)
    let result = script.executeAndReturnError(&errorInfo)
}
```

### Hybrid Execution Strategy
```swift
func executeScript(_ scriptSource: String) async throws -> String {
    // Try NSAppleScript first, fall back to OSAScript
    do {
        return try await executeWithNSAppleScript(scriptSource)
    } catch {
        return try runScript(scriptSource, timeout: timeout)
    }
}
```

## Expected Behavior

### Development Builds (Current State)
- ❌ Will still show -1743 errors in development
- ✅ Better error handling and fallback mechanisms
- ✅ User can see permission status in UI
- ✅ NSAppleScript may trigger dialog in some cases

### Notarized Builds (Production Solution)
- ✅ Apple Events permission dialog will appear
- ✅ App will be listed in System Preferences → Automation
- ✅ Full automation functionality will work

## Testing Instructions

1. **Build and Run**: Launch the app in development mode
2. **Check Services Tab**: Go to "Services" tab in the menu bar
3. **View Permissions**: Check the "Permissions" section
4. **Test Apple Events**: Click "Test" button for Apple Events
5. **Grant Accessibility**: Click "Grant" for Accessibility if needed

## Next Steps for Production

### For Development Testing
1. **Create Developer ID Build**:
   ```bash
   # Sign with Developer ID certificate
   codesign -s "Developer ID Application: Your Name" Samay-MacOS.app
   ```

2. **Notarize the Build**:
   ```bash
   # Create archive and notarize
   xcrun altool --notarize-app --file Samay-MacOS.zip
   ```

### For App Store Distribution
1. **Archive for App Store**: Use Xcode's Archive feature
2. **Submit for Review**: App Store builds are automatically notarized
3. **Distribution**: App Store signature handles TCC permissions

## Fallback Options (If Notarization Unavailable)

### 1. XPC Helper Approach
- Create unsigned helper app outside sandbox
- Use XPC communication between main app and helper
- Helper requests Apple Events permissions

### 2. Accessibility API Switch
- Replace Apple Events with AXUIElement API
- Only requires Accessibility permission (already working)
- More reliable but slightly different automation approach

### 3. Manual TCC Profile (Enterprise)
- Deploy Privacy Preferences Policy Control profile
- Pre-grant Apple Events permission via MDM
- Only works on managed/supervised devices

## Files Modified

1. **Samay_MacOSApp.swift** - Added NSApplicationDelegateAdaptor
2. **AppleScriptExecutor.swift** - Enhanced with NSAppleScript support
3. **MenuBarContentView.swift** - Added permission status UI

## Verification Commands

```bash
# Check entitlements
codesign -dv --entitlements :- /path/to/Samay-MacOS.app

# Check TCC database
sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
  "SELECT * FROM access WHERE service='kTCCServiceAppleEvents';"

# Enable TCC debug logging
sudo log config --mode "level:debug" --subsystem com.apple.tccd
```

## Expected Console Output

### Development Build (Error Expected)
```
NSAppleScript error: Not authorized to send Apple events to System Events. (-1743)
Apple Events permission required - this is expected on first run
```

### Notarized Build (Success Expected)
```
NSAppleScript executed successfully: Found 42 processes
Apple Events test successful: Found 42 processes
```

## Current Status
✅ **Implementation Complete** - All code changes applied
⏳ **Testing Required** - Need to test with notarized build
🎯 **Production Ready** - Create Developer ID build for final testing

The solution addresses the core TCC issue identified in your research and provides both immediate development improvements and a clear path to production success.