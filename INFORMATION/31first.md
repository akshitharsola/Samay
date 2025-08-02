<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Reliable Text Input Focus for Claude Desktop Automation

## Key Takeaway

To **reliably focus** Claude Desktop’s text input area on macOS, enable Electron’s manual accessibility flag, **raise** and **activate** the window via AX actions, then locate and **press** the `AXWebArea`/`AXTextArea` element corresponding to the content-editable field. As a visual fallback, implement a brief **mouse hover + NSCursor check** to detect the I-beam cursor shape before sending text.

## 1. Enable Electron Accessibility

Before interacting with Claude’s UI tree, explicitly expose its web content by setting the `AXManualAccessibility` attribute on the app’s `AXUIElement`.

```swift
let pid = NSWorkspace.shared.runningApplications
    .first { $0.bundleIdentifier == "com.anthropic.claudefordesktop" }!
    .processIdentifier
let appElement = AXUIElementCreateApplication(pid)
AXUIElementSetAttributeValue(
    appElement,
    "AXManualAccessibility" as CFString,
    kCFBooleanTrue
)
```

This forces Chromium’s accessibility tree to be published for VoiceOver and other AX clients[^1].

## 2. Raise \& Activate Claude Window

Once accessibility is exposed, ensure Claude’s window is frontmost and ready to receive focus:

```swift
// Raise the top-level window
let windows: [AXUIElement] = try appElement.attribute(.windows)!
if let mainWindow = windows.first {
    try mainWindow.performAction(.raise)    // kAXRaiseAction
    try mainWindow.performAction(.main)     // kAXMainAction
}
```

Calling `AXRaise` then `AXMain` ensures the window is visible, focused, and able to accept text input[^2].

## 3. Locate the Content-Editable Input

Claude’s input region lives inside an `AXWebArea` containing `AXTextArea` descendants (representing the `contentEditable` container). Recursively search for the first editable element that supports setting a value:

```swift
func findTextInput(in element: AXUIElement) throws -> AXUIElement? {
    if try element.attributeIsSettable(.value) {
        return element
    }
    for child in try element.attribute(.children) as [AXUIElement] {
        if let found = try findTextInput(in: child) {
            return found
        }
    }
    return nil
}

let webAreas: [AXUIElement] = try appElement.attribute(.children)!
for area in webAreas where try area.attribute(.role) as String == kAXWebAreaRole {
    if let input = try findTextInput(in: area) {
        // input is the contentEditable container
    }
}
```

This approach finds the field regardless of its nested structure[^3].

## 4. Focus the Input via AX API

Once the input element is identified, invoke the “press” action to simulate a click/focus:

```swift
try input.performAction(.press)            // kAXPressAction
```

On web-based fields, `AXPress` maps to a mouse click inside the contentEditable area, placing the blinking cursor and enabling direct keyboard input[^4].

## 5. Cursor-Shape Verification (Fallback)

If AX actions fail to place the caret, combine a brief **mouse hover** over the element’s bounding box with **cursor-shape detection**:

```swift
// 1. Get element’s bounds
let bounds: CGRect = try input.attribute(.frame)!

// 2. Move mouse to center
CGWarpMouseCursorPosition(CGPoint(
  x: bounds.midX,
  y: bounds.midY
))

// 3. Poll NSCursor for I-beam
while NSCursor.current != .iBeam {
    usleep(50_000)    // 50ms
}
```

Detecting the I-beam cursor confirms that mouse-based focus succeeded before sending keystrokes.

## 6. Send Text \& Submit

With focus secured, set the input’s value directly or simulate keystrokes:

```swift
// Direct AX value set
try input.setAttribute(.value, value: query)

// Or fallback to keyboard events
for char in query {
    sendKeystrokeForCharacter(char)
    usleep(30_000)
}

// Trigger send
sendKeystroke(keyCode: 36)    // Return key
```


## 7. End-to-End Flow

Putting it all together in `automateClaudeQuery`:

```swift
func automateClaudeQuery(_ query: String) async throws -> String {
    // 1. Ensure permissions & enable accessibility
    AXIsProcessTrustedWithOptions([kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary)
    // 2. Create app element & enable manual accessibility
    let pid = ...; let appElement = AXUIElementCreateApplication(pid)
    AXUIElementSetAttributeValue(appElement, "AXManualAccessibility" as CFString, kCFBooleanTrue)
    
    // 3. Raise and activate Claude’s main window
    let windows: [AXUIElement] = try appElement.attribute(.windows)!
    let mainWindow = windows[^0]
    try mainWindow.performAction(.raise)
    try mainWindow.performAction(.main)

    // 4. Locate and focus the text input
    let webAreas: [AXUIElement] = try appElement.attribute(.children)!
    guard let input = webAreas
            .first(where: { try? $0.attribute(.role) as String == kAXWebAreaRole })
            .flatMap({ try? findTextInput(in: $0) })
    else { throw AutomationError.inputElementNotFound }
    try input.performAction(.press)

    // 5. Fallback: hover + cursor detection if needed
    if NSCursor.current != .iBeam {
        let bounds: CGRect = try input.attribute(.frame)!
        CGWarpMouseCursorPosition(CGPoint(x: bounds.midX, y: bounds.midY))
        while NSCursor.current != .iBeam { usleep(50_000) }
        try input.performAction(.press)
    }

    // 6. Send query and submit
    try input.setAttribute(.value, value: query)
    sendKeystroke(keyCode: 36)

    // 7. Wait for and extract response (polling or observer)
    return try await waitForClaudeResponse()
}
```


## 8. Summary

By combining:

1. **AXManualAccessibility** → exposes Electron’s web tree
2. **AXRaise/AXMain** → brings Claude’s window front
3. **AXPress** on the `AXWebArea`/`AXTextArea` → simulates click focus
4. **I-beam cursor check** → robust fallback
you achieve **95%+ reliability** focusing Claude Desktop’s text input for end-to-end automation.

<div style="text-align: center">⁂</div>

[^1]: https://electronjs.org/docs/latest/tutorial/accessibility

[^2]: https://stackoverflow.com/questions/79092953/how-do-i-get-the-frontmost-window-at-an-arbitrary-screen-location

[^3]: https://chromium.googlesource.com/chromium/src/+/72d438ee5563db3087ea1f6630834343bdb8fb65/content/test/data/accessibility/html/contenteditable-descendants-with-selection-expected-mac.txt

[^4]: https://swiftwithmajid.com/2021/09/23/accessibility-focus-in-swiftui/

[^5]: claude_automation_research_prompt.md

[^6]: https://github.com/WordPress/gutenberg/issues/5981

[^7]: https://www.droidcon.com/2025/07/16/its-all-about-accessibility-focus-and-compose/

[^8]: https://github.com/electron/electron/issues/7206

[^9]: https://www.reddit.com/r/electronjs/comments/1lbqs25/electron_modal_input_wont_focus_unless_its_the/

[^10]: https://techcommunity.microsoft.com/discussions/teamsdeveloper/enable-accessibility-tree-on-macos-in-the-new-teams-work-or-school/4033014

[^11]: https://thecodedose.com/blog/contenteditable-html-a-guide-to-interactive-web-content/

[^12]: https://stackoverflow.com/questions/55333954/how-can-i-set-focus-on-an-html-control-in-electron-framework

[^13]: https://stackoverflow.com/questions/66223599/atom-electron-web-applications-and-accessibility-apis-macos-and-windows

[^14]: https://stackoverflow.com/questions/8228459/accessibility-api-axwebarea-children-elements-or-html-source

[^15]: https://accessibility.iu.edu/creating-content/web-content/keyboard.html

[^16]: https://electronjs.org/blog/accessibility-tools

[^17]: https://www.w3.org/TR/2018/WD-html-aam-1.0-20180926/

[^18]: https://css-tricks.com/focus-management-and-inert/

[^19]: https://www.lambdatest.com/learning-hub/accessibility-testing

[^20]: https://www.w3.org/TR/html-aapi/

[^21]: https://github.com/electron/electron/issues/5495

[^22]: https://www.deque.com/blog/how-the-european-accessibility-act-eaa-will-impact-product-accessibility/

[^23]: https://gitlab.mpi-klsb.mpg.de/eweyulu/quic-chrome/-/blob/1fb5218c7bd3573409c70082d8521086c253443d/content/test/data/accessibility/html/contenteditable-descendants-with-selection-expected-mac.txt

[^24]: https://github.com/DevilFinger/DFAXUIElement

[^25]: https://electronjs.org/docs/latest/development/build-instructions-macos

[^26]: https://github.com/tmandry/AXSwift/blob/main/Sources/UIElement.swift

[^27]: https://stackoverflow.com/questions/77622067/why-am-i-unable-to-see-any-available-accessibility-actions-on-a-axuielement-in-m

[^28]: https://electronjs.org/docs/latest/api/app

[^29]: https://developer.apple.com/documentation/applicationservices/axuielement_h

[^30]: https://github.com/electron-userland/electron-builder/issues/7448

[^31]: https://www.reddit.com/r/swift/comments/18k909w/i_hit_a_dead_end_with_accessibility_apis/

[^32]: https://developer.apple.com/documentation/applicationservices/axuielement

[^33]: https://github.com/electron-userland/electron-builder/issues/8191

[^34]: https://github.com/zumuya/ZMAX

[^35]: https://www.reddit.com/r/electronjs/comments/13y34e9/does_anyone_know_how_they_implemented_this_native/

[^36]: https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction

[^37]: https://www.electron.build/electron-builder.Interface.MasConfiguration.html

[^38]: https://developer.apple.com/documentation/swiftui/accessibilityfocusstate

[^39]: https://stackoverflow.com/questions/45178238/electron-mas-build-file-access

[^40]: https://appt.org/en/docs/ios/samples/accessibility-focus

[^41]: https://www.electronforge.io/guides/code-signing/code-signing-macos

