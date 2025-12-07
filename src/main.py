import csv
import sys
import asyncio

# Enforce ProactorEventLoopPolicy on Windows to ensure Playwright and other async tools work correctly
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.platforms.detector import detect_platform
from src.collectors import common, zhihu, bilibili, douyin
from src.llm.deepseek_client import summarize_markdown as deepseek_sum
from src.llm.deepseek_client import chat_completion as deepseek_chat
from typing import Tuple
from src.llm.bailian_client import summarize_markdown as bailian_sum
from src.llm.bailian_client import chat_completion as bailian_chat
from src.config import DEFAULT_SUMMARIZER
from src.feishu.client import ensure_folder, create_doc, insert_markdown_code_block
from src.collectors.browser_fallback import get_page_content
import os
import json

def collect_content(source: str, url: str) -> Tuple[str, str]:
    p = detect_platform(url)
    if p == "zhihu":
        d = zhihu.collect(url)
        return d.get("title", ""), d.get("text", "")
    if p in ("bilibili", "douyin"):
        d = bilibili.collect(url) if p == "bilibili" else douyin.collect(url)
        return d.get("title", ""), d.get("text", "")
    d = common.extract_article(url)
    return d.get("title", ""), d.get("text", "")

def ensure_zhihu_login_if_needed() -> None:
    cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cookies", "zhihu.json"))
    need_login = True
    if os.path.exists(cookie_path):
        try:
            with open(cookie_path, "r", encoding="utf-8") as f:
                arr = json.load(f)
            for c in arr:
                if c.get("name") == "z_c0" and c.get("value"):
                    need_login = False
                    break
        except Exception:
            need_login = True
    if need_login:
        get_page_content(
            "https://www.zhihu.com/",
            method="playwright",
            interactive=True,
            hold=True,
            save_cookies_path=cookie_path,
        )


def summarize(text: str) -> str:
    if DEFAULT_SUMMARIZER == "bailian":
        return bailian_sum(text)
    return deepseek_sum(text)


def summarize_with_prompt(title: str, text: str, prompt: str) -> str:
    if not prompt:
        return summarize(text)
    filled = prompt.replace("{{ $json.title }}", title or "").replace("{{ $json.content }}", text)
    try:
        if DEFAULT_SUMMARIZER == "bailian":
            out = bailian_chat(filled)
        else:
            out = deepseek_chat(filled)
    except Exception as e:
        # Fallback: simple markdown summary
        return (
            f"## 核心观点\n- {title or '未命名'}\n\n"
            f"## 正文摘录\n\n" + (text[:1000] + ("..." if len(text) > 1000 else ""))
        )
    try:
        import json
        data = json.loads(out)
        sm = data.get("summary", "")
        return sm or out
    except Exception:
        return out


def run(input_csv: str) -> None:
    # root_token = ensure_folder("知识收藏")
    # print(f"创建/使用根文件夹: {root_token}")
    import os
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "")
            source = row.get("source", "")
            prompt = row.get("prompt", row.get("提示词", ""))
            platform = detect_platform(url)
            if platform == "zhihu":
                ensure_zhihu_login_if_needed()
            # platform_folder = ensure_folder(source or platform, root_token)
            # print(f"处理[{platform}] {url} -> 子文件夹: {platform_folder}")
            print(f"Processing [{platform}] {url}")
            try:
                title, text = collect_content(source, url)
            except Exception as e:
                print(f"采集失败，跳过: {url} 错误: {e}")
                continue
            if not text:
                print("采集到的文本为空，跳过。")
                continue
            # md = summarize(text)
            md = text
            doc_title = title or f"来自{source}的内容"
            
            # Sanitize filename
            safe_title = "".join([c for c in doc_title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
            if not safe_title:
                safe_title = "untitled"
            
            # Each row writes into a dedicated folder under data
            row_dir = os.path.join(output_dir, safe_title)
            if not os.path.exists(row_dir):
                os.makedirs(row_dir)

            header = f"来源: {source}\n链接: {url}\n\n"

            raw_path = os.path.join(row_dir, "原文.md")
            with open(raw_path, "w", encoding="utf-8") as f_out:
                f_out.write(header + md)

            summary_md = summarize_with_prompt(doc_title, md, prompt)
            summary_path = os.path.join(row_dir, "总结.md")
            with open(summary_path, "w", encoding="utf-8") as f_out:
                f_out.write(header + summary_md)

            print(f"已写入: {raw_path} 和 {summary_path}")

            # doc_id = create_doc(doc_title, platform_folder or root_token)
            # print(f"已创建文档: {doc_title} -> {doc_id}")
            # header = f"来源: {source}\n链接: {url}\n\n"
            # insert_markdown_code_block(doc_id, header + md)
            # print("已写入Markdown代码块。")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/collection.csv"
    run(path)
