import requests
from ..config import DEEPSEEK_API_KEY


def summarize_markdown(text: str) -> str:
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = (
        "你是一位中文内容整理助手。请将以下内容用结构化Markdown总结，包含：\n"
        "- 标题\n- 关键要点\n- 核心观点\n- 实用步骤或清单\n- 引用与链接\n"
        "要求：用简洁中文，层级清晰，保留原有重要术语与数据。\n\n原文：\n" + text
    )
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    res = r.json()
    return res["choices"][0]["message"]["content"].strip()


def chat_completion(prompt: str) -> str:
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    res = r.json()
    return res["choices"][0]["message"]["content"].strip()
