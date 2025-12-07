import requests
from ..config import FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_ROOT_FOLDER_TOKEN
from typing import Optional


def tenant_access_token() -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    r = requests.post(url, json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}, timeout=20)
    r.raise_for_status()
    return r.json().get("tenant_access_token", "")


def ensure_folder(name: str, parent_token: Optional[str] = None) -> str:
    token = tenant_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    pt = parent_token or FEISHU_ROOT_FOLDER_TOKEN or ""
    if pt == "":
        url = "https://open.feishu.cn/open-apis/drive/v1/files/create_folder"
        body = {"name": name, "folder_token": ""}
    else:
        url = "https://open.feishu.cn/open-apis/drive/v1/files/create_folder"
        body = {"name": name, "folder_token": pt}
    r = requests.post(url, headers=headers, json=body, timeout=20)
    if r.status_code == 200 and r.json().get("code") == 0:
        data = r.json().get("data", {})
        return data.get("token", "")
    return ""


def create_doc(title: str, folder_token: Optional[str] = None) -> str:
    token = tenant_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    body = {"title": title}
    if folder_token:
        body["folder_token"] = folder_token
    r = requests.post(url, headers=headers, json=body, timeout=20)
    r.raise_for_status()
    document = r.json().get("data", {}).get("document", {})
    return document.get("document_id", "")


def insert_markdown_code_block(document_id: str, markdown_text: str) -> None:
    token = tenant_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    root_blocks = requests.get(
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks",
        headers=headers,
        params={"document_revision_id": -1, "page_size": 50},
        timeout=20,
    ).json()
    blocks = root_blocks.get("data", {}).get("items", [])
    root_id = blocks[0]["block_id"] if blocks else ""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{root_id}/children"
    body = {
        "children": [
            {
                "block_type": 14,
                "code": {
                    "elements": [{"text_run": {"content": markdown_text}}],
                    "style": {"language": 0, "wrap": True},
                },
            }
        ],
        "index": 0,
    }
    requests.post(url, headers=headers, params={"document_revision_id": -1}, json=body, timeout=20)
