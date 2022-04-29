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
<br>
#### 1.下準備～必要なモジュールをインポート～(1行目～16行目)
- バージョンを指定することでバグが発生しないようにしています。
  - バージョン変更により記述の仕方を変える必要があるモジュールが存在するからです。
```
[Shedules.py]
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
