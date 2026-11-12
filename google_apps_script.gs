/**
 * PONT AGENT ANTIGRAVITY <-> GOOGLE SHEETS (Agenda Interventionnel)
 * Version 3 :
 * - 4 onglets : Data | Consultations | Imagerie & Anesthésie | actes
 * - Dédoublonnage strict automatique sur tous les onglets (y compris actes et Consultations)
 * - Séparation visuelle par semaines (bandeaux "📅 SEMAINE <W> — Du Lundi ... au Vendredi ...")
 * - Entrées déjà passées automatiquement grisées (formatage direct + règle conditionnelle)
 * - Aucun menu déroulant (DataValidation supprimée sur les 4 onglets)
 */

var SPREADSHEET_ID = "1qOnw1VC-77U7r4loUl7qdCIXWNW1zCFzE6iQnl52g5s";
var IMG_ANESTH_SHEET_NAME = "Imagerie & Anesthésie";

/**
 * Vous pouvez cliquer directement sur "▷ Exécuter" dans Apps Script sur cette fonction
 * pour dédoublonner immédiatement tous les onglets (dont actes) et réappliquer la mise en forme.
 */
function reorganiserMaintenant() {
  var ss = getSpreadsheet_();
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    return applyUpdates_(ss, {
      data_updates: [],
      consultations_updates: [],
      imagerie_anesth_updates: [],
      actes_updates: []
    });
  } finally {
    lock.releaseLock();
  }
}

function getSpreadsheet_() {
  try {
    var active = SpreadsheetApp.getActiveSpreadsheet();
    if (active) return active;
  } catch (e) {}
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

function normalizeName_(s) {
  if (!s) return "";
  return String(s)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\b(mr|mme|mlle|m\.|dr|pr)\b/g, "")
    .replace(/[^a-z0-9]/g, "");
}

function normalizeIpp_(s) {
  return String(s || "").replace(/[^0-9]/g, "");
}

function samePatient_(aPatient, aIpp, bPatient, bIpp) {
  var ippA = normalizeIpp_(aIpp);
  var ippB = normalizeIpp_(bIpp);
  if (ippA && ippB && ippA.length >= 7 && ippA === ippB) return true;
  var normA = normalizeName_(aPatient);
  var normB = normalizeName_(bPatient);
  if (!normA || !normB) return false;
  if (normA === normB) return true;
  // Cas où l'un contient le nom de famille et l'autre nom + prénom (ex: "DE BOISSONNEAUX" vs "DE BOISSONNEAUX Bertrand")
  if (normA.length >= 8 && normB.length >= 8 && (normA.indexOf(normB) === 0 || normB.indexOf(normA) === 0)) {
    return true;
  }
  return false;
}

function examKind_(typeActe, medecin) {
  var t = String(typeActe || "").toLowerCase();
  var m = String(medecin || "").toLowerCase();
  var isCs = (t.indexOf("téléconsultation") !== -1 || t.indexOf("teleconsultation") !== -1 || t.indexOf("entretien") !== -1 || (t.indexOf("consultation") !== -1 && t.indexOf("anesth") === -1));
  if (isCs) return "cs";
  if (m.indexOf("anesth") !== -1 || t.indexOf("consultation d'anesth") !== -1 || t.indexOf("cs anesth") !== -1 || t.indexOf("consult anesth") !== -1) return "anesth";
  if (t.indexOf("irm") !== -1) return "irm";
  if (t.indexOf("arthroscan") !== -1 || t.indexOf("scanner") !== -1 || t.indexOf("tdm") !== -1) return "tdm";
  return "other";
}

function isImagerieOrAnesth_(medecin, typeActe) {
  var m = String(medecin || "").toLowerCase();
  var t = String(typeActe || "").toLowerCase();
  if (m.indexOf("anesth") !== -1) return true;
  if (t.indexOf("consultation d'anesth") !== -1 || t.indexOf("cs anesth") !== -1 || t.indexOf("consult anesth") !== -1) return true;
  if (t.indexOf("téléconsultation") !== -1 || t.indexOf("teleconsultation") !== -1 || t.indexOf("entretien") !== -1 || t.indexOf("consultation") !== -1) return false;
  if (t.indexOf("irm") !== -1 || t.indexOf("scanner") !== -1 || t.indexOf("tdm") !== -1 || t.indexOf("arthroscan") !== -1) return true;
  return false;
}

function readTabRows_(sheet, headerRow, startCol, numCols) {
  if (!sheet) return [];
  var lastRow = sheet.getLastRow();
  if (lastRow <= headerRow) return [];
  var headers = sheet.getRange(headerRow, startCol, 1, numCols).getDisplayValues()[0];
  var values = sheet.getRange(headerRow + 1, startCol, lastRow - headerRow, numCols).getDisplayValues();
  var out = [];
  for (var i = 0; i < values.length; i++) {
    var row = values[i];
    var isEmpty = row.every(function(c) { return !String(c).trim(); });
    if (isEmpty) continue;
    if (String(row[0] || "").indexOf("SEMAINE") !== -1 && !String(row[2] || "").trim()) continue;
    var obj = { _row: headerRow + 1 + i };
    for (var j = 0; j < headers.length; j++) {
      obj[headers[j]] = row[j];
    }
    out.push(obj);
  }
  return out;
}


/* ==========================================================================
 * SÉCURITÉ
 * --------------------------------------------------------------------------
 * L'adresse /exec de ce script est forcément connue (elle est dans la page
 * web publique). TOUTE requête doit donc être authentifiée :
 *  - "code d'accès" de l'app (saisi une fois par appareil) => actions de
 *    l'app uniquement (lecture + statuts + suivi bloc), liste blanche.
 *  - "jeton admin" (uniquement dans le .env local du Mac) => en plus :
 *    mises à jour en masse, eval_code, push des données perso.
 * Seules les empreintes SHA-256 sont stockées ici (jamais les secrets).
 * Pour changer un secret : calculer le SHA-256 du nouveau secret
 * (code d'accès : majuscules, sans tirets ni espaces) et remplacer la valeur,
 * puis redéployer (Gérer les déploiements > Modifier > Nouvelle version).
 * ========================================================================== */
// L'empreinte du code d'accès n'est PLUS dans le code source (dépôt public) :
// elle est lue dans les Propriétés du script (Paramètres du projet > Propriétés du script > APP_CODE_SHA256).
var APP_CODE_SHA256 = PropertiesService.getScriptProperties().getProperty("APP_CODE_SHA256") || "__non_configure__";
var ADMIN_TOKEN_SHA256 = "e09ae48cb07c575df6ee27400c66fdbe072e7491d960a924af330997e01624e0";
var AUTH_MAX_FAILURES = 8;           // échecs tolérés...
var AUTH_WINDOW_SECONDS = 15 * 60;   // ...par fenêtre de 15 minutes

var PROP_PERSO_STATUS = "cochin_perso_status_v4";
var PROP_SUIVI_BLOC = "cochin_suivi_bloc_v1";
var PROP_PERSONAL_RDVS = "cochin_personal_rdvs_v1";
var PROP_QUESTIONS_PERSO = "cochin_questions_perso_v1";
var PROP_PATIENT_CRS = "cochin_patient_crs_v1";
var GARDES_SHEET_ID = "1_XCqFLamiYM02RamAfc1khawt-jU3RG0CUU20x_M_Lw";

function sha256Hex_(str) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(str), Utilities.Charset.UTF_8);
  var out = "";
  for (var i = 0; i < bytes.length; i++) {
    var b = (bytes[i] + 256) % 256;
    out += (b < 16 ? "0" : "") + b.toString(16);
  }
  return out;
}

function constantTimeEquals_(a, b) {
  a = String(a || "");
  b = String(b || "");
  if (a.length !== b.length) return false;
  var diff = 0;
  for (var i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function normalizeAccessCode_(code) {
  return String(code || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

/** Renvoie "admin", "app" ou null. Applique un verrouillage temporaire après trop d'échecs. */
function authenticate_(payload) {
  var cache = CacheService.getScriptCache();
  var adminTok = String(payload.admin_token || "");
  if (adminTok && ADMIN_TOKEN_SHA256.indexOf("__") !== 0 &&
      constantTimeEquals_(sha256Hex_(adminTok), ADMIN_TOKEN_SHA256)) {
    return "admin";
  }
  var failures = Number(cache.get("auth_failures") || 0);
  if (failures >= AUTH_MAX_FAILURES) return null;
  var code = normalizeAccessCode_(payload.token);
  if (code && APP_CODE_SHA256.indexOf("__") !== 0 &&
      constantTimeEquals_(sha256Hex_(code), APP_CODE_SHA256)) {
    return "app";
  }
  cache.put("auth_failures", String(failures + 1), AUTH_WINDOW_SECONDS);
  return null;
}

function jsonOut_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/* --- Script Properties découpées (limite 9 Ko par propriété) --- */
function setBigProperty_(key, value) {
  var props = PropertiesService.getScriptProperties();
  var str = JSON.stringify(value);
  var CHUNK = 8000;
  var oldCount = Number(props.getProperty(key + "__chunks") || 0);
  var n = Math.ceil(str.length / CHUNK) || 1;
  var batch = {};
  for (var i = 0; i < n; i++) batch[key + "__" + i] = str.substr(i * CHUNK, CHUNK);
  batch[key + "__chunks"] = String(n);
  props.setProperties(batch, false);
  for (var j = n; j < oldCount; j++) props.deleteProperty(key + "__" + j);
}

function getBigProperty_(key, fallback) {
  var props = PropertiesService.getScriptProperties();
  var n = Number(props.getProperty(key + "__chunks") || 0);
  if (!n) return fallback;
  var str = "";
  for (var i = 0; i < n; i++) str += props.getProperty(key + "__" + i) || "";
  try { return JSON.parse(str); } catch (e) { return fallback; }
}

function getJsonProperty_(key, fallback) {
  try {
    var raw = PropertiesService.getScriptProperties().getProperty(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
}

/* --- Validation des entrées de l'app --- */
function str_(v, maxLen) {
  var s = (v === null || v === undefined) ? "" : String(v);
  return s.length > maxLen ? s.substr(0, maxLen) : s;
}

function normKey_(s) {
  return String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

/* ==========================================================================
 * POINTS D'ENTRÉE WEB
 * ========================================================================== */

// Aucune donnée n'est plus renvoyée en GET (l'adresse est publique).
function doGet(e) {
  return jsonOut_({ status: "ok", message: "Utilisez POST avec authentification." });
}

function doPost(e) {
  var payload;
  try {
    payload = JSON.parse((e && e.postData && e.postData.contents) || "{}");
  } catch (parseErr) {
    return jsonOut_({ status: "error", message: "Requête invalide" });
  }

  var role = authenticate_(payload);
  if (!role) {
    return jsonOut_({ status: "unauthorized", message: "Code d'accès invalide ou trop de tentatives." });
  }

  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var ss = getSpreadsheet_();
    var action = String(payload.action || "");

    // ---- Actions autorisées pour l'app (code d'accès) ----
    if (action === "read_all") return jsonOut_({ status: "ok", evalResult: readAllForApp_(ss) });
    if (action === "save_suivi") return jsonOut_({ status: "ok", result: saveSuivi_(ss, payload.entry || {}) });
    if (action === "set_avis_status") return jsonOut_({ status: "ok", result: setAvisStatus_(ss, payload) });
    if (action === "set_perso_status") return jsonOut_({ status: "ok", result: setPersoStatus_(payload.patch || {}) });
    if (action === "ping") return jsonOut_({ status: "ok", role: role });

    // ---- Actions réservées à l'agent local (jeton admin du .env) ----
    if (role !== "admin") {
      return jsonOut_({ status: "forbidden", message: "Action non autorisée." });
    }

    if (action === "read_tabs") {
      return jsonOut_({
        status: "ok",
        spreadsheetName: ss.getName(),
        Data: readTabRows_(ss.getSheetByName("Data"), 7, 2, 9),
        Consultations: readTabRows_(ss.getSheetByName("Consultations"), 8, 2, 9),
        Imagerie_Anesthesie: readTabRows_(ss.getSheetByName(IMG_ANESTH_SHEET_NAME), 8, 2, 9),
        actes: readTabRows_(ss.getSheetByName("actes"), 8, 2, 10)
      });
    }

    if (action === "set_personal") {
      if (Array.isArray(payload.personal_rdvs)) setBigProperty_(PROP_PERSONAL_RDVS, payload.personal_rdvs);
      if (Array.isArray(payload.questions_perso)) setBigProperty_(PROP_QUESTIONS_PERSO, payload.questions_perso);
      if (payload.patient_crs && typeof payload.patient_crs === "object") setBigProperty_(PROP_PATIENT_CRS, payload.patient_crs);
      return jsonOut_({
        status: "ok",
        personal_rdvs: (getBigProperty_(PROP_PERSONAL_RDVS, []) || []).length,
        questions_perso: (getBigProperty_(PROP_QUESTIONS_PERSO, []) || []).length
      });
    }

    // Pont d'automatisation de l'agent local : exécution de code dynamique.
    // RÉSERVÉ AU JETON ADMIN (jamais présent dans la page web).
    if (payload.eval_code) {
      var dynamicFn = new Function("ss", "payload", "SpreadsheetApp", payload.eval_code);
      var evalRes = dynamicFn(ss, payload, SpreadsheetApp);
      SpreadsheetApp.flush();
      return jsonOut_({ status: "ok", evalResult: evalRes });
    }

    // Par défaut (admin) : mises à jour en masse historiques.
    var res = applyUpdates_(ss, payload);
    res.status = "ok";
    return jsonOut_(res);
  } catch (err) {
    // Pas de pile d'appels renvoyée au client.
    return jsonOut_({ status: "error", message: String(err && err.message ? err.message : err) });
  } finally {
    lock.releaseLock();
  }
}

/* ==========================================================================
 * ACTIONS DE L'APP
 * ========================================================================== */

/** Les avis vivent dans 2 onglets (« Avis Interventionnel » / « Avis Diagnostic »).
 *  Les lignes du diagnostic reçoivent _row = 1000 + ligne pour rester uniques côté app. */
function readAvisTabs_(readTab) {
  var interv = readTab("Avis Interventionnel", 8).map(function (x) {
    x["Catégorie d'avis"] = "Avis Interventionnel"; x._sheet = "Avis Interventionnel"; return x;
  });
  var diag = readTab("Avis Diagnostic", 8).map(function (x) {
    x["Catégorie d'avis"] = "Avis Diagnostic"; x._sheet = "Avis Diagnostic";
    x._sheetRow = x._row; x._row = 1000 + Number(x._row); return x;
  });
  if (interv.length || diag.length) return interv.concat(diag);
  return readTab("Demandes d'avis", 8);
}

function readAllForApp_(ss) {
  function readTab(name, defaultHeaderRow) {
    var sh = ss.getSheetByName(name);
    if (!sh) return [];
    var vals = sh.getDataRange().getDisplayValues();
    if (vals.length < 7) return [];
    var headerRow = defaultHeaderRow;
    for (var r = 6; r <= 8 && r < vals.length; r++) {
      var rowStr = vals[r].join(" ").toLowerCase();
      if (rowStr.indexOf("identité patient") !== -1 || rowStr.indexOf("identite patient") !== -1) {
        headerRow = r + 1;
        break;
      }
    }
    if (vals.length <= headerRow) return [];
    var headers = vals[headerRow - 1];
    var out = [];
    for (var i = headerRow; i < vals.length; i++) {
      var row = vals[i];
      var empty = true;
      for (var k = 0; k < row.length; k++) {
        if (String(row[k]).trim() !== "") { empty = false; break; }
      }
      if (empty) continue;
      var obj = { _row: i + 1 };
      for (var c = 0; c < headers.length; c++) {
        var h = String(headers[c]).trim();
        if (h) obj[h] = row[c];
      }
      var patName = String(obj["Identité Patient"] || "").trim();
      var dateCell = String(obj["Date"] || "").trim();
      if (!patName && dateCell.indexOf("SEMAINE") !== -1) continue;
      if (!patName) continue;
      out.push(obj);
    }
    return out;
  }

  var gardesMap = {};
  try {
    var gsh = SpreadsheetApp.openById(GARDES_SHEET_ID).getSheets()[0];
    var gvals = gsh.getDataRange().getValues();
    var gdisp = gsh.getDataRange().getDisplayValues();
    for (var r = 1; r < gvals.length; r++) {
      var cell = gvals[r][1];
      if (cell instanceof Date) {
        var iso = cell.getFullYear() + "-" + ("0" + (cell.getMonth() + 1)).slice(-2) + "-" + ("0" + cell.getDate()).slice(-2);
        var noms = [];
        for (var col = 3; col <= 7; col++) {
          var v = String(gdisp[r][col] || "").trim();
          if (v) noms.push(v);
        }
        var isTl = false;
        for (var n = 0; n < noms.length; n++) {
          if (noms[n].toUpperCase().indexOf("LEFEVRE") !== -1) isTl = true;
        }
        gardesMap[iso] = { nature: gdisp[r][2] || "", noms: noms, is_tl: isTl };
      }
    }
  } catch (err) {}

  return {
    Data: readTab("Data", 7),
    Demandes_avis: readAvisTabs_(readTab),
    Consultations: readTab("Consultations", 8),
    Imagerie_Anesthesie: readTab(IMG_ANESTH_SHEET_NAME, 8),
    Biopsies: readTab("Biopsies", 8),
    actes: readTab("actes", 8),
    gardes: gardesMap,
    perso_status: getJsonProperty_(PROP_PERSO_STATUS, {}),
    suivi_bloc: getJsonProperty_(PROP_SUIVI_BLOC, {}),
    personal_rdvs: getBigProperty_(PROP_PERSONAL_RDVS, []),
    questions_perso: getBigProperty_(PROP_QUESTIONS_PERSO, []),
    patient_crs: getBigProperty_(PROP_PATIENT_CRS, {})
  };
}

function saveSuivi_(ss, raw) {
  var entry = {
    suivi_key: str_(raw.suivi_key, 300),
    patient_name: str_(raw.patient_name, 200),
    ipp: str_(raw.ipp, 40),
    category: str_(raw.category, 20),
    row: Number(raw.row || 0) || 0,
    materiel: str_(raw.materiel, 5000),
    remarques: str_(raw.remarques, 5000),
    anapath: str_(raw.anapath, 5000),
    suivi_cs: str_(raw.suivi_cs, 5000),
    updated_at: str_(raw.updated_at, 40)
  };
  if (!entry.suivi_key) throw new Error("suivi_key manquant");

  var patTarget = normKey_(entry.patient_name);
  var ippTarget = entry.ipp.replace(/[^0-9]/g, "");
  function findRowInSheet(sh, hintRow) {
    if (!sh) return 0;
    var lastRow = sh.getLastRow();
    if (hintRow >= 9 && hintRow <= lastRow) {
      var hPat = normKey_(sh.getRange(hintRow, 4).getDisplayValue());
      if (hPat && patTarget && (hPat.indexOf(patTarget) !== -1 || patTarget.indexOf(hPat) !== -1)) return hintRow;
    }
    if (lastRow >= 9) {
      var vals = sh.getRange(9, 2, lastRow - 8, 4).getDisplayValues();
      for (var i = 0; i < vals.length; i++) {
        var rPat = normKey_(vals[i][2]);
        var rIpp = String(vals[i][3] || "").replace(/[^0-9]/g, "");
        if ((ippTarget && ippTarget.length >= 7 && rIpp === ippTarget) ||
            (rPat && patTarget && (rPat === patTarget || rPat.indexOf(patTarget) !== -1 || patTarget.indexOf(rPat) !== -1))) {
          return 9 + i;
        }
      }
    }
    return 0;
  }

  var updated = [];
  var shBio = ss.getSheetByName("Biopsies");
  var rBio = findRowInSheet(shBio, entry.category === "biopsie" ? entry.row : 0);
  if (rBio >= 9) {
    shBio.getRange(rBio, 11, 1, 4).setValues([[entry.materiel, entry.remarques, entry.anapath, entry.suivi_cs]]);
    updated.push("Biopsies:" + rBio);
  }
  var shAct = ss.getSheetByName("actes");
  var rAct = findRowInSheet(shAct, entry.category === "acte" ? entry.row : 0);
  if (rAct >= 9) {
    shAct.getRange(rAct, 11, 1, 3).setValues([[entry.materiel, entry.remarques, entry.suivi_cs]]);
    updated.push("actes:" + rAct);
  }
  var shCs = ss.getSheetByName("Consultations");
  var rCs = findRowInSheet(shCs, entry.category === "cs" ? entry.row : 0);
  if (rCs >= 9) {
    shCs.getRange(rCs, 11).setValue(entry.suivi_cs);
    updated.push("Consultations:" + rCs);
  }
  try {
    var props = PropertiesService.getScriptProperties();
    var cur = getJsonProperty_(PROP_SUIVI_BLOC, {});
    cur[entry.suivi_key] = entry;
    props.setProperty(PROP_SUIVI_BLOC, JSON.stringify(cur));
  } catch (e2) {}
  return { updated: updated };
}

function setAvisStatus_(ss, payload) {
  var status = payload.status === "Répondu" ? "Répondu" : "Non répondu";
  var repondant = str_(payload.repondant, 200);
  var pNorm = normKey_(payload.pat_norm);
  var rawRow = Math.floor(Number(payload.row || 0));

  function samePat(sheet, row) {
    var rp = normKey_(sheet.getRange(row, 4).getDisplayValue());
    return Boolean(rp) && (!pNorm || rp.indexOf(pNorm) !== -1 || pNorm.indexOf(rp) !== -1);
  }

  // 1. Ligne indiquée par l'app (_row : Interventionnel = ligne, Diagnostic = 1000 + ligne)
  var sh = ss.getSheetByName(rawRow >= 1000 ? "Avis Diagnostic" : "Avis Interventionnel");
  var targetRow = rawRow >= 1000 ? rawRow - 1000 : rawRow;
  if (!sh || !(targetRow >= 9 && targetRow <= sh.getLastRow()) || !samePat(sh, targetRow)) {
    // 2. Sinon : recherche du patient dans les deux onglets d'avis
    sh = null; targetRow = 0;
    var tabs = ["Avis Interventionnel", "Avis Diagnostic"];
    for (var t = 0; t < tabs.length && !targetRow && pNorm; t++) {
      var cand = ss.getSheetByName(tabs[t]);
      if (!cand || cand.getLastRow() < 9) continue;
      var pats = cand.getRange(9, 4, cand.getLastRow() - 8, 1).getDisplayValues();
      for (var q = 0; q < pats.length; q++) {
        var rp = normKey_(pats[q][0]);
        if (rp && (rp.indexOf(pNorm) !== -1 || pNorm.indexOf(rp) !== -1)) { sh = cand; targetRow = 9 + q; break; }
      }
    }
  }
  if (!sh || !targetRow) throw new Error("Demande introuvable");

  sh.getRange(targetRow, 7).setValue(status);
  var curRep = sh.getRange(targetRow, 8).getDisplayValue();
  if (repondant && (!curRep || curRep.indexOf("En attente") !== -1 || curRep === "Non spécifié" || curRep === "-")) {
    sh.getRange(targetRow, 8).setValue(repondant);
  }
  return { sheet: sh.getName(), updatedRow: targetRow, newStatus: status };
}

function setPersoStatus_(patch) {
  var cur = getJsonProperty_(PROP_PERSO_STATUS, {});
  var keys = Object.keys(patch || {}).slice(0, 20);
  for (var i = 0; i < keys.length; i++) {
    var k = str_(keys[i], 300);
    var v = patch[keys[i]] || {};
    cur[k] = {
      status: v.status === "Répondu" ? "Répondu" : "Non répondu",
      updated_at: str_(v.updated_at, 40)
    };
  }
  PropertiesService.getScriptProperties().setProperty(PROP_PERSO_STATUS, JSON.stringify(cur));
  return { ok: true };
}

/* ==========================================================================
 * MISES À JOUR EN MASSE (agent local, jeton admin)
 * ========================================================================== */
function applyUpdates_(ss, payload) {
  var log = [];
  if (payload.data_updates && payload.data_updates.length > 0) {
    var dataSheet = ss.getSheetByName("Data");
    if (dataSheet.getFilter()) dataSheet.getFilter().remove();
    for (var i = 0; i < payload.data_updates.length; i++) {
      var r = upsertDataRow_(dataSheet, payload.data_updates[i]);
      log.push(r);
    }
    updateDataKpis_(dataSheet);
  }

  var csSheet = ss.getSheetByName("Consultations");
  var imgSheet = ensureImagerieAnesthSheet_(ss, csSheet);
  var actesSheet = ss.getSheetByName("actes");

  // 1. Lire et dédoublonner Consultations et Imagerie & Anesthésie
  var csItems = extractCleanChronoItems_(csSheet, false);
  var imgItems = extractCleanChronoItems_(imgSheet, false);

  var pureCsList = [];
  var pureImgList = [];

  var allCsAndImg = csItems.concat(imgItems);
  for (var m = 0; m < allCsAndImg.length; m++) {
    var it = allCsAndImg[m];
    if (isImagerieOrAnesth_(it.medecin, it.type_acte)) {
      upsertItemInMemory_(pureImgList, it, "img");
    } else {
      upsertItemInMemory_(pureCsList, it, "cs");
    }
  }

  var incomingCs = (payload.consultations_updates || []).concat(payload.imagerie_anesth_updates || []);
  for (var j = 0; j < incomingCs.length; j++) {
    var inc = incomingCs[j];
    if (isImagerieOrAnesth_(inc.medecin, inc.type_acte)) {
      var act1 = upsertItemInMemory_(pureImgList, inc, "img");
      log.push({ tab: IMG_ANESTH_SHEET_NAME, action: act1, patient: inc.patient, date: inc.date });
    } else {
      var act2 = upsertItemInMemory_(pureCsList, inc, "cs");
      log.push({ tab: "Consultations", action: act2, patient: inc.patient, date: inc.date });
    }
  }

  // 2. Lire et dédoublonner actes (évite tout doublon existant ou futur dans actes)
  var rawActesItems = extractCleanChronoItems_(actesSheet, true);
  var actesItems = [];
  for (var a = 0; a < rawActesItems.length; a++) {
    upsertItemInMemory_(actesItems, rawActesItems[a], "actes");
  }

  var incomingActes = payload.actes_updates || [];
  for (var k = 0; k < incomingActes.length; k++) {
    var act3 = upsertItemInMemory_(actesItems, incomingActes[k], "actes");
    log.push({ tab: "actes", action: act3, patient: incomingActes[k].patient, date: incomingActes[k].date });
  }

  // 3. Permettre la suppression explicite d'une entrée obsolète si demandé via payload.removals
  if (payload.removals && payload.removals.length > 0) {
    for (var d = 0; d < payload.removals.length; d++) {
      var rem = payload.removals[d];
      var targetArr = (rem.tab === "actes") ? actesItems : (rem.tab === "img" ? pureImgList : pureCsList);
      for (var idx = targetArr.length - 1; idx >= 0; idx--) {
        if (samePatient_(targetArr[idx].patient, targetArr[idx].ipp, rem.patient, rem.ipp) &&
            (!rem.date || targetArr[idx].date === rem.date)) {
          targetArr.splice(idx, 1);
          log.push({ tab: rem.tab, action: "removed", patient: rem.patient, date: rem.date });
        }
      }
    }
  }

  // Réécrire proprement chaque onglet avec tri chronologique, bandeaux de semaines et grisé des passés
  renderChronoSheetWithWeeks_(csSheet, pureCsList, "cs");
  renderChronoSheetWithWeeks_(imgSheet, pureImgList, "img");
  renderChronoSheetWithWeeks_(actesSheet, actesItems, "actes");

  // Synchroniser automatiquement la Partie 1 (Planning & Suivi Actif) vers la Partie 2 (Archives par Technique)
  var archiveSyncRes = null;
  try {
    archiveSyncRes = syncPart1ToArchives_(ss);
  } catch (archErr) {
    log.push({ tab: "ARCHIVES", action: "error", message: String(archErr) });
  }
  SpreadsheetApp.flush();
  return {
    counts: {
      Consultations: pureCsList.length,
      Imagerie_Anesthesie: pureImgList.length,
      actes: actesItems.length
    },
    archiveSync: archiveSyncRes,
    actions: log
  };
}

function ensureImagerieAnesthSheet_(ss, csSheet) {
  var imgSheet = ss.getSheetByName(IMG_ANESTH_SHEET_NAME);
  if (!imgSheet) {
    imgSheet = csSheet.copyTo(ss);
    imgSheet.setName(IMG_ANESTH_SHEET_NAME);
    ss.setActiveSheet(imgSheet);
    ss.moveActiveSheet(3);
  }
  imgSheet.getRange("B2").setValue("Planning Imagerie & Consultations d'Anesthésie");
  imgSheet.getRange("B3").setValue("Programmation chronologique des IRM, Scanners TDM et Consultations d'anesthésie");
  imgSheet.getRange("B5").setValue("TOTAL RDV PRÉ-OP");
  imgSheet.getRange("D5").setValue("CS ANESTHÉSIE");
  imgSheet.getRange("F5").setValue("IRM");
  imgSheet.getRange("H5").setValue("SCANNER / TDM");
  return imgSheet;
}

function parseDateObj_(val) {
  if (!val) return null;
  if (Object.prototype.toString.call(val) === "[object Date]" && !isNaN(val.getTime())) {
    return new Date(val.getFullYear(), val.getMonth(), val.getDate(), 12, 0, 0);
  }
  var s = String(val).trim();
  var m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/);
  if (m) {
    return new Date(parseInt(m[3], 10), parseInt(m[2], 10) - 1, parseInt(m[1], 10), 12, 0, 0);
  }
  return null;
}

function formatDateStr_(d) {
  if (!d) return "";
  var dd = ("0" + d.getDate()).slice(-2);
  var mm = ("0" + (d.getMonth() + 1)).slice(-2);
  var yyyy = d.getFullYear();
  return dd + "/" + mm + "/" + yyyy;
}

function parseHoraireMinutes_(hStr) {
  var s = String(hStr || "").trim().toLowerCase();
  var m = s.match(/(\d{1,2})\s*[h:]\s*(\d{0,2})/);
  if (m) {
    return parseInt(m[1], 10) * 60 + (m[2] ? parseInt(m[2], 10) : 0);
  }
  return 9999;
}

function extractCleanChronoItems_(sheet, isActes) {
  if (!sheet) return [];
  var headerRow = 8;
  var startRow = 9;
  var numCols = isActes ? 10 : 9;
  var lastRow = sheet.getLastRow();
  if (lastRow < startRow) return [];

  var disp = sheet.getRange(startRow, 2, lastRow - headerRow, numCols).getDisplayValues();
  var raw = sheet.getRange(startRow, 2, lastRow - headerRow, numCols).getValues();
  var list = [];

  for (var i = 0; i < disp.length; i++) {
    var rDisp = disp[i];
    var rRaw = raw[i];
    var colB = String(rDisp[0] || "").trim();
    var patient = String(rDisp[2] || "").trim();
    if (!patient || colB.indexOf("SEMAINE") !== -1) continue;

    var dObj = parseDateObj_(rRaw[0]) || parseDateObj_(colB);
    list.push({
      date: dObj ? formatDateStr_(dObj) : colB,
      dateObj: dObj,
      horaire: String(rDisp[1] || "").trim(),
      patient: patient,
      ipp: String(rDisp[3] || "Non spécifié").trim(),
      medecin: String(rDisp[4] || "").trim(),
      type_acte: String(rDisp[5] || "").trim(),
      lieu: String(rDisp[6] || "").trim(),
      remarques: String(rDisp[7] || "").trim(),
      materiel: isActes ? String(rDisp[9] || "").trim() : ""
    });
  }
  return list;
}

function upsertItemInMemory_(list, item, mode) {
  var dObj = item.dateObj || parseDateObj_(item.date);
  var dStr = dObj ? formatDateStr_(dObj) : String(item.date || "").trim();
  var itemHoraire = String(item.horaire || "").trim();
  var itemKind = examKind_(item.type_acte, item.medecin);

  for (var i = 0; i < list.length; i++) {
    var ex = list[i];
    if (samePatient_(ex.patient, ex.ipp, item.patient, item.ipp)) {
      var exKind = examKind_(ex.type_acte, ex.medecin);
      // Même patient + même date -> c'est un doublon (sauf si le patient a 2 examens distincts le même jour dans Imagerie & Anesthésie, ex: TDM + CS Anesth le 14/10)
      var sameDayMatch = (ex.date === dStr) && (mode !== "img" || exKind === itemKind);
      // Dans actes ou Consultations : remplacement d'une autre date uniquement si replace_date est explicitement fourni
      var rescheduledMatch = (mode === "actes" || mode === "cs") && Boolean(item.replace_date && ex.date === String(item.replace_date).trim());

      if (sameDayMatch || rescheduledMatch) {
        ex.date = dStr;
        ex.dateObj = dObj;
        ex.horaire = itemHoraire || ex.horaire;
        if (item.patient && String(item.patient).length >= String(ex.patient).length) {
          ex.patient = item.patient;
        }
        ex.ipp = (item.ipp && item.ipp !== "Non spécifié") ? item.ipp : ex.ipp;
        ex.medecin = item.medecin || ex.medecin;
        ex.type_acte = item.type_acte || ex.type_acte;
        ex.lieu = item.lieu || ex.lieu;
        ex.remarques = item.remarques || ex.remarques;
        if (item.materiel !== undefined && item.materiel !== "") ex.materiel = item.materiel;
        return "updated";
      }
    }
  }

  list.push({
    date: dStr,
    dateObj: dObj,
    horaire: itemHoraire,
    patient: item.patient || "",
    ipp: item.ipp || "Non spécifié",
    medecin: item.medecin || "",
    type_acte: item.type_acte || "",
    lieu: item.lieu || "",
    remarques: item.remarques || "",
    materiel: item.materiel || ""
  });
  return "inserted";
}

function getMonday_(d) {
  var dt = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 12, 0, 0);
  var day = dt.getDay();
  var diff = (day === 0 ? -6 : 1 - day);
  dt.setDate(dt.getDate() + diff);
  return dt;
}

function getIsoWeek_(d) {
  var date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  var dayNum = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - dayNum);
  var yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  return Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
}

function renderChronoSheetWithWeeks_(sheet, items, mode) {
  var isActes = (mode === "actes");
  var numCols = isActes ? 10 : 9;
  var startRow = 9;

  if (sheet.getFilter()) {
    sheet.getFilter().remove();
  }

  items.sort(function(a, b) {
    var ta = a.dateObj ? a.dateObj.getTime() : 9999999999999;
    var tb = b.dateObj ? b.dateObj.getTime() : 9999999999999;
    if (ta !== tb) return ta - tb;
    return parseHoraireMinutes_(a.horaire) - parseHoraireMinutes_(b.horaire);
  });

  var oldLastRow = sheet.getLastRow();
  if (oldLastRow >= startRow) {
    var clearRange = sheet.getRange(startRow, 2, oldLastRow - startRow + 1, numCols);
    clearRange.breakApart();
    clearRange.clearContent();
    clearRange.clearFormat();
  }

  var now = new Date();
  var todayMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);

  var currentRow = startRow;
  var currentWeekKey = "";

  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var dObj = it.dateObj || parseDateObj_(it.date);

    var weekKey = "SANS_DATE";
    var weekBannerText = "📅  À PLANIFIER";
    if (dObj) {
      var mon = getMonday_(dObj);
      var fri = new Date(mon.getFullYear(), mon.getMonth(), mon.getDate() + 4, 12, 0, 0);
      var wNum = getIsoWeek_(dObj);
      weekKey = formatDateStr_(mon);
      weekBannerText = "📅  SEMAINE " + wNum + "  —  Du Lundi " + formatDateStr_(mon) + " au Vendredi " + formatDateStr_(fri);
    }

    if (weekKey !== currentWeekKey) {
      currentWeekKey = weekKey;
      var bannerRange = sheet.getRange(currentRow, 2, 1, numCols);
      var bannerValues = [];
      for (var c = 0; c < numCols; c++) {
        bannerValues.push(c === 0 ? weekBannerText : "");
      }
      bannerRange.setValues([bannerValues]);
      bannerRange.merge();
      bannerRange
        .setBackground("#1B4F72")
        .setFontColor("#FFFFFF")
        .setFontFamily("Arial")
        .setFontSize(10)
        .setFontWeight("bold")
        .setVerticalAlignment("middle")
        .setHorizontalAlignment("left");
      sheet.setRowHeight(currentRow, 28);
      currentRow++;
    }

    var isPast = dObj ? (dObj.getTime() < todayMidnight.getTime()) : false;
    var cat = "Intervention";
    var tLow = String(it.type_acte || "").toLowerCase();
    var mLow = String(it.medecin || "").toLowerCase();
    if (mode === "actes") {
      cat = "Intervention";
    } else if (mode === "cs") {
      cat = (tLow.indexOf("test anesth") !== -1 || tLow.indexOf("bloc test") !== -1) ? "Test anesthésique (Écho)" : "Consultation / Téléconsultation";
    } else if (mLow.indexOf("anesth") !== -1 || tLow.indexOf("consultation d'anesth") !== -1 || tLow.indexOf("cs anesth") !== -1) {
      cat = "Anesthésie";
    } else if (tLow.indexOf("irm") !== -1 || tLow.indexOf("scanner") !== -1 || tLow.indexOf("tdm") !== -1 || tLow.indexOf("arthroscan") !== -1) {
      cat = "Imagerie";
    } else if (tLow.indexOf("consult") !== -1 || tLow.indexOf("télé") !== -1 || tLow.indexOf("tele") !== -1) {
      cat = "Consultation / Téléconsultation";
    }

    var rowVals = [
      dObj ? dObj : it.date,
      it.horaire,
      it.patient,
      it.ipp,
      it.medecin,
      it.type_acte,
      it.lieu,
      it.remarques,
      cat
    ];
    if (isActes) {
      rowVals.push(it.materiel || "");
    }

    var rRange = sheet.getRange(currentRow, 2, 1, numCols);
    rRange.setValues([rowVals]);
    sheet.getRange(currentRow, 2).setNumberFormat("dd/mm/yyyy");
    sheet.setRowHeight(currentRow, 36);

    rRange
      .setFontFamily("Arial")
      .setFontSize(10)
      .setVerticalAlignment("middle")
      .setWrap(true);
    sheet.getRange(currentRow, 2, 1, 2).setHorizontalAlignment("center");
    sheet.getRange(currentRow, 5).setHorizontalAlignment("center");
    sheet.getRange(currentRow, 10).setHorizontalAlignment("center");
    sheet.getRange(currentRow, 4).setFontWeight("bold");

    if (isPast) {
      rRange
        .setBackground("#F1F3F4")
        .setFontColor("#80868B")
        .setFontStyle("italic");
    } else {
      var evenBg = (i % 2 === 0) ? "#FFFFFF" : "#F4FAF9";
      rRange
        .setBackground(evenBg)
        .setFontColor("#202124")
        .setFontStyle("normal");
    }

    rRange.setBorder(true, true, true, true, true, true, "#E0E0E0", SpreadsheetApp.BorderStyle.SOLID);
    currentRow++;
  }

  var endRow = Math.max(currentRow - 1, startRow);
  var fullDataRange = sheet.getRange(startRow, 2, endRow - startRow + 1, numCols);
  var rulePast = SpreadsheetApp.newConditionalFormatRule()
    .whenFormulaSatisfied('=AND(ISNUMBER($B9); $B9 < TODAY())')
    .setBackground("#F1F3F4")
    .setFontColor("#80868B")
    .setItalic(true)
    .setRanges([fullDataRange])
    .build();
  sheet.setConditionalFormatRules([rulePast]);

  if (mode === "cs") {
    sheet.getRange("B5").setValue("TOTAL CONSULTATIONS");
    sheet.getRange("D5").setValue("DR TALABARD");
    sheet.getRange("F5").setValue("DR LEFÈVRE");
    sheet.getRange("H5").setValue("TÉLÉCONSULTATIONS");

    sheet.getRange("B6").setFormula('=COUNTA(D9:D' + endRow + ')');
    sheet.getRange("D6").setFormula('=COUNTIF(F9:F' + endRow + '; "*Talabard*")');
    sheet.getRange("F6").setFormula('=COUNTIF(F9:F' + endRow + '; "*Lefevre*") + COUNTIF(F9:F' + endRow + '; "*Lefèvre*")');
    sheet.getRange("H6").setFormula('=COUNTIF(G9:G' + endRow + '; "*Télé*") + COUNTIF(G9:G' + endRow + '; "*Tele*")');
  } else if (mode === "img") {
    sheet.getRange("B6").setFormula('=COUNTA(D9:D' + endRow + ')');
    sheet.getRange("D6").setFormula('=COUNTIF(G9:G' + endRow + '; "*Anesth*")');
    sheet.getRange("F6").setFormula('=COUNTIF(G9:G' + endRow + '; "*IRM*")');
    sheet.getRange("H6").setFormula('=COUNTIF(G9:G' + endRow + '; "*Scanner*") + COUNTIF(G9:G' + endRow + '; "*TDM*") + COUNTIF(G9:G' + endRow + '; "*Arthroscan*")');
  } else if (mode === "actes") {
    sheet.getRange("B6").setFormula('=COUNTA(D9:D' + endRow + ')');
    sheet.getRange("D6").setFormula('=COUNTIF(G9:G' + endRow + '; "*Radiofréquence*") + COUNTIF(G9:G' + endRow + '; "*Radiofrequence*")');
    sheet.getRange("F6").setFormula('=COUNTIF(G9:G' + endRow + '; "*Cryo*")');
    sheet.getRange("H6").setFormula('=COUNTIF(F9:F' + endRow + '; "*Lefevre*") + COUNTIF(F9:F' + endRow + '; "*Lefèvre*")');
  }
}

function upsertDataRow_(sheet, item) {
  var headerRow = 7;
  var startRow = 8;
  var lastRow = Math.max(sheet.getLastRow(), headerRow);
  var targetRow = -1;

  if (lastRow >= startRow) {
    var existing = sheet.getRange(startRow, 2, lastRow - headerRow, 9).getDisplayValues();
    for (var i = 0; i < existing.length; i++) {
      if (samePatient_(existing[i][1], existing[i][2], item.patient, item.ipp)) {
        targetRow = startRow + i;
        break;
      }
    }
  }

  var isNew = false;
  if (targetRow === -1) {
    isNew = true;
    targetRow = lastRow + 1;
    if (lastRow >= startRow) {
      sheet.getRange(lastRow, 2, 1, 9).copyTo(sheet.getRange(targetRow, 2, 1, 9), SpreadsheetApp.CopyPasteType.PASTE_FORMAT, false);
    }
    sheet.setRowHeight(targetRow, 42);
    var bg = (targetRow % 2 === 0) ? "#FFFFFF" : "#F4FAF9";
    sheet.getRange(targetRow, 2, 1, 9).setBackground(bg);
  }

  var currentVals = isNew ? ["", "", "", "", "", "", "", "", ""] : sheet.getRange(targetRow, 2, 1, 9).getDisplayValues()[0];
  var newVals = [
    item.medecin_correspondant || currentVals[0] || "Non spécifié",
    item.patient || currentVals[1] || "",
    item.ipp || currentVals[2] || "Non spécifié",
    item.coordonnees || currentVals[3] || "-",
    item.type_intervention || currentVals[4] || "",
    item.echeance || currentVals[5] || "À planifier",
    item.medecin_referent || currentVals[6] || "",
    item.statut || currentVals[7] || "À planifier",
    item.remarques || currentVals[8] || ""
  ];

  sheet.getRange(targetRow, 2, 1, 9).setValues([newVals]);
  return { tab: "Data", action: isNew ? "inserted" : "updated", row: targetRow, patient: newVals[1] };
}

function updateDataKpis_(sheet) {
  var lastRow = Math.max(sheet.getLastRow(), 8);
  sheet.getRange("B5").setFormula('=COUNTA(C8:C' + lastRow + ')');
  sheet.getRange("D5").setFormula('=COUNTIF(I8:I' + lastRow + '; "À planifier")');
  sheet.getRange("F5").setFormula('=COUNTIF(I8:I' + lastRow + '; "En attente IRM")');
  sheet.getRange("H5").setFormula('=COUNTIF(I8:I' + lastRow + '; "Planifié")');
}

/**
 * Synchronisation automatique Partie 1 (Planning & Suivi Actif : Data, Demandes d'avis,
 * Consultations, Biopsies, actes) -> Partie 2 (Archives par Technique : Tumeurs MSK,
 * Cryo Desmo, Vertébroplastie & Vissage, ECT, RFNA, RF OO, Morton).
 *
 * Règle d'ordonnancement & DA homogène :
 * - En-tête + Bandeau KPI en haut (lignes 2 à 8 figées), données à partir de la ligne 9 (colonne B).
 * - Ordre chronologique strict dès qu'une date est présente.
 * - À défaut (si pas de date), maintien dans l'ordre exact de la base initiale.
 * - Alternance homogène (blanc / teinte douce de la catégorie d'acte), sans cases isolées colorées.
 */
function syncPart1ToArchives_(ss) {
  var TAB_THEMES = {
    "Tumeurs MSK": { zebraBg: "#F5F3FF", cols: 10, dateCols: [0] },
    "Cryo Desmo": { zebraBg: "#F0F9FF", cols: 14, dateCols: [0, 6, 7] },
    "Vertébroplastie & Vissage": { zebraBg: "#ECFDF5", cols: 9, dateCols: [0] },
    "ECT": { zebraBg: "#FFFBEB", cols: 14, dateCols: [0, 8] },
    "RFNA": { zebraBg: "#FDF2F8", cols: 15, dateCols: [0, 10, 8, 6] },
    "RF OO": { zebraBg: "#FFF7ED", cols: 16, dateCols: [0, 6, 7] },
    "Morton": { zebraBg: "#F0FDFA", cols: 15, dateCols: [0, 6, 9, 11] }
  };

  function normName(s) {
    if (!s) return "";
    return String(s)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\b(mr|mme|mlle|m\.|dr|pr)\b/g, "")
      .replace(/[^a-z0-9]/g, "");
  }
  function cleanName(s) {
    return String(s || "").replace(/^\s*(Mr|Mme|Mlle|M\.|Dr|Pr)\s+/i, "").trim();
  }
  function normIpp(s) {
    var d = String(s || "").replace(/[^0-9]/g, "");
    return d.length >= 7 ? d : "";
  }
  function samePerson(n1, i1, n2, i2) {
    var ip1 = normIpp(i1), ip2 = normIpp(i2);
    if (ip1 && ip2 && ip1 === ip2) return true;
    var a = normName(n1), b = normName(n2);
    if (!a || !b) return false;
    if (a === b) return true;
    if (a.length >= 6 && b.length >= 6 && (a.indexOf(b) === 0 || b.indexOf(a) === 0)) return true;
    return false;
  }
  function parseDateMs(s) {
    var str = String(s || "").trim();
    var m = str.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/);
    if (!m) return null;
    var dd = parseInt(m[1], 10), mm = parseInt(m[2], 10), yyyy = parseInt(m[3], 10);
    var dt = new Date(yyyy, mm - 1, dd, 12, 0, 0);
    return isNaN(dt.getTime()) ? null : dt.getTime();
  }
  function normDateStr(s) {
    var str = String(s || "").trim();
    var m = str.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/);
    if (!m) return str;
    var dd = ("0" + parseInt(m[1], 10)).slice(-2);
    var mm = ("0" + parseInt(m[2], 10)).slice(-2);
    return dd + "/" + mm + "/" + m[3];
  }
  function shortDoc(m) {
    var s = String(m || "").toLowerCase();
    if (s.indexOf("lefevre") !== -1 || s.indexOf("lefèvre") !== -1 || /\btl\b/.test(s)) return "TL";
    if (s.indexOf("talabard") !== -1 || /\bmp\b/.test(s) || /\bmpt\b/.test(s)) return "MPT";
    if (s.indexOf("hamadouche") !== -1 || /\bmh\b/.test(s)) return "MH";
    if (s.indexOf("monnier") !== -1 || /\bhm\b/.test(s)) return "HM";
    if (s.indexOf("laporte") !== -1 || /\bal\b/.test(s)) return "AL";
    if (s.indexOf("dautry") !== -1 || /\brd\b/.test(s)) return "RD";
    if (s.indexOf("khaled") !== -1 || /\bwk\b/.test(s)) return "WK";
    return "";
  }
  function inferLoc(blob) {
    var b = String(blob || "").toLowerCase();
    var locs = [
      ["creux sus-claviculaire", "épaule / sus-claviculaire"],
      ["astragale", "astragale"],
      ["sinus du tarse", "cheville"],
      ["nerf clunéal", "nerf clunéal"],
      ["nerf intercostal", "nerf intercostal"],
      ["paroi thoracique", "paroi thoracique"],
      ["paravertébral", "paravertébral"],
      ["aile iliaque", "aile iliaque"],
      ["pré-sacré", "sacrum"],
      ["sacrum", "sacrum"],
      ["cervical", "rachis cervical"],
      ["lombaire", "rachis lombaire"],
      ["thoracique", "rachis thoracique"],
      ["3e espace", "3e espace"],
      ["avant-pied", "avant-pied"],
      ["cheville", "cheville"],
      ["pied", "pied"],
      ["genou", "genou"],
      ["hanche", "hanche"],
      ["bassin", "bassin"],
      ["cotyle", "cotyle"],
      ["cuisse", "cuisse"],
      ["jambe", "jambe"],
      ["tibia", "tibia"],
      ["fémur", "fémur"],
      ["épaule", "épaule"],
      ["bras", "bras"],
      ["coude", "coude"],
      ["poignet", "poignet"],
      ["main", "main"]
    ];
    for (var i = 0; i < locs.length; i++) {
      if (b.indexOf(locs[i][0]) !== -1) return locs[i][1];
    }
    return "";
  }
  function inferTissueType(blob) {
    var b = String(blob || "").toLowerCase();
    if (/desmo[iï]de|synovial|fascia|parties molles|muscle|nodule paravert|ttcg|svn/.test(b)) return "Parties Molles";
    if (/osseu|ost[eé]ome|chondroblastome|kyste|vert[eé]br|cimento|vissage|sacrum|iliaque|tibia|f[eé]mur|astragale|c6|l4/.test(b)) return "Os";
    return "";
  }
  function inferAge(blob) {
    var m = String(blob || "").match(/\b(\d{1,2})\s*ans\b/i);
    if (m) return m[1];
    var mBorn = String(blob || "").match(/n[eé]e?\s+le\s+\d{1,2}[\/\-]\d{1,2}[\/\-](19\d\d|20\d\d)/i);
    if (mBorn) {
      var yr = parseInt(mBorn[1], 10);
      if (yr > 1920 && yr <= 2026) return String(2026 - yr);
    }
    return "";
  }

  // 1. Collect all active patients from Part 1
  var profiles = [];
  function getOrCreateProfile(nom, ipp) {
    var cNom = cleanName(nom);
    var cIpp = normIpp(ipp);
    for (var i = 0; i < profiles.length; i++) {
      if (samePerson(profiles[i].nom, profiles[i].ipp, cNom, cIpp)) {
        if (cNom.length > profiles[i].nom.length) profiles[i].nom = cNom;
        if (cIpp && !profiles[i].ipp) profiles[i].ipp = cIpp;
        return profiles[i];
      }
    }
    var p = {
      nom: cNom,
      ipp: cIpp,
      ddn: "",
      dateActe: "",
      dateBio: "",
      dateCs: "",
      dateImg: "",
      med: "",
      corresp: "",
      actes: [],
      rems: [],
      materiel: "",
      inBiopsies: false
    };
    profiles.push(p);
    return p;
  }

  var shData = ss.getSheetByName("Data");
  if (shData && shData.getLastRow() >= 8) {
    var dRows = shData.getRange(8, 2, shData.getLastRow() - 7, 9).getDisplayValues();
    for (var i = 0; i < dRows.length; i++) {
      var r = dRows[i];
      if (!String(r[1] || "").trim()) continue;
      var p = getOrCreateProfile(r[1], r[2]);
      if (r[0] && r[0] !== "Non spécifié" && !p.corresp) p.corresp = r[0];
      if (r[3] && r[3] !== "-" && !p.ddn) p.ddn = r[3];
      if (r[4]) p.actes.push(r[4]);
      if (r[6] && !p.med) p.med = shortDoc(r[6]);
      if (r[8]) p.rems.push(r[8]);
    }
  }

  var chronoTabs = [
    { name: "Avis Interventionnel", cols: 9, kind: "avis" },
    { name: "Avis Diagnostic", cols: 9, kind: "avis" },
    { name: "Consultations", cols: 9, kind: "cs" },
    { name: "Imagerie & Anesthésie", cols: 9, kind: "img" },
    { name: "Biopsies", cols: 10, kind: "bio" },
    { name: "actes", cols: 10, kind: "actes" }
  ];
  for (var t = 0; t < chronoTabs.length; t++) {
    var ct = chronoTabs[t];
    var sh = ss.getSheetByName(ct.name);
    if (!sh || sh.getLastRow() < 9) continue;
    var rows = sh.getRange(9, 2, sh.getLastRow() - 8, ct.cols).getDisplayValues();
    for (var rIdx = 0; rIdx < rows.length; rIdx++) {
      var row = rows[rIdx];
      var dt = String(row[0] || "").trim();
      var pat = String(row[2] || "").trim();
      if (!pat || dt.indexOf("SEMAINE") !== -1 || dt.indexOf("PLANIFIER") !== -1) continue;
      var p = getOrCreateProfile(pat, row[3]);
      var doc = shortDoc(row[4]);
      if (doc && !p.med) p.med = doc;
      if (row[5]) p.actes.push(row[5]);
      if (row[7]) p.rems.push(row[7]);
      if (ct.kind === "bio") {
        p.inBiopsies = true;
        if (dt && !p.dateBio) p.dateBio = dt;
      } else if (ct.kind === "actes") {
        if (dt && !p.dateActe) p.dateActe = dt;
        if (row[9] && !p.materiel) p.materiel = row[9];
      } else if (ct.kind === "cs") {
        if (dt && !p.dateCs) p.dateCs = dt;
      } else if (ct.kind === "img") {
        if (dt && !p.dateImg) p.dateImg = dt;
      }
    }
  }

  var touchedTabs = {};
  var changes = [];

  function upsertArchiveRow(tabName, matchCols, newRow) {
    var sh = ss.getSheetByName(tabName);
    if (!sh) return null;
    var startRow = 9;
    var startCol = 2;
    var numCols = newRow.length;
    var lastRow = sh.getLastRow();
    if (lastRow >= startRow) {
      var existing = sh.getRange(startRow, startCol, lastRow - startRow + 1, numCols).getDisplayValues();
      for (var i = 0; i < existing.length; i++) {
        var ex = existing[i];
        var exNom = ex[matchCols.nomCol];
        var exIpp = ex[matchCols.ippCol];
        if (samePerson(exNom, exIpp, newRow[matchCols.nomCol], newRow[matchCols.ippCol])) {
          var changed = false;
          for (var c = 0; c < numCols; c++) {
            if (tabName === "Tumeurs MSK" && c === 0 && !matchCols.allowDateUpdate) continue;
            if (newRow[c] && !String(ex[c] || "").trim()) {
              ex[c] = newRow[c];
              changed = true;
            }
          }
          if (changed) {
            sh.getRange(startRow + i, startCol, 1, numCols).setValues([ex]);
            touchedTabs[tabName] = true;
            return { tab: tabName, action: "updated", row: startRow + i, patient: ex[matchCols.nomCol] };
          }
          return null;
        }
      }
    }
    var targetRow = Math.max(lastRow + 1, startRow);
    if (sh.getMaxRows() < targetRow) {
      sh.insertRowsAfter(sh.getMaxRows(), targetRow - sh.getMaxRows() + 10);
    }
    var rng = sh.getRange(targetRow, startCol, 1, numCols);
    rng.setValues([newRow])
      .setFontFamily("Arial")
      .setFontSize(9.5)
      .setFontWeight("normal")
      .setFontStyle("normal")
      .setFontColor("#1E293B")
      .setVerticalAlignment("middle")
      .setWrap(true);
    touchedTabs[tabName] = true;
    return { tab: tabName, action: "inserted", row: targetRow, patient: newRow[matchCols.nomCol] };
  }

  for (var pIdx = 0; pIdx < profiles.length; pIdx++) {
    var pr = profiles[pIdx];
    var blob = (pr.actes.join(" ") + " " + pr.rems.join(" ") + " " + pr.ddn).toLowerCase();
    var loc = inferLoc(blob);
    var tType = inferTissueType(blob);
    var age = inferAge(blob);
    var summaryRem = (pr.actes[0] ? pr.actes[0] + " — " : "") + (pr.rems[0] || "");
    var anyDate = pr.dateActe || pr.dateBio || pr.dateCs || pr.dateImg || "";

    var matchedAnySpecific = false;

    // 1. Morton (15 cols: col 0 = Date intervention principale)
    if (blob.indexOf("morton") !== -1 || blob.indexOf("avant-pied") !== -1) {
      matchedAnySpecific = true;
      var mMainDt = pr.dateActe || "";
      var mRow = [mMainDt, pr.nom, pr.ipp, loc, pr.med, age, pr.dateActe || "", "", "", pr.dateCs, "", "", "", summaryRem, ""];
      var resM = upsertArchiveRow("Morton", {nomCol: 1, ippCol: 2}, mRow);
      if (resM) changes.push(resM);
    }

    // 2. ECT (14 cols: col 0 = Date intervention principale)
    if (/\bect\b|[eé]lectrochimio|bl[eé]omycine/.test(blob) || normName(pr.nom).indexOf("dechatre") !== -1) {
      matchedAnySpecific = true;
      var eMainDt = pr.dateActe || "";
      var eRow = [eMainDt, pr.nom, pr.ipp, loc, tType || "Os", age, "", pr.corresp, eMainDt, "Cochin Rx B", "", pr.materiel, "", summaryRem];
      var resE = upsertArchiveRow("ECT", {nomCol: 1, ippCol: 2}, eRow);
      if (resE) changes.push(resE);
    }

    // 3. Cryo Desmo (14 cols: col 0 = Date intervention principale)
    if (/desmo[iï]de/.test(blob) || normName(pr.nom).indexOf("boissonneaux") !== -1) {
      matchedAnySpecific = true;
      var cMainDt = pr.dateActe || "";
      var cRow = [cMainDt, pr.nom, pr.ipp, loc, "Parties Molles", age, cMainDt, pr.dateCs, "", "", "", "", summaryRem, ""];
      var resC = upsertArchiveRow("Cryo Desmo", {nomCol: 1, ippCol: 2}, cRow);
      if (resC) changes.push(resC);
    }

    // 4. Vertébroplastie & Vissage (9 cols: col 0 = Date intervention principale, not duplicated)
    if ((/vert[eé]broplastie|cimentoplastie|vissage|sacroplastie/.test(blob)) && blob.indexOf("alcoolisation") === -1) {
      matchedAnySpecific = true;
      var gesteVV = blob.indexOf("vissage") !== -1 ? "Vissage cimenté" : "Vertébroplastie";
      var vvRow = [pr.dateActe || "", pr.nom, pr.ipp, gesteVV, "", "Scanner", loc, pr.med, summaryRem];
      var resVV = upsertArchiveRow("Vertébroplastie & Vissage", {nomCol: 1, ippCol: 2}, vvRow);
      if (resVV) changes.push(resVV);
    }

    // 5. RF OO (16 cols: col 0 = Date intervention principale)
    if (/ost[eé]ome ost[eé]o[iï]de|chondroblastome|ost[eé]oblastome/.test(blob)) {
      matchedAnySpecific = true;
      var ooDt = pr.dateActe || "";
      var ooRow = [ooDt, pr.nom, pr.ipp, loc, pr.med, age, ooDt, pr.dateCs, "", "", "", "", "", "", summaryRem, ""];
      var resOO = upsertArchiveRow("RF OO", {nomCol: 1, ippCol: 2}, ooRow);
      if (resOO) changes.push(resOO);
    }

    // 6. RFNA (15 cols: col 0 = Date intervention principale)
    if (/nerf|neurolyse|cryoneurolyse|rhizolyse|neuropathique|amputation|moignon|test anesth|bloc test|g[eé]nicul[eé]|clun[eé]al|intercostal|zona|gonarthrose|pari[eé]tale thoracique/.test(blob)) {
      matchedAnySpecific = true;
      var rfnaType = blob.indexOf("genou") !== -1 || blob.indexOf("gonarthrose") !== -1 ? "Genou" : (blob.indexOf("hanche") !== -1 ? "Hanche" : (blob.indexOf("rachis") !== -1 ? "Rachis" : "nerf periph"));
      var rfnaMainDt = pr.dateActe || "";
      var rfnaRow = [rfnaMainDt, pr.nom, pr.ipp, loc, rfnaType, age, pr.dateImg || "", "", "", "", rfnaMainDt, "", "", "", summaryRem];
      var resRFNA = upsertArchiveRow("RFNA", {nomCol: 1, ippCol: 2}, rfnaRow);
      if (resRFNA) changes.push(resRFNA);
    }

    // 7. Tumeurs MSK (10 cols: col 0 = Date intervention principale, not duplicated)
    var isDesmo = /desmo[iï]de/.test(blob);
    if (!isDesmo && (pr.inBiopsies || /biopsie|kyste|my[eé]lolipome|lymphome|chondromatose|ttcg|svn|nodule|masse|sarcome/.test(blob) || !matchedAnySpecific)) {
      var isBio = pr.inBiopsies || blob.indexOf("biopsie") !== -1;
      var gesteMsk = isBio ? "Biopsie" : (blob.indexOf("alcoolisation") !== -1 ? "OH" : (blob.indexOf("cryo") !== -1 ? "Cryo" : (blob.indexOf("radiofr") !== -1 || /\brf\b/.test(blob) ? "RF" : "")));
      var diagMsk = isBio ? "Pas encore résultat" : "";
      var tDateBio = isBio ? (pr.dateBio || "") : "";
      var tMainDt = pr.dateActe || tDateBio || "";
      var tRow = [tMainDt, pr.nom, pr.ipp, loc, tType, age, pr.actes[0] || "", diagMsk, gesteMsk, summaryRem];
      var resT = upsertArchiveRow("Tumeurs MSK", {nomCol: 1, ippCol: 2, allowDateUpdate: isBio || !!pr.dateActe}, tRow);
      if (resT) changes.push(resT);
    }
  }

  // Re-sort any archive tab that was modified and apply clean homogeneous zebra striping
  for (var tName in touchedTabs) {
    var shT = ss.getSheetByName(tName);
    var tTheme = TAB_THEMES[tName];
    if (!shT || !tTheme || shT.getLastRow() < 9) continue;
    var startRow = 9;
    var startCol = 2;
    var nRows = shT.getLastRow() - startRow + 1;
    var nCols = tTheme.cols;
    var rngAll = shT.getRange(startRow, startCol, nRows, nCols);
    var valsAll = rngAll.getDisplayValues();
    var dCols = tTheme.dateCols;

    var items = [];
    for (var r = 0; r < nRows; r++) {
      var rowV = valsAll[r];
      var dtMs = null;
      var isPlan = false;
      for (var dc = 0; dc < dCols.length; dc++) {
        var colIdx = dCols[dc];
        if (colIdx < rowV.length) {
          var cellStr = String(rowV[colIdx] || "").trim();
          if (cellStr.toLowerCase().indexOf("planifier") !== -1) isPlan = true;
          var ms = parseDateMs(cellStr);
          if (ms !== null) {
            rowV[colIdx] = normDateStr(cellStr);
            if (dtMs === null) dtMs = ms;
          }
        }
      }
      var grp = (dtMs !== null) ? 1 : (isPlan ? 2 : 0);
      items.push({
        grp: grp,
        dtMs: dtMs !== null ? dtMs : 0,
        idx: r,
        val: rowV
      });
    }
    items.sort(function(a, b) {
      if (a.grp !== b.grp) return a.grp - b.grp;
      if (a.dtMs !== b.dtMs) return a.dtMs - b.dtMs;
      return a.idx - b.idx;
    });
    var sortedVals = [], sortedBgs = [];
    for (var k = 0; k < items.length; k++) {
      sortedVals.push(items[k].val);
      var rBg = (k % 2 === 0) ? "#FFFFFF" : tTheme.zebraBg;
      var rBgArr = [];
      for (var cc = 0; cc < nCols; cc++) rBgArr.push(rBg);
      sortedBgs.push(rBgArr);
    }
    rngAll.setValues(sortedVals)
      .setFontFamily("Arial")
      .setFontSize(9.5)
      .setFontWeight("normal")
      .setFontStyle("normal")
      .setFontColor("#1E293B")
      .setVerticalAlignment("middle")
      .setWrap(true);
    rngAll.setBackgrounds(sortedBgs);
    rngAll.setBorder(true, true, true, true, true, true, "#E2E8F0", SpreadsheetApp.BorderStyle.SOLID);
  }

  return { syncedProfiles: profiles.length, archiveChanges: changes };
}
