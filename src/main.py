import csv
import sys
import asyncio

# Enforce ProactorEventLoopPolicy on Windows to ensure Playwright and other async tools work correctly
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.platforms.detector import detect_platform
from src.collectors import common, zhihu, bilibili, douyin
from src.llm.deepseek_client import summarize_markdown as deepseek_sum
from typing import Tuple
from src.llm.bailian_client import summarize_markdown as bailian_sum
from src.config import DEFAULT_SUMMARIZER
from src.feishu.client import ensure_folder, create_doc, insert_markdown_code_block


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


def summarize(text: str) -> str:
    if DEFAULT_SUMMARIZER == "bailian":
        return bailian_sum(text)
    return deepseek_sum(text)


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
            platform = detect_platform(url)
            # platform_folder = ensure_folder(source or platform, root_token)
            # print(f"处理[{platform}] {url} -> 子文件夹: {platform_folder}")
            print(f"Processing [{platform}] {url}")
            title, text = collect_content(source, url)
            if not text:
                print("采集到的文本为空，跳过。")
                continue
            # md = summarize(text)
            md = text  # Skip summarization, use raw text
            doc_title = title or f"来自{source}的内容"
            
            # Sanitize filename
            safe_title = "".join([c for c in doc_title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
            if not safe_title:
                safe_title = "untitled"
            
            filename = f"{safe_title}.md"
            file_path = os.path.join(output_dir, filename)

            header = f"来源: {source}\n链接: {url}\n\n"
            
            with open(file_path, "w", encoding="utf-8") as f_out:
                f_out.write(header + md)
            
            print(f"已写入本地文件: {file_path}")

            # doc_id = create_doc(doc_title, platform_folder or root_token)
            # print(f"已创建文档: {doc_title} -> {doc_id}")
            # header = f"来源: {source}\n链接: {url}\n\n"
            # insert_markdown_code_block(doc_id, header + md)
            # print("已写入Markdown代码块。")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/collection.csv"
    run(path)
