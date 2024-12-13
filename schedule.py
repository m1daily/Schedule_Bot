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
import requests  # LINE・Discord送信
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
consumer_key = os.environ["CONSUMER_KEY"]    # TwitterAPI識別キー
consumer_secret = os.environ["CONSUMER_SECRET"]    # TwitterAPI識別シークレットキー
access_token = os.environ["ACCESS_TOKEN"]    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]    # Twitterアカウントに対するアクセストークンシークレット

# LINE,Discordのtoken設定(伏せています)
line_dict = ast.literal_eval(os.environ["LINE_NOTIFY"])    # LINEグループのトークン(JSON形式)
webhook_url = os.environ["WEBHOOK"]    # Discordの時間割サーバーのWebhookのURL

# Instagram Graph APIのtoken設定
insta_business_id = os.environ["INSTA_ID"]
insta_token = os.environ["INSTA_TOKEN"]

# LINEの設定
def line_notify(line_access_token, line_message):
    """
    Line Notify API を使って Line に通知メッセージを送信

    引数
        line_access_token (str): LINE Notify API のアクセストークン
        line_message (str): 送信するメッセージ

    戻り値
        str: HTTPリクエストのステータスコード

    発生：
        requests.HTTPError: HTTP リクエストがエラー・ステータス・コードを返した場合
    """
    line_url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_access_token}"}
    payload = {"message": line_message}
    files = {"imageFile": open("update.jpg", "rb")}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    r.raise_for_status()
    return str(r.status_code)

# InstagramAPIの設定
def instagram_api(url, post_data):
    """
    指定されたURLと投稿データでInstagram APIにPOSTリクエストを送信

    引数
        url (str): Instagram APIエンドポイントのURL
        post_data (dict): POSTリクエストで送信するデータ

    戻り値
        requests.Response or None: リクエストが成功した場合はレスポンスオブジェクト、そうでない場合はNone
    """
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
time.sleep(2)
try:
    imgs_url_latest = ws.acell("C6").value.split()    # URLリスト(過去)
except:
    logger.warning("Googleスプレッドシートへのアクセス失敗\n")
    subprocess.run(["echo STATUS=Googleスプレッドシートへのアクセス失敗 >> $GITHUB_OUTPUT"], shell=True)
    exit()
logger.info(f"過去の画像:{imgs_url_latest}\n")
imgs_cv2u_latest = []    # cv2u用リスト(過去)
for e in imgs_url_latest:
    imgs_cv2u_latest.append(str(cv2u.urlread(e)))

# $GITHUB_OUTPUTに追加
before = ",".join(imgs_url_latest)
subprocess.run([f"echo BEFORE={before} >> $GITHUB_OUTPUT"], shell=True)

# 更新通知のチェック
if ws.acell("D3").value == "NoUpdate":
    # 比較
    if len(imgs_url_now) == len(imgs_url_latest):
        if set(imgs_cv2u_now) == set(imgs_cv2u_latest):
            finish("画像が一致した為、終了")
        else:
            logger.info("画像が一致しないので続行")
    else:
        if len(imgs_url_now) < len(imgs_url_latest) and set(imgs_cv2u_now).issubset(imgs_cv2u_latest):
            finish("画像の枚数が減っただけなので終了")
        else:
            logger.info("画像の枚数が異なるので続行")
    ws.update_acell("D3", "Update")
    finish("次の更新チェックで画像投稿")
else:
    logger.info("画像投稿実行")

#----------------------------------------------------------------------------------------------------
# 月間予定を日付と予定に分割
month_data = ws.acell("D6").value.split("\n")
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
    if not "next_schedule" in globals():
        next_schedule = None
        logger.info("次の予定 無")

# 画像URLを使って画像をダウンロード
imgs_path = []    # 現在の画像をcv2で読み込んだものを格納するリスト
for i in imgs_url_now:
    time.sleep(3)
    r = requests.get(i).content
    img = str(imgs_url_now.index(i)) + ".png"    # 画像の名前を0.png,1.png,...とする
    with open(img, mode="wb") as f:
        f.write(r)
    imgs_path.append(cv2.imread(img))

# 土曜加害判定
if next_schedule != None:
    if "土曜課外" in next_schedule and day - day_now == 1:
        r = requests.get(ws.acell("C7").value).content
        with open("sat.png", "wb") as f:
            f.write(r)
        imgs_path.append(cv2.imread("sat.png"))
        logger.info("土曜課外 有")

# 画像結合
h_min = min(im.shape[0] for im in imgs_path)
im_list_resize = [cv2.resize(im, (int(im.shape[1] * h_min / im.shape[0]), h_min), interpolation=cv2.INTER_CUBIC)
                  for im in imgs_path]  # 画像を小さい方に合わせてリサイズ
cv2.imwrite("update.jpg", cv2.hconcat(im_list_resize))  # 画像を横に結合

# GoogleSpreadSheetsに画像URLを書き込み
ws.update_acell("C2", time_now)
ws.update_acell("C3", "https://github.com/m1daily/Schedule_Bot/actions/runs/" + str(os.environ["RUN_ID"]))
ws.update_acell("C6", " \n".join(imgs_url_now))
ws.update_acell("D3", "NoUpdate")
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

# LINE Notifyに通知
logger.info("LINE:")
for key, value in line_dict.items():
    try:
        logger.info(f"{key}: {line_notify(value, message)}")
    except Exception as e:
        logger.info(f"{key}: {e.__class__.__name__}({e})")
        continue

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
for i in imgs_url_now:
    h, w = cv2u.urlread(i).shape[:2]
    aspect = w / h
    if 0.8 < aspect < 1.91:
        insta_imgs.append(i)
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
