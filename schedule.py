import settings
import datetime
import os
import time
import json
import requests
import ast
import gspread
import pprint
import urllib.request
import cv2
import numpy as np
import tweepy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from oauth2client.service_account import ServiceAccountCredentials


#-----------------------------------------------------------------------------
# バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
print(dt.strftime('\n[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]'))

#----------------------------------------------------------------------------------------------------
# LINEの設定
def line_notify(x):
  line_url = 'https://notify-api.line.me/api/notify'
  line_access_token = x
  headers = {'Authorization': 'Bearer ' + line_access_token}
  line_message = '時間割が更新されました。'
  line_image = 'upload.png'
  payload = {'message': line_message}
  files = {'imageFile': open(line_image, 'rb')}
  r = requests.post(line_url, headers=headers, params=payload, files=files,)

# LINE,Discordのtoken設定(伏せています)
notify_group = settings.LN
notify_27 = settings.LN27
webhook_url = settings.WEB

#----------------------------------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(10)

# Googleスプレッドシートへ移動(URLは伏せています)
driver.get(settings.GU)
WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located)
time.sleep(5)

# imgタグを含むものを抽出
li = driver.find_elements(By.TAG_NAME, "img")
for e in li:
    imgurl_n = e.get_attribute('src')
    if imgurl_n != None and "googleusercontent.com" in imgurl_n == True:
        break
if imgurl_n == None:
    print("画像が発見できなかったため終了")
    exit()

#----------------------------------------------------------------------------------------------------
# jsonファイル作成(情報漏えいを防ぐため伏せています)
dic = ast.literal_eval(settings.JSON)
with open('gss.json', mode='wt', encoding='utf-8') as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

# Google SpreadSheetsにアクセス
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('gss.json', scope)
gc = gspread.authorize(credentials)
ws = gc.open_by_key(settings.KEY).sheet1

# Google SpreadSheets上の値を読み込み
imgurl_b = ws.acell('A1').value

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
match = str(np.count_nonzero(img_1 == img_2))
print("一致度: " + match)
print(np.array_equal(img_1, img_2))

#----------------------------------------------------------------------------------------------------
# もし時間割の画像が一致しなかった(=時間割が更新されていた)場合
if np.array_equal(img_1, img_2) == False:
    
    # Google SpreadSheetsに現在の画像のURLを上書き
    ws.update_acell('A1', imgurl_n)
    
    
    # keyの指定(情報漏えいを防ぐため伏せています)
    consumer_key = settings.CK
    consumer_secret = settings.CS
    access_token = settings.AT
    access_token_secret = settings.ATC

    # tweepyの設定(認証情報を設定、APIインスタンスの作成)
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    
    # ツイート
    api.update_status_with_media(status="時間割が更新されました！", filename="upload.png")

    # LINEへ通知
    line_notify(notify_group)
    # 27組用
    line_notify(notify_27)
    
    # DiscordのWebhookを通して通知
    content = {'content': '@everyone\n時間割が更新されました。'}
    headers = {'Content-Type': 'application/json'}
    with open('upload.png', 'rb') as f:
        file_bin = f.read()
    image = {'upload' : ('upload.png', file_bin)}
    response = requests.post(webhook_url, json.dumps(content), headers=headers)
    response = requests.post(webhook_url, files = image)


else:
    print('画像が一致した為、終了')
    exit()
