<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Resolving Apple Events Authorization Problems in Sandboxed macOS Apps

Apple’s App Sandbox and modern Transparency, Consent, and Control (TCC) privacy system dramatically restrict inter-process automation. A sandboxed Swift/SwiftUI app that tries to send Apple Events to System Events often fails with −600 (“Application isn’t running”) or −1743 (“Not authorized to send Apple Events …”) even when Accessibility permissions appear granted. This report dissects why that happens on macOS 13 Ventura and macOS 14 Sonoma, how entitlements and privacy prompts evolved, where System Events is special, and when to abandon Apple Events in favor of other APIs.

## macOS Automation Architecture in 2025

Apple Events (the IPC mechanism behind AppleScript, JXA, and NSAppleScript) travel through the **appleeventsd** daemon. To prevent privilege escalation, the App Sandbox blocks outbound Apple Events unless the sender has:

1. A **team-signed code signature** that embeds the correct **app-sandbox** entitlements.
2. A user-granted TCC approval recorded in ~/Library/Application Support/com.apple.TCC/TCC.db.
3. A hardened runtime flag (`--options runtime`) that is compatible with the above entitlements when the binary is notarized[^1][^2].

If any link breaks, appleeventsd returns −1743, Script Editor shows “Not authorized…”, or an NSAppleScript error dictionary reports **NSAppleScriptErrorNumber = −600**[^3].

## Entitlements: The Canonical Reference

| Entitlement Key | Purpose | Required macOS Version | Format Example | Notes |
| :-- | :-- | :-- | :-- | :-- |
| `com.apple.security.app-sandbox` | Turns sandbox **ON** | All | `<true/>` | Must be paired with code-signing[^4] |
| `com.apple.security.scripting-targets` | Fine-grained permanent permission to send events to *scriptable apps that declare access groups* | macOS 10.8+ | <dict><key>com.apple.systemevents</key><array><string>com.apple.systemevents.files</string></array></dict> | Preferred for **Mail, Finder** etc.; App Store rejects reliance on “temporary” keys[^5][^6] |
| `com.apple.security.temporary-exception.apple-events` | Broad, legacy, per-target bundle-ID bypass | Deprecated but still honored[^7] | <array><string>com.apple.systemevents</string></array> | Required for apps that expose no sdef access-groups (e.g. **System Events**)[^6] |
| `com.apple.security.automation.apple-events` | Boolean that re-enables Apple Events once the hardened runtime is on | macOS 10.14+ | `<true/>` | Without it, hardened apps trigger **“Prompting policy for hardened runtime; invalid entitlement”** console errors[^8] |
| `NSAppleEventsUsageDescription` | Info.plist string explaining to users *why* events are needed | Mandatory when building with macOS 10.14 SDK or later[^9] | `"This app needs to automate System Events to import data"` | Missing string → instant −1743 with no prompt |

> **Key takeaway:** `scripting-targets` and `temporary-exception.apple-events` are **not mutually exclusive**[^7]. On Ventura/Sonoma you usually need both **plus** `automation.apple-events`.

## How Ventura and Sonoma Changed the Rules

### 1. User-Centric Privacy Dialogs

Ventura (13) introduced stricter TCC gating. Every first outbound event to a new receiver triggers a dialog referencing the **sender’s app name**[^10][^11]. If your helper binary is unsigned or ad-hoc-signed, the system fails to resolve the sender and silently denies the event[^12].

### 2. Container-Signature Binding

Sonoma (14) ties an app’s sandbox container in ~/Library/Containers/ to its **exact code-signature hash**. Re-signing with a different TeamID or ad-hoc signature breaks that association and resets all Automation approvals, forcing users to re-click the dialogs[^12].

### 3. Hardened Runtime Is No Longer Optional

Xcode 15 enables the hardened runtime by default for new macOS targets. Without `com.apple.security.automation.apple-events`, appleeventsd logs:

```
Prompting policy for hardened runtime; service: kTCCServiceAppleEvents
requires entitlement com.apple.security.automation.apple-events but it is missing
```

…then returns −1743[^8][^13].

## Why System Events Is Special

System Events (bundle ID `com.apple.systemevents`) ships as a **faceless background app** and publishes no `access-group` suites in its Scripting Dictionary. Therefore:

- `scripting-targets` **cannot** target it—Apple never defined access groups for System Events[^6].
- You must list `com.apple.systemevents` under **temporary-exception.apple-events** even in 2025[^14][^7].
- Because System Events can auto-quit when idle, scripts must explicitly **launch and set `quit delay 0`** to avoid −600 errors[^15].

```applescript
tell application id "com.apple.systemevents"
    launch
    set quit delay to 0
end tell
delay 0.3
```


## Common Mis-Configurations That Trigger −600 / −1743

| Symptom | Likely Cause | Fix |
| :-- | :-- | :-- |
| First AppleScript call hangs, then −600 | System Events auto-quit before the command arrived | `launch`, `quit delay 0`, 300 ms delay |
| Works in Script Editor but fails in sandboxed build | Missing `temporary-exception.apple-events` or `scripting-targets` | Add correct entitlement array[^16] |
| Works on Monterey, fails on Ventura | Missing TCC approval; Ventura asks per-receiver | Trigger AppleScript once; user must click **OK**[^11][^17] |
| Console shows **“invalid entitlement”** | Hardened runtime without `automation.apple-events` | Add boolean entitlement or disable runtime[^1][^8] |
| Dialog repeats after each build | Code-signature hash changes (ad-hoc signing) | Use a stable Developer ID or team-ID debug profile[^12] |

## Xcode and Code-Signing Checklist

1. **Enable App Sandbox** under **Signing \& Capabilities**.
2. Add required keys in *both* `.entitlements` and **Info.plist**.
3. Ensure your helper tools and XPC services share the same TeamID and entitlements[^18][^19].
4. Sign with `--options runtime` and **notarize**; otherwise macOS disables Automation at launch[^1][^2].
5. For App Store submission, avoid deprecated `temporary-exception.apple-events` unless absolutely necessary; provide reviewer justification[^5][^20].

## Alternative Automation Paths

| API | Sandboxed? | Typical Use | Caveats |
| :-- | :-- | :-- | :-- |
| **AXUIElement Accessibility** (`AXObserver`, `AXUIElementCopyAttributeValue`) | YES (requires Accessibility permission) | Inspect UI hierarchy, click buttons, read text | Must disable App Sandbox when posting events (e.g., `setAttribute`)[^21] |
| **Quartz Event Services** (`CGEventPost`) | NO (blocked by sandbox)[^22][^23] | Simulate keyboard/mouse | Apple refuses entitlement, banned from Mac App Store |
| **NSWorkspace / Service Management** | YES | Launch apps, open files/URLs | Cannot manipulate UI |
| **Shortcuts App + App Intents** | YES | High-level automation exposed via Swift | Limited to APIs declared in Intents definitions |
| **XPC Helper Outside Sandbox** | Host remains sandboxed; helper runs unsandboxed | Delegate privileged automation | Helper must live in separate target and request Accessibility directly[^24] |

When Apple Events remain brittle, prefer **Accessibility API** for reading UI state or implement a minimal **Launch Agent** signed with your Team ID to perform CGEventPost outside the sandbox—but note App Store rejection risks.

## Step-by-Step Diagnostic Workflow

### 1. Verify Code Signature

```bash
codesign -dv --entitlements :- /Applications/MyApp.app
```


### 2. Inspect TCC Database

```bash
sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client,auth_value FROM access WHERE service='kTCCServiceAppleEvents';"
```


### 3. Confirm System Events Is Running

```bash
pgrep -l "System Events" || open -a "System Events"
```


### 4. Run Minimal Script With Logging

Use `osadebug` to collect AE flow and watch for −1743.

## Example Working Entitlements File (Sonoma 14)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key><true/>
    <key>com.apple.security.automation.apple-events</key><true/>
    <key>com.apple.security.temporary-exception.apple-events</key>
    <array>
        <string>com.apple.systemevents</string>
    </array>
    <key>com.apple.security.scripting-targets</key>
    <dict>
        <key>com.apple.finder</key>
        <array>
            <string>com.apple.finder.files</string>
        </array>
    </dict>
</dict>
</plist>
```

And **Info.plist** snippet:

```xml
<key>NSAppleEventsUsageDescription</key>
<string>This app needs to automate System Events to configure user settings.</string>
```


## Comparative Table: Apple Events Policy by macOS Version

| Feature | Monterey 12 | Ventura 13 | Sonoma 14 | Sequoia 15 (beta) |
| :-- | :-- | :-- | :-- | :-- |
| Hardened runtime auto-enabled | Optional | Default for new Xcode templates[^25] | Mandatory for notarization | Mandatory |
| Container-signature binding | No | No | Yes[^12] | Yes |
| `NSAppleEventsUsageDescription` required | Only if 10.14 SDK | Yes | Yes | Yes |
| `automation.apple-events` needed | If runtime on | Always | Always | Always |
| Screen-recording privacy overlay button | n/a | n/a | New system overlay when window captured[^26] | Expanded to audio capture |

## Decision Matrix: Fix vs. Redesign

| Scenario | Chances of Success With Entitlements | Recommended Path |
| :-- | :-- | :-- |
| Control **Finder**, **Mail**, **Numbers** | High (use scripting-targets) | Stay on Apple Events |
| Control **System Events** for simple keystrokes | Medium (needs temp entitlement + launch) | Use Apple Events; fallback to Accessibility |
| Automate arbitrary third-party apps lacking sdef | Low; will require temp exception and App Store rejection likely | Switch to Accessibility API |
| Simulate global hotkeys or pasteboard typing | Zero (Apple Events unsuitable) | Use CGEventPost from helper outside sandbox; distribute outside Mac App Store |
| Mass-market App Store utility | Medium if automation limited to Apple-signed apps | Limit scope, show onboarding UI for permissions |

## Conclusion

Apple’s modern security model expects developers to negotiate three layers—entitlements, user consent, and hardened runtime—with exacting precision. The −600/−1743 errors nearly always trace back to **missing or mismatched entitlements**, **unstable code-signing**, or **expired TCC grants**. For sandboxed SwiftUI apps targeting Ventura/Sonoma:

1. **Embed all four relevant keys** (`app-sandbox`, `automation.apple-events`, `scripting-targets`, `temporary-exception.apple-events`) and a clear `NSAppleEventsUsageDescription`.
2. **Stabilize your code-signature** during development to avoid repeated TCC prompts.
3. **Explicitly launch System Events** and manage its quit delay to avoid race conditions.

When Apple Events still prove unreliable, the **Accessibility API** (AXUIElement) delivers more predictable UI scripting inside the sandbox, while **CGEventPost** or XPC helpers outside the sandbox remain options for developer-id distribution. Understanding these moving parts—and how they changed in Ventura and Sonoma—lets you decide whether to keep fighting for Apple Events or pivot to a different automation stack.

<div style="text-align: center">⁂</div>

[^1]: https://wiki.freepascal.org/Hardened_runtime_for_macOS

[^2]: https://developer.apple.com/documentation/security/hardened-runtime

[^3]: https://stackoverflow.com/questions/52601414/running-applescript-from-swift-not-working

[^4]: https://eclecticlight.co/2025/03/24/what-are-app-entitlements-and-what-do-they-do/

[^5]: https://stackoverflow.com/questions/22148986/mac-app-store-rejects-use-of-deprecated-sandbox-entitlement

[^6]: https://www.macscripter.net/t/new-sandbox-rules-and-apple-events/66670

[^7]: https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/AppSandboxTemporaryExceptionEntitlements.html

[^8]: https://stackoverflow.com/questions/65404011/prompting-policy-for-hardened-runtime-invalid-entitlement-error-for-sending-a

[^9]: https://www.felix-schwarz.org/blog/2018/08/new-apple-event-apis-in-macos-mojave

[^10]: https://mjtsai.com/blog/2018/06/28/apple-event-sandboxing-in-macos-mojave-lacks-essential-apis/

[^11]: https://www.macscripter.net/t/applescript-release-notes/73980

[^12]: https://lapcatsoftware.com/articles/2023/6/1.html

[^13]: https://forum.xojo.com/t/ktccserviceappleevents-com-apple-security-automation-apple-events/49922

[^14]: https://lapcatsoftware.com/articles/hardened-runtime-sandboxing.html

[^15]: https://apple.stackexchange.com/questions/416086/what-is-system-events

[^16]: https://stackoverflow.com/questions/21924932/how-to-run-an-applescript-from-a-sandboxed-application-on-a-mac-os-x

[^17]: https://discussions.apple.com/thread/254151477

[^18]: https://forum.xojo.com/t/running-applescript-with-admin-on-sandboxed-app/80614

[^19]: https://github.com/electron-userland/electron-builder/issues/3989

[^20]: https://forum.xojo.com/t/how-can-you-determine-what-entitlements-an-app-is-using/25746

[^21]: https://stackoverflow.com/questions/79606344/accessibility-api-axfocuseduielement-always-returns-nil

[^22]: https://stackoverflow.com/questions/10936028/can-mac-app-store-sandboxed-apps-use-cgeventpost

[^23]: https://stackoverflow.com/questions/47086375/how-to-post-a-quartz-event-after-swift-application-launch

[^24]: https://jhftss.github.io/A-New-Era-of-macOS-Sandbox-Escapes/

[^25]: https://developer.apple.com/documentation/xcode/configuring-the-hardened-runtime

[^26]: https://github.com/electron/electron/issues/40814

[^27]: https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html

[^28]: https://support.apple.com/en-us/120875

[^29]: https://stackoverflow.com/questions/51635321/mac-app-store-sandbox-file-exceptions-not-working

[^30]: https://support.apple.com/en-us/120331

[^31]: https://www.youtube.com/watch?v=r4J2gKXxRCE

[^32]: https://developer.apple.com/library/archive/qa/qa1888/_index.html

[^33]: https://developer.apple.com/forums/thread/113050

[^34]: https://stackoverflow.com/questions/51299066/macos-mojave-automator-not-authorized-to-send-apple-events-to-system-events

[^35]: https://www.youtube.com/watch?v=2Y-YHVJE1dE

[^36]: https://indiestack.com/2018/08/apple-events-usage-description/

[^37]: https://forum.latenightsw.com/t/ventura-not-authorised-to-send-apple-events-to-music/4387

[^38]: https://developer.apple.com/documentation/macos-release-notes/macos-14-release-notes

[^39]: https://appleinsider.com/inside/macos/tips/how-to-get-started-with-macos-applescript-dictionaries-syntax-and-more

[^40]: https://iboysoft.com/tips/not-authorized-to-send-apple-events-to-system-events.html

[^41]: https://support.apple.com/en-in/guide/script-editor/scpedt1126/mac

[^42]: https://www.helpnetsecurity.com/2022/10/10/macos-ventura-video/

[^43]: https://www.sonnysoftware.com/support/user-guides/scripting

[^44]: https://discussions.apple.com/thread/254928051

[^45]: https://support.apple.com/en-in/guide/script-editor/scpedt11560/mac

[^46]: https://discussions.apple.com/thread/254481674

[^47]: https://github.com/DevilFinger/DFAXUIElement

[^48]: https://developer.apple.com/forums/tags/app-sandbox?page=2

[^49]: https://www.reddit.com/r/swift/comments/18k909w/i_hit_a_dead_end_with_accessibility_apis/

[^50]: https://forum.latenightsw.com/t/mojave-and-apple-events-sandboxing/1386

[^51]: https://docs.huihoo.com/apple/wwdc/2011/session_207__user_level_device_access.pdf

[^52]: https://chromium.googlesource.com/chromium/src/+/e842ab5f98..35f882550d

[^53]: https://macdevelopers.wordpress.com/2014/01/31/accessing-text-value-from-any-system-wide-application-via-accessibility-api/

[^54]: https://en.wikipedia.org/wiki/List_of_built-in_macOS_apps

[^55]: https://developer.apple.com/documentation/coregraphics/cgevent/post(tap:)?changes=_6__8\&language=objc

[^56]: https://developerspace.gpii.net/tags/osx

[^57]: https://quartznetwork.com/event/connect-hr-fall

[^58]: https://discuss.wxpython.org/t/simulating-keyboard-events/21784

[^59]: https://developer.apple.com/documentation/applicationservices/axuielement_h

[^60]: https://developer.apple.com/documentation/coregraphics/quartz-event-services

[^61]: https://stackoverflow.com/questions/tagged/xpc

[^62]: https://stackoverflow.com/questions/tagged/accessibility-api

[^63]: https://www.macosxautomation.com/automator/security.html

[^64]: https://stackoverflow.com/questions/59125192/authorization-by-aedeterminepermissiontoautomatetarget-waits-infinit-time

[^65]: https://gitlab.com/gnachman/iterm2/-/issues/11078

[^66]: https://www.youtube.com/watch?v=sxgYBi-PuGI

[^67]: https://www.noodlesoft.com/blog/

[^68]: https://github.com/openstenoproject/plover/issues/1134

[^69]: https://mjtsai.com/blog/tag/privacy/

[^70]: https://www.microsoft.com/en-us/security/blog/2022/07/13/uncovering-a-macos-app-sandbox-escape-vulnerability-a-deep-dive-into-cve-2022-26706/

[^71]: https://github.com/sindresorhus/active-win/issues/135

[^72]: https://stackoverflow.com/questions/64826527/how-to-security-privacy-settings-for-a-watch-me-do-quickaction-in-automator

[^73]: https://mjtsai.com/blog/2019/10/09/settings-urls-supported-by-ios-and-ipados-13-1/

