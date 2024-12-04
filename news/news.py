# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import re  # 正規表現用
import subprocess  # GitHubActionsの環境変数追加
from logging import DEBUG, Formatter, StreamHandler, getLogger  # ログ出力
# サードパーティライブラリ
import gspread  # SpreadSheet操作
import requests  # Discord送信
import tweepy  # Twitter送信
from bs4 import BeautifulSoup  # 予定取得
from misskey import Misskey  # Misskey送信
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作
from PIL import Image, ImageDraw, ImageFont  # 画像処理


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

# LINEの設定
def line_notify(line_access_token, line_message):
    line_url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_access_token}"}
    payload = {"message": line_message}
    files = {"imageFile": open("image.png", "rb")}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    r.raise_for_status()
    return str(r.status_code)

# ユーザーエージェントを変更、403エラー対策
ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
headers = {"User-Agent": ua}

# 月間予定の要素を抽出
url = "https://www.mito1-h.ibk.ed.jp/"
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
news_soup = soup.select("#box-18 > section:nth-child(4) > div.panel-body.block > article > p")
news_len = 0
for i in range(1, len(news_soup)+1):
    if str(soup.select_one(f"#box-18 > section:nth-child(4) > div.panel-body.block > article > p:nth-child({i})")).count("<br/>") > 5:
        news_len = str(i)
        break
if news_len == 0:
    logger.info("要素抽出失敗 (news_len=0)\n")
    raise Exception("要素抽出失敗")
schedule = soup.select_one(f"#box-18 > section:nth-child(4) > div.panel-body.block > article > p:nth-child({news_len})")
logger.info("要素抽出完了\n")

#-----------------------------------------------------------------------------------------------------------------------------------
# 余計な文字列を削除
for i in schedule.select("br"):
    i.replace_with("\n")

# 外観調整
schedule = schedule.text.replace("※変更の場合あり", "").split("\n")
schedule = list(filter(None, schedule))
li = []
subprocess.run(["echo '::group::parts'"], shell=True)
for i in range(len(schedule)):
    news = schedule[i].translate(str.maketrans({"　": "", " ": "", "（": "(", "）": ")", u"\xa0": "", u"\u3000": ""}))  # 余計なスペースを削除、全角括弧を半角括弧に変換
    news = news.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))  # 全角数字を半角数字に変換
    news = news.strip()  # 文字列の先頭と末尾の空白を削除
    if not news:  # newsが空の場合、continue
        continue
    if re.match("\d", news[0]) is not None:  # 先頭が数字の場合
        day_pattern = news[:news.find("(")]  # (の前の部分を取得
        if "/" in day_pattern:  # 日付部分に/が含まれている場合 例: 1/6日(月)教職員代休(1/12)
            if i == 0:  # 1つ目の要素の場合
                day_delete = day_pattern.find("/")  # /で分割
                news = news[day_delete + 1:]  # 例: 6日(月)教職員代休(1/12)
                check = "number(1)"
            else:
                news = "、" + news  # カンマを追加(文字列の場合と同じ扱い)
                check = "number"
        else:
            news = "\n" + news
    else:  # 先頭が文字列の場合、カンマを追加
        news = "、" + news
        check = "string"
    li.append(news)
    subprocess.run([f"echo '{news} [{check}]'"], shell=True)
subprocess.run(["echo '::endgroup::'"], shell=True)
li = [i for i in li if i != ""]  # 空の要素を削除
li[0] = li[0].replace("\n", "")
txt = "".join(li)
logger.info(txt)

#-----------------------------------------------------------------------------------------------------------------------------------
# Google SpreadSheetsにアクセス
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name("gss.json", scope))
try:
    ws = gc.open_by_key(os.environ["SHEET_ID"]).sheet1
except:
    logger.warning("Googleスプレッドシートへのアクセス失敗\n")
    exit()

# テキスト比較
if txt == ws.acell("D6").value:
    logger.info("更新されていないので終了")
    exit()
else:
    logger.info("更新されているので続行\n")
    month = soup.select_one("#box-18 > section:nth-child(4) > div.panel-heading.clearfix > span").contents[0].translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    logger.info(f"月の表記: {month}")
    month_li = month[:month.find("月")].split("・")
    if max(month_li) == "12" and "1" in month_li:
        month = "1"
    else:
        month = max(month_li)
    logger.info(f"月: {month}")
    ws.update_acell("D2", int(month))
    ws.update_acell("D6", txt)

#-----------------------------------------------------------------------------------------------------------------------------------
# 画像に文字を入れる
length = 0
for i in txt.split("\n"):
    if len(i) > length:
        length = len(i)
im = Image.new("RGB", ((length+1)*12, (txt.count("\n")+2)*24+20), (256, 256, 256))
draw = ImageDraw.Draw(im)
font = ImageFont.truetype("./news/NotoSansCJKjp-Light.otf", 12)
draw.text((20, 10), txt, fill=(0, 0, 0), font=font, spacing=12)
im.save("image.png")
logger.info("画像化完了\n")

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
img = api.media_upload("image.png")
client.create_tweet(text="今月の予定です。", media_ids=[img.media_id])
logger.info("Twitter: ツイート完了")

# LINE Notifyに通知
logger.info("LINE:")
line_dict = ast.literal_eval(os.environ["LINE_NOTIFY"])    # LINEグループのトークン(JSON形式)
for key, value in line_dict.items():
    try:
        logger.info(f"{key}: {line_notify(value, '今月の予定です。')}")
    except Exception as e:
        logger.info(f"{key}: {e.__class__.__name__}({e})")
        continue

# Discordに投稿
webhook_url = os.environ["WEBHOOK"]
payload2 = {
    "payload_json" : {
        "content" :"今月の予定です。",
        "embeds": [
            {
                "color" : 5419910,
                "footer": {
                    "icon_url" : "https://raw.githubusercontent.com/SoniPana/images/main/m1.jpg",
                    "text" : "By 水戸一高時間割Bot",
                },
                "image": {
                    "url" : "attachment://image.png"
                },
            }
        ]
    }
}
with open("image.png", "rb") as f:
    file_bin_image = f.read()
files_qiita = {
    "image" : ("image.png", file_bin_image),
}
payload2["payload_json"] = json.dumps(payload2["payload_json"], ensure_ascii=False)
res = requests.post(webhook_url, files = files_qiita, data = payload2)
logger.info(f"Discord: {res.status_code}")

# Misskeyに投稿
date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
mk = Misskey("https://misskey.io/", i=os.environ["MISSKEY"])
with open("image.png", "rb") as f:
    data = mk.drive_files_create(f, name=date.strftime("news_%y-%m-%d_%H-%M"), folder_id="9e8gee0xd2")
mk.notes_create("今月の予定です。", visibility="home", file_ids=[data["id"]])
logger.info("Misskey: 投稿完了")

# imgurにアップロード
imgur = os.environ["IMGUR"]
headers = {"authorization": f"Client-ID {imgur}"}
files = {"image": open("image.png", "rb")}
r = requests.post("https://api.imgur.com/3/image", headers=headers, files=files)
logger.info(f"imgur: {r.status_code}")
ws.update_acell("D7", json.loads(r.text)["data"]["link"])
