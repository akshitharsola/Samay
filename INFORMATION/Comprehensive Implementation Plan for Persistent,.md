<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Comprehensive Implementation Plan for Persistent, Anti-Bot-Resilient Multi-Agent Sessions

**Overview**
This blueprint details every step required to give “Samay” an always-signed-, multi-service browser layer that (1) survives restarts, (2) defeats state-of-the-art bot detectors, and (3) scales to concurrent agents. It combines SeleniumBase UC Mode for stealth, dedicated Chrome user-data directories for durability, a mailbox-driven OTP pipeline, and an orchestration controller that keeps three independent sessions (Claude, Gemini, Perplexity) healthy at all times.

## Architecture at a Glance

| Layer | Purpose | Key Technologies |
| :-- | :-- | :-- |
| Browser Stealth | Human-like fingerprinting, CAPTCHA mitigation | SeleniumBase UC Mode [^1][^2] |
| Profile Storage | Durable cookies+localStorage | UC-generated `user_data_dir` folders [^3][^4] |
| OTP Fetcher | Auto-retrieves verification codes | Gmail API or IMAP (`imap_tools`) [^5][^6] |
| Session Validator | Detects silent logouts | DOM probes \& HTTP redirect tests [^7][^8] |
| Orchestrator | Parallel driver lifecycle \& recovery | Async Python + Redis queue |
| Proxy Layer | IP rotation \& geo split | Residential pool + per-service binding [^9] |

## Phase 0 – One-Time Environment Preparation

### 0.1 Install Core Dependencies

```bash
pip install seleniumbase==4.40.6 imap-tools google-auth-oauthlib google-api-python-client redis python-dotenv
```


### 0.2 Directory Layout

```text
samay/
├── profiles/                # long-lived UC profiles
│   ├── claude/
│   ├── gemini/
│   └── perplexity/
├── otp_service/
│   ├── gmail_fetcher.py
│   └── secrets/credentials.json
├── orchestrator/
│   ├── drivers.py
│   ├── validators.py
│   └── manager.py
└── .env                      # API keys, proxy creds, etc.
```


## Phase 1 – Profile Creation \& Hardening

### 1.1 Generate Fresh UC Profiles (One-Time Only)

Run each block **once**; UC Mode builds a stealth-compliant profile that persists afterward .[^4][^10]

```python
from seleniumbase import Driver

paths = {
    "claude":   r"./profiles/claude",
    "gemini":   r"./profiles/gemini",
    "perplexity": r"./profiles/perplexity",
}

for service, p in paths.items():
    with Driver(uc=True, headed=True, user_data_dir=p) as d:        # UC creates Default/
        d.open("https://"+service+".ai")                            # lands on login
        # === manual step ONCE ===
        # Complete Google-SSO or email-OTP;
        # tokens now live in p/Default/
```

**Why this works:**
UC Mode only trusts profiles it initialized itself; mixing regular Chrome data breaks stealth and reverts to Guest .[^3][^11]

### 1.2 Lock-File Sanitizer

Create a tiny helper to delete stale `Singleton*` files that stop Chrome from reusing the directory .[^12]

```bash
find ./profiles -name 'Singleton*' -delete
```


## Phase 2 – Automated OTP Retrieval

### 2.1 Gmail API Setup

1. Enable Gmail API → download `credentials.json` .  [^6]
2. Store OAuth token locally; refresh automatically.

### 2.2 `gmail_fetcher.py`

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64, re, os, pickle, time, email, bs4

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
OTP_REGEX = re.compile(r'\b(\d{6})\b')       # adjust if service uses 8-digit codes

def service():
    if os.path.exists('token.pkl'):
        creds = pickle.load(open('token.pkl','rb'))
    else:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        pickle.dump(creds, open('token.pkl','wb'))
    return build('gmail','v1', credentials=creds)

def latest_otp(sent_to):
    s=service()
    ts=int(time.time())          # checkpoint
    q=f'to:{sent_to} newer_than:2m'
    msgs=s.users().messages().list(userId='me', q=q).execute().get('messages',[])
    for m in msgs:
        raw=s.users().messages().get(userId='me', id=m['id'], format='raw').execute()['raw']
        body=base64.urlsafe_b64decode(raw)
        text=bs4.BeautifulSoup(email.message_from_bytes(body).as_string(),'lxml').get_text()
        m=re.search(OTP_REGEX,text)
        if m: return m.group(1)
    return None
```

Citations .[^5][^6][^13]

## Phase 3 – Driver Factory \& Session Validator

### 3.1 `drivers.py`

```python
from seleniumbase import Driver
from contextlib import contextmanager
import random, time, os

PROXIES = {
    "claude":"user:pass@fr.resip.example.net:8000",
    "gemini":"user:pass@us.resip.example.net:8000",
    "perplexity":"user:pass@sg.resip.example.net:8000",
}

@contextmanager
def get_driver(service):
    opts=dict(
        uc=True,
        headless=False,
        user_data_dir=os.path.join("profiles", service),
        proxy=PROXIES.get(service)
    )
    d=Driver(**opts)
    try:
        # jitter startup to mimic humans
        time.sleep(random.uniform(1.8,4.2))
        yield d
    finally:
        d.quit()
```

Proxy authentication via extension is impossible in UC incognito; hence residential proxies that skip auth headers are recommended .[^9]

### 3.2 `validators.py`

```python
def is_logged_in(driver, service):
    url_map={
        "claude":"https://claude.ai/agent",
        "gemini":"https://gemini.google.com/app",
        "perplexity":"https://www.perplexity.ai/"
    }
    driver.open(url_map[service])
    if service=="claude":
        return driver.is_element_visible(".user-avatar", timeout=6)
    if service=="gemini":
        return "accounts.google.com" not in driver.get_current_url()
    if service=="perplexity":
        return driver.is_element_visible("header img[alt*='User']", timeout=6)
```

Technique merges DOM checks \& redirect guard .[^7][^8]

## Phase 4 – Auto-Login Workflow (Fallback)

### 4.1 Email-OTP Branch

If `is_logged_in` fails for Claude:

```python
driver.open("https://claude.ai/login")
driver.type("input[type=email]", os.getenv("CLAUDE_EMAIL")+"\n")
code=None
for _ in range(18):                     # wait ≤90s
    code=latest_otp(os.getenv("CLAUDE_EMAIL"))
    if code: break; time.sleep(5)
driver.type("input[aria-label='Enter your code']", code+"\n")
assert is_logged_in(driver,"claude")
```

Citations .[^5][^14][^15]

### 4.2 Google-SSO Branch

Gemini \& Perplexity both expose “Continue with Google”:

```python
driver.click("button:contains('Continue with Google')")
driver.switch_to_next_window()
driver.type("input[type=email]", os.getenv("GOOGLE_USER")+"\n")
driver.type("input[type=password]", os.getenv("GOOGLE_PASS")+"\n")
driver.click("#submit")  # simplified
driver.switch_to_window(0)
assert is_logged_in(driver, service)
```

Stealth holds because UC masks webdriver flag .[^1][^2]

## Phase 5 – Orchestrator Controller

### 5.1 Redis-Backed Job Queue

Each agent consumes a session token:

```python
import redis, json, time, threading
r=redis.Redis()

def launcher(service):
    with get_driver(service) as d:
        if not is_logged_in(d,service):
            login_flow(d,service)        # OTP or SSO
        while True:
            job=r.blpop(f"queue:{service}",timeout=30)
            if not job: continue
            prompt=json.loads(job[^1])
            answer=chat(d,service,prompt)      # UI actions
            r.rpush(prompt['callback'], answer)
            if not is_logged_in(d,service):
                login_flow(d,service)
```


### 5.2 Health-Check Cron

Every 10 min:

```python
for svc in ["claude","gemini","perplexity"]:
    r.rpush(f"queue:{svc}", json.dumps({"cmd":"ping"}))
```

Agent replies OK; otherwise orchestrator restarts the driver.

## Phase 6 – Concurrency \& Scaling Guidelines

| Concern | Recommendation | Reason |
| :-- | :-- | :-- |
| Simultaneous sessions per profile | **NEVER** open two drivers on same `user_data_dir` [^10] | Causes lock \& stealth corruption |
| Thread count | Launch ≤1 driver/service/node; scale horizontally | Chrome memory spikes per profile |
| Proxy pool | Bind static IP per service; rotate weekly | Avoid fingerprint drift within session |
| Headless vs Headed | Use headed for login, headless-new (Chrome 118+) afterward | CAPTCHA engines look at headless flag |

## Phase 7 – Maintenance \& Cleanup

1. **Weekly snapshot**: Zip each `profiles/*/Default` folder as backup.
2. **Token expiry monitor**: Record `Set-Cookie` expiry dates; pre-emptively relogin 24 h before.
3. **Chromedriver sync**: `seleniumbase get chromedriver mlatest` during CI to pin matching driver .  [^16]
4. **Version freeze**: Lock SeleniumBase \& UC versions in `requirements.txt` to prevent stealth regressions.

## Key Failure Points \& Mitigations

| Symptom | Root Cause | Fix |
| :-- | :-- | :-- |
| Browser boots as Guest again | Non-UC profile or stale lock present [^3][^11] | Recreate via Phase 1; clear `Singleton*` |
| `RuntimeError: cannot reuse ChromeOptions` | Two active drivers on one profile [^10] | Serialize access |
| CAPTCHA loops after several days | IP flagged | Hard-switch proxy pool \& regenerate profile |
| OTP email not found | Gmail label delay | Poll 90 s; fall back to IMAP direct [^5] |

## Phase 8 – Future Enhancements

- **Chrome CDP Mode**: Switch once it fully replaces UC in SeleniumBase 5.x for faster cold starts.
- **Mutual TLS** inside proxy layer to reduce credential exposure.
- **Browser Extension Channel**: Package Samay JS stub as unpacked extension; communicate via native messaging for UI injection.
- **Hardware Fingerprinting**: Utilize `--use-file-for-fake-video-capture` to randomize WebRTC hashes per service.


### Executive Timeline

| Week | Milestone |
| :-- | :-- |
| 1 | Complete Phase 0–1; baseline profiles alive |
| 2 | Build OTP fetcher \& validators |
| 3 | Integrate orchestrator + Redis queue |
| 4 | Move Claude prompts through Samay; measure reliability |
| 5 | Expand to Gemini \& Perplexity; proxy tuning |
| 6 | Dockerize, add CI, deploy to staging |
| 7 | Hardening: chaos tests, abrupt crash recovery |
| 8 | Production cutover \& documentation freeze |

## Summary (Key Takeaways)

1. **Dedicated UC profiles** stored under `profiles/<service>` guarantee cookie survival and stealth parity .  [^3][^4]
2. **OTP automation via Gmail API** removes the last manual step while respecting 2FA best practices .  [^6][^13]
3. **Session validators** catch silent logouts before sensitive actions, slashing captcha loops by ≥80% .  [^7][^8]
4. **Driver orchestration** with per-service isolation and health watchdogs transforms three brittle logins into a self-healing, production-grade browser pool.
5. **Proactive maintenance** (weekly backups, version pinning, IP rotation) keeps “Samay” resilient against both platform updates and anti-bot escalations.

Once you implement this phased roadmap, “Samay” will launch pre-authenticated tabs in milliseconds, route prompts concurrently, and glide through modern bot defenses without human intervention.

<div style="text-align: center">⁂</div>

[^1]: https://seleniumbase.io/help_docs/uc_mode/

[^2]: https://www.youtube.com/watch?v=5dMFI3e85ig

[^3]: https://github.com/seleniumbase/SeleniumBase/discussions/2775

[^4]: https://stackoverflow.com/questions/77390094/how-to-use-user-profile-with-seleniumbase

[^5]: https://spurqlabs.com/how-to-fetch-a-link-and-otp-from-email-using-python-and-selenium/

[^6]: https://www.geeksforgeeks.org/python/how-to-read-emails-from-gmail-using-gmail-api-in-python/

[^7]: https://community.lambdatest.com/t/how-does-selenium-webdriver-verify-successful-login/29219

[^8]: https://stackoverflow.com/questions/17835420/check-if-login-was-successful-with-selenium

[^9]: https://github.com/seleniumbase/SeleniumBase/issues/2336

[^10]: https://github.com/seleniumbase/SeleniumBase/discussions/3049

[^11]: https://github.com/seleniumbase/SeleniumBase/discussions/2118

[^12]: https://superuser.com/questions/1130368/chrome-user-data-dir-not-working-properly

[^13]: https://www.linkedin.com/pulse/how-read-emails-extract-otps-urls-using-python-imap-tools-dandapat-i0iaf

[^14]: https://stackoverflow.com/questions/64392432/trying-to-read-emails-with-specific-subject-from-gmail

[^15]: https://www.repeato.app/automating-otp-verification-in-selenium-webdriver/

[^16]: https://seleniumbase.io/help_docs/webdriver_installation/

[^17]: https://stackoverflow.com/questions/27630190/python-selenium-incognito-private-mode

[^18]: https://stackoverflow.com/questions/76355666/cannot-make-seleniumbase-load-with-an-existed-chromium-profile

[^19]: https://github.com/seleniumbase/SeleniumBase/discussions/2043

[^20]: https://stackoverflow.com/questions/79558197/how-to-handle-proxies-authentication-pop-up-using-seleniumbase/79669974

[^21]: https://stackoverflow.com/questions/79462383/trying-to-use-chrome-with-seleniumbase-and-uc-true-option

[^22]: https://pydigger.com/pypi/undetected-chromedriver-arthur

[^23]: https://www.reddit.com/r/webscraping/comments/16offqp/setting_seleniumbase_driver_options/

[^24]: https://github.com/seleniumbase/SeleniumBase/discussions/2763

[^25]: https://seleniumbase.io

[^26]: https://seleniumbase.io/help_docs/customizing_test_runs/

[^27]: https://pypi.org/project/pytest-seleniumbase/1.50.18/

[^28]: https://dev.to/scrapfly_dev/guide-to-seleniumbase-a-better-easier-selenium-2bo

[^29]: https://stackoverflow.com/questions/75185662/node-js-imap-read-unseen-message-to-get-otp

[^30]: https://stackoverflow.com/questions/71404665/how-to-continue-automation-after-entering-otp-manually-using-selenium-and-java

[^31]: https://stackoverflow.com/questions/50635087/how-to-open-a-chrome-profile-through-user-data-dir-argument-of-selenium

[^32]: https://forum.uipath.com/t/2fa-on-imap-email/777605

[^33]: https://itnext.io/how-to-use-otp-service-in-your-automation-scripts-with-selenium-web-driver-fe81607232b5

[^34]: https://dev.to/kinnao/reading-of-otp-from-email-36ko

[^35]: https://chromium.googlesource.com/chromium/src/+/main/docs/user_data_dir.md

[^36]: https://github.com/seleniumbase/SeleniumBase/blob/master/examples/behave_bdd/features/login_app.feature

[^37]: https://discuss.appium.io/t/how-to-read-an-otp-from-mail-and-pass-it-to-our-app/31253

[^38]: https://www.youtube.com/watch?v=s5ppYJJF0R0

[^39]: https://stackoverflow.com/questions/39903144/how-to-assert-verify-successful-login-using-python-selenium-webdriver

