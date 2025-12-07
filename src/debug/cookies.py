from src.auth.cookies import cookie_header_for
from src.collectors.common import fetch_html

def main():
    for site in ["https://www.bilibili.com", "https://www.zhihu.com"]:
        ck = cookie_header_for(site) or ""
        print(f"{site} cookie length: {len(ck)}")
    try:
        html = fetch_html("https://www.zhihu.com/question/263391776/answer/2307916676")
        print("Zhihu fetch status: OK, size:", len(html))
    except Exception as e:
        print("Zhihu fetch failed:", e)

if __name__ == "__main__":
    main()
