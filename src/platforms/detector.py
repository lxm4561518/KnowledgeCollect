from urllib.parse import urlparse


def detect_platform(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if "zhihu.com" in netloc:
        return "zhihu"
    if "bilibili.com" in netloc or "b23.tv" in netloc:
        return "bilibili"
    if "douyin.com" in netloc or "iesdouyin.com" in netloc:
        return "douyin"
    return "generic"
