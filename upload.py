import settings
import datetime
import tweepy
import discord
import os
import requests
from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

#-----------------------------------------------------------------------------
#バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
print(dt.strftime('\n[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]'))
#-----------------------------------------------------------------------------
#jsonファイル作成(情報漏えいを防ぐため伏せています)
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

# tweepyの設定(認証情報を設定)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# tweepyの設定(APIインスタンスの作成)
api = tweepy.API(auth, wait_on_rate_limit=True)

#LINEの設定(伏せています)
def line_notify(x):
  line_url = 'https://notify-api.line.me/api/notify'
  line_access_token = x
  headers = {'Authorization': 'Bearer ' + line_access_token}
  line_message = '時間割が更新されました。'
  line_image = 'upload.png'
  payload = {'message': line_message}
  files = {'imageFile': open(line_image, 'rb')}
  r = requests.post(line_url, headers=headers, params=payload, files=files,)

notify_group = settings.LN
notify_27 = settings.LN27

#Discordの接続に必要なオブジェクトを生成
client = discord.Client()

#Discordの設定
Discord_token = settings.DT
channel_id = int(settings.DI)

#Googleにログイン
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
#-----------------------------------------------------------------------------
#画像取得(時間割)
file_id = drive.ListFile({'q': 'title = "upload.png"'}).GetList()[0]['id']
f = drive.CreateFile({'id': file_id})
f.GetContentFile('upload.png')

#画像付きツイート
api.update_status_with_media(status="時間割が更新されました！", filename="upload.png")
  
#LINEへ通知
line_notify(notify_group)
#27組用
line_notify(notify_27)
  
#Discordに通知
@client.event
async def on_ready():
    channel = client.get_channel(channel_id)
    await channel.send('@everyone\n時間割が更新されました。', file=discord.File('upload.png'))
    await client.close()
client.run(Discord_token)
print('通知完了')
