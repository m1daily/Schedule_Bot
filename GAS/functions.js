// 次の予定取得
function get_schedules(sheet) {
  try{
    // 予定取得
    const month = sheet.getRange("D2").getValue();
    const monthData = sheet.getRange("D6").getValue().replace(" ", "").split("\n");

    // 現在の月日取得
    const time = new Date();
    const m = time.getMonth() + 1;
    const d = time.getDate();

    // 日付と予定のデータを整理
    const days = [];
    const schedules = [];

    for (let i = 0; i < monthData.length; i++) {
      let dayData = monthData[i];
      let dayParts = dayData.split(")");
      let yotei = [];

      for (let n = 0; n < dayParts.length; n++) {
        // 日付の場合「)」を追加
        if (dayParts.length - n > 1) {
          dayParts[n] = dayParts[n] + ")";
        };
        if (n > 0) {
          yotei.push(dayParts[n]);
        }else if (n === 0) {
          days.push(dayParts[n]);
        };
      };
      schedules.push(yotei.join(""));
    };

    // スプレッドシートの予定の月と現在の月が一致しないなら終了
    if (month != String(m)) {
      return {
        "type": "text",
        "text": `${month}月${days[0]}に ${schedules[0]} があります。`
      };
    };

    // 予定取得
    let schedule = ""
    for (let i = 0; i < days.length; i++) {
      let day = parseInt(days[i].slice(0, 2).replace("日", ""));
      if (d < day) {
        return {
          "type": "text",
          "text": `${days[i]}に ${schedules[i]} があります。`
        };
      };
    };
    if (schedule == "") {
      return {
        "type": "text",
        "text": "次の予定はまだ取得できません。"
      };
    };
  }catch(e){
    return error(e.stack);
  };
}


// 時間割画像取得
function get_images(sheet, cell) {
  try{
    const images = [];
    const image_urls = sheet.getRange(cell).getValue().replace(" ", "").split("\n");
    for (let i = 0; i < image_urls.length; i++){
      let image = {
            "type": "image",
            "originalContentUrl": image_urls[i],
            "previewImageUrl": image_urls[i]
      };
      images.push(image);
    };
    return images;
  }catch(e){
    return [error(e.stack)];
  };
}


// ニュース取得
function get_news(sheet) {
  try{
    // 直近のニュースを5件取得
    const news_all = sheet.getRange("E6").getValue().split("\n").slice(0, 5);

    // カラム作成
    const columns = [];
    const url = {
      "部活動の紹介": "https://www.mito1-h.ibk.ed.jp/f3f2a48def04f2d9c4586f42bda6b409/%E5%AD%A6%E6%A0%A1%E7%94%9F%E6%B4%BB/%E9%83%A8%E6%B4%BB%E5%8B%95%E7%B4%B9%E4%BB%8B",
      "部活動ニュース": "https://www.mito1-h.ibk.ed.jp/f3f2a48def04f2d9c4586f42bda6b409/%E5%AD%A6%E6%A0%A1%E7%94%9F%E6%B4%BB/%E9%83%A8%E6%B4%BB%E5%8B%95%E3%83%8B%E3%83%A5%E3%83%BC%E3%82%B9",
      "医学コースについて": "https://www.mito1-h.ibk.ed.jp/%E5%8C%BB%E5%AD%A6%E3%82%B3%E3%83%BC%E3%82%B9%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/%E5%8C%BB%E5%AD%A6%E3%82%B3%E3%83%BC%E3%82%B9%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/%E5%8C%BB%E5%AD%A6%E3%82%B3%E3%83%BC%E3%82%B9%E3%81%AE%E5%AE%9F%E8%B7%B5",
      "水戸一高の風景": "https://www.mito1-h.ibk.ed.jp/%E6%B0%B4%E6%88%B8%E4%B8%80%E9%AB%98%E3%81%AE%E9%A2%A8%E6%99%AF",
    }
    for (let i = 0; i < news_all.length; i++){
      let label = "詳細を見る"
      let uri = "https://www.mito1-h.ibk.ed.jp/#frame-587"
      for (let key in url){
        if (news_all[i].includes(key)) {
          label = key
          uri = url[key]
        };
      };
      let txt = {
        "imageBackgroundColor": "#FFFFFF",
        "text": news_all[i].slice(0,100),
        "actions": [
          {
            "type": "uri",
            "label": label,
            "uri": uri
          }
        ]
      };
      columns.push(txt);
      console.log(txt)
    };

    // message作成
    const news = {
      "type": "template",
      "altText": "直近のニュース5件",
      "template": {
        "type": "carousel",
        "columns": columns
      }
    };
    return news;
  }catch(e){
    return [error(e.stack)];
  };
}


// SNSリンク集の取得
function get_sns() {
  try{
    // サービス名, 画像URL, リンク
    const sns_all = [
      ["Twitter", "https://cdn-icons-png.flaticon.com/512/124/124021.png", "詳細を見る", "https://x.com/mito1daily"],
      ["Instagram", "https://cdn-icons-png.flaticon.com/512/15713/15713420.png", "詳細を見る", "https://www.instagram.com/mito1daily/"],
      ["Discord", "", "詳細を見る", ""]
      ["GoogleForm", "", "お問い合わせ", ""]
    ];

    // カラム作成
    const columns = [];
    for (let i = 0; i < sns_all.length; i++){
      let txt = {
        "thumbnailImageUrl": sns_all[i][1],
        "imageBackgroundColor": "#FFFFFF",
        "text": sns_all[i][0],
        "actions": [
          {
            "type": "uri",
            "label": sns_all[i][2],
            "uri": sns_all[i][3],
          }
        ]
      };
      columns.push(txt);
    };

    // message作成
    const sns = {
      "type": "template",
      "altText": "SNS",
      "template": {
        "type": "carousel",
        "columns": columns
      },
      "imageAspectRatio": "square",
      "imageSize": "cover"
    };
    return sns;
  }catch(e){
    return [error(e.stack)];
  };
}


// 辞書からランダムに単語と意味取得
function get_word() {
  try{
    // 辞書データ取得
    const ss =SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DICT"));
    const sheet = ss.getSheetByName("フォームの回答 1");
    const rows = sheet.getLastRow();
    console.log(rows);

    // 乱数生成,単語取得
    const num = Math.floor(Math.random()*rows)+1;
    const words = sheet.getRange(num, 1, 1, 5).getValues()[0];
    const time = Utilities.formatDate(words[0], "JST", "yy/MM/dd HH:mm");

    // message作成
    let mes = `単語: ${words[1]} (${num}/${rows})\n品詞: ${words[2]}\n意味: ${words[3]}`;
    if (words[4] != ""){
      mes = mes + `\n補足: ${words[4]}`
    };
    const txt = {
      "type": "text",
      "text": mes + `\n\n作成日: ${time}`
    };
    return txt;
  }catch(e){
    return [error(e.stack)];
  };
}


// スプレッドシートから情報取得
function get_info(cell) {
  try{
    // 辞書データ取得
    const ss =SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DEBUG"));
    const sheet = ss.getSheetByName("Messages");
    const info = sheet.getRange(cell).getValue();

    // message作成
    const txt = {
      "type": "text",
      "text": info
    };
    return txt;
  }catch(e){
    return [error(e.stack)];
  };
}


// テーマ取得
function get_themes(get_array) {
  try{
    // 全てのテーマ取得
    const ss =SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DEBUG"));
    const sheet = ss.getSheetByName("Themes");
    const rows = sheet.getLastRow();
    const themes_all = sheet.getRange(3, 2, rows - 2, 4).getValues();
    console.log(themes_all);
    if (get_array) {
      return themes_all;
    };

    // カラム作成
    const columns = [];
    for (let i = 0; i < themes_all.length; i++){
      const theme = themes_all[i];
      let txt = {
        "thumbnailImageUrl": theme[2],
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
      columns.push(txt);
      console.log(txt);
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
    console.log(themes)
    return themes;
  }catch(e){
    return [error(e.stack)];
  };
}


// テーマ変更
function change_theme(name, user_id) {
  try{
    // テーマ名からリッチメニューIDを取得
    const theme_name = name;
    const theme_all = get_themes(true);
    let i = 0;
    while (theme_name != theme_all[i][0]){
      i = i + 1;
      if (theme_all.length === i) {
        return false
      };
    };
    const theme_id = theme_all[i][3];

    // リッチメニューとユーザーをリンク
    const theme_options = {
      "method"  : "POST",
      "headers" : {"Authorization": `Bearer ${PropertiesService.getScriptProperties().getProperty("TOKEN")}`}
    };
    UrlFetchApp.fetch(`https://api.line.me/v2/bot/user/${user_id}/richmenu/${theme_id}`, theme_options);
    return false;
  }catch(e){
    return [error(e.stack)];
  };
};


// メッセージのテスト
// スプレッドシートから情報取得
function get_test(cell, type) {
  try{
    // 辞書データ取得
    const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DEBUG"));
    const sheet = ss.getSheetByName("Test");
    const test = sheet.getRange(cell).getValue();

    // message作成
    let mes = ""
    if (type === "text"){
      mes = {
        "type": "text",
        "text": test
      };
    } else if (type === "image") {
      mes = {
        "type": "image",
        "originalContentUrl": test,
        "previewImageUrl": test
      };
    } else {
      return false;
    };
    return mes;
  }catch(e){
    return [error(e.stack)];
  };
}


// エラーのテスト
function error_test() {
  try{
    throw new Error("error_test");
  }catch(e){
    return error(e.stack);
  };
}


// エラーメッセージ
function error(error_message) {
  debug(error_message);
  return {
      "type": "text",
      "text": `エラーが発生しました。\nエラー内容:\n${error_message}\n\nhttps://works.do/R/ti/p/schedule@mito1daily\n↑から作者の公式アカウントを追加して連絡くれると助かります。連絡くれる場合は↑のエラー内容も伝えてください。`
  };
}


// スプレッドシートに出力
function debug(value) {
  const sheet = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DEBUG"));
  const ss = sheet.getSheetByName("Debug");
  const date = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy/MM/dd HH:mm:ss");
  const targetRow = ss.getLastRow() + 1;
  ss.getRange('A' + targetRow).setValue(date);
  ss.getRange('B' + targetRow).setValue(value);
}


// カウンター
function count(ce) {
  const sheet = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DEBUG"));
  const ss = sheet.getSheetByName("Count");
  const column = ["C", "D", "E", "F"];
  for (let i in column){
    let cell = ss.getRange(column[i] + String(ce));
    const currentValue = cell.getValue();
    if (!isNaN(currentValue)) { // セルが数値の場合のみ
      cell.setValue(currentValue + 1);
    } else {
      cell.setValue(1); // セルが数値でない場合は1に設定
    };
  };
}
