import os
from dotenv import load_dotenv

load_dotenv()

SALES_BOT_TOKEN: str = os.getenv("SALES_BOT_TOKEN", "")
SUPPORT_BOT_TOKEN: str = os.getenv("SUPPORT_BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
CARD_NUMBER: str = os.getenv("CARD_NUMBER", "")
SUPPORT_BOT_USERNAME: str = os.getenv("SUPPORT_BOT_USERNAME", "")
DB_PATH: str = os.getenv("DB_PATH", "data.db")
GROUPS_PER_PAGE: int = 5
