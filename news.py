import os
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
url = "https://www.mito1-h.ibk.ed.jp/"
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
ht = soup.select_one('#box-18 > section:nth-child(3) > div.panel-body.block > article > p')

#-----------------------------------------------------------------------------------------------------------------------------------
# 余計な文字列を削除
ht = [i.strip() for i in ht.text.splitlines()]
ht = [i for i in ht if i != ""]
ht = ht[0].split()
# 外観調整
li = []
for i in ht:
    a = ''.join(i.split())
    table = str.maketrans('（）', '()')
    a = a.translate(table)
    if a[0].isdecimal() == True:
        a = "\n" + a
    elif a[0] == "(":
        a = a
    else:
        a = "\n                " + a
    li.append(a)
# リスト結合
li = ''.join(li)
print(li)

#-----------------------------------------------------------------------------------------------------------------------------------
# 画像に文字を入れる
im = Image.new("RGB", (512, 680), (256, 256, 256))
draw = ImageDraw.Draw(im)
font = ImageFont.truetype('NotoSansCJKjp-Medium.otf', 16)
draw.text((20, 0), li, fill=(25, 40, 100), font=font, spacing=8)
im.save("image.png")

#-----------------------------------------------------------------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")

# tweepyの設定(認証情報を設定,APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# ツイート
api.update_status_with_media(status="今月の予定です。", filename="image.png")
#-----------------------------------------------------------------------------------------------------------------------------------
# Discordに投稿
webhook_url = os.environ.get("WEBHOOK")
content = {'content': '今月の予定です。'}
headers = {'Content-Type': 'application/json'}
with open('image.png', 'rb') as f:
    file_bin = f.read()
image = {'upload' : ('image.png', file_bin)}
response = requests.post(webhook_url, json.dumps(content), headers=headers)
response = requests.post(webhook_url, files = image)
