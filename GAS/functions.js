function test() {
  const a = 1;
  try {
    const ss = SpreadsheetApp.getActive();
    const b = 2;
    debug2(b, `s`, ss, "debug2");
    throw new Error("aaa")
  } catch (e) {
    console.log(a);
  }
}

function test2() {
  const ss = SpreadsheetApp.getActive();
  console.log(swhich_Message(ss, "予定+時間割", ""));
}


function dict() {
  return [];
}


//-------------------------------------------------------------------------------------------------------------
// 2次元配列の検索
function search_2dArray(array, value) {
  let index = 0;
  while (array[index][0] != value) {
    index++;
    if (index == array.length) {
      return false;
    };
  };
  return index;
}


// LINEで返信するのに必要なメッセージレスポンスの形式で返す
function make_Response(value, type) {
  let response = "";
  switch (type) {
    case "text":
      response = [{
        "type": "text",
        "text": value
      }];
      return response;
    case "image":
      response = [{
        "type": "image",
        "originalContentUrl": value,
        "previewImageUrl": value
      }];
      return response;
    default:
      return [];
  };
}


// エラーのテスト
function error_test() {
  try {
    throw new Error("error_test");
  } catch (e) {
    const ss = SpreadsheetApp.getActive();
    return error(e, ss);
  };
}


// エラーメッセージ
function error(e, ss) {
  debug(e, ss);
  return [{
    "type": "text",
    "text": `エラーが発生しました。\nエラー内容:\n${e}\n\nhttps://works.do/R/ti/p/schedule@mito1daily\nもし「最新情報」でエラー発生中といったメッセージが確認できなかった場合は、↑から作者の公式アカウントを追加して連絡をいただけると助かります。連絡する場合は↑のエラー内容も伝えてください。`
  }];
}


// スプレッドシートにエラー出力
function debug(e, ss) {
  const sheet = ss.getSheetByName("debug");
  const targetRow = sheet.getLastRow() + 1;
  const date = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy/MM/dd HH:mm:ss");
  const values = [targetRow - 1, date, e, e.stack];
  sheet.getRange(`A${targetRow}:D${targetRow}`).setValues([values]);
}


// スプレッドシートに自由に出力
function debug2(value, message, ss, sheet_name) {
  const sheet = ss.getSheetByName(sheet_name);
  const targetRow = sheet.getLastRow() + 1;
  const date = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy/MM/dd HH:mm:ss");
  const values = [targetRow - 1, date, value, message];
  sheet.getRange(`A${targetRow}:D${targetRow}`).setValues([values]);
}


// カウンター
function count(ss, value) {
  const sheet = ss.getSheetByName("count");
  let items = sheet.getDataRange().getValues();
  items.shift();  // 先頭はデータではないので削除
  const index = search_2dArray(items, value);
  if (typeof (index) != "number") {
    return false;
  };
  let values = items[index];

  // 値増加
  for (let i = 1; i < values.length; i++) {
    if (!isNaN(values[i])) { // セルが数値の場合のみ
      values[i] = values[i] + 1;
    } else {
      values[i] = 1; // セルが数値でない場合は1に設定
    };
  };
  sheet.getRange(`A${index + 2}:E${index + 2}`).setValues([values]);
}


//-------------------------------------------------------------------------------------------------------------
// 次の予定のテキストを取得
function get_schedules(ss) {
  try {
    // 現在の月日取得
    const time = new Date();
    const m = time.getMonth() + 1;
    const d = time.getDate();
    const h = Utilities.formatDate(time, "JST", "HH");

    // 現在の月を元に月間予定データを取得
    let items = ss.getSheetByName("month").getDataRange().getValues();
    items.shift();  // 先頭はデータではないので削除
    const index = search_2dArray(items, m);
    if (typeof (index) == "number") {
      // 日付と予定のデータをそれぞれ用意
      const monthData = items[index][1].split("\n");
      const days = [];
      const schedules = [];
      for (let dayData of monthData) {
        const day = `${dayData.split(")", 1)[0]})`;  //例) "8日(水)R、土曜課外(1)" => ["8日(水"] => "8日(水)"
        const schedule = dayData.replace(day, "");
        days.push(day);
        schedules.push(schedule);
      };

      // 予定送信
      for (let i = 0; i < days.length; i++) {
        const day = parseInt(days[i].split("日", 1)[0]);  //例) "8日(水)" => 8
        // 午前中はその日の予定を返す, 午後なら次の日の予定を返す
        if ((h < 12 && d == day) || (d < day)) {
          return make_Response(`${days[i]}に ${schedules[i]} があります。`, "text");
        };
      };
    };

    // 予定が見つからなかった場合は翌月の最初の予定を返す
    const nextIndex = search_2dArray(items, m + 1);
    if (typeof (nextIndex) == "number") {
      const nextMonthData = items[nextIndex][1].split("\n");
      const firstDayData = nextMonthData[0];
      const firstDay = `${firstDayData.split(")", 1)[0]})`
      const firstSchedule = firstDayData.replace(firstDay, "");
      return make_Response(`${m + 1}月${firstDay}に ${firstSchedule} があります。`, "text");
    } else {
      return make_Response("次の予定はまだ公開されていません。このメッセージが長期間続くなら以下のアカウントに連絡をお願いします。\n\nhttps://works.do/R/ti/p/schedule@mito1daily", "text");
    };
  } catch (e) {
    return error(e, ss);
  };
}


// Parserライブラリで時間割画像取得
function parse_images() {
  try {
    let images = [];
    const response = UrlFetchApp.fetch("https://docs.google.com/spreadsheets/d/1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U/htmlview");
    const content = response.getContentText("utf-8");
    // const image_urls = Parser.data(content).from('<img src="').to('" style="').iterate();
    const image_urls = Parser.data(content).from("<img src='").to("' style").iterate();
    console.log(image_urls);

    // urlかどうかチェック
    let urls = [];
    for (let url of image_urls) {
      if (url.slice(0, 8) == "https://") {
        urls.push(url);
      };
    };
    if (!urls.length) {
      const image_urls2 = Parser.data(content).from('<img src="').to('" style="').iterate();
      urls = [];
      for (let url of image_urls2) {
        if (url.slice(0, 8) == "https://") {
          urls.push(url);
        };
      };
      if (!urls.length) {
        return make_Response("画像が取得できませんでした。このメッセージが長期間続くなら以下のアカウントに連絡をお願いします。\n\nhttps://works.do/R/ti/p/schedule@mito1daily", "text");
      };
    };

    // 返信
    for (let url of urls) {
      images = images.concat(make_Response(url, "image"));
    };
    return images;
  } catch (e) {
    const ss = SpreadsheetApp.getActive();
    return error(e, ss);
  };
}


// 月間予定取得
function month(ss) {
  try {
    console.time("month()");
    // 現在の月日取得
    const time = new Date();
    const m = time.getMonth() + 1;

    // 現在の月を元に月間予定データを取得
    let items = ss.getSheetByName("month").getDataRange().getValues();
    items.shift();  // 先頭はデータではないので削除
    let index = search_2dArray(items, m);
    if (typeof (index) != "number") {
      index = search_2dArray(items, m + 1);
      if (typeof (index) != "number") {
        return make_Response("次の予定はまだ公開されていません。このメッセージが長期間続くなら以下のアカウントに連絡をお願いします。\n\nhttps://works.do/R/ti/p/schedule@mito1daily", "text");
      };
    };
    const monthData = items[index][1];
    const monthImage = items[index][2];

    let messages = [];
    messages = messages.concat(make_Response(monthData, "text"));
    messages = messages.concat(make_Response(monthImage, "image"));
    console.timeEnd("month()");
    return messages;
  } catch (e) {
    return error(e, ss);
  };
}


// ニュース取得
function get_news(ss) {
  try {
    // 直近のニュースを5件取得
    const news_all = ss.getSheetByName("news").getRange("B2:B6").getValues();

    // カラム作成
    const columns = [];
    const url = {
      "部活動の紹介": "https://www.mito1-h.ibk.ed.jp/f3f2a48def04f2d9c4586f42bda6b409/%E5%AD%A6%E6%A0%A1%E7%94%9F%E6%B4%BB/%E9%83%A8%E6%B4%BB%E5%8B%95%E7%B4%B9%E4%BB%8B",
      "部活動ニュース": "https://www.mito1-h.ibk.ed.jp/f3f2a48def04f2d9c4586f42bda6b409/%E5%AD%A6%E6%A0%A1%E7%94%9F%E6%B4%BB/%E9%83%A8%E6%B4%BB%E5%8B%95%E3%83%8B%E3%83%A5%E3%83%BC%E3%82%B9",
      "医学コースについて": "https://www.mito1-h.ibk.ed.jp/%E5%8C%BB%E5%AD%A6%E3%82%B3%E3%83%BC%E3%82%B9%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/%E5%8C%BB%E5%AD%A6%E3%82%B3%E3%83%BC%E3%82%B9%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/%E5%8C%BB%E5%AD%A6%E3%82%B3%E3%83%BC%E3%82%B9%E3%81%AE%E5%AE%9F%E8%B7%B5",
      "水戸一高の風景": "https://www.mito1-h.ibk.ed.jp/%E6%B0%B4%E6%88%B8%E4%B8%80%E9%AB%98%E3%81%AE%E9%A2%A8%E6%99%AF",
    };
    for (let news of news_all) {
      let label = "詳細を見る";
      let uri = "https://www.mito1-h.ibk.ed.jp/#frame-587";
      for (let key in url) {
        if (news[0].includes(key)) {
          label = key;
          uri = url[key];
        };
      };
      let txt = {
        "imageBackgroundColor": "#FFFFFF",
        "text": news[0].slice(0, 100),
        "actions": [
          {
            "type": "uri",
            "label": label,
            "uri": uri
          }
        ]
      };
      columns.push(txt);
      console.log(txt);
    };

    // message作成
    return [{
      "type": "template",
      "altText": "直近のニュース5件",
      "template": {
        "type": "carousel",
        "columns": columns
      }
    }];
  } catch (e) {
    return error(e, ss);
  };
}


// テーマ取得
function get_themes(ss) {
  try {
    // 全てのテーマ取得
    let items = ss.getSheetByName("themes").getDataRange().getValues();
    items.shift();  // 先頭はデータではないので削除

    // カラム作成
    const columns = [];
    for (let theme of items) {
      let txt = {
        "thumbnailImageUrl": theme[3],
        "imageBackgroundColor": "#FFFFFF",
        "text": theme[1],
        "actions": [
          {
            "type": "postback",
            "label": "このテーマに変更",
            "data": `themechanged-${theme[0]}`,
            "inputOption": "openRichMenu"
          }
        ]
      };
      console.log(txt);
      columns.push(txt);
    };

    // message作成
    const themes = {
      "type": "template",
      "altText": "テーマ一覧",
      "template": {
        "type": "carousel",
        "columns": columns,
        "imageAspectRatio": "rectangle",
        "imageSize": "cover"
      }
    };
    return themes;
  } catch (e) {
    return error(e, ss);
  };
}


// テーマ変更
function change_theme(ss, theme_name, user_id) {
  try {
    console.time("change_theme()");
    // テーマ名からリッチメニューIDを取得
    let items = ss.getSheetByName("themes").getDataRange().getValues();
    items.shift();  // 先頭はデータではないので削除

    const index = search_2dArray(items, theme_name);
    if (typeof (index) != "number") {
      return [];
    };
    const theme_id = items[index][2];

    // リッチメニューとユーザーをリンク
    const theme_options = {
      "method": "POST",
      "headers": { "Authorization": `Bearer ${PropertiesService.getScriptProperties().getProperty("TOKEN")}` }
    };
    UrlFetchApp.fetch(`https://api.line.me/v2/bot/user/${user_id}/richmenu/${theme_id}`, theme_options);
    console.timeEnd("change_theme()");
    return [];
  } catch (e) {
    return error(e, ss);
  };
};


// 辞書データ送信
function get_word(ss) {
  try {
    // 辞書データ取得
    const dict = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DICT"));
    const sheet = dict.getSheetByName("フォームの回答 1");
    const rows = sheet.getLastRow() - 1;
    console.log(rows);

    // 乱数生成,単語取得
    let num = Math.floor(Math.random() * rows) + 2;
    const words = sheet.getRange(num, 1, 1, 5).getValues()[0];
    const time = Utilities.formatDate(words[0], "JST", "yy/MM/dd HH:mm");

    // message作成
    let mes = `単語: ${words[1]} (${num - 1}/${rows})\n品詞: ${words[2]}\n意味: ${words[3]}`;
    if (words[4] != "") {
      mes = mes + `\n補足: ${words[4]}`
    };
    return make_Response(`${mes}\n\n作成日: ${time}`, "text");
  } catch (e) {
    return error(e, ss);
  };
}


// 追加情報
function add_info(ss) {
  try {
    // データ取得
    let items = ss.getSheetByName("add").getDataRange().getValues();
    items.shift();  // 先頭はデータではないので削除

    // メッセージ作成
    let messages = [];
    for (let i of items) {
      const now_date = new Date();
      const [next_date, type, content] = [i[1], i[2], i[3]];
      if (now_date <= next_date) {
        messages = messages.concat(make_Response(content, type));
      };
    };
    return messages;
  } catch (e) {
    return error(e, ss);
  };
}


// その他のコマンド
function commands(ss, command) {
  try {
    console.time("commands()");
    // コマンドを元にメッセージデータを取得
    let items = ss.getSheetByName("commands").getDataRange().getValues();
    items.shift();  // 先頭はデータではないので削除
    const index = search_2dArray(items, command);
    if (typeof (index) != "number") {
      return [];
    };
    const type = items[index][1];
    const message = items[index][2];
    console.timeEnd("commands()");
    return make_Response(message, type);
  } catch (e) {
    return error(e, ss);
  };
}
