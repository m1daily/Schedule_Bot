import os    # 環境変数用
import time    # 待機
import tweepy    # Twitter送信
import requests    # LINE・Discord送信
import json    # webhook用
from dotenv import load_dotenv


load_dotenv()
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
imgur = os.environ['IMGUR']

#----------------------------------------------------------------------------------------------------
imgs_path = ['blob.png', 'now.png']
imgs_url = []

for i in imgs_path:
    headers = {'authorization': f'Client-ID {imgur}'}
    files = {'image': (open(i, 'rb'))}
    r = requests.post('https://api.imgur.com/3/upload', headers=headers, files=files)
    imgs_url.append(json.loads(r.text)['data']['link'])

# ツイート
media_ids = []
for image in imgs_path:
   img = api.media_upload(image)
   media_ids.append(img.media_id)
api.update_status(status='時間割が更新されました！', media_ids=media_ids)

# LINEへ通知
line_dict = {'公式グループ' : notify_group, '27組' : notify_27, '13組' : notify_13}
print('\n[LINE]')
for key, value in line_dict.items():
    for i, image in enumerate(imgs_path, 1):
        print(key + '-' + str(i) + '枚目: ' + line_notify(value, image))

# DiscordのWebhookを通して通知
payload2 = {'payload_json' : {'content' : '@everyone\n時間割が更新されました。(手動)'}}
embed = []
# 画像の枚数分"embed"の値追加
for i in imgs_url:
    if imgs_url.index(i) == 0:
        img_embed = {'color' : 10931421, 'url' : 'https://www.google.com/', 'image' : {'url' : i}}
    else:
        img_embed = {'url' : 'https://www.google.com/', 'image' : {'url' : i}}
    embed.append(img_embed)
payload2['payload_json']['embeds'] = embed
payload2['payload_json'] = json.dumps(payload2['payload_json'], ensure_ascii=False)
res = requests.post(webhook_url, data=payload2)
print('Discord_Webhook: ' + str(res.status_code))
print('投稿完了')
