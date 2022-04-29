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
Schedule_Bot
│  a.txt
│  client_secrets.json
│  credentials.json
│  README.md
│  schedule.py
│  settings.py
│  settings.yaml
│  
└─.github
    └─workflows
            Schedule.yml

#### 1.必要なモジュールをインポート(1行目～16行目)
- バージョンを指定することでバグが発生しないようにしています。
  - バージョンが変更されると記述の仕方を変える必要があるモジュールが存在するからです。
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
from selenium import webdriver  (スプレッドシートから画像を取得)
from selenium.webdriver.chrome.options import Options  (〃)
from selenium.webdriver.common.by import By  (〃)
from selenium.webdriver.support.ui import WebDriverWait  (〃)
from selenium.webdriver.support import expected_conditions as EC  (〃)
```

[意味解説]
- 環境変数
  - リポジトリ内にあるファイル全てに使える変数
  - Schedule.ymlでsecret を環境変数に入れている
