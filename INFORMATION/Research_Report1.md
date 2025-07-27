<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Automating Browser-Based AI Chat Interfaces with SeleniumBase UC Mode

**Main Takeaway:** Enhance `web_agent_dispatcher.py` to replace mock logic with real SeleniumBase UC Mode automation, programmatic chat interactions with Claude, Gemini, and Perplexity while preserving stealth, session persistence, and robust error handling.

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────┐
│              web_agent_dispatcher.py            │
├──────────────────────────────────────────────────┤
│ • load_profile(service_name) → WebDriver        │
│ • send_message(driver, service, message)        │
│ • capture_streaming_response(driver, service)   │
│ • parse_and_validate(response)                  │
│ • retry_on_failure(fn, retries, backoff)        │
└──────────────────────────────────────────────────┘
           ↑                    ↑
           │ uses               │ uses
┌─────────────────┐      ┌─────────────────────────┐
│    drivers.py   │◄─────┤ SeleniumBase UC Mode    │
│ • profile paths │      │ • Stealth UC Mode flags │
│ • session reuse │      │ • Anti-bot evasion      │
└─────────────────┘      └─────────────────────────┘
```


## 2. Step-by-Step Enhancement Plan

### 2.1 Load and Reuse Logged-In Profiles

1. In `drivers.py`, ensure each service (Claude, Gemini, Perplexity) has a distinct UC Mode profile directory.
2. In `web_agent_dispatcher.py`, implement:

```python
from drivers import get_uc_driver

def load_profile(service_name: str):
    return get_uc_driver(service_name)  # returns SeleniumBase UC Mode WebDriver
```


### 2.2 Sending Messages Programmatically

1. Identify the chat input selector for each service (e.g., `textarea`, `div[contenteditable]`).
2. Implement a generic method:

```python
def send_message(driver, service: str, message: str):
    input_el = driver.wait_for_element(f"{service}_input_selector")
    for char in message:
        input_el.send_keys(char)
        sleep(random.uniform(0.05, 0.15))  # human-like typing
    input_el.send_keys(Keys.ENTER)
```


### 2.3 Capturing Streaming Responses

1. Determine the dynamic container that receives tokens in real time.
2. Implement polling or subscription to WebSocket/SSE:

```python
def capture_streaming_response(driver, service: str) -> str:
    response = ""
    while not driver.element_contains(f"{service}_end_of_response_marker"):
        new_chunks = driver.find_elements(f"{service}_token_selector")
        response = "".join([chunk.text for chunk in new_chunks])
        sleep(0.1)
    return response
```


### 2.4 Parsing and Quality Verification

1. Define service-specific JSON schema or validation rules.
2. Use Python’s `json` module or regex to parse:

```python
def parse_and_validate(raw: str, schema: dict) -> dict:
    try:
        data = json.loads(raw)
        validate(data, schema)  # raise if invalid
        return data
    except Exception:
        raise ValueError("Invalid response format")
```


### 2.5 Retry and Error Handling

1. Wrap critical operations in a retry decorator:

```python
def retry_on_failure(fn, retries=3, backoff=2):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            sleep(backoff ** attempt)
    raise RuntimeError(f"{fn.__name__} failed after {retries} retries")
```

2. Apply to `send_message`, `capture_streaming_response`, and `parse_and_validate`.

## 3. Human-Like Interaction Patterns

- **Typing Delays:** Randomize keystroke intervals (0.05–0.2 s).
- **Mouse Movements:** Use `driver.move_to_element()` with small offsets and pauses.
- **Scroll Behavior:** Periodically scroll the chat container:

```python
driver.execute_script("arguments[^0].scrollTop += arguments[^0].scrollHeight*0.1", chat_container)
```

- **Idle Pauses:** Insert small random pauses (0.5–2 s) between actions.


## 4. Session Management and Stealth

- **Persistent Cookies \& Local Storage:** Profiles loaded via UC Mode already preserve cookies, bypassing anti-bot login checks.
- **Headed vs. Headless:** Use headed mode in development; switch to headless with UC Mode flags in production for performance.
- **Rate-Limit Awareness:** Track message timestamps per service and throttle to stay below documented limits (e.g., ≤1 msg/5 s).


## 5. Implementation Outline for `web_agent_dispatcher.py`

```python
from drivers import get_uc_driver
from selenium.webdriver.common.keys import Keys
import time, random, json
from jsonschema import validate

SERVICE_SELECTORS = {
   "claude": { "input": "#claude-input", "token": ".claude-token", "end": ".claude-end" },
   # similarly for gemini, perplexity
}

def retry(fn):
   def wrapper(*args, **kwargs):
       return retry_on_failure(lambda: fn(*args, **kwargs))
   return wrapper

@retry
def send_message(driver, service, message):
   sel = SERVICE_SELECTORS[service]["input"]
   input_el = driver.wait_for_element(sel)
   for c in message:
       input_el.send_keys(c)
       time.sleep(random.uniform(0.05, 0.15))
   input_el.send_keys(Keys.ENTER)

@retry
def capture_streaming_response(driver, service):
   sel_token = SERVICE_SELECTORS[service]["token"]
   sel_end = SERVICE_SELECTORS[service]["end"]
   response = ""
   while not driver.is_element_present(sel_end):
       chunks = driver.find_elements(sel_token)
       response = "".join([c.text for c in chunks])
       time.sleep(0.1)
   return response

def parse_and_validate(raw, schema):
   data = json.loads(raw)
   validate(instance=data, schema=schema)
   return data

def chat_with_service(service, message, schema):
   driver = get_uc_driver(service)
   send_message(driver, service, message)
   raw = capture_streaming_response(driver, service)
   return parse_and_validate(raw, schema)
```


## 6. Testing \& Validation

1. **Unit Tests:** Mock page elements to simulate responses and timeouts.
2. **Integration Tests:** Run end-to-end chat session against a test account.
3. **Load Tests:** Send bursts of messages to ensure rate limiting and retry logic function correctly.

By following this enhancement plan, `web_agent_dispatcher.py` will orchestrate genuine, human-like chat sessions on Claude, Gemini, and Perplexity—leveraging existing SeleniumBase UC Mode profiles, capturing streaming responses reliably, and maintaining stealth without any API calls.

<div style="text-align: center">⁂</div>

[^1]: https://www.browserstack.com/guide/selenium-stealth

[^2]: https://www.zenrows.com/blog/playwright-stealth

[^3]: https://www.reddit.com/r/webscraping/comments/mo11x8/is_there_anything_for_python_that_compares_to/

[^4]: https://www.zenrows.com/blog/selenium-avoid-bot-detection

[^5]: https://dev.to/hasdata_com/nodejs-playwright-stealth-bypass-cloudflare-1020-in-5-minutes-3e03

[^6]: https://scrapingant.com/blog/javascript-detection-avoidance-libraries

[^7]: https://iproyal.com/blog/selenium-stealth-python-tutorial/

[^8]: https://scrapeops.io/playwright-web-scraping-playbook/nodejs-playwright-make-playwright-undetectable/

[^9]: https://webscraping.fyi/lib/compare/javascript-puppeteer-stealth-vs-python-undetected-chromedriver/

[^10]: https://www.zenrows.com/blog/selenium-stealth

[^11]: https://pypi.org/project/playwright-stealth/

[^12]: https://github.com/omkarcloud/botasaurus-vs-undetected-chromedriver-vs-puppeteer-stealth-benchmarks

[^13]: https://scrapeops.io/selenium-web-scraping-playbook/python-selenium-make-selenium-undetectable/

[^14]: https://mcpmarket.com/server/stealth-browser

[^15]: https://www.zenrows.com/alternative/puppeteer

[^16]: https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/

[^17]: https://brightdata.com/blog/how-tos/avoid-bot-detection-with-playwright-stealth

[^18]: https://www.scrapingdog.com/blog/puppeteer-stealth/

[^19]: https://stackoverflow.com/questions/75632071/how-to-make-python-selenium-less-detectable

[^20]: https://github.com/pvinis/mcp-playwright-stealth

