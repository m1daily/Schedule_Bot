# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import time  # スリープ用
import urllib.request  # 画像取得
from logging import DEBUG, Formatter, StreamHandler, getLogger
# サードパーティライブラリ
import gspread  # SpreadSheet操作
import requests  # LINE・Discord送信
import tweepy  # Twitter送信
from misskey import Misskey  # Misskey送信
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作

#----------------------------------------------------------------------------------------------------
# 日付取得
date = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
time_now = date.strftime("[%Y年%m月%d日(" + weekdays[date.weekday()] + ") %H:%M:%S]")

# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.info(time_now)

#----------------------------------------------------------------------------------------------------
# json変換
local_dic = ast.literal_eval(os.environ["DICT"])
logger.info(f"url: {local_dic['url']}\nmessage: {local_dic['message']}\n中学生: {local_dic['junior']}\n")

# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ["JSON"])
with open("gss.json", mode="wt", encoding="utf-8") as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ["CONSUMER_KEY"]    # TwitterAPI識別キー
consumer_secret = os.environ["CONSUMER_SECRET"]    # TwitterAPI識別シークレットキー
access_token = os.environ["ACCESS_TOKEN"]    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]    # Twitterアカウントに対するアクセストークンシークレット

# LINE,Discordのtoken設定(伏せています)
line_dict = ast.literal_eval(os.environ["LINE_NOTIFY"])    # LINEグループのトークン(JSON形式)
webhook_url = os.environ["WEBHOOK"]    # Discordの時間割サーバーのWebhookのURL

logger.info("セットアップ完了")

#----------------------------------------------------------------------------------------------------
# 画像URLを使って画像をダウンロード
with open("upload.jpg", "wb") as f:
    f.write(requests.get(local_dic["url"]).content)

# Googleスプレッドシートへのアクセス
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name("gss.json", scope))
try:
    ws = gc.open_by_key(os.environ["SHEET_ID"]).sheet1
except:
    logger.warning("Googleスプレッドシートへのアクセス失敗\n")
    exit()

# 月間予定を日付と予定に分割
month_data = ws.acell("D6").value.split("\n")
days, schedules = [], []
for i, day_data in enumerate(month_data):
    day_parts = day_data.split(")")
    for j in range(2):
        d = day_parts[j]
        # 日付の場合「)」を追加
        if j == 0 or len(day_parts) > 2:
            d = d + ")"
        if j == 0:
            days.append(d)
        else:
            schedules.append(d)

# 次の予定を取得
month_now = int(date.strftime("%m"))
day_now = int(date.strftime("%d"))
next_day = None
if month_now != int(ws.acell("D2").value):
    next_day, next_schedule = days[0], schedules[0]
    logger.info(f"次の予定: {next_day} {next_schedule}")
else:
    for i in days:
        if day_now < int(i[:2].replace("日", "")):
            next_day, next_schedule = i, schedules[days.index(i)]
            logger.info(f"次の予定: {next_day} {next_schedule}")
            break
"""
#----------------------------------------------------------------------------------------------------
# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Twitterに投稿
if next_day != None:
    message = local_dic["message"] + f"\n{next_day}に {next_schedule} があります。"
else:
    message = local_dic["message"]
api.update_status_with_media(status=message, filename="upload.jpg")
logger.info("Twitter: ツイート完了")

# LINE Notifyに通知
logger.info("LINE:")
for key, value in line_dict.items():
    line_url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + value}
    payload = {"message": local_dic["message"]}
    files = {"imageFile": open("upload.jpg", "rb")}
    if local_dic["junior"] != "YES" or key in "A" or key in "B":
        r = requests.post(line_url, headers=headers, params=payload, files=files)
        r.raise_for_status()
        logger.info(f"{key}: {str(r.status_code)}")

# Discordに通知
payload2 = {
    "payload_json" : {
        "content" : "@everyone\n" + local_dic["message"],
        "embeds" : [
            {
                "color" : 10931421,
                "url" : "https://www.google.com/",
                "image" : {"url" : local_dic["url"]}
                }
            ]
        }
    }
payload2["payload_json"] = json.dumps(payload2["payload_json"], ensure_ascii=False)
r = requests.post(webhook_url, data=payload2)
logger.info(f"Discord: {r.status_code}")
r.raise_for_status()

# Misskeyに投稿
mk = Misskey("https://misskey.io/", i=os.environ["MISSKEY"])
misskey_ids = []
with open("upload.jpg", "rb") as f:
    data = mk.drive_files_create(f, name=date.strftime("%y-%m-%d_%H-%M_")+str(i), folder_id="9e8gee0xd2")
    misskey_ids.append(data["id"])
mk.notes_create(message, visibility="home", file_ids=misskey_ids)
logger.info("Misskey: 投稿完了")
"""
