import os
import re
import tempfile
from yt_dlp import YoutubeDL
from ..auth.cookies import cookie_header_for


def _read_subtitles_text(temp_dir: str) -> str:
    lines = []
    for f in os.listdir(temp_dir):
        if f.lower().endswith((".srt", ".ass", ".vtt")):
            p = os.path.join(temp_dir, f)
            with open(p, encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if re.match(r"^\d+$", line.strip()):
                        continue
                    if re.match(r"^\d{2}:\d{2}:\d{2}", line.strip()):
                        continue
                    if line.strip() and not line.strip().startswith(('{', 'Dialogue:')):
                        lines.append(line.strip())
    return "\n".join(lines)


def collect(url: str) -> dict:
    temp_dir = tempfile.mkdtemp(prefix="douyin_")
    out = os.path.join(temp_dir, "%(title)s-%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["zh", "zh-CN", "zh-Hans", "zh-Hant"],
        "skip_download": True,
        "noplaylist": True,
        "cookiesfrombrowser": ("edge", None, None),
    }
    cookie = cookie_header_for(url)
    if cookie:
        ydl_opts.setdefault("http_headers", {})["Cookie"] = cookie
    info = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception:
        ydl_opts["cookiesfrombrowser"] = ("chrome", None, None)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    title = info.get("title", "") if info else ""
    text = _read_subtitles_text(temp_dir)
    if not text and info:
        desc = info.get("description", "") or info.get("webpage_url_basename", "")
        text = desc
    return {"title": title, "text": text}
