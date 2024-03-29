# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import subprocess  # GitHubActionsの環境変数追加
from logging import DEBUG, Formatter, StreamHandler, getLogger  # ログ出力
# サードパーティライブラリ
import cv2u  # 画像URLから読み込み
import gspread  # SpreadSheet操作
import requests  # LINE・Discord送信
from bs4 import BeautifulSoup  # 画像取得
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
# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ["JSON"])
with open("gss.json", mode="wt", encoding="utf-8") as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

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
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
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
if len(imgs_url_now) == len(imgs_url_latest):
    if bool(set(imgs_cv2u_now) == set(imgs_cv2u_latest)) == True:
        finish("画像が一致した為、終了")
    else:
        logger.info("画像が一致しないので続行")
else:
    logger.info("画像の枚数が異なるので続行")

# GoogleSpreadSheetsに画像URLを書き込み
ws.update_acell("C2", time_now)
ws.update_acell("C3", "https://github.com/m1daily/Schedule_Bot/actions/runs/" + str(os.environ["RUN_ID"]))
ws.update_acell("C6", " \n".join(imgs_url_now))
logger.info("画像DL完了、セル上書き完了\n")

finish("完了")
