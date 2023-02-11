import ast
import base64  # blob対策
import datetime  # 日付取得
import json  # webhook用
import os  # 環境変数用
import subprocess  # GitHubActionsの環境変数追加
import time  # 待機
import urllib.request  # 画像取得
import cv2
import cv2u  # 画像URLから読み込み
import gspread
import numpy as np
import requests  # LINE・Discord送信
import tweepy  # Twitter送信
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver  # サイトから画像取得(以下略)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


#----------------------------------------------------------------------------------------------------
# バグが発生した場合様々が情報が必要になるため、日付を取得(日本時間)
date = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekdays = ['月', '火', '水', '木', '金', '土', '日']
time_now = date.strftime('[%Y年%m月%d日(' + weekdays[date.weekday()] + ') %H:%M:%S]')
print('\n' + time_now)
subprocess.run([f'echo "TIME={time_now}" >> $GITHUB_OUTPUT'], shell=True)

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

# tweepyの設定(認証情報を設定、APIインスタンスの作成)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# LINE,Discordのtoken設定(伏せています)
notify_group = os.environ['LINE_NOTIFY']    # 時間割LINEグループのトークン
notify_27 = os.environ['LINE_NOTIFY_27']    # 自分のクラスのライングループのトークン
notify_13 = os.environ['LINE_NOTIFY_13']    # 13組のライングループのトークン
webhook_url = os.environ['WEBHOOK']    # Discordの時間割サーバーのWebhookのURL
imgur = os.environ['IMGUR']    # 画像URL取得用

# LINEの設定
def line_notify(line_access_token, image):
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + line_access_token}
    payload = {'message': '時間割が更新されました。'}
    files = {'imageFile': open(image, 'rb')}
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    return str(r.status_code)

# 終了時用
def finish(exit_message):
    print(exit_message)
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
    js = """
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
    """
    js += "return getBinaryResourceText(\"{url}\");".format(url=url)

    data_bytes = driver.execute_script(js)
    with open('blob.jpeg', 'wb') as bin_out:
        bin_out.write(bytes(data_bytes))
    # result = driver.execute_async_script("""
    #     var url = arguments[0];
    #     var callback = arguments[1];
    #     var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
    #     var xhr = new XMLHttpRequest();
    #     xhr.responseType = 'arraybuffer';
    #     xhr.onload = function(){ callback(toBase64(xhr.response)) };
    #     xhr.onerror = function(){ callback(xhr.status) };
    #     xhr.open('GET', url);
    #     xhr.send();
    #     """, url)
    # if type(result) == int :
    #     raise Exception("Request failed with status %s" % result)
    # jpg = np.frombuffer(base64.b64decode(result), dtype=np.uint8)
    # cv2.imwrite('blob.jpeg', cv2.imdecode(jpg, cv2.IMREAD_COLOR))
    image = upload_imgur('blob.jpeg')
    return image



#----------------------------------------------------------------------------------------------------
# Chromeヘッドレスモード起動
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver', options=options)
driver.implicitly_wait(5)

# Googleスプレッドシートへ移動(URLは伏せています)
driver.get(os.environ['GOOGLE_URL'])    # 時間割の画像があるGoogleSpreadSheetのURL
WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located)
time.sleep(15)

# imgタグを含むものを抽出
imgs_tag = driver.find_elements(By.TAG_NAME, 'img')
if imgs_tag == []:
    finish('画像が発見できなかったため終了(img無)')

# 時間割の画像以外も取り出している場合があるため時間割の画像のみ抽出(GoogleSpreadSheet上の画像は画像URLの末尾が「alr=yes」)
imgs_cv2u_now = []    # cv2u用リスト(現在)
imgs_url_now = []     # URLリスト(現在)
print('[抽出画像]')
for index, e in enumerate(imgs_tag, 1):
    img_url = e.get_attribute('src')
    print(str(index) + '枚目: ' + img_url)
    # URLがBlob形式又は「alr=yes」が含まれる場合はImgurに画像アップロード
    if ('blob:' in img_url) or ('alr=yes' in img_url):
        if 'blob:' in img_url:
            img_url = get_blob_file(driver, img_url)
        else:
            img_url = upload_imgur(img_url)
        print(' → ' + img_url)
        if bool(str(cv2u.urlread(img_url)) in imgs_cv2u_now) == False:
            print(' → append')
            imgs_cv2u_now.append(str(cv2u.urlread(img_url)))
            imgs_url_now.append(img_url)
# 時間割の画像が見つからなかった場合は終了
if imgs_url_now == []:
    finish('画像が発見できなかったため終了(alr=yes無)')
print('\n-------------------------------------------------------------------------------------------------------------------------------------------------')
print(imgs_url_now)

# $GITHUB_OUTPUTに追加
now = ','.join(imgs_url_now)
subprocess.run([f'echo NOW={now} >> $GITHUB_OUTPUT'], shell=True)

#----------------------------------------------------------------------------------------------------
# Google SpreadSheetsにアクセス
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name('gss.json', scope))
ws = gc.open_by_key(os.environ['SHEET_ID']).sheet1

# 最後に投稿した画像のリストを読み込み
imgs_url_latest = ws.acell('C6').value.split()    # URLリスト(過去)
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
ws.update_acell('C6', ' \n'.join(imgs_url_now))
ws.update_acell('C3', 'https://github.com/Geusen/Schedule_Bot/actions/runs/' + str(os.environ['RUN_ID']))

#----------------------------------------------------------------------------------------------------`
# ツイート
# media_ids = []
# for image in imgs_path:
#    img = api.media_upload(image)
#    media_ids.append(img.media_id)
# api.update_status(status='時間割が更新されました！', media_ids=media_ids)

# # LINEへ通知
# line_dict = {'公式グループ' : notify_group, '27組' : notify_27, '13組' : notify_13}
# print('\n[LINE]')
# for key, value in line_dict.items():
#     for i, image in enumerate(imgs_path, 1):
#         print(key + '-' + str(i) + '枚目: ' + line_notify(value, image))

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
# res.raise_for_status()
# finish('投稿完了')
