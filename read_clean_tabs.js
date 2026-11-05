function readAllCleanTabs(ss) {
  function readTab(sheet, defaultHeaderRow, startCol, numCols) {
    if (!sheet) return [];
    var lastRow = sheet.getLastRow();
    if (lastRow < defaultHeaderRow) return [];
    var headerRow = defaultHeaderRow;
    for (var r = 6; r <= 9 && r <= lastRow; r++) {
      var candidate = sheet.getRange(r, startCol, 1, numCols).getDisplayValues()[0].join(" ").toLowerCase();
      if (candidate.indexOf("identité patient") !== -1 || candidate.indexOf("identite patient") !== -1) {
        headerRow = r;
        break;
      }
    }
    if (lastRow <= headerRow) return [];
    var actualCols = Math.min(numCols, Math.max(1, sheet.getLastColumn() - startCol + 1));
    var headers = sheet.getRange(headerRow, startCol, 1, actualCols).getDisplayValues()[0];
    var values = sheet.getRange(headerRow + 1, startCol, lastRow - headerRow, actualCols).getDisplayValues();
    var out = [];
    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      var isEmpty = row.every(function(c) { return !String(c).trim(); });
      if (isEmpty) continue;
      var patColIdx = headers.indexOf("Identité Patient");
      if (patColIdx === -1) patColIdx = 2;
      var patCell = String(row[patColIdx] || "").trim();
      var firstCell = String(row[0] || "").trim();
      if (!patCell && (firstCell.indexOf("SEMAINE") !== -1 || firstCell.indexOf("DEMANDES D'AVIS") !== -1 || firstCell.indexOf("AVIS INTERVENTIONNEL") !== -1 || firstCell.indexOf("AVIS DIAGNOSTIC") !== -1)) {
        continue;
      }
      if (!patCell) continue;
      var obj = { _row: headerRow + 1 + i };
      for (var j = 0; j < headers.length; j++) {
        obj[headers[j]] = row[j];
      }
      out.push(obj);
    }
    return out;
  }

  var avInterv = readTab(ss.getSheetByName("Avis Interventionnel"), 8, 2, 10).map(function(x) {
    x["Catégorie d'avis"] = "Avis Interventionnel";
    x._sheet = "Avis Interventionnel";
    return x;
  });
  var avDiag = readTab(ss.getSheetByName("Avis Diagnostic"), 8, 2, 10).map(function(x, idx) {
    x["Catégorie d'avis"] = "Avis Diagnostic";
    x._sheet = "Avis Diagnostic";
    x._sheetRow = x._row;
    x._row = 1000 + Number(x._row || idx);
    return x;
  });
  var avCombined = (avInterv.length || avDiag.length)
    ? avInterv.concat(avDiag)
    : readTab(ss.getSheetByName("Demandes d'avis"), 8, 2, 10);

  return {
    Data: readTab(ss.getSheetByName("Data"), 8, 2, 9),
    Avis_Interventionnel: avInterv,
    Avis_Diagnostic: avDiag,
    Demandes_avis: avCombined,
    Consultations: readTab(ss.getSheetByName("Consultations"), 8, 2, 9),
    Imagerie_Anesthesie: readTab(ss.getSheetByName("Imagerie & Anesthésie"), 8, 2, 9),
    Biopsies: readTab(ss.getSheetByName("Biopsies"), 8, 2, 9),
    actes: readTab(ss.getSheetByName("actes"), 8, 2, 10)
  };
}
return readAllCleanTabs(ss);
