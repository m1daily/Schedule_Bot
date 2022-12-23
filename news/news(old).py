import os    # 環境変数用
import time    # 待機
import cv2
import numpy as np
import tweepy    # Twitter送信
import requests    # LINE・Discord送信
import json    # webhook用
from selenium import webdriver    # サイトから画像取得(以下略)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager


#----------------------------------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--disable-gpu')
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(5)

# M1のサイトへ移動
driver.get('https://www.mito1-h.ibk.ed.jp/')
WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located)
time.sleep(10)
now = driver.find_element(By.XPATH, '/html/body/main/div/div[2]/div/div/section[3]').screenshot_as_png
driver.close()

with open('news/now.png', 'wb') as f:
    f.write(now)
before_img = cv2.imread('news/news.png')
now_img = cv2.imread('news/now.png')
if np.array_equal(before_img, now_img) == True:
    print('更新されていないので終了')
    exit()
else:
    print('更新されているので続行')

with open('news/news.png', 'wb') as f:
    f.write(now)

#-----------------------------------------------------------------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

# tweepyの設定(認証情報を設定,APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# ツイート
api.update_status_with_media(status='今月の予定です。', filename='./news/news.png')

#-----------------------------------------------------------------------------------------------------------------------------------
# Discordに投稿
webhook_url = os.environ['WEBHOOK']
payload2 = {
    'payload_json' : {
        'content' :'今月の予定です。',
        'embeds': [
            {
                'color' : 5419910,
                'footer': {
                    'icon_url' : 'https://raw.githubusercontent.com/Geusen/images/main/m1.jpg',
                    'text' : 'By 水戸一高時間割Bot'},
                'image': {
                    'url' : 'attachment://news.png'
                }
            }
        ]
    }
}
with open('./news/news.png', 'rb') as f:
    file_bin_image = f.read()
files_qiita = {
    'image' : ('./news/news.png', file_bin_image),
}
payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
res = requests.post(webhook_url, files = files_qiita, data = payload2)
