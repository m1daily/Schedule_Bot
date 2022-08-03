import settings
import datetime
import tweepy
import discord
import os
import time
import requests
import cv2 
import numpy as np
from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#-----------------------------------------------------------------------------
# バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
print(dt.strftime('\n[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]'))
#-----------------------------------------------------------------------------
# jsonファイル作成(情報漏えいを防ぐため伏せています)
GDA = {'credentials.txt':settings.JSON, 'client_secrets.txt':settings.CLIENT}
for key, value in GDA.items():
  f = open(key, 'w')
  f.write(value)
  f.close()
for f in Path('.').rglob('*.txt'):
  f.rename(f.stem+'.json')

# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = settings.CK
consumer_secret = settings.CS
access_token = settings.AT
access_token_secret = settings.ATC

# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# LINEの設定
def line_notify(x, Lmessage, Limage):
  line_url = 'https://notify-api.line.me/api/notify'
  line_access_token = x
  headers = {'Authorization': 'Bearer ' + line_access_token}
  line_message = Lmessage
  line_image = Limage
  payload = {'message': line_message}
  files = {'imageFile': open(line_image, 'rb')}
  r = requests.post(line_url, headers=headers, params=payload, files=files,)

# LINE,Discordのtoken設定(伏せています)
notify_group = settings.LN
notify_27 = settings.LN27
notify_admin = settings.LNA
Discord_token = settings.DT
channel_id = int(settings.DI)

# Googleにログイン
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
os.remove('credentials.json')
os.remove('client_secrets.json')
#-----------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(10)

# Googleスプレッドシートへ移動(URLは伏せています)
driver.get(settings.GU)
WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
  
# ウインドウ幅,高さ指定
windowSizeWidth = 680
windowSizeHeight = 700
windowWidth = windowSizeWidth if windowSizeWidth else driver.execute_script('return document.body.scrollWidth;')
windowHeight = windowSizeHeight if windowSizeHeight else driver.execute_script('return document.body.scrollHeight;')
driver.set_window_size(windowWidth, windowHeight)
time.sleep(4)

# スクリーンショットを格納し、ブラウザ稼働終了
driver.save_screenshot('before.png')
time.sleep(1)
driver.quit()

# 画像トリミング
im = Image.open('before.png')
im.crop((35, 145, 640, 645)).save('now.png', quality=95)
#-----------------------------------------------------------------------------
# ブラックリスト(リスト内の画像なら動作停止)
Black_List = ["white1.jpg", "white2.jpg", "error.png"]

# now.pngとリスト内の画像を比較
for Black_image in Black_List:
  GetFile = '\"' + Black_image + '\"'
  file_id = drive.ListFile({'q': f'title = {GetFile}'}).GetList()[0]['id']
  f = drive.CreateFile({'id': file_id})
  f.GetContentFile(Black_image)
  # 画像比較
  img_1 = cv2.imread('now.png')
  img_2 = cv2.imread(Black_image)
  # 画像が一致する(編集中orエラー)なら中止
  if np.array_equal(img_1, img_2) == True:
    print('編集中orエラーの為、終了(' + Black_image + ')')
    exit()
#-----------------------------------------------------------------------------
# GoogleDriveから画像取得(旧時間割)
file_id = drive.ListFile({'q': 'title = "upload.png"'}).GetList()[0]['id']
f = drive.CreateFile({'id': file_id})
f.GetContentFile('upload.png')

# スクリーンショットした画像(現在の時間割)とGoogleDriveから取得した画像(旧時間割)を比較
img_1 = cv2.imread('now.png')
img_2 = cv2.imread('upload.png')
match = str(np.count_nonzero(img_1 == img_2))
print("一致度: " + match)

# 2つの画像が全く一致しない(＝時間割が更新された)場合
if np.count_nonzero(img_1 == img_2) <= 400000:
  # 既にGoogleDriveにある画像(旧時間割)を削除後、現在の時間割の画像をアップロード
  os.remove('upload.png')
  os.rename('now.png', 'upload.png')
  f.Delete()
  f = drive.CreateFile()
  f.SetContentFile('upload.png')
  f.Upload()
  print('アップロード完了') 
  
  # ツイート
  api.update_status_with_media(status="時間割が更新されました！", filename="upload.png")
  
  # LINEへ通知
  line_notify(notify_group, '時間割が更新されました。', 'upload.png')
  # 27組用
  line_notify(notify_27, '時間割が更新されました。', 'upload.png')
  
  # Discordの接続に必要なオブジェクトを生成
  client = discord.Client()
  # DiscordBot起動時に動作する処理
  @client.event
  async def on_ready():
      channel = client.get_channel(channel_id)
      await channel.send('@everyone\n時間割が更新されました。', file=discord.File('upload.png'))
      await client.close()
  client.run(Discord_token)
  print('通知完了')

# 2つの画像が微妙に一致しない(=時間割が更新されたか判断できない)場合
elif 400000 < np.count_nonzero(img_1 == img_2) < 900000:
  # LINEに通知
  line_notify(notify_admin, '一致度が' + match + 'でした。', 'upload.png')
  line_notify(notify_admin, '(1枚目=前の時間割,2枚目=現在)', 'now.png')
  print('報告完了')
  # 既にGoogleDriveにある画像(旧時間割)を削除後、現在の時間割の画像をアップロード
  os.remove('upload.png')
  os.rename('now.png', 'upload.png')
  f.Delete()
  f = drive.CreateFile()
  f.SetContentFile('upload.png')
  f.Upload()
  print('アップロード完了')

# 2つの画像が一致する(=時間割が更新されてない)場合
else:
  # 終了
  print('画像が一致した為、終了')
  exit()
