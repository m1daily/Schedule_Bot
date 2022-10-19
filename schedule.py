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
dt = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
w_list = ['月', '火', '水', '木', '金', '土', '日']
time_now = dt.strftime('[%Y年%m月%d日(' + w_list[dt.weekday()] + ') %H:%M:%S]')
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
web_li = driver.find_elements(By.TAG_NAME, 'img')
if web_li == []:
    finish('画像が発見できなかったため終了')
# 時間割の画像以外も取り出している場合があるため時間割の画像のみ抽出(GoogleSpreadSheet上の画像は画像URLの末尾が「alr=yes」)
imgcv2u_n = []    # cv2u用リスト(現在)
imgurl_n = []     # URLリスト(現在)
for e in web_li:
    imgurl = e.get_attribute('src')
    # リストに既に同じ画像がない場合リストに追加
    if 'alr=yes' in imgurl and bool(str(cv2u.urlread(imgurl)) in imgcv2u_n) == False:
        imgcv2u_n.append(str(cv2u.urlread(imgurl)))
        imgurl_n.append(imgurl)
# 時間割の画像が見つからなかった場合は終了
if imgurl_n == []:
    finish('画像が発見できなかったため終了')
print(imgurl_n)

# $GITHUB_OUTPUTに追加
now = ','.join(imgurl_n)
subprocess.run([f'echo NOW={now} >> $GITHUB_OUTPUT'], shell=True)

#----------------------------------------------------------------------------------------------------
# 最後に投稿した画像のリストを読み込み
with open('url.txt', 'r') as f:
    imgurl_b = f.read().split()    # URLリスト(過去)
    f.close()
print(imgurl_b)
imgcv2u_b = []    # cv2u用リスト(過去)
for e in imgurl_b:
    imgcv2u_b.append(str(cv2u.urlread(e)))

# $GITHUB_OUTPUTに追加
before = ','.join(imgurl_b)
subprocess.run([f'echo BEFORE={before} >> $GITHUB_OUTPUT'], shell=True)

# 比較
if len(imgurl_n) == len(imgurl_b):
    if bool(set(imgcv2u_n) == set(imgcv2u_b)) == True:
        finish('画像が一致した為、終了')
    else:
        print('画像が一致しないので続行')
else:
    print('画像の枚数が異なるので続行')

#----------------------------------------------------------------------------------------------------
# 画像URLを使って画像をダウンロード
images = []    # 画像のファイル名用リスト
for i in imgurl_n:
    with urllib.request.urlopen(i) as web_file:
        time.sleep(5)
        data = web_file.read()
        img = str(imgurl_n.index(i) + 1) + '.png'    # ファイル名を"リストの順番.png"に
        images.append(img)
        with open(img, mode='wb') as local_file:
            local_file.write(data)

# # 上書き
# with open('url.txt', 'w') as f:
#     f.write(' \n'.join(imgurl_n))

# # MARKDOWN編集
# with open("README.md", encoding="utf-8") as f:
#     text_list = f.readlines()
# url = 'img.shields.io/badge/最終時間割更新-#' + str(os.environ['RUN_NUMBER']) + ' ' + time_now + '-0374b5.svg'
# text_list[2] = '<a href="https://github.com/Geusen/Schedule_Bot/actions/runs/' + str(os.environ['RUN_ID']) + '"><img src="https://' + urllib.parse.quote(url) + '"></a>\n'
# with open("README.md", mode='w', encoding='utf-8')as f:
#     f.writelines(text_list)

# #----------------------------------------------------------------------------------------------------
# # ツイート
# media_ids = []
# for image in images:
#    img = api.media_upload(image)
#    media_ids.append(img.media_id)
# api.update_status(status='時間割が更新されました！', media_ids=media_ids)

# # LINEへ通知
# line_list = [notify_group, notify_27, notify_13]    # 送信先のグループ
# for l in line_list:
#     for i in images:
#         line_notify(l, i)

# DiscordのWebhookを通して通知
payload2 = {'payload_json' : {'content' : '@everyone\n時間割が更新されました。','embeds': ''}}
embed = []
# 画像の枚数分"embed"の値追加
for i in imgurl_n:
    if imgurl_n.index(i) == 0:
        new_d = {'color' : 10931421, 'url' : 'https://www.google.com/','image' : {'url' : i}},
    else:
        new_d = {'url' : 'https://www.google.com/','image' : {'url' : i}},
    embed.append(new_d)
payload2['payload_json']['embeds'] = embed
payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
res = requests.post(webhook_url, data=payload2)
print(payload2)
print('Discord_Webhook: ' +str(res.status_code))
finish('投稿完了')
