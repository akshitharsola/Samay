<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# macOS System Events “Application isn’t running” (−600) Deep Dive

**Key Recommendation:**
To reliably drive UI automation via System Events in sandboxed or non-sandboxed apps, ensure proper activation of System Events, request the correct Apple Events entitlements, grant Accessibility (UI Scripting) permissions, and explicitly launch and keep System Events running before issuing commands.

## 1. Sandbox Restrictions and Required Entitlements

By default, sandboxed apps:

- Can receive Apple events but **cannot** send them to other apps without explicit entitlements[^1].
- Must declare in their `.entitlements` file:
    - `com.apple.security.app-sandbox` (boolean true)
    - `com.apple.security.temporary-exception.apple-events` (array of target bundle IDs)
    - Or `com.apple.security.scripting-targets` (array of bundle IDs) for fine-grained Apple Events sending[^2].

Example entitlements snippet:

```xml
<key>com.apple.security.temporary-exception.apple-events</key>
<array>
  <string>com.apple.systemevents</string>
  <string>com.apple.finder</string>
</array>
```

Specifying `com.apple.systemevents` allows sending Apple events to System Events[^2].

## 2. Granting Accessibility (UI Scripting) Permissions

UI scripting via System Events requires granting **Accessibility** permissions in **System Settings → Privacy \& Security → Accessibility**:

- Add both your app and **Script Editor** (if used) to this list.
- In macOS 10.14+ permissions are per-target: your app must appear under **Automation** with permission to control **System Events**[^3].

Failure to do so yields:

```
System Events got an error: Script Editor is not allowed assistive access.
```

or

```
System Events got an error: Application isn’t running. (error -600)
```


## 3. System Events Process Management and Lifecycle

### 3.1 Auto-launch and Auto-quit Behavior

- **System Events** is a faceless background app (`appleeventsd`).
- It can auto-quit if idle. To prevent this, set its “quit delay” to zero:

```applescript
tell application "System Events" to set quit delay to 0
```

This keeps System Events running indefinitely during automation[^4][^5].


### 3.2 Explicit Startup Sequence

Before issuing any UI-scripting commands, explicitly ensure **System Events** is running and front-most:

```applescript
tell application id "com.apple.systemevents"
    launch
    activate
    set quit delay to 0
end tell
```

Then wrap all subsequent UI commands within:

```applescript
tell application "System Events"
    -- UI scripting here
end tell
```

Delays (`delay 0.5`) may be needed to allow the process to finish launching[^6][^7].

## 4. Timing and Synchronization

- **Delays** are crucial when automating UI actions:
    - After `activate`, wait before sending keystrokes or clicks.
    - When targeting sandboxed apps, additional latency may occur; adjust delays accordingly[^8].
- **Checking process availability**:

```applescript
repeat until application id "com.apple.systemevents" is running
    delay 0.2
end repeat
```

This loop blocks until System Events is ready for commands.


## 5. Alternative Approaches

When Apple Script with **System Events** remains unreliable, consider:

1. **CGEventPost** (Quartz Event Services)
    - Generate low-level keyboard or mouse events from code (Swift/Objective-C)[^9].
    - Bypasses Apple Events entirely but still requires **Accessibility** permissions.
2. **Accessibility API (AXUIElement)**
    - Directly manipulate UI elements via the Accessibility framework in Swift/Objective-C.
    - More robust than GUI scripting when combined with AX attributes.
3. **Automator Actions or JXA (JavaScript for Automation)**
    - JXA may exhibit slightly different timing characteristics; can be tested as a fallback[^7].

## 6. Summary Steps to Resolve “Application isn’t running” (−600)

1. **Entitlements**
    - Add `com.apple.security.temporary-exception.apple-events` for `com.apple.systemevents` in your app’s `.entitlements`[^2].
2. **Accessibility Permission**
    - Grant your app and any script host (Script Editor, Terminal) under **Accessibility** and **Automation** settings.
3. **Initialize System Events**

```applescript
tell application id "com.apple.systemevents"
    launch
    activate
    set quit delay to 0
end tell
delay 0.5
```

4. **UI Scripting Block**

```applescript
tell application "System Events"
    -- your commands here
end tell
```

5. **Incorporate Delays**
    - Use `delay` before and between UI interactions to allow for process readiness.
6. **Consider Alternatives**
    - If AppleScript remains brittle, switch to CGEventPost or the Accessibility API for direct event generation.

By following these guidelines—correct entitlements, explicit launch and activation of **System Events**, granting of Accessibility permissions, and appropriate synchronization—you can eliminate the −600 error and achieve reliable UI automation on macOS.

<div style="text-align: center">⁂</div>

[^1]: https://developer.apple.com/library/archive/qa/qa1888/_index.html

[^2]: https://stackoverflow.com/questions/21924932/how-to-run-an-applescript-from-a-sandboxed-application-on-a-mac-os-x

[^3]: https://stackoverflow.com/questions/60449827/got-application-isn-t-running-error-600-when-executing-applescript-in-swif

[^4]: https://www.macscripter.net/t/why-system-events-isnt-running/66548

[^5]: https://stackoverflow.com/questions/65947911/applescript-tell-application-system-events-extremely-slow-only-on-1-account-of

[^6]: https://www.macscripter.net/t/application-isnt-running-error-600/67845

[^7]: https://www.macscripter.net/t/tell-section-being-executed-several-times-with-no-loop/74535

[^8]: https://www.youtube.com/watch?v=MOdIFEU1WV8

[^9]: https://stackoverflow.com/questions/19798583/accessibility-api-alternative-to-get-selected-text-from-any-app-in-osx

[^10]: https://www.reddit.com/r/applescript/comments/ll0zti/applescript_problem_since_updating_mac/

[^11]: https://github.com/Hammerspoon/hammerspoon/issues/2290

[^12]: https://www.noodlesoft.com/forums/viewtopic.php?f=4\&t=4696

[^13]: https://forum.xojo.com/t/running-applescript-with-admin-on-sandboxed-app/80614

[^14]: https://stackoverflow.com/questions/34517286/cant-get-last-text-item-of-alias-error-when-running-applescript

[^15]: https://leancrew.com/all-this/2011/08/the-app-store-sandboxing-and-applescript/

[^16]: https://discussions.apple.com/thread/6715260

[^17]: https://mikebian.co/scripting-macos-with-javascript-automation/

[^18]: https://www.jessesquires.com/blog/2018/11/17/executing-applescript-in-mac-app-on-macos-mojave/

[^19]: https://forum.c-command.com/t/eaglefiler-hazel-script-integration-import-into-ef-and-let-ef-check-duplicates/12144

[^20]: https://www.macscripter.net/t/applescript-and-sandboxing/63827

[^21]: https://stackoverflow.com/questions/75769490/apple-script-in-gitlabrunner-failing-error-code-600/75810998

[^22]: https://github.com/Hammerspoon/hammerspoon/issues/2031

[^23]: https://www.objc.io/issues/14-mac/sandbox-scripting/

[^24]: https://www.macscripter.net/t/system-events-got-an-error-application-isnt-running/75646

[^25]: https://stackoverflow.com/questions/70548909/how-to-run-applescript-from-c-in-macos-sandbox-environment-without-entitlement/70554738

[^26]: https://eclecticlight.co/2025/03/24/what-are-app-entitlements-and-what-do-they-do/

[^27]: https://www.browserstack.com/guide/accessibility-automation-tools

[^28]: https://app.studyraid.com/en/read/12377/399674/system-events-and-ui-scripting

[^29]: https://www.codebit-inc.com/blog/mastering-file-access-macos-sandboxed-apps/

[^30]: https://www.microsoft.com/en-us/security/blog/2022/07/13/uncovering-a-macos-app-sandbox-escape-vulnerability-a-deep-dive-into-cve-2022-26706/

[^31]: https://dev.to/steady5063/choosing-your-accessibility-ui-testing-library-1o09

[^32]: https://www.macscripter.net/t/system-events-question/46974

[^33]: https://www.reddit.com/r/MacOS/comments/14uqxpv/how_to_grant_accessibility_permissions_when/

[^34]: https://codoid.com/accessibility-testing/top-accessibility-testing-tools-screen-readers-audit-solutions/

[^35]: https://en.wikibooks.org/wiki/AppleScript_Programming/System_Events

[^36]: https://stackoverflow.com/questions/32116095/how-to-use-accessibility-with-sandboxed-app

[^37]: https://github.com/ediblecode/accessibility-resources

[^38]: https://apple.stackexchange.com/questions/271603/how-to-rework-a-system-events-command-in-applescript-so-that-it-automatically

[^39]: https://developer.apple.com/documentation/xcode/configuring-the-macos-app-sandbox

[^40]: https://www.qualitestgroup.com/insights/technical-hub/best-web-accessibility-testing-tools/

[^41]: https://www.reddit.com/r/applescript/comments/ykpinw/macos_ventura_system_settings_with_system_events/

[^42]: https://developer.apple.com/documentation/Security/accessing-files-from-the-macos-app-sandbox

[^43]: https://testguild.com/accessibility-testing-tools-automation/

[^44]: https://docs.nestjs.com/fundamentals/lifecycle-events

[^45]: https://discussions.apple.com/thread/253248516

[^46]: https://www.reddit.com/r/applescript/comments/yhihxe/how_to_setup_command_to_autoquit_app_if_opened/

[^47]: https://loopback.io/doc/en/lb4/Life-cycle.html

[^48]: https://www.macscripter.net/t/system-events-and-the-dock/38511

[^49]: https://docs.aws.amazon.com/opsworks/latest/userguide/workingcookbook-events.html

[^50]: https://www.clouddefense.ai/system-development-life-cycle/

[^51]: https://discussions.apple.com/thread/253552383

[^52]: https://docs.oracle.com/cd/E13222_01/wls/docs92/programming/lifecycle.html

[^53]: https://docs.oracle.com/cd/E24329_01/web.1211/e24368/lifecycle.htm

[^54]: https://discussions.apple.com/thread/1392446

[^55]: https://www.servicenow.com/docs/bundle/yokohama-build-workflows/page/administer/platform-events/concept/events.html

