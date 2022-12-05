# Schedule_Bot

<a href="https://github.com/Geusen/Schedule_Bot/actions/runs/3617509221"><img src="https://img.shields.io/badge/%E6%9C%80%E7%B5%82%E6%99%82%E9%96%93%E5%89%B2%E6%9B%B4%E6%96%B0-%239167%20%5B2022%E5%B9%B412%E6%9C%8805%E6%97%A5%28%E6%9C%88%29%2015%3A24%3A31%5D-0374b5.svg"></a>

<img src='https://github.com/Geusen/Schedule_Bot/actions/workflows/Schedule.yml/badge.svg'>&emsp;<img src='https://img.shields.io/github/last-commit/Geusen/Schedule_Bot?label=%E3%83%AA%E3%83%9D%E3%82%B8%E3%83%88%E3%83%AA%E6%9C%80%E7%B5%82%E6%9B%B4%E6%96%B0'>

<img src='https://www.codefactor.io/repository/github/geusen/schedule_bot/badge'><br><br>

## About

- Googleスプレッドシート上にある時間割が更新されたらTwitterとLINEとDiscordにその時間割を投稿するBotです。

- LINEで通知を受け取りたい場合は&ensp;<a href='https://twitter.com/mito1daily'><img src='https://img.shields.io/twitter/follow/mito1daily?label=%40mito1daily&style=social'></a>&ensp;のDMへどうぞ。<br><br>

## 大雑把な解説

1.10分おきにスプレッドシートが更新されているかどうかチェック<br>
2.もし更新されてるなら今日の時間割の画像のURLをurl.txtに保存(明日比較するときに使用)<br>
3.画像をTwitter、LINE、Discordに送信してプログラム終了
