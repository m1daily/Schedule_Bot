# 標準ライブラリ
import re  # 正規表現用
import subprocess  # GitHubActionsの環境変数追加
from logging import DEBUG, Formatter, StreamHandler, getLogger  # ログ出力
# サードパーティライブラリ
from PIL import Image, ImageDraw, ImageFont  # 画像処理


#-----------------------------------------------------------------------------------------------------------------------------------
# ログ設定
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
format = Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.info("セットアップ完了")

with open("news/test.txt", mode="r", encoding="utf-8") as file:
  schedule = file.read()
logger.info("要素抽出完了\n")

#-----------------------------------------------------------------------------------------------------------------------------------
# 外観調整
schedule = schedule.replace("変更の場合あり", "").replace("※", "").split("\n")
schedule = list(filter(None, schedule))
li = []
subprocess.run(["echo '::group::parts'"], shell=True)
for i in range(len(schedule)):
    news = schedule[i].translate(str.maketrans({"　": "", " ": "", "（": "(", "）": ")", u"\xa0": "", u"\u3000": ""}))  # 余計なスペースを削除、全角括弧を半角括弧に変換
    news = news.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))  # 全角数字を半角数字に変換
    news = news.strip()  # 文字列の先頭と末尾の空白を削除
    if not news:  # newsが空の場合、continue
        continue
    if re.match("\d", news[0]) is not None:  # 先頭が数字の場合
        day_pattern = news[:news.find("(")]  # (の前の部分を取得
        if "/" in day_pattern:  # 日付部分に/が含まれている場合 例: 1/6日(月)教職員代休(1/12)
            if i == 0:  # 1つ目の要素の場合
                day_delete = day_pattern.find("/")  # /で分割
                news = news[day_delete + 1:]  # 例: 6日(月)教職員代休(1/12)
                check = "number(1)"
            else:
                news = "、" + news  # カンマを追加(文字列の場合と同じ扱い)
                check = "number(/)"
        else:
            news = "\n" + news
            check = "number"
    else:  # 先頭が文字列の場合、カンマを追加
        news = "、" + news
        check = "string"
    li.append(news)
    subprocess.run([f"echo '{news} [{check}]'"], shell=True)
subprocess.run(["echo '::endgroup::'"], shell=True)
li = [i for i in li if i != ""]  # 空の要素を削除
li[0] = li[0].replace("\n", "")
txt = "".join(li)
logger.info(txt)

#-----------------------------------------------------------------------------------------------------------------------------------
# 画像に文字を入れる
length = 0
for i in txt.split("\n"):
    if len(i) > length:
        length = len(i)
im = Image.new("RGB", ((length+1)*12, (txt.count("\n")+2)*24+20), (256, 256, 256))
draw = ImageDraw.Draw(im)
font = ImageFont.truetype("./news/NotoSansCJKjp-Light.otf", 12)
draw.text((20, 10), txt, fill=(0, 0, 0), font=font, spacing=12)
im.save("image.png")
logger.info("画像化完了\n")
