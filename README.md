# Schedule_Bot  

## About

![update](img.shields.io/badge/%E6%9C%80%E7%B5%82%E6%99%82%E9%96%93%E5%89%B2%E6%9B%B4%E6%96%B0-%237449%20%5B2022%E5%B9%B410%E6%9C%8814%E6%97%A5%28%E9%87%91%29%2021%3A10%3A21%5D-blue.svg)

![twitter](https://img.shields.io/twitter/follow/mito1daily?label=%40mito1daily&style=social)

![actions](https://github.com/Geusen/Schedule_Bot/actions/workflows/Schedule.yml/badge.svg)

- Googleスプレッドシート上にある時間割が更新されたらTwitterとLINEとDiscordにその時間割を投稿するBotです。
- LINEで通知を受け取りたい場合は[@mito1daily](https://twitter.com/mito1daily)のDMへどうぞ。

--------------------------------------------------------------------------------------

## 大雑把な解説

1.10分おきにスプレッドシートが更新されているかどうかチェック  
2.もし更新されてるなら今日の時間割の画像のURLをurl.txtに保存(明日比較するときに使用)  
3.画像をツイートし、LINE Notify経由で送信してプログラム終了
