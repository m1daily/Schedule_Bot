import settings
import datetime
import tweepy
import discord
import os
import time
import requests
import cv2 
import numpy as np
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#-----------------------------------------------------------------------------
#バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
print('')
print(dt.strftime('[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]'))
#-----------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = settings.CK
consumer_secret = settings.CS
access_token = settings.AT
access_token_secret = settings.ATC

# tweepyの設定(認証情報を設定)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# tweepyの設定(APIインスタンスの作成)
api = tweepy.API(auth, wait_on_rate_limit=True)

#LINEの設定(伏せています)
line_url = 'https://notify-api.line.me/api/notify'
line_access_token = settings.LN
headers = {'Authorization': 'Bearer ' + line_access_token}

#Discordの設定
Discord_token = settings.DT
channel_id = int(settings.DI)

#Googleにログイン
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
#-----------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(10)

# ウインドウ幅、高さ指定
windowSizeWidth = 680
windowSizeHeight = 700

# サイトURL取得(伏せています)
driver.get(settings.GU)
WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
  
# ウインドウ幅・高さ指定
windowWidth = windowSizeWidth if windowSizeWidth else driver.execute_script('return document.body.scrollWidth;')
windowHeight = windowSizeHeight if windowSizeHeight else driver.execute_script('return document.body.scrollHeight;')
driver.set_window_size(windowWidth, windowHeight)
time.sleep(3)

# スクリーンショット格納
driver.save_screenshot('before.png')

# サーバー負荷軽減処理
time.sleep(1)

# ブラウザ稼働終了
driver.quit()

# 画像トリミング
im = Image.open('before.png')
im.crop((35, 145, 640, 645)).save('now.png', quality=95)
#-----------------------------------------------------------------------------
#画像取得(白)
file_id = drive.ListFile({'q': 'title = "white.jpg"'}).GetList()[0]['id']
f = drive.CreateFile({'id': file_id})
f.GetContentFile('white.jpg')

#画像比較
img_1 = cv2.imread('now.png')
img_2 = cv2.imread('white.jpg')

#画像が真っ白なら中止
if np.array_equal(img_1, img_2) == True:
  print('編集中の為、終了')
  exit()

#画像取得(白)
file_id = drive.ListFile({'q': 'title = "white2.jpg"'}).GetList()[0]['id']
f = drive.CreateFile({'id': file_id})
f.GetContentFile('white2.jpg')

#画像比較
img_1 = cv2.imread('now.png')
img_2 = cv2.imread('white2.jpg')

#画像が真っ白なら中止
if np.array_equal(img_1, img_2) == True:
  print('編集中の為、終了')
  exit()
#-----------------------------------------------------------------------------
#画像取得(時間割)
file_id = drive.ListFile({'q': 'title = "upload.png"'}).GetList()[0]['id']
f = drive.CreateFile({'id': file_id})
f.GetContentFile('upload.png')

#画像比較
img_1 = cv2.imread('now.png')
img_2 = cv2.imread('upload.png')
print("一致度: " + str(np.count_nonzero(img_1 == img_2)))

#もしスクショした画像とアップロード済みの画像が異なる(＝時間割が更新された)なら
if np.count_nonzero(img_1 == img_2) < 450000:
  #既にある画像を削除後、アップロード
  os.remove('upload.png')
  os.rename('now.png', 'upload.png')
  f.Delete()
  f = drive.CreateFile()
  f.SetContentFile('upload.png')
  f.Upload()
  print('アップロード完了')
  #画像付きツイート
  #api.update_status_with_media(status="時間割が更新されました！", filename="upload.png")
  #LINEへ通知
  line_message = '時間割が更新されました。'
  line_image = 'upload.png'
  payload = {'message': line_message}
  files = {'imageFile': open(line_image, 'rb')}
  #r = requests.post(line_url, headers=headers, params=payload, files=files,)
  #27組用
  line_url = 'https://notify-api.line.me/api/notify'
  line_access_token = settings.LN27
  headers = {'Authorization': 'Bearer ' + line_access_token}
  line_message = '時間割が更新されました。'
  line_image = 'upload.png'
  payload = {'message': line_message}
  files = {'imageFile': open(line_image, 'rb')}
  #r = requests.post(line_url, headers=headers, params=payload, files=files,)
  #Discordの接続に必要なオブジェクトを生成
  client = discord.Client()
  #DiscordBot起動時に動作する処理
  @client.event
  async def on_ready():
      channel = client.get_channel(channel_id)
      await channel.send('時間割が更新されました。', file=discord.File('upload.png'))
      await client.close()
  #client.run(Discord_token)
  print('通知完了')


else:
  #終了
  print('画像が一致した為、終了')
  exit()

