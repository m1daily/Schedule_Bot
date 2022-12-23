import os
import codecs
import json
import requests
import tweepy
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

#-----------------------------------------------------------------------------------------------------------------------------------
# ユーザーエージェントを変更し、403エラー対策
ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
headers = {'User-Agent': ua}

# 月間予定のタグを抽出
url = 'https://www.mito1-h.ibk.ed.jp/'
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
schedule = soup.select_one('#box-18 > section:nth-child(3) > div.panel-body.block > article > p')

#-----------------------------------------------------------------------------------------------------------------------------------
# 余計な文字列を削除
for i in schedule.select('br'):
    i.replace_with('\n')
schedule.text.strip()
schedule = str(schedule)
schedule = schedule.replace('<p>', '')
schedule = schedule.replace('<p style="text-align: left;">', '')
schedule = schedule.replace('</p>', '')

# 最後に投稿した予定を読み込み
with codecs.open('./news/news.txt', 'r', 'utf-8') as f:
    schedule_latest = f.read()

# テキスト比較
if schedule == schedule_latest:
    print('更新されていないので終了')
    exit()
else:
    print('更新されているので続行')
    with codecs.open('./news/news.txt', 'w', 'utf-8') as f:
        f.write(schedule)
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
print(txt)

#-----------------------------------------------------------------------------------------------------------------------------------
# 画像に文字を入れる
im = Image.new('RGB', (720, len(li)*19), (256, 256, 256))
draw = ImageDraw.Draw(im)
font = ImageFont.truetype('./news/NotoSansCJKjp-Light.otf', 12)
draw.text((20, 10), txt, fill=(0, 0, 0), font=font, spacing=12)
im.save('image.png')

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
