<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Integrating macOS Shortcuts into Swift for AI Service Automation

**Key Recommendation**
Use the built-in `/usr/bin/shortcuts` command-line tool invoked via Swift’s `Process` API, piping its output through `Pipe` to capture JSON or text responses. Pass parameters with `--input-path`/`-i` and retrieve structured output with `--output-path -`/`-o -`. Wrap this in an async/await Swift interface for robust error handling and timeouts.

## 1. Executing Shortcuts via CLI

Apple provides the `shortcuts` tool on macOS for running and managing shortcuts:

```
shortcuts run "<Shortcut Name>" 
    -i  <input-path>         # or --input-path
    -o  -                     # or --output-path -
    --output-type public.json # to specify JSON output UTI
```

- `-i <input-path>`: passes a file or text as input
- `-o -`          : writes the shortcut’s output to **stdout**
- `--output-type <UTI>`: controls data format (e.g. `public.json`, `public.utf8-plain-text`)

When you run this in Terminal, piping captures output:

```bash
shortcuts run "Fetch AI Response" -i prompt.json -o - --output-type public.json | jq .
```


## 2. Swift Wrapper with `Process` and `Pipe`

### 2.1. Basic Function

```swift
import Foundation

enum ShortcutError: Error {
    case notFound, executionFailed(code: Int32, stderr: String)
}

struct Shortcut {
    let name: String

    func run(inputPath: String, outputType: String = "public.json", timeout: TimeInterval = 10) async throws -> String {
        // Prepare the process
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/shortcuts")
        process.arguments = [
            "run", name,
            "-i", inputPath,
            "-o", "-",
            "--output-type", outputType
        ]

        // Capture output & error
        let outPipe = Pipe()
        let errPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError  = errPipe

        // Launch
        try process.run()

        // Timeout handling
        let deadline = Date().addingTimeInterval(timeout)
        while process.isRunning && Date() < deadline {
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        if process.isRunning {
            process.terminate()
            throw ShortcutError.executionFailed(code: -1, stderr: "Timeout")
        }

        // Read stderr
        let errData = errPipe.fileHandleForReading.readDataToEndOfFile()
        if process.terminationStatus != 0 {
            let msg = String(data: errData, encoding: .utf8) ?? "Unknown error"
            throw ShortcutError.executionFailed(code: process.terminationStatus, stderr: msg)
        }

        // Read stdout
        let outData = outPipe.fileHandleForReading.readDataToEndOfFile()
        guard let output = String(data: outData, encoding: .utf8) else {
            throw ShortcutError.executionFailed(code: process.terminationStatus, stderr: "Invalid output encoding")
        }

        return output.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
```


### 2.2. Usage Example

```swift
Task {
    do {
        let shortcut = Shortcut(name: "Fetch AI Response")
        let jsonResponse = try await shortcut.run(inputPath: "/path/to/prompt.json")
        print("Shortcut output:", jsonResponse)
        // Parse JSON as needed
    } catch {
        print("Error running shortcut:", error)
    }
}
```


## 3. Bidirectional Data Flow

- **Input**: Write JSON or text to a temp file, supply its path via `-i`.
- **Output**: Use `-o -` to direct response JSON/text to stdout, read via `Pipe`.
- **Parsing**: Convert the string to a Swift `Data` object and decode with `JSONDecoder` or simple string operations.


## 4. Error Handling \& Timeouts

- Detect nonzero exit codes and capture `stderr` for diagnostics.
- Enforce a configurable timeout; terminate long-running shortcuts.
- Wrap failures in descriptive `Error` enums for uniform handling.


## 5. Performance \& Reliability

- `Process.run()` avoids shell interpolation issues by passing arguments directly.
- Piping avoids opening the Shortcuts GUI; runs headless in background.
- Async polling of `process.isRunning` ensures responsive cancellation.
- Use `--output-type public.json` to standardize JSON formatting across services.


## 6. Summary

By leveraging the **`shortcuts` CLI** within **Swift’s `Process`/`Pipe`** ecosystem, you achieve:

1. **✅ Reliable invocation** of any macOS Shortcut from native Swift code
2. **✅ Bidirectional data flow** via file-based parameters and stdout piping
3. **✅ Structured output capture** (JSON or plain text) for easy parsing
4. **✅ Robust error/time-out handling** to maintain app responsiveness
5. **✅ Consistent performance** and headless execution without GUI side-effects

This approach can serve as a **hybrid automation bridge**, letting **Samay macOS** delegate AI service calls—ChatGPT, Claude web, Gemini, Private Cloud Compute, etc.—to pre-built Shortcuts, while retaining full control and error recovery within your Swift session manager.

<div style="text-align: center">⁂</div>

[^1]: https://stackoverflow.com/questions/72452345/how-can-a-native-macos-app-programmatically-run-a-shortcut-from-apples-shortcut

[^2]: https://github.com/a2/swift-shortcuts

[^3]: https://flower.ai/docs/framework/how-to-use-cli-json-output.html

[^4]: https://forums.swift.org/t/using-swift-for-ios-mac-os-shortcuts/65110

[^5]: https://www.youtube.com/watch?v=a3S8i87Xo5Y

[^6]: https://stackoverflow.com/questions/352098/how-can-i-pretty-print-json-in-a-shell-script

[^7]: https://apple.stackexchange.com/questions/452812/how-to-launch-mac-app-via-ios-shortcuts-app

[^8]: https://stackoverflow.com/questions/71120759/call-the-sirikit-api-to-create-automation-shortcuts

[^9]: https://moldstud.com/articles/p-getting-started-with-aws-cli-a-beginners-tutorial-on-json-output

[^10]: https://stackoverflow.com/questions/78447430/display-siri-shortcuts-programs-in-a-picker-swift-macos

[^11]: https://www.kodeco.com/40950083-creating-shortcuts-with-app-intents

[^12]: https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/

[^13]: https://www.reddit.com/r/shortcuts/comments/118xe5p/running_siri_shortcuts_from_inside_a_macos/

[^14]: https://www.reddit.com/r/shortcuts/comments/v82oiv/is_it_possible_to_make_a_shortcut_run_a_swift_or/

[^15]: https://docs.aws.amazon.com/cli/v1/userguide/cli-usage-output-format.html

[^16]: https://www.macscripter.net/t/run-a-shortcuts-app-shortcut-with-asobjc/75481

[^17]: https://developer.apple.com/shortcuts/

[^18]: https://news.ycombinator.com/item?id=29435786

[^19]: https://support.apple.com/en-in/guide/shortcuts-mac/apd163eb9f95/mac

[^20]: https://swifteducation.github.io/assets/pdfs/XcodeKeyboardShortcuts.pdf

[^21]: https://www.reddit.com/r/shortcuts/comments/kkm1h9/shortcuts_output_to_json_file/

[^22]: https://forum.latenightsw.com/t/example-of-passing-parameters-to-a-shortcut-and-getting-the-return/3395

[^23]: https://osxdaily.com/2022/02/28/run-shortcuts-from-the-command-line-on-mac/

[^24]: https://anotioneer.substack.com/p/using-json-data-in-apple-shortcuts

[^25]: https://www.reddit.com/r/shortcuts/comments/1fun5rw/how_to_i_read_a_json_file/

[^26]: https://www.firehousesoftware.com/webhelp/FHWeb/Content/FHWebAdministratorsGuide/113_UseShortcutParamsMacOSX.htm

[^27]: https://http-shortcuts.rmy.ch/scripting

[^28]: https://talk.automators.fm/t/trouble-grabbing-and-parsing-json-data/17748

[^29]: https://superuser.com/questions/1479444/create-application-shortcut-with-parameters-in-macos

[^30]: https://support.apple.com/en-in/guide/shortcuts/apdde2dfe749/ios

[^31]: https://support.apple.com/en-in/guide/shortcuts/apd0f2e057df/ios

[^32]: https://talk.automators.fm/t/can-i-run-a-terminal-command-via-shortcuts-on-macos/14325

[^33]: https://talk.automators.fm/t/json-data-from-api-output-to-shortcuts-or-textfile-via-scriptable/5291

[^34]: https://apple.stackexchange.com/questions/466912/reading-command-line-arguments-for-shortcut

[^35]: https://support.apple.com/en-in/guide/shortcuts-mac/apd455c82f02/mac

[^36]: https://www.youtube.com/watch?v=TXzrk3b9sKM

[^37]: https://terragrunt.gruntwork.io/docs/reference/cli-options/

[^38]: https://support.apple.com/en-in/guide/terminal/trmlshtcts/mac

[^39]: https://forum.keyboardmaestro.com/t/keyboard-maestro-and-macos-shortcuts-data-transfer-examples/28414

[^40]: https://code.visualstudio.com/shortcuts/keyboard-shortcuts-macos.pdf

[^41]: https://forums.getdrafts.com/t/getting-the-output-of-a-shortcuts-into-drafts-using-scripting/13804

[^42]: https://www.reddit.com/r/shortcuts/comments/qdj478/exporting_shortcuts/

[^43]: https://stackoverflow.com/questions/52786022/shortcut-for-running-terminal-command-in-vs-code

[^44]: https://support.apple.com/guide/shortcuts/shortcut-completion-apda9578f70f/ios

[^45]: https://forums.swift.org/t/swift-run-scripts/18158

[^46]: https://github.com/shortcut-cli/shortcut-cli

[^47]: https://selkie.design/blog/the-shortcut-to-integrating-PCC/

[^48]: https://sixcolors.com/post/2023/01/create-visual-feedback-for-running-shortcuts/

[^49]: https://stackoverflow.com/questions/43836861/how-to-run-a-command-in-visual-studio-code-with-launch-json

[^50]: https://www.reddit.com/r/shortcuts/comments/y31gix/ios_tip_how_the_shortcutsrunshortcut_url_scheme/

[^51]: https://stackoverflow.com/questions/76119211/in-swift-how-do-i-run-the-open-app-action-that-can-be-seen-in-the-shortcuts-a

[^52]: https://support.apple.com/en-om/guide/shortcuts-mac/apd0f2e057df/mac

[^53]: https://forums.swift.org/t/process-run-fails-to-actually-execute-until-parent-process-terminates/54627

[^54]: https://stackoverflow.com/questions/52970040/custom-siri-shortcut-output-a-value-in-shortcuts-app

[^55]: https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac

[^56]: https://developer.apple.com/videos/play/wwdc2025/260/

[^57]: https://httpie.io/docs/cli/json

[^58]: https://stackoverflow.com/questions/29514738/get-terminal-output-after-a-command-swift

[^59]: https://learning.postman.com/docs/postman-cli/postman-cli-options/

[^60]: https://fig.io/manual/shortcuts/run

[^61]: https://eclecticlight.co/2017/01/17/lessons-from-swift-2-processes-running-commands-predicates-playgrounds/

[^62]: https://forums.swift.org/t/xcodebuild-process-output/33042

[^63]: https://arturgruchala.com/asynchronous-process-handling/

[^64]: https://github.com/feedback-assistant/reports/issues/468

[^65]: https://phatbl.at/2019/01/08/intercepting-stdout-in-swift.html

[^66]: https://www.macscripter.net/t/running-a-shell-script-in-a-shortcut/77069

[^67]: https://www.youtube.com/watch?v=zMQMQiVvp0s

[^68]: https://www.reddit.com/r/shortcuts/comments/vv9fxg/write_a_directory_path_as_a_variable/

[^69]: https://discussions.apple.com/thread/255454141

[^70]: https://www.tekramer.com/observing-real-time-ouput-from-shell-commands-in-a-swift-script

[^71]: https://www.reddit.com/r/shortcuts/comments/nw4bqe/macos_beta_command_line_output/

[^72]: https://github.com/sigoden/argc-completions/blob/main/completions/macos/shortcuts.sh

[^73]: https://scriptingosx.com/2023/08/build-a-macos-application-to-run-a-shell-command-with-xcode-and-swiftui-part-2/

[^74]: https://swiftsenpai.com/xcode/top-10-most-useful-xcode-shortcuts-for-navigation/

[^75]: https://rtsw.co.uk/document/swift-cg-keyboard-shortcuts/

[^76]: https://eclecticlight.co/2019/02/02/scripting-in-swift-process-deprecations/

[^77]: https://support.apple.com/en-in/guide/shortcuts/apd9ba41d21b/ios

[^78]: https://github.com/kareman/SwiftShell/blob/master/Sources/SwiftShell/Command.swift

[^79]: https://blog.yudiz.com/creating-and-understanding-siri-shortcut-swift-4-2/

[^80]: https://www.dextronet.com/swift-to-do-list-software/hotkeys

[^81]: https://rderik.com/blog/using-swift-for-scripting/

[^82]: https://support.apple.com/guide/shortcuts/welcome/ios

[^83]: https://www.jessesquires.com/blog/2021/03/18/using-pipes-in-swift-scripts/

[^84]: https://whynotestflight.com/excuses/hello-usd-part-16-swift-just-sipping-openusd-through...-a-pipe/

[^85]: https://coderspacket.com/posts/running-terminal-commands-in-swift-script/

[^86]: https://forums.swift.org/t/can-you-pipe-process-output-on-a-non-standard-stream/71224

[^87]: https://forums.swift.org/t/pipe-child-processes-together/12527

[^88]: https://stackoverflow.com/questions/76914479/read-process-standardoutput-and-standarderror-in-parallel-in-swift-without-block

[^89]: https://www.reddit.com/r/swift/comments/9oz12a/using_process_and_pipe_output_sometimes_output_to/

[^90]: https://developer.apple.com/documentation/foundation/process/standardoutput

[^91]: https://swifttoolkit.dev/posts/pipe

[^92]: https://blog.smittytone.net/2024/09/14/how-to-intercept-stdout-and-stderr-output-in-swift-cli-code/

[^93]: https://stackoverflow.com/questions/41711408/chaining-shell-commands-with-pipe-in-a-swift-script

[^94]: https://swiftpackageindex.com/Zollerboy1/SwiftCommand

[^95]: https://github.com/swiftlang/swift-foundation/blob/main/Proposals/0007-swift-subprocess.md

[^96]: https://www.chrisrcook.com/2022/07/01/leaking-pipes-with-swift-and-external-executables/

[^97]: https://forums.swift.org/t/running-launching-an-existing-executable-program-from-swift-on-macos/47653

[^98]: https://support.apple.com/en-in/guide/shortcuts/apd624386f42/ios

[^99]: https://www.reddit.com/r/swift/comments/9zp4ac/get_running_process_in_macos/

[^100]: https://support.apple.com/en-in/guide/shortcuts/apda283236d7/ios

[^101]: https://www.youtube.com/watch?v=G101ZKyxaIk

[^102]: https://www.reddit.com/r/shortcuts/comments/zymah3/swift_developers_is_it_possible_to_get_a_list_of/

[^103]: https://developer.apple.com/videos/play/wwdc2021/10232/

[^104]: https://stackoverflow.com/questions/36434785/how-do-i-interrogate-the-current-apps-url-scheme-programmatically

[^105]: https://stackoverflow.com/questions/5463998/how-to-programmatically-register-a-custom-url-scheme

[^106]: https://blog.alexbeals.com/posts/reverse-engineering-ios-deeplinking-for-shortcuts

[^107]: https://gist.github.com/deanlyoung/368e274945a6929e0ea77c4eca345560

[^108]: https://gist.github.com/myleshyson/1bf057c2174332d6bcff81448dd8d095

[^109]: https://developer.apple.com/forums/tags/shortcuts?page=2

[^110]: https://developer.apple.com/forums/tags/command-line-tools

[^111]: https://mjtsai.com/blog/2021/06/

[^112]: https://swifttoolkit.dev/posts/command-package

[^113]: https://www.reddit.com/r/shortcuts/comments/11r7nrc/runing_shortcut_via_commandline_and_getting/

[^114]: https://www.educative.io/answers/how-to-file-handle-in-swift-using-filehandler

[^115]: https://talk.macpowerusers.com/t/shortcuts-output-on-the-command-line/29495

[^116]: https://stackoverflow.com/questions/33820746/swift-how-to-read-standard-output-in-a-child-process-without-waiting-for-proces

[^117]: https://github.com/ttscoff/bunch/discussions/241

[^118]: https://developer.apple.com/documentation/foundation/filehandle/readdatatoendoffile()?language=objc

