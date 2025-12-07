from .common import fetch_html
from bs4 import BeautifulSoup
import cloudscraper
import os

def collect(url: str) -> dict:
    print(f"Collecting Zhihu content from: {url}")
    
    # Method 1: Try Cloudscraper first (Bypass Cloudflare/Anti-bot)
    text = ""
    title = ""
    try:
        print("Attempting with Cloudscraper...")
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        r = scraper.get(url)
        # Use content (bytes) for BS4 to detect encoding, or force utf-8
        html_bytes = r.content
        soup = BeautifulSoup(html_bytes, "html.parser")
        title = soup.title.string if soup.title else ""
        
        # Check if we got a valid page or an error page
        # Added "知乎" slogan parts and login keywords
        error_keywords = [
            "访问异常", "Traffic Control", "403 Forbidden", "安全验证", 
            "系统监测到您的网络环境存在异常", "有问题，就会有答案", "请求存在异常", 
            "注册/登录", "加入知乎", "登录知乎", "发现问题背后的世界",
            "让每一次点击都充满意义"
        ]
        is_error = False
        
        # Check title first
        if any(k in title for k in error_keywords):
            is_error = True
            
        # Extract text candidates
        if not is_error and len(html_bytes) > 500:
             article = soup.select_one("article") or soup.select_one(".Post-RichTextContainer")
             if article:
                 text = article.get_text("\n")
             else:
                 question = soup.select_one(".QuestionRichText")
                 if question:
                     text = question.get_text("\n")
                     answers = soup.select(".RichContent-inner")
                     for ans in answers:
                         text += "\n\n" + ans.get_text("\n")
                 else:
                     # Fallback to general text if it looks like content
                     text = soup.get_text("\n")
                     
        # Check text for error keywords
        if any(k in text for k in error_keywords):
            is_error = True
            text = "" # Clear invalid text

    except Exception as e:
        print(f"Cloudscraper failed: {e}")

    # Method 2: Fallback to standard fetch_html (requests with cookies) if Cloudscraper failed or got blocked
    if not text or len(text) < 50 or "访问异常" in text:
                print("Cloudscraper result invalid, falling back to standard fetch_html...")
                try:
                    html = fetch_html(url)
                    # Check if html is None (browser fallback failed and requests failed/skipped)
                    if not html:
                        raise Exception("fetch_html returned None")
                        
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.string if soup.title else ""
                    article = soup.select_one("article") or soup.select_one(".Post-RichTextContainer")
                    if article:
                        text = article.get_text("\n")
                    else:
                        text = soup.get_text("\n")
                except Exception as e:
                    print(f"fetch_html failed: {e}")
                    # If everything fails, maybe we have partial text from cloudscraper?
                    # No, we are here because cloudscraper failed.
                    pass
            
            # Check for known error messages again
    error_keywords = [
        "访问异常", "Traffic Control", "403 Forbidden", "安全验证", 
        "系统监测到您的网络环境存在异常", "有问题，就会有答案", "请求存在异常", 
        "注册/登录", "加入知乎", "登录知乎", "发现问题背后的世界",
        "让每一次点击都充满意义", "40362"
    ]
    # "有问题，就会有答案" is the slogan, but sometimes it appears on error pages too? No, that's the title.
    # If the text is very short and contains "登录" (Login), it's likely a login wall.
    
    is_error = False
    if any(k in text for k in error_keywords) or any(k in title for k in error_keywords):
        is_error = True
    
    if is_error or len(text) < 50: # If text is suspiciously short
        print(f"Detected access restriction or empty content for {url}. Content length: {len(text)}")
        # Try browser fallback explicitly if we haven't already (fetch_html tries it on 400+, but maybe we got 200 OK with error text)
        from .browser_fallback import get_page_content
        
        # Try UC first
        print("Attempting browser fallback for Zhihu (method: uc)...")
        html = get_page_content(url, method="uc")
        
        # Check if UC returned error or None
        uc_failed = False
        if not html:
            uc_failed = True
        elif any(k in html for k in error_keywords) or "40362" in html:
            uc_failed = True
            print("UC fallback returned error page.")
            
        if uc_failed:
            print("Attempting browser fallback for Zhihu (method: playwright)...")
            cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cookies", "zhihu.json"))
            html_pw = get_page_content(url, method="playwright", interactive=True, hold=True, save_cookies_path=cookie_path)
            if html_pw:
                html = html_pw
        
        if html:
            soup = BeautifulSoup(html, "html.parser")
            if not title:
                title = soup.title.string if soup.title else ""
            article = soup.select_one("article") or soup.select_one(".Post-RichTextContainer")
            if article:
                text = article.get_text("\n")
            else:
                # Try to get the main content if article tag is missing (e.g. Question page)
                question = soup.select_one(".QuestionRichText")
                if question:
                    text = question.get_text("\n")
                    # Append answers if any
                    answers = soup.select(".RichContent-inner")
                    for ans in answers:
                        text += "\n\n" + ans.get_text("\n")
                else:
                    text = soup.get_text("\n")
    
    # Final check for error content in text
    if "40362" in text or "请求存在异常" in text:
         print("Collection failed: Zhihu access denied (40362).")
         text = "Error: Zhihu access denied (Traffic Control 40362). Please try setting ZHIHU_COOKIE in .env or try again later."

    return {"title": title, "text": text}
