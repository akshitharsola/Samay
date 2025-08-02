<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Native macOS App: The Definitive Migration Plan

**Main Recommendation:** Adopt a **Swift + SwiftUI** menu-bar application architecture to eliminate Python environment issues, leverage native mac automation APIs, and deliver a professional, App Store-ready user experience.

## 1. Core Technical Architecture

1. **Menu Bar Host**
    - Use SwiftUI’s `MenuBarExtra` scene for a lightweight, always-available UI.
    - Hide Dock icon via `LSUIElement` in Info.plist to operate as a background utility.
2. **Service Managers**
    - Define an `AIServiceManager` protocol for launch, detection, query, and close operations.
    - Implement concrete managers (e.g., `ClaudeManager`, `PerplexityManager`) using `NSWorkspace` for app control and OSAKit for AppleScript automation.
3. **Accessibility \& Permissions**
    - Request Accessibility permissions with `AXIsProcessTrustedWithOptions`.
    - Use native **NSAccessibility** APIs for more robust control than AppleScript alone.
4. **Response Processing**
    - Implement a Swift `ResponseProcessor` that:
        - Uses `NSRegularExpression` to extract JSON code blocks.
        - Decodes with `JSONDecoder` into a `ProcessedResponse` struct (`content`, `summary`, `keyPoints`, `confidence`).
5. **Query Orchestrator**
    - Build a central `QueryOrchestrator` class using Swift `async/await` for:

6. Detecting installed AI apps
7. Launching and automating queries
8. Parallel execution via `TaskGroup` for multi-service coordination
9. Synthesizing and returning a unified response

## 2. Development Roadmap

| Phase | Duration | Deliverables |
| :-- | :-- | :-- |
| **Phase 1: Core Infrastructure** | 1–2 weeks | -  Xcode SwiftUI menu-bar project<br>-  App detection + launch<br>-  Basic AppleScript automation<br>-  JSON extraction in Swift |
| **Phase 2: AI Service Integration** | 2–3 weeks | -  Claude \& Perplexity native automators<br>-  Asynchronous query flow<br>-  Single-service query UI |
| **Phase 3: Response Processing** | 1 week | -  Machine-code template handling<br>-  JSON parsing<br>-  Response history caching |
| **Phase 4: Advanced Features** | 2–3 weeks | -  Parallel multi-service queries<br>-  Response synthesis algorithms<br>-  Quality scoring |
| **Phase 5: Polish \& Distribution** | 1–2 weeks | -  System notifications<br>-  Hotkey support<br>-  Settings panel<br>-  Code signing \& notarization |

## 3. Priority Feature Migration

| Priority | Feature | Swift Approach |
| :-- | :-- | :-- |
| **🚨 P1** | Desktop App Detection \& Control | `NSWorkspace.shared.urlForApplication(withBundleIdentifier:)` |
| **🚨 P1** | Claude-Specific Workaround | AppleScript sequences via OSAKit, wrapped in Swift `async` functions |
| **🚨 P1** | Machine Code JSON Extraction | `NSRegularExpression` + `JSONDecoder` |
| **🟡 P2** | Multi-Service Concurrency | Swift structured concurrency (`TaskGroup`) |
| **🟡 P2** | Response Synthesis | Combine `ProcessedResponse` objects, deduplicate, consensus logic |
| **🟡 P2** | AppleScript Automation | `OSAScript` execution with proper entitlements |
| **🟢 P3** | Configuration Management | `UserDefaults` or property lists |
| **🟢 P3** | Health Monitoring \& Logging | Background checks, `os.log` for structured diagnostics |

## 4. Research Prompts for Deep Dives

1. **Technical Architecture Research**
“Investigate best practices for macOS menu bar apps using SwiftUI and AppKit, focusing on NSAccessibility integration, AppleScript via OSAKit, and coordinating multiple AI services asynchronously.”
2. **User Experience Research**
“Analyze leading AI-assistant menu bar apps on macOS for UI patterns, hotkey strategies, notification timing, and workflow integration to optimize Samay’s UX.”
3. **Performance \& Distribution Research**
“Benchmark native Swift UI/AppleScript automation performance versus Python on macOS, and outline App Store distribution requirements including sandboxing, code signing, and notarization for AI automation apps.”
4. **Migration Strategy Research**
“Compile hybrid migration patterns for desktop automation from Python to Swift: component-by-component porting, maintaining dual-environment testing, and ensuring feature parity.”

## 5. Immediate Action Plan

1. **Quick Prototype (2–3 days)**
    - Create SwiftUI menu-bar app skeleton with `MenuBarExtra`.
    - Implement simple “Hello, world” popover and quit button.
2. **Core Migration (1 week)**
    - Port desktop app detection and basic AppleScript execution.
    - Validate Claude fullscreen workaround in Swift.
3. **Service Integration (1 week)**
    - Build `ClaudeManager` and `PerplexityManager` with native automation.
    - Expose a simple SwiftUI view for sending prompts and displaying raw responses.
4. **Performance Test (2–3 days)**
    - Measure query latency and memory usage against Python version.
    - Iterate on AppleScript timing and Accessibility calls.
5. **Full Migration Decision (1 day)**
    - Review prototype stability, performance, and UX.
    - Plan full rollout or hybrid continuation.

**By prioritizing critical automation features and leveraging Swift’s native APIs, this plan ensures a smooth transition off Python’s dependency complexities, delivering a performant, maintainable, and professional macOS application.**

<div style="text-align: center">⁂</div>

[^1]: NATIVE_MACOS_APP_RESEARCH.md

[^2]: https://danielsaidi.com/blog/2023/11/22/customizing-the-macos-menu-bar-in-swiftui

[^3]: https://stackoverflow.com/questions/68305958/creating-a-macos-windowless-menu-bar-application-with-swiftui

[^4]: https://developer.apple.com/videos/play/wwdc2022/10075/

[^5]: https://www.youtube.com/watch?v=568mNVqFx-I

[^6]: https://developer.apple.com/videos/play/wwdc2021/10119/

[^7]: https://www.reddit.com/r/swift/comments/1hy6puo/apple_script_in_swiftui_software/

[^8]: https://nilcoalescing.com/blog/BuildAMacOSMenuBarUtilityInSwiftUI

[^9]: https://developer.apple.com/documentation/appkit/nsaccessibility-swift.struct/attribute/menubar

[^10]: https://stackoverflow.com/questions/61988694/how-to-run-applescript-from-inside-a-swiftui-view

[^11]: https://steipete.me/posts/2025/showing-settings-from-macos-menu-bar-items

[^12]: https://developer.apple.com/documentation/appkit/nsaccessibility-swift.struct/attribute/menubar?changes=_9

[^13]: https://spin.atomicobject.com/swift-automator-workflows/

[^14]: https://www.kodeco.com/books/macos-by-tutorials/v1.0/chapters/3-adding-menus-toolbars

[^15]: https://www.createwithswift.com/creating-and-customizing-the-menu-bar-of-a-swiftui-app/

[^16]: https://forum.latenightsw.com/t/integrate-applescript-into-a-swift-app/4674

[^17]: https://capgemini.github.io/development/macos-development-with-swift/

[^18]: https://www.youtube.com/watch?v=d4qwt3zcLvA

[^19]: https://www.macscripter.net/t/swift-scripting/75639

[^20]: https://www.youtube.com/watch?v=CuMLpnjPr2Y

[^21]: https://kyan.com/news/using-swift-swiftui-to-build-a-modern-macos-menu-bar-app

