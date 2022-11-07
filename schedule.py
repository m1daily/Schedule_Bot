import datetime    # 日付取得
import os    # 環境変数用
import time    # 待機
import subprocess    # GitHubActionsの環境変数追加
import cv2u    # 画像URLから読み込み
import urllib.parse    # urlエンコード
import tweepy    # Twitter送信
import requests    # LINE・Discord送信
import json    # webhook用
import urllib.request    # 画像取得
from selenium import webdriver    # サイトから画像取得(以下略)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


#----------------------------------------------------------------------------------------------------
# バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
date = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekdays = ['月', '火', '水', '木', '金', '土', '日']
time_now = date.strftime('[%Y年%m月%d日(' + weekdays[date.weekday()] + ') %H:%M:%S]')
print('\n' + time_now)
subprocess.run([f'echo "TIME={time_now}" >> $GITHUB_OUTPUT'], shell=True)

#----------------------------------------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']    # TwitterAPI識別キー
consumer_secret = os.environ['CONSUMER_SECRET']    # TwitterAPI識別シークレットキー
access_token = os.environ['ACCESS_TOKEN']    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']    # Twitterアカウントに対するアクセストークンシークレット

# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# LINEの設定
def line_notify(line_access_token, image):
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + line_access_token}
    payload = {'message': '時間割が更新されました。'}
    files = {'imageFile': open(image, 'rb')}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    return str(r.status_code)

# LINE,Discordのtoken設定(伏せています)
notify_group = os.environ['LINE_NOTIFY']    # 時間割LINEグループのトークン
notify_27 = os.environ['LINE_NOTIFY_27']    # 自分のクラスのライングループのトークン
notify_13 = os.environ['LINE_NOTIFY_13']    # 13組のライングループのトークン
webhook_url = os.environ['WEBHOOK']    # Discordの時間割サーバーのWebhookのURL

# 終了時用
def finish(exit_message):
    print(exit_message)
    subprocess.run([f'echo STATUS={exit_message} >> $GITHUB_OUTPUT'], shell=True)
    exit()

#----------------------------------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(5)

# Googleスプレッドシートへ移動(URLは伏せています)
driver.get(os.environ['GOOGLE_URL'])    # 時間割の画像があるGoogleSpreadSheetのURL
WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located)
time.sleep(5)

# imgタグを含むものを抽出
imgs_tag = driver.find_elements(By.TAG_NAME, 'img')
if imgs_tag == []:
    finish('画像が発見できなかったため終了')
# 時間割の画像以外も取り出している場合があるため時間割の画像のみ抽出(GoogleSpreadSheet上の画像は画像URLの末尾が「alr=yes」)
imgs_cv2u_now = []    # cv2u用リスト(現在)
imgs_url_now = []     # URLリスト(現在)
for e in imgs_tag:
    img_url = e.get_attribute('src')
    # リストに既に同じ画像がない場合リストに追加
    if 'alr=yes' in img_url and bool(str(cv2u.urlread(img_url)) in imgs_cv2u_now) == False:
        imgs_cv2u_now.append(str(cv2u.urlread(img_url)))
        imgs_url_now.append(img_url)
# 時間割の画像が見つからなかった場合は終了
if imgs_url_now == []:
    finish('画像が発見できなかったため終了')
print(imgs_url_now)

# $GITHUB_OUTPUTに追加
now = ','.join(imgs_url_now)
subprocess.run([f'echo NOW={now} >> $GITHUB_OUTPUT'], shell=True)

#----------------------------------------------------------------------------------------------------
# 最後に投稿した画像のリストを読み込み
with open('url.txt', 'r') as f:
    imgs_url_latest = f.read().split()    # URLリスト(過去)
print(imgs_url_latest)
imgs_cv2u_latest = []    # cv2u用リスト(過去)
for e in imgs_url_latest:
    imgs_cv2u_latest.append(str(cv2u.urlread(e)))

# $GITHUB_OUTPUTに追加
before = ','.join(imgs_url_latest)
subprocess.run([f'echo BEFORE={before} >> $GITHUB_OUTPUT'], shell=True)

# 比較
if len(imgs_url_now) == len(imgs_url_latest):
    if bool(set(imgs_cv2u_now) == set(imgs_cv2u_latest)) == True:
        finish('画像が一致した為、終了')
    else:
        print('画像が一致しないので続行')
else:
    print('画像の枚数が異なるので続行')

#----------------------------------------------------------------------------------------------------
# 画像URLを使って画像をダウンロード
imgs_path = []    # 画像のファイル名用リスト
for i in imgs_url_now:
    with urllib.request.urlopen(i) as web_file:
        time.sleep(5)
        data = web_file.read()
        img = str(imgs_url_now.index(i) + 1) + '.png'    # ファイル名を"リストの順番.png"に
        imgs_path.append(img)
        with open(img, mode='wb') as local_file:
            local_file.write(data)

# 上書き
with open('url.txt', 'w') as f:
    f.write(' \n'.join(imgs_url_now))

# MARKDOWN編集
with open("README.md", encoding="utf-8") as f:
    markdown_texts = f.readlines()
url = 'img.shields.io/badge/最終時間割更新-#' + str(os.environ['RUN_NUMBER']) + ' ' + time_now + '-0374b5.svg'
markdown_texts[2] = '<a href="https://github.com/Geusen/Schedule_Bot/actions/runs/' + str(os.environ['RUN_ID']) + '"><img src="https://' + urllib.parse.quote(url) + '"></a>\n'
with open("README.md", mode='w', encoding='utf-8')as f:
    f.writelines(markdown_texts)

#----------------------------------------------------------------------------------------------------
# # ツイート
# media_ids = []
# for image in imgs_path:
#    img = api.media_upload(image)
#    media_ids.append(img.media_id)
# api.update_status(status='時間割が更新されました！', media_ids=media_ids)

# # LINEへ通知
# line_list = [notify_group, notify_27, notify_13]    # 送信先のグループ
# print('[LINE]')
# for ll, line in enumerate(line_list, 1):
#     for i, image in enumerate(imgs_path, 1):
#         print(str(ll) + '-' + str(i) + ': ' + line_notify(line, image))

# # DiscordのWebhookを通して通知
# payload2 = {'payload_json' : {'content' : '@everyone\n時間割が更新されました。'}}
# embed = []
# # 画像の枚数分"embed"の値追加
# for i in imgs_url_now:
#     if imgs_url_now.index(i) == 0:
#         img_embed = {'color' : 10931421, 'url' : 'https://www.google.com/', 'image' : {'url' : i}}
#     else:
#         img_embed = {'url' : 'https://www.google.com/', 'image' : {'url' : i}}
#     embed.append(img_embed)
# payload2['payload_json']['embeds'] = embed
# payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
# res = requests.post(webhook_url, data=payload2)
# print('Discord_Webhook: ' + str(res.status_code))
# finish('投稿完了')
