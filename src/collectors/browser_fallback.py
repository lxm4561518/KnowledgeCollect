import os
import sys
import subprocess
import tempfile
import json
from typing import Optional, List, Dict

def _run_browser_script(url: str, action: str, method: Optional[str] = None, interactive: bool = False, hold: bool = False, save_cookies_path: Optional[str] = None) -> Optional[str]:
    try:
        suffix = ".json" if action == "cookies" else ".html"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            output_path = tmp.name
            
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fetcher_script = os.path.join(current_dir, "browser_fetcher.py")
        
        cmd = [sys.executable, fetcher_script, url, output_path, "--action", action]
        
        # Determine method if not provided
        if method:
            cmd.extend(["--method", method])
        elif "zhihu.com" in url and action == "content":
             cmd.extend(["--method", "uc"])
        else:
             cmd.extend(["--method", "playwright"])

        if interactive:
            cmd.append("--interactive")
        if hold:
            cmd.append("--hold")
        if save_cookies_path:
            cmd.extend(["--save-cookies", save_cookies_path])
        
        print(f"Running browser fetcher for {url} (action={action}, method={cmd[-1]})...")
        timeout = 60 if action == "content" else 45
        if interactive or hold:
            timeout = 3600
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            print(f"Browser fetcher failed: {result.stderr}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None
            
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            os.remove(output_path)
            return content
        else:
            print("Browser fetcher did not produce output file")
            return None
            
    except Exception as e:
        print(f"Browser fallback execution failed: {e}")
        return None

def get_page_content(url: str, timeout_ms: int = 30000, method: Optional[str] = None, interactive: bool = False, hold: bool = False, save_cookies_path: Optional[str] = None) -> Optional[str]:
    return _run_browser_script(url, "content", method=method, interactive=interactive, hold=hold, save_cookies_path=save_cookies_path)

def get_cookies(url: str, method: Optional[str] = None) -> List[Dict]:
    content = _run_browser_script(url, "cookies", method=method)
    if content:
        try:
            return json.loads(content)
        except:
            return []
    return []

def _edge_user_data_dir() -> Optional[str]:
    # Kept for reference
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        return None
    return os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data', 'Default')
