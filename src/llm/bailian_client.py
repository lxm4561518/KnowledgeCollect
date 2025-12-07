import requests
from ..config import ALI_DASHSCOPE_API_KEY


def summarize_markdown(text: str) -> str:
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {"Content-Type": "application/json", "X-DashScope-API-Key": ALI_DASHSCOPE_API_KEY}
    prompt = (
        "你是一位中文内容整理助手。请将以下内容用结构化Markdown总结，包含：\n"
        "- 标题\n- 关键要点\n- 核心观点\n- 实用步骤或清单\n- 引用与链接\n"
        "要求：用简洁中文，层级清晰，保留原有重要术语与数据。\n\n原文：\n" + text
    )
    data = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt},
        "parameters": {"result_format": "text", "temperature": 0.3},
    }
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    res = r.json()
    output = res.get("output", {})
    return output.get("text", "").strip()
