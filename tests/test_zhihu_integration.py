import os
import json
import unittest
from src.collectors.zhihu import collect
from src.collectors.common import fetch_html

ZHIHU_URL = "https://www.zhihu.com/question/263391776/answer/2307916676"
COOKIE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cookies", "zhihu.json"))

def has_login_cookie():
    try:
        with open(COOKIE_PATH, "r", encoding="utf-8") as f:
            arr = json.load(f)
        return any(c.get("name") == "z_c0" and c.get("value") for c in arr)
    except Exception:
        return False

class TestZhihuIntegration(unittest.TestCase):
    @unittest.skipUnless(has_login_cookie(), "Zhihu login cookie required")
    def test_fetch_html_no_block(self):
        html = fetch_html(ZHIHU_URL)
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 1000)
        self.assertNotIn("40362", html)
        self.assertNotIn("安全验证", html)
        self.assertNotIn("请求存在异常", html)

    @unittest.skipUnless(has_login_cookie(), "Zhihu login cookie required")
    def test_collect_text(self):
        d = collect(ZHIHU_URL)
        text = d.get("text", "")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 500)
        self.assertNotIn("40362", text)
        self.assertNotIn("安全验证", text)
        self.assertNotIn("请求存在异常", text)

