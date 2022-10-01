import datetime
import os
import time
import json
import requests
import urllib.request
import cv2
import numpy as np
import tweepy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


#----------------------------------------------------------------------------------------------------
# バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
print(dt.strftime('\n[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]'))

#----------------------------------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']    # TwitterAPI識別キー
consumer_secret = os.environ['CONSUMER_SECRET']    # TwitterAPI識別シークレットキー
access_token = os.environ['ACCESS_TOKEN']    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']    # Twitterアカウントに対するアクセストークンシークレット

# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# LINEの設定
def line_notify(x):
    line_url = 'https://notify-api.line.me/api/notify'
    line_access_token = x
    headers = {'Authorization': 'Bearer ' + line_access_token}
    line_message = '時間割が更新されました。'
    line_image = 'upload.png'
    payload = {'message': line_message}
    files = {'imageFile': open(line_image, 'rb')}
    r = requests.post(line_url, headers=headers, params=payload, files=files)

# LINE,Discordのtoken設定(伏せています)
notify_group = os.environ['LINE_NOTIFY']    # 時間割LINEグループのトークン
notify_27 = os.environ['LINE_NOTIFY_27']    # 自分のクラスのライングループのトークン
notify_13 = os.environ['LINE_NOTIFY_13']    # 13組のライングループのトークン
webhook_url = os.environ['WEBHOOK']    # Discordの時間割サーバーのWebhookのURL

# 終了時用
def finish(x):
    print(x)
    exit()

#----------------------------------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(10)

# Googleスプレッドシートへ移動(URLは伏せています)
driver.get(os.environ['GOOGLE_URL'])    # 時間割の画像があるGoogleSpreadSheetのURL
WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located)
time.sleep(5)

# imgタグを含むものを抽出
li = driver.find_elements(By.TAG_NAME, 'img')
if li == []:
    finish('画像が発見できなかったため終了')

# 時間割の画像以外も取り出している場合があるため、時間割の画像のみ抽出(GoogleSpreadSheet上の画像は画像URLの末尾が「alr=yes」)
for e in li:
    imgurl_n = e.get_attribute('src')
    if imgurl_n != None and 'alr=yes' in imgurl_n == True:
        break
# 時間割の画像が見つからなかった場合は終了
if imgurl_n == None:
    finish('画像が発見できなかったため終了')

#----------------------------------------------------------------------------------------------------
# 旧時間割の画像URL取得
f = open('url.txt', 'r')
imgurl_b = f.read()
f.close()

#----------------------------------------------------------------------------------------------------
# 画像URLを使って画像をダウンロード
def download(url, name, when):
    with urllib.request.urlopen(url) as web_file:
        time.sleep(3)
        data = web_file.read()
        with open(name, mode='wb') as local_file:
            local_file.write(data)
    print(when + ': ' + url)

# 現在の時間割と旧時間割を比較
download(imgurl_b, 'before.png', '前')
download(imgurl_n, 'upload.png', '現在')
img_1 = cv2.imread('before.png')
img_2 = cv2.imread('upload.png')
print('判定: ' + str(np.array_equal(img_1, img_2)))

#----------------------------------------------------------------------------------------------------
# 時間割の画像が一致しなかった(=時間割が更新されていた)場合
if np.array_equal(img_1, img_2) == False:
    
    # url.txtに現在の画像のURLを上書き
    f = open('url.txt', 'w')
    f.write(imgurl_n)
    f.close()
    
    # ツイート
    api.update_status_with_media(status = '時間割が更新されました！', filename = 'upload.png')

    # LINEへ通知
    line_list = [notify_group, notify_27, notify_13]
    for l in line_list:
        line_notify(l)
    
    # DiscordのWebhookを通して通知
    payload2 = {
        'payload_json' : {
            'content' : '@everyone\n時間割が更新されました。',
            'embeds' : [
                {
                    'color' : 10931421,
                    'image' : {'url' : imgurl_n}
                }
            ]
        }
    }
    payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
    res = requests.post(webhook_url, data = payload2)
    finish('投稿完了')

# 時間割の画像が一致した(=時間割が更新されていなかった)場合
else:
    finish('画像が一致した為、終了')
