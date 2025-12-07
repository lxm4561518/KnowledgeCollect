import os
import json
import base64
import sqlite3
import shutil
import tempfile
from typing import Optional, List
from ctypes import wintypes, windll, byref, c_void_p, c_char, cast, POINTER
from ctypes import Structure
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class DATA_BLOB(Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", c_void_p)]


def _crypt_unprotect(data: bytes) -> bytes:
    in_buffer = (c_char * len(data)).from_buffer_copy(data)
    blob_in = DATA_BLOB(len(data), cast(in_buffer, c_void_p))
    blob_out = DATA_BLOB()
    if windll.crypt32.CryptUnprotectData(byref(blob_in), None, None, None, None, 0, byref(blob_out)):
        try:
            out_buffer = (c_char * blob_out.cbData).from_address(blob_out.pbData)
            return bytes(out_buffer)
        finally:
            windll.kernel32.LocalFree(c_void_p(blob_out.pbData))
    return b""


def _get_local_state_key(local_state_path: str) -> Optional[bytes]:
    if not os.path.exists(local_state_path):
        return None
    with open(local_state_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    enc_key_b64 = data.get("os_crypt", {}).get("encrypted_key", "")
    if not enc_key_b64:
        return None
    enc_key = base64.b64decode(enc_key_b64)
    # On Windows: DPAPI encrypted key has 'DPAPI' prefix first 5 bytes
    if enc_key[:5] == b"DPAPI":
        return _crypt_unprotect(enc_key[5:])
    return None


def _chrome_profiles(base_dir: str) -> List[str]:
    profiles = []
    if not os.path.isdir(base_dir):
        return profiles
    for name in os.listdir(base_dir):
        if name in ("Default",) or name.startswith("Profile"):
            profiles.append(name)
    return profiles


def _cookies_path(base_dir: str, profile: str) -> str:
    p1 = os.path.join(base_dir, profile, "Network", "Cookies")
    p2 = os.path.join(base_dir, profile, "Cookies")
    return p1 if os.path.exists(p1) else p2


def _local_state_path(base_dir: str) -> str:
    return os.path.join(base_dir, "Local State")


def get_cookie_header_windows(domain: str) -> Optional[str]:
    # Try Edge
    localapp = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(localapp, "Microsoft", "Edge", "User Data"),
        os.path.join(localapp, "Google", "Chrome", "User Data"),
    ]
    for base in candidates:
        profiles = _chrome_profiles(base)
        key = _get_local_state_key(_local_state_path(base))
        for prof in profiles:
            cookies_db = _cookies_path(base, prof)
            if not os.path.exists(cookies_db):
                continue
            try:
                temp_copy = tempfile.mktemp(prefix="cookies_")
                shutil.copy2(cookies_db, temp_copy)
                conn = sqlite3.connect(temp_copy)
                cur = conn.cursor()
                cur.execute("SELECT name, encrypted_value, value FROM cookies WHERE host_key LIKE ?", (f"%{domain}%",))
                rows = cur.fetchall()
                conn.close()
                try:
                    os.remove(temp_copy)
                except Exception:
                    pass
                pairs = []
                for name, enc, val in rows:
                    if val:
                        pairs.append(f"{name}={val}")
                        continue
                    data = enc
                    if not data:
                        continue
                    data = bytes(data)
                    if data.startswith(b"v10") or data.startswith(b"v11"):
                        if not key:
                            continue
                        nonce = data[3:15]
                        ct = data[15:]
                        aesgcm = AESGCM(key)
                        try:
                            dec = aesgcm.decrypt(nonce, ct, None)
                            pairs.append(f"{name}={dec.decode('utf-8')}")
                        except Exception:
                            continue
                    else:
                        # DPAPI fallback
                        try:
                            dec = _crypt_unprotect(data)
                            pairs.append(f"{name}={dec.decode('utf-8')}")
                        except Exception:
                            continue
                if pairs:
                    return "; ".join(pairs)
            except Exception:
                continue
    return None
