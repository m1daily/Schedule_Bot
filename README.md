# Schedule_Bot
- Googleスプレッドシート上にある時間割が更新されたらTwitterとLINEにその時間割を投稿するBotです。
- たまに真っ白な時間割が投稿される場合もありますが、その10分後にはちゃんとした時間割が投稿されるのでご安心を。
LINEで通知を受け取りたい場合は@M1_SchedulesのDMへどうぞ。<br><br><br><br>


--------------------------------------------------------------------------------------
### [大雑把な解説]
1.10分おきにスプレッドシートが更新されているかどうかチェック<br>
2.今日スクショした時間割の画像をGoogleDriveへアップロード(明日比較するときに使用)<br>
3.画像をツイートし、LINE Notify経由で送信してプログラム終了<br><br><br>

--------------------------------------------------------------------------------------
### [細かく解説]

#### 0.各ファイルの役割
```
Schedule_Bot
│  README.md  (このファイル)
│  client_secrets.json  (GoogleDriveアクセス用)
│  credentials.json  (〃)
│  schedule.py  (プログラムが記述してある)
│  settings.py  (環境変数関連)
│  settings.yaml  (GoogleDriveアクセス用)
│  
└─.github
    └─workflows
            Schedule.yml  (定期実行用ファイル)
```
ここからはschedule.pyの解説をしていきます。
<br>

#### 1.下準備～必要なモジュールをインポート～(1行目～16行目)
- バージョンを指定することでバグが発生しないようにしています。
  - バージョン変更により記述の仕方を変える必要があるモジュールが存在するからです。
```
import settings  (settings.pyから環境変数をインポート)
import datetime  (日付を扱う)
import tweepy  (Twitter投稿)
import os  (ファイル取得)
import time  (時間取得)
import requests  (LINE通知用)
import cv2   (画像比較)
import numpy as np  (〃)
from pydrive.auth import GoogleAuth  (GoogleDriveAPI用)
from pydrive.drive import GoogleDrive  (〃)
from PIL import Image  (画像トリミング)
from selenium import webdriver  (Gooleスプレッドシートから画像を取得)
from selenium.webdriver.chrome.options import Options  (〃)
from selenium.webdriver.common.by import By  (〃)
from selenium.webdriver.support.ui import WebDriverWait  (〃)
from selenium.webdriver.support import expected_conditions as EC  (〃)
```

[意味解説]
- 環境変数
  - リポジトリ内にあるファイル全てに使える変数
  - Schedule.ymlでsecretを環境変数に入れ、settings.pyで環境変数を楽に扱えるようにしている
- secret
  - 暗号化された環境変数
  - パスワードなどを記述しても誰も見ることができない
- API
  - 「Application Programming Interface」の略
  - 簡潔に言うと、他サービスの機能連携
   - TwitterAPIを導入するとPythonからツイートすることができたり、GoogleDriveAPIを導入するとPythonからファイルのアップロードができたりする
- Gooleスプレッドシート
  - Google版Excel
  - M1はこれに時間割の画像を貼り付けている
<br>

#### 2.下準備～時間取得、各サービス使用準備～(18行目～46行目)
- 18行目～23行目 時刻の取得
  - プログラムを実行したタイミングを記録しています。
  - [2022年04月1日(金) 10:30:45]という風に表示されます。

```
#バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
print('')
print(dt.strftime('[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]'))
```

- 24行目～36行目 Twitterの設定
  - Twitterへの投稿が可能になります。
  - 「settings.CK」はsettings.pyのCKという変数の中身を表しています。
- 38行目～41行目 LINEの設定
  - LINEへの画像、メッセージ送信が可能になります。
- 43行目～46行目 Googleにログイン
  - client_secrets.jsonなどのファイルを使ってログインしています。
```
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

#Googleにログイン
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
```

[意味解説]
- OAuth(オーオース)
  - 複数のWebサービスを連携して動作させるために使われる仕組み 
  - 通常、Webサービスを利用するためは、個別にユーザーIDとパスワードを入力してユーザーを認証する必要があるが、OAuthを利用することで、IDやパスワードを入力することなく、アプリケーション間の連動ができる(アクセストークンなどが必要)
- Token(トークン)
