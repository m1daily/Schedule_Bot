import ast
import json
import os
from logging import DEBUG, Formatter, StreamHandler, getLogger
import gspread
import requests
import tweepy
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont


#-----------------------------------------------------------------------------------------------------------------------------------
# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ['JSON'])
with open('gss.json', mode='wt', encoding='utf-8') as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(format)
logger.addHandler(handler)
logger.info('セットアップ完了')

# ユーザーエージェントを変更し、403エラー対策
ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
headers = {'User-Agent': ua}

# 月間予定の要素を抽出
url = 'https://www.mito1-h.ibk.ed.jp/'
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
schedule = soup.select_one('#box-18 > section:nth-child(3) > div.panel-body.block > article > p')
logger.info('要素抽出完了\n')

#-----------------------------------------------------------------------------------------------------------------------------------
# 余計な文字列を削除
for i in schedule.select('br'):
    i.replace_with('\n')
schedule.text.strip()
schedule = str(schedule)
schedule = schedule.replace('<p>', '')
schedule = schedule.replace('<p style="text-align: left;">', '')
schedule = schedule.replace('</p>', '')

# Google SpreadSheetsにアクセス
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name('gss.json', scope))
ws = gc.open_by_key(os.environ['SHEET_ID']).sheet1

# 最後に投稿した予定を読み込み
schedule_latest = ws.acell('D6').value

# テキスト比較
if schedule == schedule_latest:
    logger.info('更新されていないので終了')
    exit()
else:
    logger.info('更新されているので続行\n')
    ws.update_acell('D6', schedule)
    schedule = schedule.split('\n')

# 外観調整
li = []
for i in schedule:
    news = ''.join(i.split())
    table = str.maketrans('（）', '()')
    news = news.translate(table)
    news = news.strip()
    if news[0].isdecimal() == True:
        news = '\n' + news
    elif news[0] == '(':
        news = news
    else:
        news = ',    ' + news
    li.append(news)
# リスト結合
txt = ''.join(li)
logger.info(txt)

#-----------------------------------------------------------------------------------------------------------------------------------
# 画像に文字を入れる
im = Image.new('RGB', (720, len(li)*19), (256, 256, 256))
draw = ImageDraw.Draw(im)
font = ImageFont.truetype('./news/NotoSansCJKjp-Light.otf', 12)
draw.text((20, 10), txt, fill=(0, 0, 0), font=font, spacing=12)
im.save('image.png')
logger.info('画像化完了\n')

#-----------------------------------------------------------------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

# tweepyの設定(認証情報を設定,APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# ツイート
api.update_status_with_media(status='今月の予定です。', filename='image.png')
logger.info('Twitter: ツイート完了')
#-----------------------------------------------------------------------------------------------------------------------------------
# Discordに投稿
webhook_url = os.environ['WEBHOOK']
payload2 = {
    'payload_json' : {
        'content' :'今月の予定です。',
        'embeds': [
            {
                'color' : 5419910,
                'footer': {
                    'icon_url' : 'https://raw.githubusercontent.com/Geusen/images/main/m1.jpg',
                    'text' : 'By 水戸一高時間割Bot',
                },
                'image': {
                    'url' : 'attachment://image.png'
                },
            }
        ]
    }
}
with open('image.png', 'rb') as f:
    file_bin_image = f.read()
files_qiita = {
    'image' : ('image.png', file_bin_image),
}
payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
res = requests.post(webhook_url, files = files_qiita, data = payload2)
logger.info(f'Discord: {res.status_code}')
