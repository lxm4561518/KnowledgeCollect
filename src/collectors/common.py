import requests
from bs4 import BeautifulSoup
from readability import Document
from ..config import ZHIHU_COOKIE, BILIBILI_COOKIE
from ..auth.cookies import cookie_header_for
import browser_cookie3
from .browser_fallback import get_page_content, get_cookies
import shutil
import tempfile
import json
import os


def load_cookies_safely(domain_name: str):
    # Try standard load first
    try:
        return browser_cookie3.load(domain_name=domain_name)
    except Exception as e:
        print(f"Standard cookie load failed: {e}")

    # Try copying Edge cookies to temp file
    try:
        localapp = os.environ.get("LOCALAPPDATA", "")
        # Check both new and old paths
        paths = [
            os.path.join(localapp, "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies"),
            os.path.join(localapp, "Microsoft", "Edge", "User Data", "Default", "Cookies")
        ]
        cookie_path = next((p for p in paths if os.path.exists(p)), None)
        
        if cookie_path:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                tmp_path = tmp.name
            shutil.copy2(cookie_path, tmp_path)
            print(f"Copied cookies to temp file: {tmp_path}")
            try:
                # Force use of Edge with this cookie file
                cj = browser_cookie3.edge(cookie_file=tmp_path, domain_name=domain_name)
                return cj
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
    except Exception as e:
        print(f"Safe cookie load failed: {e}")
    raise Exception("Could not load cookies")


import random
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def fetch_html(url: str) -> str:
    # Random delay to simulate human behavior
    time.sleep(random.uniform(1.0, 3.0))
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": url,
    }
    cookie = None
    if "zhihu.com" in url and ZHIHU_COOKIE:
        headers["Cookie"] = ZHIHU_COOKIE
    if "bilibili.com" in url and BILIBILI_COOKIE:
        headers["Cookie"] = BILIBILI_COOKIE
    session = requests.Session()
    # Prefer full CookieJar to header string for robust handling
    # Navigate up two levels from src/collectors to root, then to data
    zhihu_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cookies", "zhihu.json"))
    try:
        parsed = url.split("/")[2]
        base_domain = "." + ".".join(parsed.split(".")[-2:])
        print(f"Attempting to load cookies for domain: {base_domain}")
        jar = None
        if "zhihu.com" in url and os.path.exists(zhihu_json_path):
            try:
                with open(zhihu_json_path, "r", encoding="utf-8") as f:
                    lst = json.load(f)
                cj = requests.cookies.RequestsCookieJar()
                for c in lst:
                    cj.set(c.get("name"), c.get("value"), domain=c.get("domain"), path=c.get("path", "/"))
                jar = cj
            except Exception as e:
                print(f"Failed to load cookies from json: {e}")
        if jar is None:
            jar = load_cookies_safely(base_domain)
        session.cookies = jar  # type: ignore
        print(f"Successfully loaded {len(jar)} cookies via browser_cookie3")
    except Exception as e:
        print(f"Failed to load cookies via browser_cookie3: {e}")
        auto_cookie = cookie_header_for(url)
        if auto_cookie:
            headers["Cookie"] = auto_cookie
        else:
            try:
                lst = get_cookies(url, method="playwright")
                if lst:
                    cj = requests.cookies.RequestsCookieJar()
                    for c in lst:
                        cj.set(c.get("name"), c.get("value"), domain=c.get("domain"), path=c.get("path", "/"))
                    session.cookies = cj
            except Exception as e2:
                print(f"Failed to load cookies via browser fallback: {e2}")
    r = session.get(url, headers=headers, timeout=20)
    if r.status_code >= 400:
        html = get_page_content(url, method="playwright", interactive=True, hold=True, save_cookies_path=zhihu_json_path if "zhihu.com" in url else None)
        if html:
            return html
        r.raise_for_status()
    return r.text


def extract_article(url: str) -> dict:
    html = fetch_html(url)
    doc = Document(html)
    title = doc.short_title()
    content_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(content_html, "html.parser")
    text = soup.get_text("\n")
    return {"title": title, "text": text}
