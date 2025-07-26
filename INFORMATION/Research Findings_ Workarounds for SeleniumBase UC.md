<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Research Findings: Workarounds for SeleniumBase UC Mode Profile Persistence

**Main Takeaway:**
To achieve true Chrome profile persistence **and** maintain anti-bot stealth, you must decouple handling from UC Mode. Three viable approaches emerged:

1. **Direct undetected-chromedriver** for login/profile creation, then
2. **SeleniumBase Standard Mode + Selenium-Stealth** for session reuse, or
3. **Hybrid pipeline**: initial UC Mode login → export cookies/localStorage → reload via standard SeleniumBase with `--user-data-dir`.

## 1. Direct undetected-chromedriver Integration

**Why:** Bypasses UC Mode’s forced temporary profiles and incognito flags.
**Key Points:**

- Use `uc.ChromeOptions()` with explicit `user_data_dir` and `profile-directory` arguments.
- Avoid UC Mode; instantiate driver directly:

```python
import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument(r"--user-data-dir=C:\chrome_profiles\claude")
options.add_argument(r"--profile-directory=Default")
driver = uc.Chrome(options=options, use_subprocess=False)
driver.get("https://claude.ai")
# Perform login via Google SSO
# After successful login, cookies/localStorage are persisted in C:\chrome_profiles\claude\Default
```

**Notes:**

- Must close all other Chrome instances using that profile to avoid “directory in use” errors.[^1]
- Some reported issues (\#1232) override the folder to a temp path—workaround is to pin `use_subprocess=False` and avoid mixing with UC Mode internals.[^2]


## 2. SeleniumBase Standard Mode + Selenium-Stealth

**Why:** Leverages SeleniumBase ecosystem and PyTest integration, while using Selenium-Stealth for anti-bot evasion without UC Mode’s profile restrictions.

**Implementation:**

1. Install plugins:

```bash
pip install seleniumbase selenium-stealth
```

2. Create a customized BaseCase:

```python
from seleniumbase import BaseCase
from selenium_stealth import stealth

class StealthTest(BaseCase):
    def setUp(self):
        super().setUp()
        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    def test_with_profile(self):
        # Load pre-authenticated profile
        self.driver.get("https://claude.ai")
        # Stealth actions...
```

3. Launch with profile persistence:

```bash
pytest --browser=chrome --user-data-dir=C:\chrome_profiles\claude tests/stealth_test.py
```


**Benefits:**

- Real Chrome profile usage.
- Uses Selenium-Stealth evasion modules.[^3]
- Full SeleniumBase features (reporting, fixtures, parallelization).


## 3. Hybrid Approach: UC Mode for Login, Standard Mode for Persistence

**Why:** Combines UC Mode’s superior CAPTCHA bypass for initial login, then switches to persistent profile environment.

**Workflow:**

1. **UC Mode Authentication**

```python
from seleniumbase import SB
with SB(uc=True, incognito=True) as sb:
    sb.open("https://claude.ai")
    sb.click("button:contains('Continue with Google')")
    # Automate Google SSO button click + OTP if needed
    sb.get_cookies()
    with open("claude_cookies.json","w") as f: json.dump(sb.get_cookies(),f)
    sb.disconnect()
```

2. **Profile Pre-Warming**
    - Use a one-time script with undetected-chromedriver to load cookies/localStorage into `C:\chrome_profiles\claude`.
3. **Standard SeleniumBase Session**

```python
from seleniumbase import SB
with SB(browser="chrome", user_data_dir="C:\\chrome_profiles\\claude") as sb:
    sb.open("https://claude.ai")
    sb.assert_element("div.user-avatar")
    # Continue interactions
```


**Key Techniques:**

- **Cookie \& LocalStorage Sync**: Save both after UC Mode login and restore before standard runs[session persistence guide].
- **Behavioral Mimicking**: Randomized delays, human-like mouse movements.


## 4. Profile Pre-warming Strategy

1. **Manual Pre-Authentication**
    - Launch Chrome manually with desired profile; log in once.
2. **Automated Loading \& Freezing**
    - Use direct undetected-chromedriver to point at that profile, then quit.
3. **Subsequent Runs**
    - Standard SeleniumBase uses the same folder; profile is already authenticated.
```shell
# Pre-warm:
python prewarm.py
# Then regular runs:
pytest --browser=chrome --user-data-dir=C:\chrome_profiles\claude tests/
```


## 5. Production Alternatives \& Cost-Benefit Analysis

| Approach | Pros | Cons |
| :-- | :-- | :-- |
| Direct undetected-chromedriver | True profile support; UC-level stealth | Manual porting of SeleniumBase features |
| SeleniumBase + Selenium-Stealth | Full framework integration; persistent profiles | Slightly weaker vs. UC Mode CAPTCHAs |
| Hybrid (UC Mode → Standard) | Best of both; UC Mode bypass + persistence | More complex orchestration |

**Professional Services:**
Consider **ZenRows**, **ScrapingBee**, or **Bright Data** for managed proxy \& session persistence if in-house complexity outweighs cost benefits.

**Recommendation:**
For an **internal** solution, adopt the **Hybrid Approach**: automate initial Google SSO via UC Mode, export cookies/localStorage, then run standard SeleniumBase with `--user-data-dir` pointing to the pre-warmed profile. This maintains maximum stealth while ensuring real profile persistence.

<div style="text-align: center">⁂</div>

[^1]: https://stackoverflow.com/questions/50635087/how-to-open-a-chrome-profile-through-user-data-dir-argument-of-selenium

[^2]: https://stackoverflow.com/questions/73838436/why-cant-i-connect-to-chrome-when-using-the-undetected-chromedriver

[^3]: https://github.com/seleniumbase/SeleniumBase/issues/2404

[^4]: https://github.com/ultrafunkamsterdam/undetected-chromedriver/discussions/1101

[^5]: https://seleniumbase.io/help_docs/uc_mode/

[^6]: https://stackoverflow.com/questions/74981809/im-using-selenium-undetected-chromedriver-and-i-cant-open-multiple-profiles-at

[^7]: https://www.zenrows.com/blog/selenium-avoid-bot-detection

[^8]: https://github.com/seleniumbase/SeleniumBase/issues/2336

[^9]: https://superuser.com/questions/1130368/chrome-user-data-dir-not-working-properly

[^10]: https://www.reddit.com/r/webscraping/comments/1jbwz6v/the_library_i_built_because_i_enjoy_selenium/

[^11]: https://stackoverflow.com/questions/76444662/how-can-i-use-undetected-chromedriver-to-init-function

[^12]: https://stackoverflow.com/questions/72073046/targetting-chrome-profile-in-selenium/72077446

[^13]: https://www.zenrows.com/blog/undetected-chromedriver-vs-selenium-stealth

[^14]: https://brightdata.com/blog/web-data/web-scraping-with-seleniumbase

[^15]: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1150

[^16]: https://www.browserstack.com/guide/selenium-stealth

[^17]: https://www.youtube.com/watch?v=2pTpBtaE7SQ

[^18]: https://www.zenrows.com/blog/undetected-chromedriver

[^19]: https://seleniumbase.io

[^20]: https://seleniumbase.io/help_docs/method_summary/

[^21]: https://www.youtube.com/watch?v=6SDzRN1aHiI

[^22]: https://seleniumbase.io/help_docs/customizing_test_runs/

[^23]: https://github.com/seleniumbase/SeleniumBase/discussions/2763

[^24]: https://www.microfocus.com/documentation/silk-test/205/en/silktestclassic-help-en/GUID-60416FD0-B58B-444D-8BF4-68336CEFA909.html

[^25]: https://chromium.googlesource.com/chromium/src/+/main/docs/user_data_dir.md

[^26]: https://chromium.googlesource.com/experimental/chromium/src/+/refs/heads/lkgr-ios-internal/docs/user_data_dir.md

[^27]: https://www.youtube.com/watch?v=5dMFI3e85ig

[^28]: https://github.com/seleniumbase/SeleniumBase/discussions/2856

[^29]: https://seleniumbase.io/help_docs/features_list/

[^30]: https://scrapeops.io/selenium-web-scraping-playbook/python-selenium-stealth-web-scraping/

[^31]: https://github.com/seleniumbase/SeleniumBase/discussions/2118

[^32]: https://github.com/seleniumbase/SeleniumBase/discussions/3049

[^33]: https://www.chromium.org/developers/creating-and-using-profiles/

[^34]: https://pypi.org/project/undetected-chromedriver/

[^35]: https://groups.google.com/g/chromedriver-users/c/10tDMX0b8mA

[^36]: https://stackoverflow.com/questions/79426051/why-my-profil-is-not-loaded-with-undetected-chrome-driver

[^37]: https://www.zenrows.com/blog/selenium-stealth

[^38]: https://seleniumbase.io/help_docs/recorder_mode/

[^39]: https://python-forum.io/thread-39745.html

[^40]: https://thedispatch.ai/reports/3217/

[^41]: https://github.com/seleniumbase/SeleniumBase/discussions/1221

[^42]: https://www.scrapingbee.com/blog/undetected-chromedriver-python-tutorial-avoiding-bot-detection/

[^43]: https://seleniumbase.com/recorder_mode/

[^44]: https://github.com/kaliiiiiiiiii/Selenium-Profiles

[^45]: https://www.reddit.com/r/learnpython/comments/1b5nr7j/opening_chrome_with_a_specific_profile_using/

[^46]: https://stackoverflow.com/questions/52394408/how-to-use-chrome-profile-in-selenium-webdriver-python-3

[^47]: https://stackoverflow.com/questions/75714486/undetected-chromedriver-alternative

[^48]: https://sqa.stackexchange.com/questions/2755/handling-browser-level-authentication-using-selenium

[^49]: https://www.youtube.com/watch?v=-EpZlhGWo9k\&vl=en

[^50]: https://www.neovasolutions.com/2024/06/13/automating-chrome-with-existing-profiles-using-playwright-and-typescript/

[^51]: https://stackoverflow.com/questions/76355666/cannot-make-seleniumbase-load-with-an-existed-chromium-profile

[^52]: https://www.selenium.dev/documentation/webdriver/drivers/options/

[^53]: https://github.com/seleniumbase/SeleniumBase/issues/2213

[^54]: https://toolsqa.com/selenium-webdriver/run-selenium-tests-on-chrome/

[^55]: https://github.com/seleniumbase/SeleniumBase/discussions/2536

[^56]: https://www.lambdatest.com/blog/python-selenium-with-chrome/

[^57]: https://www.reddit.com/r/webscraping/comments/16offqp/setting_seleniumbase_driver_options/

[^58]: https://www.selenium.dev/documentation/webdriver/drivers/

[^59]: https://seleniumbase.com/new-video-undetectable-automation-2-with-uc-mode-and-python/

[^60]: https://groups.google.com/g/selenium-users/c/caHDBDyyRYY/m/dkKcCFCsBgAJ

[^61]: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1670

[^62]: https://stackoverflow.com/questions/77191221/undetected-chromedriver-attributeerror-chromeoptions-object-has-no-attribute

[^63]: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1232

[^64]: https://pypi.org/project/undetected-chromedriver/2.1.1/

[^65]: https://pydigger.com/pypi/undetected-chromedriver-arthur

[^66]: https://brightdata.com/blog/web-data/web-scraping-with-undetected-chromedriver

[^67]: https://www.youtube.com/watch?v=H8O-2Wb2pkI

[^68]: https://www.blackhatworld.com/seo/evading-selenium-detection-the-ultimate-guide.1569690/

[^69]: https://app.soos.io/research/packages/Python/-/st-undetected-chromedriver

[^70]: https://cloud.tencent.com/developer/ask/sof/107316572

[^71]: https://github.com/seleniumbase/SeleniumBase/discussions/2775

[^72]: https://stackoverflow.com/questions/77907712/how-to-avoid-selenium-detection-or-change-approach

[^73]: https://github.com/seleniumbase/SeleniumBase

[^74]: https://github.com/seleniumbase/SeleniumBase/discussions/2482

[^75]: https://stackoverflow.com/questions/66209119/automation-google-login-with-python-and-selenium-shows-this-browser-or-app-may

[^76]: https://seleniumbase.io/examples/cdp_mode/ReadMe/

[^77]: https://issues.ecosyste.ms/hosts/GitHub/repositories/seleniumbase%2FSeleniumBase/issues?page=2\&per_page=100

[^78]: https://yashaka.github.io/selene/faq/custom-user-profile-howto/

[^79]: https://www.educative.io/answers/how-to-use-a-specific-chrome-profile-in-python-selenium

[^80]: https://developer.chrome.com/docs/chromedriver/capabilities

[^81]: https://www.zenrows.com/blog/undetected-chromedriver-proxy

[^82]: https://stackoverflow.com/questions/68289474/selenium-headless-how-to-bypass-cloudflare-detection-using-selenium

[^83]: https://automation-help.com/selenium-web-driver-chrome-profile-in-python/

[^84]: https://github.com/ultrafunkamsterdam/undetected-chromedriver

[^85]: https://pydigger.com/pypi/seleniumbase

[^86]: https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver

[^87]: https://scrapfly.io/blog/posts/web-scraping-without-blocking-using-undetected-chromedriver

[^88]: https://rebrowser.net/blog/undetected-chromedriver-the-ultimate-guide-to-bypassing-bot-detection

[^89]: https://www.reddit.com/r/Heroku/comments/1imrtas/need_help_with_selenium_on_heroku_session_not/

[^90]: https://stackoverflow.com/questions/64387126/python-selenium-chrome-user-data-directory-is-already-in-use/70443995

[^91]: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1667

