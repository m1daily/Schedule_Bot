import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

CK = os.environ.get("CONSUMER_KEY") # 環境変数の値をCKに代入(以下同様)
CS = os.environ.get("CONSUMER_SECRET")
AT = os.environ.get("ACCESS_TOKEN")
ATC = os.environ.get("ACCESS_TOKEN_SECRET")
GU = os.environ.get("GOOGLE_URL")
LN = os.environ.get("LINE_NOTIFY")
LN27 = os.environ.get("LINE_NOTIFY_27")
LNA = os.environ.get("LINE_NOTIFY_ADMIN")
#DT = os.environ.get("DISCORD_TOKEN")
#DI = os.environ.get("DISCORD_ID")
#DID = os.environ.get("DISCORD_ID_DEBUG")
WEB = os.environ.get("WEBHOOK")
JSON = os.environ.get("JSON")
CLIENT = os.environ.get("CLIENT")
