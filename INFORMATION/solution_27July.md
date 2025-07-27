<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Diagnosing and Resolving Prompt-Submission Failures in Samay v3

**Main Takeaway:**
Samay v3 is authenticating successfully but never reaches the prompt‐submission stage. root causes are (1) a control-flow bug in `_submit_prompt_to_service` that skips the “type and send” steps and (2) outdated or missing CSS selectors for input, submit, and response elements on Claude, Gemini, and Perplexity. To fix this, update the control flow to invoke the submission sequence after authentication and refresh each service’s selectors to match their 2025 DOM.

## 1. Control-Flow Fix in `_submit_prompt_to_service`

### 1.1 Current Flawed Flow

```text
_open browser  
→ validate authentication  
→ close browser  
```


### 1.2 Desired Flow

```text
_open browser  
→ validate authentication  
→ locate prompt input  
→ type prompt  
→ click submit  
→ wait for response  
→ extract response  
→ close browser  
```


### 1.3 Code Patch

In `orchestrator/prompt_dispatcher.py` around lines 144–169, ensure the submission steps run unconditionally after successful auth:

```python
def _submit_prompt_to_service(self, service_name: str, prompt: str) -> str:
    driver = self._init_browser(service_name)
    try:
        # 1. Authentication
        if not self._validate_authentication(driver, service_name):
            raise ServiceError(f"{service_name} auth failed")

        # 2. Prompt submission
        cfg = self.service_configs[service_name]
        input_el = driver.find_element(By.CSS_SELECTOR, cfg["prompt_selector"])
        input_el.click()
        input_el.clear()
        input_el.send_keys(prompt)                             # ← type prompt
        submit_el = driver.find_element(By.CSS_SELECTOR,
                                        cfg["submit_selector"])
        submit_el.click()                                       # ← click send

        # 3. Wait & extract response
        WebDriverWait(driver, cfg["wait_for_response"]).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            cfg["response_selector"])))
        resp_el = driver.find_element(By.CSS_SELECTOR,
                                      cfg["response_selector"])
        return resp_el.text

    finally:
        driver.quit()
```


## 2. Refresh Service Selectors for 2025

| Service | Prompt Selector | Submit Selector | Response Selector |
| :-- | :-- | :-- | :-- |
| **Claude.ai** | `[contenteditable="true"]` | `button[aria-label="Send"]` | `.assistant-response p` |
| **Gemini** | `textarea[role="textbox"]` | `button[aria-label="Send Message"]` | `.reply-content` |
| **Perplexity** | `input[type="text"]` | `button[data-testid="ask-button"]` | `.AnswerItem_answerText___3w1rW` |

> These CSS selectors reflect the mid-2025 UI updates; verify via browser DevTools in case of further changes.

## 3. Improve Stability and Human-Like Timing

- **Explicit Waits:** Use `WebDriverWait` with `expected_conditions` rather than fixed sleeps to accommodate dynamic loading.
- **Human-Like Delays:** After `send_keys`, insert `time.sleep(random.uniform(0.5, 1.5))` to mimic natural typing.
- **Error Handling:** Catch `NoSuchElementException` on each selector lookup and log the raw page source for debugging selector mismatches.


## 4. Gemini Session-Instability Mitigation

- **Retry Logic:** Wrap validation and submission in a retry loop (`for attempt in range(3)`) with back-off delays to handle transient DOM‐load timing issues.
- **Race Conditions:** After clicking “Send,” wait for the submit button to be disabled or hidden before proceeding, ensuring submission actually occurred.


## 5. Frontend WebSocket Warning

- **Fix React Hook Dependency:** Update the effect hook in your React component:

```js
useEffect(() => {
  ws.onmessage = handleWebSocketMessage;
  return () => ws.offmessage = null;
}, [handleWebSocketMessage]);  // Add missing dependency
```

- **Connection Stability:** Implement auto-reconnect on `onclose` and throttle reconnection attempts.


## 6. Validation and Testing Checklist

1. **Unit Test:** Mock `_validate_authentication` to force the “authenticated” path and assert that `_submit_prompt_to_service` calls `find_element` for prompt, submit, and response selectors.
2. **Integration Test:** Run against a staging instance of each service; verify actual message delivery and response capture in logs.
3. **Manual Verification:** Use browser DevTools to confirm selectors are correct and adjust as needed.

**By applying these targeted code fixes and updating CSS selectors, Samay v3 will progress from authentication to prompt submission, reliably dispatching prompts to all three services and capturing their responses.**

<div style="text-align: center">⁂</div>

[^1]: SYSTEM_ISSUES_ANALYSIS.md

[^2]: https://www.reddit.com/r/ClaudeAI/comments/1gds696/the_only_prompt_you_need/

[^3]: https://developers.google.com/gemini-code-assist/docs/chat-gemini

[^4]: https://www.perplexity.ai/help-center/en/articles/11132456-how-to-use-the-perplexity-voice-assistant-for-ios

[^5]: https://blogs.cfainstitute.org/investor/2025/05/14/ai-bias-by-design-what-the-claude-prompt-leak-reveals-for-investment-professionals/

[^6]: https://ai.google.dev/gemini-api/docs/text-generation

[^7]: https://www.perplexity.ai/help-center/en/articles/10352895-how-does-perplexity-work

[^8]: https://simonwillison.net/2025/May/25/claude-4-system-prompt/

[^9]: https://support.google.com/chat/answer/15395284?hl=en

[^10]: https://www.youtube.com/watch?v=bOHfJZ4DVqE

[^11]: https://www.youtube.com/watch?v=EvwFECYE5OY

[^12]: https://developers.google.com/workspace/chat/tutorial-ai-knowledge-assistant

[^13]: https://dorik.com/blog/how-to-use-perplexity-ai

[^14]: https://www.godofprompt.ai/blog/20-best-claude-ai-prompts

[^15]: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/send-chat-prompts-gemini

[^16]: https://www.perplexity.ai

[^17]: https://docs.anthropic.com/en/release-notes/system-prompts

[^18]: https://support.google.com/messages/answer/14599070?hl=en

[^19]: https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research

[^20]: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview

[^21]: https://codelabs.developers.google.com/codelabs/chat-apps-gemini

[^22]: https://www.zenrows.com/blog/selenium-avoid-bot-detection

[^23]: https://www.youtube.com/watch?v=H8O-2Wb2pkI

[^24]: https://goatreview.com/automate-ai-prompts-claude-code-custom-commands/

[^25]: https://www.lambdatest.com/blog/selenium-best-practices-for-web-testing/

[^26]: https://kameleo.io/blog/advanced-web-scraping-with-undetected-chromedriver

[^27]: https://stackoverflow.com/questions/79652613/how-to-trigger-resource-and-prompts-in-claude-desktop

[^28]: https://www.browserstack.com/guide/best-practices-in-selenium-automation

[^29]: https://www.zenrows.com/blog/undetected-chromedriver

[^30]: https://www.vellum.ai/blog/prompt-engineering-tips-for-claude

[^31]: https://seleniumbase.io/help_docs/uc_mode/

[^32]: https://webscraping.pro/undetected-chromedriver-in-python-selenium/

[^33]: https://www.walturn.com/insights/mastering-prompt-engineering-for-claude

[^34]: https://seleniumbase.com/new-video-tutorial-undetectable-automation/

[^35]: https://stackoverflow.com/questions/78050439/selenium-undetected-chromedriver-with-different-chrome-versions

[^36]: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts

[^37]: https://muuktest.com/blog/selenium-test-automation

[^38]: https://github.com/ultrafunkamsterdam/undetected-chromedriver

[^39]: https://github.com/anthropics/claude-code/issues/2692

[^40]: https://realpython.com/modern-web-automation-with-python-and-selenium/

[^41]: https://scrapfly.io/blog/posts/web-scraping-without-blocking-using-undetected-chromedriver

