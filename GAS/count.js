function reset_day() {
  reset("B");
}

function reset_week() {
  reset("C");
}

function reset_month() {
  reset("D");
}

function reset(column) {
  const ss = SpreadsheetApp.getActive().getSheetByName("Count");
  const lastRow = ss.getLastRow();
  const cell = ss.getRange(`${column}2:${column}${lastRow}`);
  cell.setValue(0);
}
