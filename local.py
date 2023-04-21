# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import time  # スリープ用
import urllib.request  # 画像取得
from logging import DEBUG, Formatter, StreamHandler, getLogger
# サードパーティライブラリ
import requests  # LINE・Discord送信
import tweepy  # Twitter送信

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
logger.info(time_now)

#----------------------------------------------------------------------------------------------------
# json変換
dic = ast.literal_eval(os.environ['DICT'])

# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']    # TwitterAPI識別キー
consumer_secret = os.environ['CONSUMER_SECRET']    # TwitterAPI識別シークレットキー
access_token = os.environ['ACCESS_TOKEN']    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']    # Twitterアカウントに対するアクセストークンシークレット

# LINE,Discordのtoken設定(伏せています)
line_dict = ast.literal_eval(os.environ['LINE_NOTIFY'])    # LINEグループのトークン(JSON形式)
webhook_url = os.environ['WEBHOOK']    # Discordの時間割サーバーのWebhookのURL

logger.info('セットアップ完了')

#----------------------------------------------------------------------------------------------------
# 画像URLを使って画像をダウンロード
with urllib.request.urlopen(dic['url']) as web_file:
    time.sleep(5)
    data = web_file.read()
    with open('upload.jpg', mode='wb') as local_file:
        local_file.write(data)

#----------------------------------------------------------------------------------------------------
# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Twitterに投稿
api.update_status_with_media(status=dic['message'], filename='upload.jpg')
logger.info('Twitter: ツイート完了')

# LINE Notifyに通知
logger.info('LINE:')
for key, value in line_dict.items():
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + value}
    payload = {'message': dic['message']}
    files = {'imageFile': open('upload.jpg', 'rb')}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    r.raise_for_status()
    logger.info(f'{key}: {str(r.status_code)}')

# Discordに通知
payload2 = {
    'payload_json' : {
        'content' : dic['message'],
        'embeds' : [
            {
                'color' : 10931421,
                'url' : 'https://www.google.com/',
                'image' : {'url' : dic['url']}
                }
            ]
        }
    }
payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
r = requests.post(webhook_url, data=payload2)
logger.info(f'Discord: {r.status_code}')
r.raise_for_status()
