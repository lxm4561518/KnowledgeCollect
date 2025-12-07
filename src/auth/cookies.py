from urllib.parse import urlparse
import http.cookiejar
from typing import Optional, List
import platform
from .wincookies import get_cookie_header_windows


def _cookie_header_from_jar(jar: http.cookiejar.CookieJar, domains: List[str]) -> Optional[str]:
    pairs = []
    for c in jar:
        dom = (c.domain or "")
        if any(d in dom for d in domains):
            pairs.append(f"{c.name}={c.value}")
    if not pairs:
        return None
    return "; ".join(pairs)


def cookie_header_for(url: str) -> Optional[str]:
    parsed = urlparse(url)
    host = parsed.netloc
    domains = [host]
    parts = host.split(".")
    if len(parts) >= 2:
        domains.append("." + ".".join(parts[-2:]))
        domains.append(parts[-2] + "." + parts[-1])
    try:
        import browser_cookie3
    except Exception:
        browser_cookie3 = None
    # Prefer exact domain loading to improve hit rate
    if browser_cookie3:
        for loader_name in ("edge", "chrome", "firefox", "chromium"):
            getter = getattr(browser_cookie3, loader_name, None)
            if getter is None:
                continue
            try:
                jar = getter(domain_name=domains[-1])
                header = _cookie_header_from_jar(jar, domains)
                if header:
                    return header
            except Exception:
                try:
                    jar = getter()
                    header = _cookie_header_from_jar(jar, domains)
                    if header:
                        return header
                except Exception:
                    continue
    # Final fallback: auto loader
    if browser_cookie3:
        try:
            jar = browser_cookie3.load(domain_name=domains[-1])
            header = _cookie_header_from_jar(jar, domains)
            if header:
                return header
        except Exception:
            pass
    # Windows deep read
    if platform.system().lower() == "windows":
        header = get_cookie_header_windows(domains[-1])
        if header:
            return header
    return None
