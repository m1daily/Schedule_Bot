# 標準ライブラリ
import ast  # 文字列→JSON
import datetime  # 日付取得
import json  # JSONファイル読み込み
import os  # GitHubActionsの環境変数追加
import subprocess  # GitHubActionsの環境変数追加
import time  # スリープ用
import urllib.request  # 画像取得
from logging import DEBUG, Formatter, StreamHandler, getLogger
# サードパーティライブラリ
import cv2u  # 画像URLから読み込み
import gspread  # SpreadSheet操作
import requests  # LINE・Discord送信
import tweepy  # Twitter送信
from oauth2client.service_account import ServiceAccountCredentials  # SpreadSheet操作
from selenium import webdriver  # ブラウザ操作
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

#----------------------------------------------------------------------------------------------------
# 日付取得
date = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekdays = ['月', '火', '水', '木', '金', '土', '日']
time_now = date.strftime('[%Y年%m月%d日(' + weekdays[date.weekday()] + ') %H:%M:%S]')
subprocess.run([f'echo "TIME={time_now}" >> $GITHUB_OUTPUT'], shell=True)

# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(format)
logger.addHandler(handler)

#----------------------------------------------------------------------------------------------------
# jsonファイル準備(SpreadSheetログイン用)
dic = ast.literal_eval(os.environ['JSON'])
with open('gss.json', mode='wt', encoding='utf-8') as file:
    json.dump(dic, file, ensure_ascii=False, indent=2)

# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = os.environ['CONSUMER_KEY']    # TwitterAPI識別キー
consumer_secret = os.environ['CONSUMER_SECRET']    # TwitterAPI識別シークレットキー
access_token = os.environ['ACCESS_TOKEN']    # Twitterアカウントに対するアクセストークン
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']    # Twitterアカウントに対するアクセストークンシークレット

# LINE,Discordのtoken設定(伏せています)
line_dict = ast.literal_eval(os.environ['LINE_NOTIFY'])    # INEグループのトークン
webhook_url = os.environ['WEBHOOK']    # Discordの時間割サーバーのWebhookのURL
imgur = os.environ['IMGUR']    # 画像URL取得用

# LINEの設定
def line_notify(line_access_token, image):
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + line_access_token}
    payload = {'message': '時間割が更新されました。'}
    files = {'imageFile': open(image, 'rb')}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    r.raise_for_status()
    return str(r.status_code)

# 終了時用
def finish(exit_message):
    logger.info(f'{exit_message}\n')
    subprocess.run([f'echo STATUS={exit_message} >> $GITHUB_OUTPUT'], shell=True)
    exit()

# Imgurアップロード
def upload_imgur(image):
    headers = {'authorization': f'Client-ID {imgur}'}
    if 'http' in image:
        with urllib.request.urlopen(image) as web_file:
            time.sleep(3)
            data = web_file.read()
            with open('imgur.png', mode='wb') as local_file:
                local_file.write(data)
            image = 'imgur.png'
    files = {'image': (open(image, 'rb'))}
    time.sleep(2)
    r = requests.post('https://api.imgur.com/3/upload', headers=headers, files=files)
    r.raise_for_status()
    return json.loads(r.text)['data']['link']

# blob形式のURLの対策
def get_blob_file(driver, url):
    js = '''
    var getBinaryResourceText = function(url) {
        var req = new XMLHttpRequest();
        req.open('GET', url, false);
        req.overrideMimeType('text/plain; charset=x-user-defined');
        req.send(null);
        if (req.status != 200) return '';
        var filestream = req.responseText;
        var bytes = [];
        for (var i = 0; i < filestream.length; i++){
            bytes[i] = filestream.charCodeAt(i) & 0xff;
        }
        return bytes;
    }
    '''
    js += 'return getBinaryResourceText("{url}");'.format(url=url)
    data_bytes = driver.execute_script(js)
    with open('blob.png', 'wb') as bin_out:
        bin_out.write(bytes(data_bytes))
    image = upload_imgur('blob.png')
    return image

#----------------------------------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver', options=options)
driver.implicitly_wait(5)
logger.info('セットアップ完了')

# Googleスプレッドシートへ移動(URLは伏せています)
driver.get(os.environ['GOOGLE_URL'])    # 時間割の画像があるGoogleSpreadSheetのURL
WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located)
time.sleep(10)

# imgタグを含むものを抽出
imgs_tag = driver.find_elements(By.TAG_NAME, 'img')
if imgs_tag == []:
    finish('画像が発見できなかったため終了(img無)')
logger.info('imgタグ抽出\n')

# 時間割の画像のみ抽出
imgs_cv2u_now = []    # cv2u用リスト(現在)
imgs_url_now = []     # URLリスト(現在)
for index, e in enumerate(imgs_tag, 1):
    img_url = e.get_attribute('src')
    logger.info(f'{index}枚目: {img_url}')
    # URLがBlob形式又は「alr=yes」が含まれる場合はImgurに画像アップロード
    if ('blob:' in img_url) or ('alr=yes' in img_url):
        if 'blob:' in img_url:
            img_url = get_blob_file(driver, img_url)
        else:
            img_url = upload_imgur(img_url)
        logger.info(f' → {img_url}')
        if bool(str(cv2u.urlread(img_url)) in imgs_cv2u_now) == False:
            logger.info(' → append')
            imgs_cv2u_now.append(str(cv2u.urlread(img_url)))
            imgs_url_now.append(img_url)
# 時間割の画像が見つからなかった場合は終了
if imgs_url_now == []:
    finish('画像が発見できなかったため終了(alr=yes無)')
logger.info(f'現在の画像:{imgs_url_now}')

# $GITHUB_OUTPUTに追加
now = ','.join(imgs_url_now)
subprocess.run([f'echo NOW={now} >> $GITHUB_OUTPUT'], shell=True)

#----------------------------------------------------------------------------------------------------
# Googleスプレッドシートへのアクセス
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name('gss.json', scope))
ws = gc.open_by_key(os.environ['SHEET_ID']).sheet1

# 最後に投稿した画像のリストを読み込み
imgs_url_latest = ws.acell('C6').value.split()    # URLリスト(過去)
logger.info(f'過去の画像:{imgs_url_latest}\n')
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
        logger.info('画像が一致しないので続行')
else:
    logger.info('画像の枚数が異なるので続行')

#----------------------------------------------------------------------------------------------------
# 画像URLを使って画像をダウンロード
imgs_path = []    # ダウンロードする画像のパスを格納するリスト
for i in imgs_url_now:
    with urllib.request.urlopen(i) as web_file:
        time.sleep(5)
        data = web_file.read()
        img = str(imgs_url_now.index(i) + 1) + '.png'    # 画像の名前を1.png,2.png,...とする
        imgs_path.append(img)
        with open(img, mode='wb') as local_file:
            local_file.write(data)

# GoogleSpreadSheetsに画像URLを書き込み
ws.update_acell('C2', time_now)
ws.update_acell('C6', ' \n'.join(imgs_url_now))
ws.update_acell('C3', 'https://github.com/m1daily/Schedule_Bot/actions/runs/' + str(os.environ['RUN_ID']))
logger.info('画像DL完了、セル上書き完了\n')

#----------------------------------------------------------------------------------------------------
# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Twitterに投稿
media_ids = []
for image in imgs_path:
   img = api.media_upload(image)
   media_ids.append(img.media_id)
api.update_status(status='時間割が更新されました！', media_ids=media_ids)
logger.info('Twitter: ツイート完了')

# LINE Notifyに通知
logger.info('LINE:')
for key, value in line_dict.items():
    for i, image in enumerate(imgs_path, 1):
        logger.info(f'{key}-{i}枚目: {line_notify(value, image)}')

# Discordに通知
payload2 = {'payload_json' : {'content' : '@everyone\n時間割が更新されました。'}}
embed = []
# 画像の枚数分"embed"の値追加
for i in imgs_url_now:
    if imgs_url_now.index(i) == 0:
        img_embed = {'color' : 10931421, 'url' : 'https://www.google.com/', 'image' : {'url' : i}}
    else:
        img_embed = {'url' : 'https://www.google.com/', 'image' : {'url' : i}}
    embed.append(img_embed)
payload2['payload_json']['embeds'] = embed
payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
r = requests.post(webhook_url, data=payload2)
logger.info(f'Discord: {r.status_code}')
r.raise_for_status()

# One SignalでWeb Push通知
headers = {'Authorization': 'Basic ' + os.environ['API_KEY'], 'accept': 'application/json', 'content-type': 'application/json'}
json_data = {
    'included_segments': [
        'Subscribed Users',
        'Active Users',
        'Inactive Users',
    ],
    'contents': {
        'en': '時間割が更新されました。',
        'ja': '時間割が更新されました。',
    },
    'name': 'mito1daily',
    'app_id': os.environ['APP_ID'],
}
r = requests.post('https://onesignal.com/api/v1/notifications', headers=headers, json=json_data)
logger.info(f'One Signal: {r.status_code}')
r.raise_for_status()
finish('投稿完了')
