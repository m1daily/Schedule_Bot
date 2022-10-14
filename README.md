# Schedule_Bot  

## About

#7443[2022年10月14日(金) 20:47:03]

![twitter](https://img.shields.io/twitter/follow/mito1daily?label=%40mito1daily&style=social)

![actions](https://github.com/Geusen/Schedule_Bot/actions/workflows/Schedule.yml/badge.svg)

- Googleスプレッドシート上にある時間割が更新されたらTwitterとLINEとDiscordにその時間割を投稿するBotです。
- LINEで通知を受け取りたい場合は[@mito1daily](https://twitter.com/mito1daily)のDMへどうぞ。

--------------------------------------------------------------------------------------

## 大雑把な解説

1.10分おきにスプレッドシートが更新されているかどうかチェック  
2.もし更新されてるなら今日の時間割の画像のURLをurl.txtに保存(明日比較するときに使用)  
3.画像をツイートし、LINE Notify経由で送信してプログラム終了
