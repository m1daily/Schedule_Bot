import settings
import datetime
import discord
import os
import time
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
gda = settings.JSON
cs = settings.CLIENT
f = open('credentials.txt', 'w')
f.write(gda)
f.close()
f = open('client_secrets.txt', 'w')
f.write(cs)
f.close()
for f in Path('.').rglob('*.txt'):
    f.rename(f.stem+'.json')

#Googleにログイン
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

#-----------------------------------------------------------------------------

#Discordの設定
Discord_token = settings.DT2
debug_channel_id = int(settings.DID)
channel = client.get_channel(debug_channel_id)

#Discordの接続に必要なオブジェクトを生成
client = discord.Client()
#DiscordBot起動時に動作する処理
@client.event
async def on_message(message):
    if message.author.bot:
      return
    if message.content == '/upload':
      #画像取得(時間割)
      file_id = drive.ListFile({'q': 'title = "upload.png"'}).GetList()[0]['id']
      f = drive.CreateFile({'id': file_id})
      f.GetContentFile('upload.png')
      os.remove('upload.png')
      os.rename('error.png', 'upload.png')
      f.Delete()
      f = drive.CreateFile()
      f.SetContentFile('upload.png')
      f.Upload()
      await channel.send('アップロード完了')
client.run(Discord_token)
