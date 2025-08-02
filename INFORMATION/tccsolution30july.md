<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Understanding the Missing TCC Dialog for Apple Events in Sequoia

**Main Finding:**
In macOS 15 (Sequoia), **development-signed SwiftUI apps** using OSAKit no longer trigger the TCC Apple Events permission dialog nor register under **System Preferences → Security \& Privacy → Automation** because Sequoia’s TCC daemon (`tccd`) **requires a notarized, Developer ID–signed** bundle to recognize and record an Apple Events request. Development builds—even with correct entitlements and usage descriptions—are silently denied at launch without prompting the user, and no TCC entry is created.

## 1. TCC Changes in macOS 15 (Sequoia)

Sequoia introduces stricter **TCC registration logic** for Apple Events:

1. **Code-signature binding to containers**
    - Sequoia enforces a one-to-one mapping between an app’s sandbox container and its exact **Developer ID** signature hash.
    - Non-notarized or development-only signatures do **not** bind to a persistent container, so `tccd` refrains from prompting and refuses Apple Events silently[^1].
2. **Hardened runtime enforcement**
    - The hardened runtime is automatically enabled for new Xcode targets; without a valid **com.apple.security.automation.apple-events** entitlement in a notarized app, `tccd` rejects events with **−1743** before user consent[^2].
3. **Requirement for Developer ID signing**
    - Only Developer ID–signed and notarized apps qualify for Apple Events request dialogs in Sequoia. Ad-hoc or Xcode development signatures are skipped entirely, preventing the dialog from ever appearing[^3].

## 2. Development vs. Production Signing

| Build Type | Code Signature | TCC Dialog Shown | Appears in Automation Pane |
| :-- | :-- | :-- | :-- |
| Xcode development certificate | Ad-hoc / Team Development | No | No |
| Developer ID (non-notarized) | Developer ID without notarization | No | No |
| Developer ID + Notarized (App ID) | Developer ID + notarization | Yes (once) | Yes |
| App Store build | App Store signature + notarization | Yes (once) | Yes |

- **Development builds** fail silently (error −1743) because `tccd` considers them unrecognized senders and does not create Automation entries or show prompts[^3].
- **Notarized Developer ID builds** trigger the “App wants to control System Events” dialog on first launch and appear under Automation once allowed[^3].


## 3. SwiftUI vs. AppKit Lifecycle Effects

- **SwiftUI apps** use the new Swift `App` protocol rather than an `NSApplicationDelegate` by default.
- Without explicit `NSApplicationDelegate` integration, some early Apple Events may occur **before** TCC checks are registered, causing silent denials.
- **Workaround:** Adopt an `NSApplicationDelegateAdaptor` to delay Apple Events until after the app has fully launched under AppKit, ensuring TCC can intercept the request[^4].


## 4. OSAKit vs. NSAppleScript Differences

- **OSAScript.executeAndReturnError()** runs Apple Events internally without going through the same high-level trigger that `osascript` (Terminal) uses, bypassing the system prompt mechanism entirely in sandboxed development builds[^5].
- **NSAppleScript** in a notarized binary still triggers TCC dialogs correctly because it invokes the legacy AppleScript runtime that routes through the system’s event request path.


## 5. How TCC Registers Apple Events Clients

- `tccd` registers a client only when:

1. The app’s **code signature** is trusted (notarized Developer ID).
2. The app sends a **user-prompted** Apple Events request (first request).
- **First-request trigger:** Only high-level APIs (`NSAppleScript`, `osascript` CLI) in a recognized signer context generate the prompt[^6]. Direct OSAKit calls from unrecognized apps are denied silently.


## 6. Workarounds and Alternatives

1. **Notarize** your Developer ID build even for local testing:
    - Sign with `Developer ID Application` certificate plus hardened runtime + `com.apple.security.automation.apple-events` entitlement.
    - Notarize via Xcode or `xcrun altool`.
2. **Use an XPC helper** outside the sandbox:
    - Host an unsigned helper with Accessibility and Apple Events entitlements; communicate via XPC from your SwiftUI app.
3. **Switch to Accessibility API (AXUIElement)** for UI automation:
    - Requires only Accessibility permission and appears under **Privacy → Accessibility**, bypassing Apple Events entirely[^7].
4. **Embed an `NSApplicationDelegate`** and delay Apple Events until after `applicationDidFinishLaunching`:
    - Ensures TCC dialog integration and gives the system time to recognize the app context[^4].
5. **Manual TCC profile via MDM**:
    - Deploy a **Privacy Preferences Policy Control** profile granting AppleEvents for your bundle ID. Requires MDM supervision and only applies on managed devices[^8].

## 7. Diagnostic Tips

- **Console filters:** Look for `service: kTCCServiceAppleEvents` rejection logs mentioning missing entitlement or unrecognized code signature.
- **tccd logging:** Increase verbosity via `sudo log config --mode "level:debug" --subsystem com.apple.tccd`.
- **Verify entitlements:**

```bash
codesign -dv --entitlements :- /Applications/Samay-MacOS.app
```

- **Check TCC database:**

```bash
sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
  "SELECT * FROM access WHERE service='kTCCServiceAppleEvents' AND client LIKE '%Samay-MacOS%';"
```


**Conclusion:**
On macOS Sequoia, the TCC system **deliberately ignores** ad-hoc and development-signed Apple Events requests. Achieving a permission prompt and Automation entry for a SwiftUI app requires a **notarized Developer ID** build or an alternative out-of-sandbox helper. Once notarized, high-level AppleScript APIs will invoke the TCC dialog, and the app will appear in **Automation** for user approval.

<div style="text-align: center">⁂</div>

[^1]: https://atlasgondal.com/macos/priavcy-and-security/app-permissions-priavcy-and-security/a-guide-to-tcc-services-on-macos-sequoia-15-0/

[^2]: https://mjtsai.com/blog/2025/03/28/macos-15-4-adds-tcc-events-to-endpoint-security/

[^3]: https://www.macscripter.net/t/apple-event-authorization-dialog-never-shows-up/71663

[^4]: https://www.youtube.com/watch?v=iyOikcL5GAU

[^5]: https://stackoverflow.com/questions/51299066/macos-mojave-automator-not-authorized-to-send-apple-events-to-system-events

[^6]: https://apple.stackexchange.com/questions/468354/macos-ventura-cannot-reset-automation-preferences-for-a-single-app

[^7]: https://attack.mitre.org/techniques/T1548/006/

[^8]: https://support.apple.com/en-in/guide/deployment/dep38df53c2a/web

[^9]: https://objective-see.org/blog/blog_0x7F.html

[^10]: https://www.youtube.com/watch?v=FDFaxhW0OW4

[^11]: https://9to5mac.com/2025/03/28/security-bite-macos-15-4-hits-allow-on-tcc-event-support/

[^12]: https://support.apple.com/en-in/120283

[^13]: https://eclecticlight.co/2018/11/20/what-does-the-tcc-compatibility-database-do/

[^14]: https://www.youtube.com/watch?v=RaO_zMZPEiE

[^15]: https://cycling74.com/forums/sendreceive-apple-events-from-external-object

[^16]: https://eclecticlight.co/2025/03/26/how-macos-sequoia-launches-an-app/

[^17]: https://www.rainforestqa.com/blog/macos-tcc-db-deep-dive

[^18]: https://developer.apple.com/support/xcode/

[^19]: https://support.apple.com/en-us/121238

[^20]: https://www.crn.com/news/security/2024/apple-s-macos-sequoia-release-causing-issues-for-edr-tools-reports

[^21]: https://developer.apple.com/forums/thread/692758

[^22]: https://wts.dev/posts/tcc-who/

[^23]: https://developer.apple.com/videos/play/wwdc2022/10075/

[^24]: https://stackoverflow.com/questions/72444259/cast-appdelegate-in-swiftui-lifecycle

[^25]: https://www.reddit.com/r/AutomateYourself/comments/uefcge/how_do_i_give_my_app_apple_events_permission/

[^26]: https://stackoverflow.com/questions/58527740/the-difference-between-create-mac-os-app-project-and-ios-app-project-with-xcode

[^27]: https://milen.me/writings/appkit-vs-swiftui-stable-vs-shiny/

[^28]: https://auth0.com/blog/get-started-ios-authentication-swift-swiftui-part-1-login-logout/

[^29]: https://stackoverflow.com/questions/63940427/ios-14-how-to-trigger-local-network-dialog-and-check-user-answer

[^30]: https://www.reddit.com/r/swift/comments/1gj02p4/swiftui_vs_appkit/

[^31]: https://stackoverflow.com/questions/27144113/subclass-nsapplication-in-swift

[^32]: https://betterprogramming.pub/handling-ios-13-location-permissions-5482abc77961

[^33]: https://dev.to/raphacmartin/what-really-are-the-differences-between-swiftui-and-uikit-1o2j

[^34]: https://developer.apple.com/documentation/appkit/nsapplication

[^35]: https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications

[^36]: https://news.ycombinator.com/item?id=32524462

[^37]: https://developer.apple.com/reference/appkit/nsapplication

[^38]: https://developer.apple.com/documentation/corelocation/requesting-authorization-to-use-location-services

[^39]: https://www.youtube.com/watch?v=t358ej3LWvY

[^40]: https://developer.apple.com/documentation/UIKit/requesting-access-to-protected-resources

[^41]: https://lessons.livecode.com/m/4069/l/308242-how-do-i-create-a-development-profile-for-ios

[^42]: https://www.youtube.com/watch?v=Tl7V0FvL384

[^43]: https://docs.42gears.com/AstroFarm/DownloadtheAppleDeveloperCertifi.html

[^44]: https://developer.apple.com/videos/play/wwdc2025/324/

[^45]: https://www.youtube.com/watch?v=RrQZxRd27YY

[^46]: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/

[^47]: https://developer.apple.com/help/account/certificates/create-developer-id-certificates/

[^48]: https://developer.apple.com/videos/play/wwdc2021/10171/

[^49]: https://developer.apple.com/support/certificates/

[^50]: https://appinventiv.com/blog/ios-app-development-cost/

[^51]: https://developer.apple.com/app-store/in-app-events/

[^52]: https://github.com/objective-see/LuLu/issues/705

[^53]: https://developer.apple.com/events/

[^54]: https://github.com/carlashley/tccprofile

[^55]: https://developer.apple.com/videos/play/tech-talks/110347/

[^56]: https://learn.jamf.com/en-US/bundle/technical-articles/page/Resetting_Transparency_Consent_and_Control_Prompts_on_macOS.html

[^57]: https://www.apple.com/in/app-store/developing-for-the-app-store/

[^58]: https://developer.apple.com/help/app-store-connect/manage-builds/choose-a-build-to-submit/

[^59]: https://developer.apple.com/programs/

[^60]: https://macblog.org/reset-tcc-privacy/

[^61]: https://community.jamf.com/t5/jamf-pro/apple-script-tcc-bypass/td-p/308036

[^62]: https://forum.latenightsw.com/t/ventura-not-authorised-to-send-apple-events-to-music/4387?page=2

[^63]: https://github.com/AtlasGondal/macos-pentesting-resources/blob/main/tccd/kTCCService.md

[^64]: https://kb.filewave.com/books/profiles-apple/page/create-tcc-privacy-policy-control-payloads

[^65]: https://angelica.gitbook.io/hacktricks/macos-hardening/macos-security-and-privilege-escalation/macos-security-protections/macos-tcc

[^66]: https://scriptingosx.com/2020/09/avoiding-applescript-security-and-privacy-requests/

[^67]: https://community.adobe.com/t5/indesign/indesign-16-3-2-not-authorised-to-send-apple-events-to-other-apps/td-p/12312871

[^68]: https://developer.apple.com/business/documentation/Configuration-Profile-Reference.pdf

