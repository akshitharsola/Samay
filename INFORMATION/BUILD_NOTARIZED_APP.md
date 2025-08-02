# How to Create a Notarized Build for TCC Apple Events

## Current Status
✅ **Apple Events TCC fix implemented** - App now uses NSAppleScript for better compatibility
✅ **Better error handling** - Improved debugging and user feedback
⚠️ **Development certificate only** - Need Developer ID for production TCC

## Step 1: Get Developer ID Certificate

### Option A: Via Xcode (Recommended)
1. **Open Xcode** → Preferences → Accounts
2. **Select your Apple ID** (harsolaakshit@gmail.com)  
3. **Click "Manage Certificates"**
4. **Click "+" → "Developer ID Application"**
5. **Let Xcode create and download the certificate**

### Option B: Via Apple Developer Website
1. Go to [developer.apple.com](https://developer.apple.com/account/resources/certificates)
2. Click **"+"** to create new certificate
3. Select **"Developer ID Application"**
4. Follow the wizard to create and download

## Step 2: Build with Developer ID Signing

Once you have the Developer ID certificate, run this command:

```bash
cd /Users/akshitharsola/Documents/Samay/Samay_MacOS

# Build with Developer ID signing
xcodebuild \
  -project Samay_MacOS.xcodeproj \
  -scheme Samay_MacOS \
  -configuration Release \
  -derivedDataPath ./build \
  -destination 'generic/platform=macOS' \
  archive \
  -archivePath ./build/Samay_MacOS.xcarchive \
  CODE_SIGN_IDENTITY="Developer ID Application: Akshit Harsola (P5A6FC5MY7)" \
  DEVELOPMENT_TEAM=P5A6FC5MY7 \
  CODE_SIGN_STYLE=Manual
```

## Step 3: Export and Notarize

### Create App Bundle
```bash
# Export the app from archive
cd /Users/akshitharsola/Documents/Samay/Samay_MacOS
xcodebuild \
  -exportArchive \
  -archivePath ./build/Samay_MacOS.xcarchive \
  -exportPath ./build/Export \
  -exportOptionsPlist ./export_options.plist
```

### Create Export Options Plist
```bash
cat > export_options.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>developer-id</string>
    <key>teamID</key>
    <string>P5A6FC5MY7</string>
    <key>signingStyle</key>
    <string>manual</string>
    <key>stripSwiftSymbols</key>
    <true/>
</dict>
</plist>
EOF
```

### Notarize the App
```bash
# Create ZIP for notarization
cd ./build/Export
zip -r Samay_MacOS.zip Samay_MacOS.app

# Submit for notarization (requires app-specific password)
xcrun notarytool submit Samay_MacOS.zip \
  --apple-id harsolaakshit@gmail.com \
  --team-id P5A6FC5MY7 \
  --password [APP_SPECIFIC_PASSWORD] \
  --wait

# Staple the notarization ticket
xcrun stapler staple Samay_MacOS.app
```

## Step 4: Test TCC Functionality

Once notarized, test the app:

```bash
# Launch the notarized app
open /Users/akshitharsola/Documents/Samay/Samay_MacOS/build/Export/Samay_MacOS.app

# In the app's chat, type: "trigger apple events"
# You should now see the actual TCC permission dialog!
```

## Quick Alternative - Manual Signing

If you can't get Developer ID certificate immediately, try this manual approach:

```bash
# Build unsigned first
xcodebuild -project Samay_MacOS.xcodeproj -scheme Samay_MacOS -configuration Release -derivedDataPath ./build build CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO

# Then sign manually (after getting Developer ID cert)
codesign --force --deep --sign "Developer ID Application: Akshit Harsola (P5A6FC5MY7)" \
  --options runtime \
  --entitlements Samay_MacOS/Samay_MacOS.entitlements \
  ./build/Build/Products/Release/Samay_MacOS.app
```

## Expected Results

### Before Notarization (Development Build)
```
❌ Failed to trigger Apple Events permission request.
Error Details: NSAppleScript error: Not authorized to send Apple events to System Events. (-1743)
```

### After Notarization (Production Build)
```
✅ Apple Events Permission Request Triggered!
[System shows actual TCC dialog: "Samay_MacOS would like to control System Events. Allow?"]
```

## Troubleshooting

### If notarization fails:
1. Check entitlements are correct
2. Ensure hardened runtime is enabled
3. Verify Developer ID certificate is valid
4. Check for code signing issues

### If TCC dialog still doesn't appear:
1. Reset TCC: `tccutil reset AppleEvents com.akshitharsola.Samay-MacOS`
2. Clear app from quarantine: `xattr -dr com.apple.quarantine Samay_MacOS.app`
3. Launch from Terminal: `open Samay_MacOS.app`

## App-Specific Password Setup
1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign In → App-Specific Passwords → Generate
3. Name: "Samay Notarization"
4. Use this password in notarytool commands

---

**Next Steps:**
1. Get Developer ID certificate via Xcode
2. Build and notarize using commands above
3. Test "trigger apple events" in notarized app
4. Verify TCC dialog appears and permissions work