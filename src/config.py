import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ALI_DASHSCOPE_API_KEY = os.getenv("ALI_DASHSCOPE_API_KEY", "")
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_ROOT_FOLDER_TOKEN = os.getenv("FEISHU_ROOT_FOLDER_TOKEN", "")

DEFAULT_SUMMARIZER = os.getenv("DEFAULT_SUMMARIZER", "deepseek")

ZHIHU_COOKIE = os.getenv("ZHIHU_COOKIE", "")
BILIBILI_COOKIE = os.getenv("BILIBILI_COOKIE", "")
ZHIHU_PROFILE_DIR = os.getenv(
    "ZHIHU_PROFILE_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".profiles", "zhihu"))
)
