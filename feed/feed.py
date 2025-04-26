# 標準ライブラリ
import ast  # 文字列→JSON
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import re  # 正規表現用
from logging import DEBUG, Formatter, StreamHandler, getLogger  # ログ出力
# サードパーティライブラリ
import gspread  # SpreadSheet操作
import requests  # Discord送信
import tweepy  # Twitter送信
from bs4 import BeautifulSoup  # 予定取得
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作


#-----------------------------------------------------------------------------------------------------------------------------------
# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ["JSON"])
with open("gss.json", mode="wt", encoding="utf-8") as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.info("セットアップ完了")

def log(msg: str, li: list):
    logger.info(f"{msg}:")
    for i, item in enumerate(li):
        logger.info(f"{i+1}: {item}")

# ユーザーエージェントを変更、403エラー対策
ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
headers = {"User-Agent": ua}

# 月間予定の要素を抽出
url = "https://www.mito1-h.ibk.ed.jp/"
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
pattern = re.compile("<div>.*</div>")
f = re.findall(pattern, r.text)
articles = []
index = 0
while len(articles) < 10:
    ar = f[index].replace('<div><span style="font-size: 11pt;">', "").replace("</span></div>", "").replace("&nbsp;", "")
    ar = re.sub('<a href=".*?">', "", ar)  # タグを削除
    ar = re.sub("<.*?>", "", ar)  # タグを削除
    ar = ar.translate(str.maketrans({"　": "", " ": "", "（": "(", "）": ")", u"\xa0": "", u"\u3000": "", "\n": ""}))  # 余計なスペースを削除、全角括弧を半角括弧に変換
    ar = ar.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))  # 全角数字を半角数字に変換
    index += 1
    if ar == "の記事を掲載しました。":
        continue
    articles.append(ar)
log("取得した記事", articles)

#-----------------------------------------------------------------------------------------------------------------------------------
# Google SpreadSheetsにアクセス
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name("gss.json", scope))
try:
    ws = gc.open_by_key(os.environ["SHEET_ID"]).news
except Exception as e:
    logger.warning(f"{e.__class__.__name__}: {e}")
    exit()

# テキスト比較
old_articles = ws.col_values(2)
old_articles.pop(0)  # 1行目はヘッダーなので削除
log("\n旧記事", old_articles)
if articles == old_articles:
    logger.info("更新されていないので終了")
    exit()
else:
    logger.info("更新されているので続行\n")
    index = 0
    while index < 10:
        if articles[index] == old_articles[0]:
            break
        index += 1
    diff = articles[:index]
    if diff == []:
        logger.info("差分なし")
        exit()
    log("差分", diff)

    # spreadsheetに書き込み
    values = []
    for i in articles:
        values.append([i])
    ws.update("B2:B11", values)

#-----------------------------------------------------------------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ["CONSUMER_KEY"]
consumer_secret = os.environ["CONSUMER_SECRET"]
access_token = os.environ["ACCESS_TOKEN"]
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)
client = tweepy.Client(
   consumer_key=consumer_key,
   consumer_secret=consumer_secret,
   access_token=access_token,
   access_token_secret=access_token_secret)

# ツイート
update = "\n・".join(diff)
post = f"https://www.mito1-h.ibk.ed.jp/\n水戸一高のHPが更新されました。\n\n・{update}"
if len(post) > 139:
    post = f"{post[:130]}...(以下略)"
client.create_tweet(text=post)
logger.info("Twitter: ツイート完了")
