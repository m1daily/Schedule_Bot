# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import subprocess  # GitHubActionsの環境変数追加
import time  # スリープ用
from logging import DEBUG, Formatter, StreamHandler, getLogger  # ログ出力
# サードパーティライブラリ
import cv2u  # 画像URLから読み込み
import gspread  # SpreadSheet操作
import requests  # LINE・Discord送信
import tweepy  # Twitter送信
from bs4 import BeautifulSoup  # 画像取得
from misskey import Misskey  # Misskey送信
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作


#----------------------------------------------------------------------------------------------------
# 日付取得
date = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
time_now = date.strftime("[%Y年%m月%d日(" + weekdays[date.weekday()] + ") %H:%M:%S]")
subprocess.run([f"echo 'TIME={time_now}' >> $GITHUB_OUTPUT"], shell=True)

# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)

#----------------------------------------------------------------------------------------------------
# デバッグ確認
debug = os.environ["DEBUG"]
if debug == "ON":
    logger.warning("DEBUG MODE\n")

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

# LINEの設定
def line_notify(line_access_token, message, image):
    line_url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + line_access_token}
    payload = {"message": message}
    files = {"imageFile": open(image, "rb")}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    r.raise_for_status()
    return str(r.status_code)

# 終了時用
def finish(exit_message):
    logger.info(f"{exit_message}\n")
    subprocess.run([f"echo STATUS={exit_message} >> $GITHUB_OUTPUT"], shell=True)
    exit()

logger.info("セットアップ完了")

#----------------------------------------------------------------------------------------------------
# imgタグを含むものを抽出
imgs_tag = []
soup = BeautifulSoup(requests.get(os.environ["GOOGLE_URL"]).text, "html.parser")
for i in soup.find("div", id="0").select("img"):
    imgs_tag.append(i.get("src"))
if imgs_tag == []:
    finish("画像が発見できなかったため終了(img無)")
logger.info("imgタグ抽出\n")

# 時間割の画像のみ抽出
imgs_cv2u_now = []    # cv2u用リスト(現在)
imgs_url_now = []     # URLリスト(現在)
for index, e in enumerate(imgs_tag, 1):
    logger.info(f"{index}枚目: {e}")
    if bool(str(cv2u.urlread(e)) in imgs_cv2u_now) == False:
        logger.info(" → append")
        imgs_cv2u_now.append(str(cv2u.urlread(e)))
        imgs_url_now.append(e)
logger.info(f"現在の画像:{imgs_url_now}")

# $GITHUB_OUTPUTに追加
now = ",".join(imgs_url_now)
subprocess.run([f"echo NOW={now} >> $GITHUB_OUTPUT"], shell=True)

#----------------------------------------------------------------------------------------------------
# Googleスプレッドシートへのアクセス
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name("gss.json", scope))
try:
    ws = gc.open_by_key(os.environ["SHEET_ID"]).sheet1
except:
    logger.warning("Googleスプレッドシートへのアクセス失敗\n")
    subprocess.run(["echo STATUS=Googleスプレッドシートへのアクセス失敗 >> $GITHUB_OUTPUT"], shell=True)
    exit()

# 最後に投稿した画像のリストを読み込み
imgs_url_latest = ws.acell("C6").value.split()    # URLリスト(過去)
logger.info(f"過去の画像:{imgs_url_latest}\n")
imgs_cv2u_latest = []    # cv2u用リスト(過去)
for e in imgs_url_latest:
    imgs_cv2u_latest.append(str(cv2u.urlread(e)))

# $GITHUB_OUTPUTに追加
before = ",".join(imgs_url_latest)
subprocess.run([f"echo BEFORE={before} >> $GITHUB_OUTPUT"], shell=True)

# 比較
if debug != "ON":
    if len(imgs_url_now) == len(imgs_url_latest):
        if bool(set(imgs_cv2u_now) == set(imgs_cv2u_latest)) == True:
            finish("画像が一致した為、終了")
        else:
            logger.info("画像が一致しないので続行")
    else:
        logger.info("画像の枚数が異なるので続行")
else:
    logger.info("DEBUG MODEなので続行")

#----------------------------------------------------------------------------------------------------
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
    next_day, next_schedule = str(ws.acell("D2").value) + "月" + days[0], schedules[0]
    logger.info(f"次の予定: {next_day} {next_schedule}")
else:
    for i in days:
        day = int(i[:2].replace("日", ""))
        if day_now < day:
            next_day, next_schedule = i, schedules[days.index(i)]
            logger.info(f"次の予定: {next_day} {next_schedule}")
            break

# 土曜加害判定
violence = False
if "土曜課外" in next_schedule and day - day_now == 1:
    violence = True
    r = requests.get(ws.acell("C7").value).content
    with open("sat.jpg", "wb") as f:
        f.write(r)
    logger.info("土曜課外 有")

# 画像URLを使って画像をダウンロード
imgs_path = []    # ダウンロードする画像のパスを格納するリスト
for i in imgs_url_now:
    time.sleep(3)
    r = requests.get(i).content
    img = str(imgs_url_now.index(i) + 1) + ".png"    # 画像の名前を1.png,2.png,...とする
    imgs_path.append(img)
    with open(img, mode="wb") as f:
        f.write(r)

# GoogleSpreadSheetsに画像URLを書き込み
if debug != "ON":
    ws.update_acell("C2", time_now)
    ws.update_acell("C3", "https://github.com/m1daily/Schedule_Bot/actions/runs/" + str(os.environ["RUN_ID"]))
    ws.update_acell("C6", " \n".join(imgs_url_now))
    logger.info("画像DL完了、セル上書き完了\n")

#----------------------------------------------------------------------------------------------------
# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)
client = tweepy.Client(
   consumer_key=consumer_key,
   consumer_secret=consumer_secret,
   access_token=access_token,
   access_token_secret=access_token_secret)

# 環境次第でメッセージ変更
if debug == "ON":
    message = "テスト投稿です。"
else:
    message = "時間割が更新されました。"
if next_day != None:
    message = f"{message}\n{next_day}に {next_schedule} があります。"

# Twitterに投稿
media_ids = []
for image in imgs_path:
   img = api.media_upload(image)
   media_ids.append(img.media_id)
if debug != "ON":
    client.create_tweet(text=message, media_ids=media_ids)

# 土曜加害がある場合は加害の時間割画像も投稿
if violence:
    media_ids = []
    img = api.media_upload("sat.jpg")
    media_ids.append(img.media_id)
    client.create_tweet(text="土曜課害の時間割です。", media_ids=media_ids)
logger.info("Twitter: ツイート完了")

# LINE Notifyに通知
logger.info("LINE:")
for key, value in line_dict.items():
    for i, image in enumerate(imgs_path, 1):
        logger.info(f"{key}-{i}枚目: {line_notify(value, message, image)}")
    if violence:
        logger.info(f"{key}-土曜課害: {line_notify(value, '土曜課外の時間割です。', 'sat.jpg')}")

# Discordに通知
payload2 = {"payload_json" : {"content" : f"@everyone\n{message}"}}
embed = []
# 画像の枚数分"embed"の値追加
for i in imgs_url_now:
    if imgs_url_now.index(i) == 0:
        img_embed = {
            "color" : 10931421,
            "url" : "https://www.google.com/",
            "image" : {"url" : i}
            }
    else:
        img_embed = {
            "url" : "https://www.google.com/",
            "image" : {"url" : i}
            }
    embed.append(img_embed)
payload2["payload_json"]["embeds"] = embed
payload2["payload_json"] = json.dumps(payload2["payload_json"], ensure_ascii=False)
r = requests.post(webhook_url, data=payload2)
logger.info(f"Discord: {r.status_code}")
r.raise_for_status()

# Misskeyに投稿
mk = Misskey("https://misskey.io/", i=os.environ["MISSKEY"])
misskey_ids = []
for i, path in enumerate(imgs_path, 1):
    with open(path, "rb") as f:
        data = mk.drive_files_create(f, name=date.strftime("%y-%m-%d_%H-%M_")+str(i), folder_id="9e8gee0xd2")
        misskey_ids.append(data["id"])
if debug != "ON":
    visibility = "home"
else:
    visibility = "specified"
mk.notes_create(message, visibility=visibility, file_ids=misskey_ids)
logger.info("Misskey: 投稿完了")

# One SignalでWeb Push通知
headers = {
    "Authorization": "Basic " + os.environ["API_KEY"],
    "accept": "application/json",
    "content-type": "application/json"
}
json_data = {
    "included_segments": [
        "Subscribed Users",
        "Active Users",
        "Inactive Users",
    ],
    "contents": {
        "en": message,
        "ja": message,
    },
    "name": "mito1daily",
    "app_id": os.environ["APP_ID"],
}
r = requests.post("https://onesignal.com/api/v1/notifications", headers=headers, json=json_data)
logger.info(f"One Signal: {r.status_code}")
r.raise_for_status()
finish("投稿完了")
