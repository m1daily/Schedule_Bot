import settings
import requests
import time
import datetime
from PIL import Image
from bs4 import BeautifulSoup
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
#---------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(10)

# ウインドウ幅、高さ指定
windowSizeWidth = 1000
windowSizeHeight = 1000

# サイトURL取得
driver.get('https://translate.google.co.jp/translate?u=https%3A%2F%2Fopenweathermap.org%2Fcity%2F2111901')
WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
  
# ウインドウ幅・高さ指定
windowWidth = windowSizeWidth if windowSizeWidth else driver.execute_script('return document.body.scrollWidth;')
windowHeight = windowSizeHeight if windowSizeHeight else driver.execute_script('return document.body.scrollHeight;')
driver.set_window_size(windowWidth, windowHeight)
time.sleep(4)

# スクリーンショット格納
driver.save_screenshot('before.png')

# サーバー負荷軽減処理
time.sleep(1)

# ブラウザ稼働終了
driver.quit()

# 画像トリミング
im = Image.open('before.png')
im.crop((535, 490, 920, 870)).save('upload.png', quality=95)
print("トリミング完了")
#-----------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
token = settings.LT

#LINEの設定(伏せています)
line_url = 'https://notify-api.line.me/api/notify'
line_access_token = token
headers = {'Authorization': 'Bearer ' + line_access_token}
line_message = 'test2'
line_image = 'upload.png'
payload = {'message': line_message}
files = {'imageFile': open(line_image, 'rb')}
r = requests.post(line_url, headers=headers, params=payload, files=files,)
print("通知完了")
