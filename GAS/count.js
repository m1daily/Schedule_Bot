// 公式アカウントのボタンが押されたらカウント
// 日,週,月でカウントリセット
function reset_day() {
  reset("C");
}

function reset_week() {
  reset("D");
}

function reset_month() {
  reset("E");
}

function reset(column) {
  const sheet = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("DEBUG"));
  const ss = sheet.getSheetByName("Count");
  const lastRow = ss.getLastRow();
  const cell = ss.getRange(`${column}3:${column}${lastRow}`);
  cell.setValue(0);
}
