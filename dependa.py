# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import urllib.request  # 画像取得
from logging import DEBUG, Formatter, StreamHandler, getLogger
# サードパーティライブラリ
import cv2u  # 画像URLから読み込み
import gspread  # SpreadSheet操作
import requests  # LINE・Discord送信
import tweepy  # Twitter送信
from bs4 import BeautifulSoup  # 画像取得
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作
from PIL import Image  # pillow

#----------------------------------------------------------------------------------------------------
# 日付取得
date = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekdays = ['月', '火', '水', '木', '金', '土', '日']
time_now = date.strftime('[%Y年%m月%d日(' + weekdays[date.weekday()] + ') %H:%M:%S]')

# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(format)
logger.addHandler(handler)

#----------------------------------------------------------------------------------------------------
# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ['JSON'])
with open('gss.json', mode='wt', encoding='utf-8') as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']    # TwitterAPI識別キー
consumer_secret = os.environ['CONSUMER_SECRET']    # TwitterAPI識別シークレットキー
access_token = os.environ['ACCESS_TOKEN']    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']    # Twitterアカウントに対するアクセストークンシークレット

# LINE,Discordのtoken設定(伏せています)
line_dict = ast.literal_eval(os.environ['LINE_NOTIFY'])    # LINEグループのトークン(JSON形式)

# LINEの設定
def line_notify(line_access_token):
    headers = {'Authorization': 'Bearer ' + line_access_token}
    r = requests.get('https://notify-api.line.me/api/status', headers=headers)
    r.raise_for_status()
    return r.text

logger.info(f'{time_now}\n')

#----------------------------------------------------------------------------------------------------
# beautifulsoup、requests
soup = BeautifulSoup(requests.get('https://m1daily.github.io/mito1daily/').text, 'html.parser')
url = soup.find('img').get('src')
logger.info(url)
with urllib.request.urlopen(url) as web_file:
    with open('debug.png', mode='wb') as local_file:
        local_file.write(web_file.read())
logger.info('Beautifulsoup => OK')
logger.info('requests => OK\n')

# gspread
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name('gss.json', scope))
ws = gc.open_by_key('128mFFj6w1drdDzxsKsoc9Xdba2FEWSffcM2iUSrnZ0c').sheet1
logger.info('gspread => OK')
logger.info('oauth2client => OK\n')

# pillow
img = Image.open('debug.png')
logger.info('pillow => OK')

# python-opencv-utils
cv2u.urlread(url)
logger.info('python-opencv-utils => OK\n')

# tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)
logger.info('tweepy => OK\n')

#----------------------------------------------------------------------------------------------------
# LINE Notify
for key, value in line_dict.items():
    logger.info(f'{key}: {line_notify(value)}')
