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

#### 1.必要なモジュールをインポート(1行目～18行目)
- バージョンを指定することでバグが発生しないようにしています。
  - バージョンが変更されると記述の仕方を変える必要があるモジュールが存在するからです。
```
import settings  (環境変数をインポート)
import datetime  (日付を扱う)
import tweepy  (Twitter投稿)
import shutil  (ファイル操作)
import os  (〃)
import time  ()
import requests  ()
import cv2   (画像比較)
import numpy as np  (〃)
import pprint  ()
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
  - 
