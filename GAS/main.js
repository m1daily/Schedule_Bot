function doPost(e) {
  const json = JSON.parse(e.postData.contents).events[0];
  try {
    // LINEの情報取得
    const replyToken = json.replyToken;
    const type = json.type;
    const lineToken = PropertiesService.getScriptProperties().getProperty("TOKEN");

    // ポストバックかテキストの場合のみ続行
    let userMessage = "";
    if (type === "postback") {
      userMessage = json.postback.data;
    } else if (type === "message") {
      userMessage = json.message.text.toLowerCase();
    } else {
      return false;
    };

    // スプレッドシートシートの設定
    const ss = SpreadsheetApp.getActive();

    // 返信するメッセージを取得
    const messages = swhich_Message(ss, userMessage, json);
    if (!messages.length) {
      return false;
    };  

    // APIリクエスト時にセットするペイロード値設定
    const payload = {
      "replyToken": replyToken,
      "messages": messages
    };

    //HTTPSのPOST時のオプションパラメータ設定
    const options = {
      "payload": JSON.stringify(payload),
      "myamethod": "POST",
      "headers": { "Authorization": `Bearer ${lineToken}` },
      "contentType": "application/json",
      "muteHttpExceptions": true
    };

    // LINE Messaging APIリクエスト
    UrlFetchApp.fetch("https://api.line.me/v2/bot/message/reply", options);

    //コマンドカウント
    count(ss, userMessage);
  } catch (ee) {
    // LINEの情報取得
    const ss = SpreadsheetApp.getActive();
    debug2(`${json.message.text}`, `${json.message}`, ss, "debug2");
    error(ee, ss);
  };
}


//-------------------------------------------------------------------------------------------------------------
// LINEのメッセージ次第で画像,予定等取得
function swhich_Message(ss, userMessage, json) {
  try {
    let messages = [];
    switch (userMessage) {
      case "予定+時間割":
        messages = messages.concat(get_schedules(ss));
        messages = messages.concat(parse_images());
        messages = messages.concat(add_info(ss));
        break;
      case "予定":
        messages = messages.concat(get_schedules(ss));
        break;
      case "時間割":
        messages = messages.concat(parse_images());
        break;
      case "月間予定":
        messages = messages.concat(month(ss));
        break;
      case "ニュース":
        messages = messages.concat(get_news(ss));
        break;
      case "テーマ":
        messages = messages.concat(get_themes(ss));
        break;
      case userMessage.startsWith("themechanged") && userMessage:
        messages = messages.concat(change_theme(ss, userMessage.split("-")[1], json.source.userId));
        count(ss, "テーマ変更");
        break;
      case "辞書":
        messages = messages.concat(get_word(ss));
        break;
      case "error175":
        messages = messages.concat(error_test());
        break;
      default:
        messages = messages.concat(commands(ss, userMessage));
        break;
    };
    return messages;
  } catch (e) {
    return error(e, ss);
  };
}
