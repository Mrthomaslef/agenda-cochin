function splitAndFormatAvisSheets(ss) {
  var avisSheet = ss.getSheetByName("Demandes d'avis");
  if (!avisSheet) throw new Error("Onglet Demandes d'avis introuvable");

  var lastRow = avisSheet.getLastRow();
  var rawRows = lastRow >= 9 ? avisSheet.getRange(9, 2, lastRow - 8, 9).getDisplayValues() : [];

  var INTERV_REGEX = /biops|ponction|drainage|infiltrat|radiofr[eé]quence|\brf\b|rfna|cryo|thermoablation|ablation|cimentoplast|vert[eé]broplast|kyphoplast|alcoolisation|embolisation|vissage|ost[eé]osynth|spondylod[eè]se|[eé]lectrochimio|\bect\b|test\s+anesth|bloc\s+nerveux|neurolyse|prp|trituration|lavage\s+calcique|geste\s+percutan|traitement\s+percutan|prise\s+en\s+charge\s+intervention|ost[eé]ome\s+ost[eé]o[iï]de|morton|chondroblastome|kyste\s+essentiel|\bkoa\b|kyste\s+osseux/i;

  function classifyAvisRow(r) {
    var motif = String(r[4] || "");
    var decision = String(r[8] || "");
    var combined = (motif + " " + decision).toLowerCase();
    if (combined.indexOf("complément tdm à visée diagnostique") !== -1 || combined.indexOf("biopsié en cs ce") !== -1) {
      return "diagnostic";
    }
    if (INTERV_REGEX.test(combined)) return "interventionnel";
    return "diagnostic";
  }

  function parseAvisTs(dateStr) {
    var s = String(dateStr || "").trim();
    if (!s) return 0;
    var reDate = /(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?/g;
    var m;
    var bestDate = 0;
    while ((m = reDate.exec(s)) !== null) {
      var dd = parseInt(m[1], 10);
      var mm = parseInt(m[2], 10);
      var yyyy = m[3] ? parseInt(m[3], 10) : 2026;
      if (yyyy < 100) yyyy += 2000;
      if (mm >= 1 && mm <= 12 && dd >= 1 && dd <= 31) {
        var val = yyyy * 100000000 + mm * 1000000 + dd * 10000;
        if (val > bestDate) bestDate = val;
      }
    }
    if (bestDate === 0) return 0;
    var reTime = /(\d{1,2})\s*[h:]\s*(\d{0,2})/gi;
    var mt;
    var lastTime = 0;
    while ((mt = reTime.exec(s)) !== null) {
      var hh = parseInt(mt[1], 10);
      var mn = mt[2] ? parseInt(mt[2], 10) : 0;
      if (hh >= 0 && hh <= 23 && mn >= 0 && mn <= 59) {
        lastTime = hh * 100 + mn;
      }
    }
    return bestDate + lastTime;
  }

  // Dédupliquer et nettoyer les vraies lignes (hors bannières éventuelles)
  var validItems = [];
  var seenKeys = {};
  for (var i = 0; i < rawRows.length; i++) {
    var r = rawRows[i];
    var pat = String(r[2] || "").trim();
    var dt = String(r[0] || "").trim();
    if (!pat) continue;
    if (dt.indexOf("DEMANDES D'AVIS") !== -1 || dt.indexOf("SEMAINE") !== -1) continue;
    var key = pat.toLowerCase().replace(/[^a-z0-9]/g, "") + "__" + String(r[4] || "").slice(0, 40).toLowerCase().replace(/[^a-z0-9]/g, "");
    if (seenKeys[key]) continue;
    seenKeys[key] = true;
    var cat = classifyAvisRow(r);
    validItems.push({
      row9: r.slice(0, 9),
      cat: cat,
      catLabel: cat === "interventionnel" ? "Avis Interventionnel" : "Avis Diagnostic",
      ts: parseAvisTs(r[0]),
      origIdx: i
    });
  }

  function sortNewestFirst(a, b) {
    if (b.ts !== a.ts) return b.ts - a.ts;
    return a.origIdx - b.origIdx;
  }

  var intervItems = validItems.filter(function(x) { return x.cat === "interventionnel"; }).sort(sortNewestFirst);
  var diagItems = validItems.filter(function(x) { return x.cat === "diagnostic"; }).sort(sortNewestFirst);

  var headers10 = [
    "Date Demande",
    "Médecin Demandeur (Service)",
    "Identité Patient",
    "N° Dossier / IPP",
    "Motif de l'avis / Question clinique",
    "Statut Réponse",
    "Médecin Répondant (Radio B)",
    "Date Réponse",
    "Décision & Suite donnée",
    "Catégorie d'avis"
  ];

  function styleHeaderAndCols(sheet) {
    if (sheet.getFilter()) sheet.getFilter().remove();
    sheet.setColumnWidth(1, 24);
    sheet.setColumnWidth(2, 135);
    sheet.setColumnWidth(3, 220);
    sheet.setColumnWidth(4, 195);
    sheet.setColumnWidth(5, 120);
    sheet.setColumnWidth(6, 360);
    sheet.setColumnWidth(7, 150);
    sheet.setColumnWidth(8, 200);
    sheet.setColumnWidth(9, 135);
    sheet.setColumnWidth(10, 360);
    sheet.setColumnWidth(11, 165);

    var hRange = sheet.getRange(8, 2, 1, 10);
    hRange.breakApart();
    hRange.setValues([headers10]);
    hRange
      .setBackground("#1A365D")
      .setFontColor("#FFFFFF")
      .setFontFamily("Arial")
      .setFontSize(10)
      .setFontWeight("bold")
      .setHorizontalAlignment("center")
      .setVerticalAlignment("middle")
      .setWrap(true);
    sheet.setRowHeight(8, 34);
  }

  function styleDataRows(sheet, startRow, itemsList) {
    if (itemsList.length === 0) return startRow;
    var vals = itemsList.map(function(it) {
      return it.row9.concat([it.catLabel]);
    });
    var n = vals.length;
    var dataRange = sheet.getRange(startRow, 2, n, 10);
    dataRange.breakApart();
    dataRange.setValues(vals);
    dataRange
      .setFontFamily("Arial")
      .setFontSize(10)
      .setFontColor("#202124")
      .setVerticalAlignment("middle")
      .setWrap(true)
      .setBorder(true, true, true, true, true, true, "#E0E0E0", SpreadsheetApp.BorderStyle.SOLID);

    var bgs = [];
    var fontWeightsD = [];
    var stBgs = [];
    var stColors = [];
    var catBgs = [];
    var catColors = [];

    for (var i = 0; i < n; i++) {
      var rowBg = (i % 2 === 0) ? "#FFFFFF" : "#F8FAFC";
      bgs.push([rowBg, rowBg, rowBg, rowBg, rowBg, rowBg, rowBg, rowBg, rowBg, rowBg]);
      fontWeightsD.push(["bold"]);
      var st = String(vals[i][5] || "").trim();
      var isRep = st.toLowerCase().indexOf("répondu") === 0 || st.toLowerCase().indexOf("repondu") === 0;
      stBgs.push([isRep ? "#E6F4EA" : "#FCE8E6"]);
      stColors.push([isRep ? "#137333" : "#C5221F"]);

      var isInterv = vals[i][9] === "Avis Interventionnel";
      catBgs.push([isInterv ? "#E8F0FE" : "#E0F2F1"]);
      catColors.push([isInterv ? "#1967D2" : "#00695C"]);
      sheet.setRowHeight(startRow + i, 44);
    }

    dataRange.setBackgrounds(bgs);
    sheet.getRange(startRow, 2, n, 1).setHorizontalAlignment("center");
    sheet.getRange(startRow, 4, n, 1).setFontWeights(fontWeightsD);
    sheet.getRange(startRow, 5, n, 1).setHorizontalAlignment("center");
    sheet.getRange(startRow, 7, n, 1).setHorizontalAlignment("center").setFontWeight("bold").setBackgrounds(stBgs).setFontColors(stColors);
    sheet.getRange(startRow, 9, n, 1).setHorizontalAlignment("center");
    sheet.getRange(startRow, 11, n, 1).setHorizontalAlignment("center").setFontWeight("bold").setBackgrounds(catBgs).setFontColors(catColors);

    return startRow + n;
  }

  function applyCondFormatting(sheet, maxRow) {
    var statusRange = sheet.getRange(9, 7, Math.max(maxRow - 8, 20), 1);
    var catRange = sheet.getRange(9, 11, Math.max(maxRow - 8, 20), 1);
    var rules = [
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextContains("Répondu")
        .setBackground("#E6F4EA")
        .setFontColor("#137333")
        .setBold(true)
        .setRanges([statusRange])
        .build(),
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextContains("Non répondu")
        .setBackground("#FCE8E6")
        .setFontColor("#C5221F")
        .setBold(true)
        .setRanges([statusRange])
        .build(),
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo("Avis Interventionnel")
        .setBackground("#E8F0FE")
        .setFontColor("#1967D2")
        .setBold(true)
        .setRanges([catRange])
        .build(),
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo("Avis Diagnostic")
        .setBackground("#E0F2F1")
        .setFontColor("#00695C")
        .setBold(true)
        .setRanges([catRange])
        .build()
    ];
    sheet.setConditionalFormatRules(rules);
  }

  function writeBannerRow(sheet, rowNum, titleText, bgHex) {
    var rRange = sheet.getRange(rowNum, 2, 1, 10);
    rRange.breakApart();
    var rowVals = [titleText, "", "", "", "", "", "", "", "", ""];
    rRange.setValues([rowVals]);
    rRange.merge();
    rRange
      .setBackground(bgHex)
      .setFontColor("#FFFFFF")
      .setFontFamily("Arial")
      .setFontSize(11)
      .setFontWeight("bold")
      .setVerticalAlignment("middle")
      .setHorizontalAlignment("left")
      .setBorder(true, true, true, true, false, false, bgHex, SpreadsheetApp.BorderStyle.SOLID);
    sheet.setRowHeight(rowNum, 32);
  }

  // =========================================================================
  // 1. Mettre à jour l'onglet principal "Demandes d'avis" avec 2 sections séparées
  // =========================================================================
  var maxR = avisSheet.getMaxRows();
  if (maxR >= 9) {
    var clearR = avisSheet.getRange(9, 2, maxR - 8, 10);
    clearR.breakApart();
    clearR.clearContent();
    clearR.clearFormat();
  }
  styleHeaderAndCols(avisSheet);

  var curRow = 9;
  writeBannerRow(
    avisSheet,
    curRow,
    "🔪  DEMANDES D'AVIS INTERVENTIONNEL  —  Gestes percutanés, biopsies & ablations (" + intervItems.length + " demandes)",
    "#1B4F72"
  );
  curRow++;
  curRow = styleDataRows(avisSheet, curRow, intervItems);

  writeBannerRow(
    avisSheet,
    curRow,
    "🩻  DEMANDES D'AVIS DIAGNOSTIC  —  Relectures d'imagerie & avis diagnostiques (" + diagItems.length + " demandes)",
    "#0E6251"
  );
  curRow++;
  curRow = styleDataRows(avisSheet, curRow, diagItems);

  var endAvisRow = curRow - 1;
  avisSheet.getRange("B2").setValue("Suivi des Demandes d'Avis (Interventionnel & Diagnostic) — Service de Radiologie B (Pr A. Feydy)");
  avisSheet.getRange("B5").setValue("TOTAL DEMANDES D'AVIS");
  avisSheet.getRange("D5").setValue("🔪 AVIS INTERVENTIONNEL");
  avisSheet.getRange("F5").setValue("🩻 AVIS DIAGNOSTIC");
  avisSheet.getRange("H5").setValue("RÉPONDU PAR L'ÉQUIPE");
  avisSheet.getRange("J5:J6").setBackground("#F8FAFC").setHorizontalAlignment("center").setVerticalAlignment("middle");
  avisSheet.getRange("J5").setValue("À TRAITER / EN ATTENTE").setFontFamily("Arial").setFontSize(9).setFontWeight("bold").setFontColor("#5F6368");
  avisSheet.getRange("J6").setFontFamily("Arial").setFontSize(16).setFontWeight("bold").setFontColor("#C5221F");

  avisSheet.getRange("B6").setFormula('=COUNTA(D9:D' + endAvisRow + ')');
  avisSheet.getRange("D6").setFormula('=COUNTIF(K9:K' + endAvisRow + '; "Avis Interventionnel")');
  avisSheet.getRange("F6").setFormula('=COUNTIF(K9:K' + endAvisRow + '; "Avis Diagnostic")');
  avisSheet.getRange("H6").setFormula('=COUNTIF(G9:G' + endAvisRow + '; "*Répondu*")');
  avisSheet.getRange("J6").setFormula('=MAX(0; B6-H6)');
  applyCondFormatting(avisSheet, endAvisRow + 15);
  avisSheet.setTabColor("#1A365D");

  // =========================================================================
  // 2. Créer / Mettre à jour les 2 onglets dédiés : "Avis Interventionnel" & "Avis Diagnostic"
  // =========================================================================
  function buildDedicatedCategorySheet(tabName, titleText, kpi1Title, items, tabColorHex, bannerText, bannerHex) {
    var sh = ss.getSheetByName(tabName);
    if (!sh) {
      sh = avisSheet.copyTo(ss);
      sh.setName(tabName);
    }
    var mR = sh.getMaxRows();
    if (mR >= 9) {
      var cl = sh.getRange(9, 2, mR - 8, 10);
      cl.breakApart();
      cl.clearContent();
      cl.clearFormat();
    }
    styleHeaderAndCols(sh);
    sh.getRange("B2").setValue(titleText);
    sh.getRange("B5").setValue(kpi1Title);
    sh.getRange("D5").setValue("NON RÉPONDU / À TRAITER");
    sh.getRange("F5").setValue("RÉPONDU PAR L'ÉQUIPE");
    sh.getRange("H5").setValue("TAUX DE RÉPONSE");
    sh.getRange("J5:J6").clearContent().clearFormat();

    var rPtr = 9;
    writeBannerRow(sh, rPtr, bannerText, bannerHex);
    rPtr++;
    rPtr = styleDataRows(sh, rPtr, items);
    var lastDataR = Math.max(rPtr - 1, 10);

    sh.getRange("B6").setFormula('=COUNTA(D9:D' + lastDataR + ')');
    sh.getRange("D6").setFormula('=MAX(0; B6-F6)');
    sh.getRange("F6").setFormula('=COUNTIF(G9:G' + lastDataR + '; "*Répondu*")');
    sh.getRange("H6").setFormula('=IF(B6>0; F6/B6; 1)');
    applyCondFormatting(sh, lastDataR + 15);
    sh.setTabColor(tabColorHex);
    return sh;
  }

  buildDedicatedCategorySheet(
    "Avis Interventionnel",
    "Suivi des Demandes d'Avis Interventionnel — Service de Radiologie B (Pr A. Feydy)",
    "🔪 TOTAL AVIS INTERVENTIONNEL",
    intervItems,
    "#1967D2",
    "🔪  DEMANDES D'AVIS INTERVENTIONNEL  —  Gestes percutanés, biopsies & ablations (" + intervItems.length + " demandes)",
    "#1B4F72"
  );

  buildDedicatedCategorySheet(
    "Avis Diagnostic",
    "Suivi des Demandes d'Avis Diagnostic — Service de Radiologie B (Pr A. Feydy)",
    "🩻 TOTAL AVIS DIAGNOSTIC",
    diagItems,
    "#00897B",
    "🩻  DEMANDES D'AVIS DIAGNOSTIC  —  Relectures d'imagerie & avis diagnostiques (" + diagItems.length + " demandes)",
    "#0E6251"
  );

  // Ordonner les onglets de la Partie 1
  var desiredOrder = [
    "Data",
    "Demandes d'avis",
    "Avis Interventionnel",
    "Avis Diagnostic",
    "Consultations",
    "Imagerie & Anesthésie",
    "Biopsies",
    "actes"
  ];
  for (var pos = 0; pos < desiredOrder.length; pos++) {
    var s = ss.getSheetByName(desiredOrder[pos]);
    if (s) {
      ss.setActiveSheet(s);
      ss.moveActiveSheet(pos + 1);
    }
  }
  ss.setActiveSheet(avisSheet);
  SpreadsheetApp.flush();

  return {
    status: "ok",
    total: validItems.length,
    interventionnel: intervItems.length,
    diagnostic: diagItems.length,
    endAvisRow: endAvisRow
  };
}
return splitAndFormatAvisSheets(ss);
