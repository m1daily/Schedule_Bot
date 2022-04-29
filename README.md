# Schedule_Bot
Googleスプレッドシート上にある時間割が更新されたらTwitterとLINEにその時間割を投稿するBotです。
たまに真っ白な時間割が投稿される場合もありますが、その10分後にはちゃんとした時間割が投稿されるのでご安心を。
LINEで通知を受け取りたい場合は@M1_SchedulesのDMへどうぞ。


--------------------------------------------------------------------------------------
## [大雑把な解説]
1.10分おきにスプレッドシートが更新されているかどうかチェック	
2.今日スクショした時間割の画像をGoogleDriveへアップロード(明日比較するときに使用)
3.画像をツイートし、LINE Notify経由で送信してプログラム終了

--------------------------------------------------------------------------------------
## [細かく解説]

### 1.必要なモジュールをインポート
- バージョンを指定することでバグが発生しないようにしています。
```
import settings
import datetime
～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
```
