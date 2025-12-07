import sys
import os
import argparse
import time
import random
import json

def run_uc_task(url: str, output_path: str, action: str = "content"):
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        
        options = uc.ChromeOptions()
        # options.add_argument('--headless') # UC headless is often detected, use headful
        # Use a random user agent? UC handles this usually, but we can set one.
        
        # Specify version_main to match installed Chrome if needed
        # Error observed: This version of ChromeDriver only supports Chrome version 143. Current browser version is 128.
        # We try to force version 128 if auto-detection picks a too-new version.
        try:
             driver = uc.Chrome(options=options, version_main=128)
        except Exception as e:
             print(f"UC init with version_main=128 failed: {e}, trying default...", file=sys.stderr)
             # Re-create options as they cannot be reused
             options = uc.ChromeOptions()
             driver = uc.Chrome(options=options)
        try:
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # Human behavior
            if action == "content":
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(2)
                
                content = driver.page_source
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            elif action == "cookies":
                cookies = driver.get_cookies()
                # Convert to playwright format (list of dicts) - Selenium cookies are similar
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f)
                    
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Error in uc_task: {e}", file=sys.stderr)
        sys.exit(1)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import ZHIHU_PROFILE_DIR

def run_playwright_task(url: str, output_path: str, action: str = "content", interactive: bool = False, hold: bool = False, save_cookies_path: str = ""):
    from playwright.sync_api import sync_playwright
    # Enforce ProactorEventLoopPolicy on Windows
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        with sync_playwright() as p:
            browser = None
            context = None

            if "zhihu.com" in url:
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=ZHIHU_PROFILE_DIR,
                        headless=False,
                        args=["--disable-blink-features=AutomationControlled"]
                    )
                except Exception:
                    context = None

            if not context:
                browser = p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                    extra_http_headers={
                        "Referer": "https://www.zhihu.com/",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
                    }
                )
            
            page = context.new_page()
            
            # Anti-detection
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                page.goto(url, timeout=45000)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                
                if action == "content":
                    time.sleep(random.uniform(2, 4))
                    try:
                        for _ in range(3):
                            x = random.randint(100, 700)
                            y = random.randint(100, 500)
                            page.mouse.move(x, y, steps=5)
                            time.sleep(random.uniform(0.1, 0.5))
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
                        time.sleep(random.uniform(1, 2))
                        page.mouse.move(random.randint(100, 700), random.randint(100, 500), steps=5)
                        time.sleep(1)
                    except:
                        pass

                    content = page.content()
                    if interactive:
                        max_wait = 3600 if hold else 600
                        start = time.time()
                        ok = False
                        print(f"Waiting for interaction... (Hold: {hold}, Max wait: {max_wait}s)", file=sys.stderr)
                        while time.time() - start < max_wait:
                            try:
                                t = page.title()
                                html = page.content()
                                cookies = context.cookies()
                                has_login_cookie = any((c.get("name") == "z_c0" and c.get("value")) for c in cookies)
                                not_blocked = ("安全验证" not in t) and ("40362" not in html) and ("请求存在异常" not in html)
                                
                                is_login_url = "signin" in page.url or "signup" in page.url
                                
                                # Check for positive login indicator (Avatar or Message icon)
                                try:
                                    # .AppHeader-profile is the container for avatar in top right
                                    # "消息" (Messages) is usually visible in header for logged-in users
                                    user_indicator = page.locator(".AppHeader-profile").is_visible() or page.locator("text=消息").is_visible()
                                except:
                                    user_indicator = False

                                should_break = False
                                if hold:
                                    # In hold mode, strictly wait for login cookie AND positive login indicator
                                    if has_login_cookie and user_indicator:
                                        print(f"Login verified! (Cookie: Yes, Indicator: Yes, Title: {t})", file=sys.stderr)
                                        print("Closing browser in 5 seconds...", file=sys.stderr)
                                        time.sleep(5)
                                        should_break = True
                                else:
                                    # Normal mode: proceed if logged in (and confirmed) OR not blocked
                                    if (has_login_cookie and user_indicator) or not_blocked:
                                        should_break = True
                                
                                if should_break:
                                    content = html
                                    ok = True
                                    break
                                time.sleep(2)
                            except Exception as e:
                                print(f"Browser interaction ended or error: {e}", file=sys.stderr)
                                break

                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    if save_cookies_path:
                        try:
                            cookies = context.cookies()
                            d = os.path.dirname(save_cookies_path)
                            os.makedirs(d, exist_ok=True)
                            with open(save_cookies_path, "w", encoding="utf-8") as f:
                                json.dump(cookies, f)
                        except Exception:
                            pass
                        
                elif action == "cookies":
                    cookies = context.cookies()
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(cookies, f)
                    
            finally:
                if context:
                    context.close()
                if browser:
                    browser.close()
                    
    except Exception as e:
        print(f"Error in playwright_task: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output_path")
    parser.add_argument("--action", choices=["content", "cookies"], default="content")
    parser.add_argument("--method", choices=["playwright", "uc"], default="playwright")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--hold", action="store_true")
    parser.add_argument("--save-cookies", default="")
    args = parser.parse_args()
    if args.method == "uc":
        run_uc_task(args.url, args.output_path, args.action)
    else:
        run_playwright_task(args.url, args.output_path, args.action, interactive=args.interactive, hold=args.hold, save_cookies_path=args.save_cookies)
