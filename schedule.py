# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import subprocess  # GitHubActionsの環境変数追加
import time  # スリープ用
from logging import DEBUG, Formatter, StreamHandler, getLogger  # ログ出力
# サードパーティライブラリ
import cv2  # 画像処理
import cv2u  # 画像URLから読み込み
import gspread  # SpreadSheet操作
import requests  # Discord送信
import tweepy  # Twitter送信
from bs4 import BeautifulSoup  # 画像取得
from misskey import Misskey  # Misskey送信
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作


#----------------------------------------------------------------------------------------------------
# 日付取得
date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
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
# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ["JSON"])
with open("gss.json", mode="wt", encoding="utf-8") as file:
  json.dump(dic, file, ensure_ascii=False, indent=2)

# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ["CONSUMER_KEY"]  # TwitterAPI識別キー
consumer_secret = os.environ["CONSUMER_SECRET"]  # TwitterAPI識別シークレットキー
access_token = os.environ["ACCESS_TOKEN"]  # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]  # Twitterアカウントに対するアクセストークンシークレット

# Discordのtoken設定(伏せています)
webhook_url = os.environ["WEBHOOK"]  # Discordの時間割サーバーのWebhookのURL

# Instagram Graph APIのtoken設定
insta_business_id = os.environ["INSTA_ID"]
insta_token = os.environ["INSTA_TOKEN"]

# InstagramAPIの設定
def instagram_api(url, post_data):
  try:
    headers = {"Authorization": f"Bearer {insta_token}", "Content-Type": "application/json"}
    options = {"headers": headers, "data": json.dumps(post_data)}
    response = requests.post(url, **options)
    return response
  except Exception as error:
    logger.warning(f"Instagram APIのリクエスト中にエラー発生\n{error}\n")
    return None

# 終了時用
def finish(exit_message):
  logger.info(f"{exit_message}\n")
  subprocess.run([f"echo STATUS={exit_message} >> $GITHUB_OUTPUT"], shell=True)
  exit()

logger.info("セットアップ完了")

#----------------------------------------------------------------------------------------------------
# imgタグを含むものを抽出
src = []
soup = BeautifulSoup(requests.get(os.environ["GOOGLE_URL"]).text, "html.parser")
for im in soup.select('img[src^="https://lh7-rt.googleusercontent.com/sheets/"]'):
  src.append(im["src"])
if src:
  logger.info(f"imgタグ抽出: {src}")
else:
  finish("画像が発見できなかったため終了(img無)")

# 時間割の画像のみ抽出
url_now = []
cv2u_now = []
for i in range(len(src)):
  url = src[i]
  logger.info(f"{i}枚目: {url}")
  if src[i]:
    if not str(cv2u.urlread(url)) in cv2u_now:
      logger.info(" → append")
      url_now.append(url)
      cv2u_now.append(str(cv2u.urlread(url)))
  else:
    logger.info(f"{i}枚目の画像が空")
logger.info(f"現在の画像:{url_now}")
subprocess.run([f"echo NOW={",".join(url_now)} >> $GITHUB_OUTPUT"], shell=True)

#----------------------------------------------------------------------------------------------------
# Googleスプレッドシートへのアクセス
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name("gss.json", scope))
try:
  ws = gc.open_by_key(os.environ["SHEET_ID"]).worksheet("schedule")
  time.sleep(2)
  ws2 = gc.open_by_key(os.environ["SHEET_ID"]).worksheet("month")
  time.sleep(2)
  ws3 = gc.open_by_key(os.environ["SHEET_ID"]).worksheet("commands")
  time.sleep(2)
except Exception as e:
  logger.warning(f"{e.__class__.__name__}: {e}")
  subprocess.run(["echo STATUS=Googleスプレッドシートへのアクセス失敗 >> $GITHUB_OUTPUT"], shell=True)
  exit()

# 最後に投稿した画像を読み込み
try:
  url_old = ws.acell("C2").value.split()
except:
  logger.warning("Googleスプレッドシートへのアクセス失敗\n")
  subprocess.run(["echo STATUS=Googleスプレッドシートへのアクセス失敗 >> $GITHUB_OUTPUT"], shell=True)
  exit()
cv2u_old = []
for im in url_old:
    cv2u_old.append(str(cv2u.urlread(im)))
logger.info(f"過去の画像:{url_old}")
subprocess.run([f"echo BEFORE={",".join(url_old)} >> $GITHUB_OUTPUT"], shell=True)

# 更新通知のチェック
if ws.acell("C3").value == "Update":
  logger.info("画像投稿実行")
else:
  if len(url_now) == len(url_old):
    if set(url_now) == set(url_old):
      finish("画像が一致した為、終了")
    else:
      logger.info("画像が一致しないので続行")
  else:
    if len(url_now) < len(url_old) and set(cv2u_now).issubset(cv2u_old):
      finish("画像の枚数が減っただけなので終了")
    else:
      logger.info("画像の枚数が異なるので続行")
  if ws.acell("C3").value == "NoUpdate":
    ws.update_acell("C3", "Update")
    finish("次の更新チェックで画像投稿")
  else:
    finish("C3セルの値が不正なため終了")

# 画像情報のリスト作成
images = []
for i in range(len(url_now)):
  images.append({"path": f"{i}.png", "url": url_now[i]})

#----------------------------------------------------------------------------------------------------
# 月間予定を日付と予定に分割
month_data = ws2.acell("B2").value.split("\n")
days, schedules = [], []
for i, day_data in enumerate(month_data):
  day_parts = day_data.split(")")  # day_parts = ["5日(金", "①②実力試験(1", "、③校内模試(2", "、④ベネ記述模試"]
  yotei = []
  for n, d in enumerate(day_parts):
    # 日付の場合「)」を追加
    if len(day_parts) - n > 1:
      d = d + ")"
    if n > 0:
      yotei.append(d)
    if n == 0:
      days.append(d)
  schedules.append("".join(yotei))

# 次の予定を取得
month_now = int(date.strftime("%m"))
day_now = int(date.strftime("%d"))
next_day = None
if month_now != int(ws2.acell("A2").value):
  next_day, next_schedule = str(ws2.acell("A2").value) + "月" + days[0], schedules[0]
  logger.info(f"次の予定: {next_day} {next_schedule}")
else:
  for i in days:
    day = int(i[:2].replace("日", ""))
    if day_now < day:
      next_day, next_schedule = i, schedules[days.index(i)]
      logger.info(f"次の予定: {next_day} {next_schedule}")
      break
  if not "next_schedule" in globals():
    next_schedule = None
    logger.info("次の予定 無")

# 土曜加害判定
if next_schedule != None:
  if "土曜課外" in next_schedule and day - day_now == 1:
    images.append({"path": "sat.jpg", "url": ws3.acell("C6").value})
    logger.info("土曜課外 有")

# 画像ダウンロード
for im in images:
  time.sleep(2)
  r = requests.get(im["url"])
  with open(im["path"], mode="wb") as f:
    f.write(r.content)
  im["cv2"] = cv2.imread(im["path"])

# 画像結合
h_min = min(im["cv2"].shape[0] for im in images)  # 画像の高さの最小値を取得
im_list_resize = [cv2.resize(im["cv2"], (int(im["cv2"].shape[1] * h_min / im["cv2"].shape[0]), h_min), interpolation=cv2.INTER_CUBIC)
          for im in images]  # 画像を小さい方に合わせてリサイズ
cv2.imwrite("update.jpg", cv2.hconcat(im_list_resize))  # 画像を横に結合

# GoogleSpreadSheetsに画像URLを書き込み
ws.update_acell("C2", " \n".join(url_now))
ws.update_acell("C3", "NoUpdate")
ws.update_acell("C4", time_now)
ws.update_acell("C5", "https://github.com/m1daily/Schedule_Bot/actions/runs/" + str(os.environ["RUN_ID"]))
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
if next_schedule != None:
  message = f"時間割が更新されました。\n{next_day}に {next_schedule} があります。"
else:
  message = "時間割が更新されました。"

# Twitterに投稿
client.create_tweet(text=message, media_ids=[api.media_upload("update.jpg").media_id])
logger.info("Twitter: ツイート完了")

# Discord, Misskey用に画像をバイナリに変換
with open("update.jpg", mode='rb') as f:
  image_rb = f.read()

# Discordに通知
payload2 = {"payload_json": {"content" : f"@everyone\n{message}",}}
payload2["payload_json"] = json.dumps(payload2["payload_json"], ensure_ascii=False)
r = requests.post(webhook_url, data=payload2, files={"attachment": ("update.jpg", image_rb)})
logger.info(f"Discord: {r.status_code}\n{r.json()}")
r.raise_for_status()

# Misskeyに投稿
mk = Misskey("https://misskey.io/", i=os.environ["MISSKEY"])
misskey_ids = []
data = mk.drive_files_create(image_rb, name=date.strftime("%y-%m-%d_%H-%M_"), folder_id="9e8gee0xd2")
misskey_ids.append(data["id"])
mk.notes_create(message, visibility="home", file_ids=misskey_ids)
logger.info("Misskey: 投稿完了")

# Instagramに投稿
insta_imgs = []
for im in images:
  h, w = im["cv2"].shape[:2]
  aspect = w / h
  if 0.8 < aspect < 1.91:
    insta_imgs.append(im["url"])
if len(insta_imgs) > 1:
  logger.info("Instagram: カルーセル投稿")
  contena_ids = []  # 複数枚ある場合はカルーセル投稿
  for insta_url in insta_imgs:
    post_data = {"image_url": insta_url, "media_type": ""}
    r = instagram_api(f"https://graph.facebook.com/v21.0/{insta_business_id}/media?", post_data)  # 画像のアップロード
    logger.info(f"画像アップロード: {str(r.status_code)}\n{r.json()}")
    r.raise_for_status()
    contena_ids.append(r.json()["id"]) # 画像のIDを取得
  post_data = {"media_type": "CAROUSEL", "children": contena_ids, "caption": message}
  r = instagram_api(f"https://graph.facebook.com/v21.0/{insta_business_id}/media?", post_data)
  logger.info(f"グループ化コンテナID取得: {str(r.status_code)}\n{r.json()}")
  r.raise_for_status()
  post_data = {"media_type": "CAROUSEL", "creation_id": r.json()["id"]}
elif len(insta_imgs) == 0:
  logger.info("Instagram: 画像なし")
  finish("投稿完了")
else:
  logger.info("Instagram: 画像投稿")
  post_data = {"image_url": insta_imgs[0], "caption": message, "media_type": ""}
  r = instagram_api(f"https://graph.facebook.com/v21.0/{insta_business_id}/media?", post_data)  # 画像のアップロード
  logger.info(f"画像アップロード: {str(r.status_code)}\n{r.json()}")
  r.raise_for_status()
  post_data = {"creation_id": r.json()["id"]}  # 画像のIDを取得
r = instagram_api(f"https://graph.facebook.com/v21.0/{insta_business_id}/media_publish?", post_data) # 投稿
logger.info(f"投稿: {str(r.status_code)}\n{r.json()}")
r.raise_for_status()
finish("投稿完了")
