#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de l'application web (PWA) autonome pour les Internes du Service de Radiologie B
Hôpital Cochin (AP-HP) — Semestre Hiver 2026–2027 (Pr A. Feydy)
Répertoire : /Users/thomaslefevre/Documents/Agendainterventionnel/agenda-internes/
Aucune donnée patient n'est incluse ni autorisée dans cette application.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import stat

from build_internes_data import (
    BASE_DIR,
    CLOUD_PROP_KEY,
    DATA_FILE,
    ICON_FILE,
    INDEX_FILE,
    INTERNES_SHEET_ID,
    LAUNCHER_FILE,
    MANIFEST_FILE,
    SW_FILE,
    WEBHOOK_URL,
    assert_zero_patient_data,
    build_full_dataset,
    sync_initial_state_to_cloud,
)


def js_json(obj) -> str:
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="Internes Radio B" />
  <meta name="application-name" content="Internes Radio B — Cochin" />
  <meta name="theme-color" content="#0B1120" />
  <link rel="manifest" href="manifest.json?v=1" />
  <link rel="icon" type="image/svg+xml" href="icon.svg?v=1" />
  <link rel="apple-touch-icon" href="icon.svg?v=1" />
  <title>Cochin Radio B — Espace Internes (Hiver 2026–2027)</title>
  <style>
    :root {
      --bg: #0B1120;
      --bg-card: #131C31;
      --bg-elevated: #1E293B;
      --border: rgba(148, 163, 184, 0.16);
      --text: #F8FAFC;
      --text-muted: #94A3B8;
      --primary: #38BDF8;
      --primary-dark: #0284C7;
      --tdm: #F59E0B;
      --irm: #A855F7;
      --echo: #14B8A6;
      --gestes: #F43F5E;
      --cs: #3B82F6;
      --off: #64748B;
      --vac: #10B981;
      --rg: #EF4444;
      --success: #22C55E;
      --warning: #F59E0B;
      --danger: #EF4444;
      --safe-top: env(safe-area-inset-top, 0px);
      --safe-bottom: env(safe-area-inset-bottom, 0px);
    }

    * {
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }

    html, body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.45;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Sticky Top Header */
    .app-header {
      position: sticky;
      top: 0;
      z-index: 100;
      padding: calc(var(--safe-top) + 10px) 14px 10px;
      background: rgba(11, 17, 32, 0.94);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border-bottom: 1px solid var(--border);
    }

    .header-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      max-width: 1180px;
      margin: 0 auto;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .brand-logo {
      width: 38px;
      height: 38px;
      border-radius: 11px;
      background: linear-gradient(135deg, #38BDF8 0%, #6366F1 55%, #A855F7 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
      color: #fff;
      box-shadow: 0 4px 14px rgba(56, 189, 248, 0.3);
      flex-shrink: 0;
    }

    .brand-title {
      font-size: 15px;
      font-weight: 800;
      letter-spacing: -0.02em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .brand-sub {
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .privacy-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 7px;
      border-radius: 99px;
      font-size: 10px;
      font-weight: 700;
      background: rgba(16, 185, 129, 0.14);
      color: #34D399;
      border: 1px solid rgba(16, 185, 129, 0.32);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }

    .btn-icon {
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--text);
      padding: 7px 11px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
    }

    .btn-icon:hover {
      background: var(--bg-elevated);
      border-color: rgba(56, 189, 248, 0.4);
    }

    .btn-primary {
      background: linear-gradient(135deg, #0284C7, #2563EB);
      border-color: rgba(56, 189, 248, 0.4);
      color: #fff;
    }

    /* Personal Space Selector Bar (Internes Pills) */
    .interne-selector-wrap {
      max-width: 1180px;
      margin: 10px auto 0;
      display: flex;
      align-items: center;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 4px;
      scrollbar-width: none;
    }
    .interne-selector-wrap::-webkit-scrollbar { display: none; }

    .interne-chip {
      border: 1px solid var(--border);
      background: rgba(30, 41, 59, 0.65);
      color: var(--text-muted);
      padding: 6px 11px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }

    .interne-chip .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .interne-chip.active {
      background: rgba(56, 189, 248, 0.18);
      color: #fff;
      border-color: var(--primary);
      box-shadow: 0 2px 10px rgba(56, 189, 248, 0.2);
    }

    /* Main Layout */
    .container {
      max-width: 1180px;
      margin: 0 auto;
      padding: 12px 14px calc(var(--safe-bottom) + 90px);
    }

    /* Personal Space Banner + KPIs */
    .personal-banner {
      background: linear-gradient(135deg, rgba(19, 28, 49, 0.96), rgba(30, 41, 59, 0.92));
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      margin-bottom: 14px;
      box-shadow: 0 8px 26px rgba(0, 0, 0, 0.26);
    }

    .personal-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .personal-identity {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .avatar-circle {
      width: 44px;
      height: 44px;
      border-radius: 13px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 16px;
      color: #fff;
      flex-shrink: 0;
    }

    .personal-name {
      font-size: 16px;
      font-weight: 800;
    }

    .personal-meta {
      font-size: 12px;
      color: var(--text-muted);
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
      gap: 8px;
    }

    .kpi-card {
      background: rgba(11, 17, 32, 0.65);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 9px 11px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .kpi-val {
      font-size: 18px;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .kpi-lbl {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 600;
    }

    /* Navigation Tabs */
    .main-tabs {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 6px;
      background: var(--bg-card);
      padding: 5px;
      border-radius: 14px;
      border: 1px solid var(--border);
      margin-bottom: 14px;
    }

    .tab-btn {
      border: none;
      background: transparent;
      color: var(--text-muted);
      padding: 9px 6px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.15s ease;
      text-align: center;
    }

    .tab-btn.active {
      background: var(--bg-elevated);
      color: var(--primary);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }

    /* Toolbar for Planning View */
    .planning-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .segmented {
      display: inline-flex;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 3px;
      gap: 3px;
    }

    .seg-btn {
      border: none;
      background: transparent;
      color: var(--text-muted);
      padding: 6px 11px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }

    .seg-btn.active {
      background: var(--primary-dark);
      color: #fff;
    }

    .date-nav {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .date-label {
      font-size: 14px;
      font-weight: 800;
      min-width: 170px;
      text-align: center;
    }

    /* Day Strip (like Chefs App) */
    .day-strip {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 6px;
      margin-bottom: 12px;
      scrollbar-width: none;
    }
    .day-strip::-webkit-scrollbar { display: none; }

    .day-pill {
      min-width: 58px;
      padding: 8px 6px;
      border-radius: 12px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }

    .day-pill.active {
      background: rgba(56, 189, 248, 0.18);
      border-color: var(--primary);
      color: #fff;
    }

    .day-pill .dow {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
    }

    .day-pill.active .dow { color: var(--primary); }

    .day-pill .dom {
      font-size: 15px;
      font-weight: 800;
    }

    .day-pill .dots {
      display: flex;
      gap: 3px;
      margin-top: 2px;
    }

    .day-pill .mini-dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
    }

    /* Post Badges (Chefs-style pills) */
    .poste-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 9px;
      border-radius: 8px;
      font-size: 11.5px;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .poste-tdm { background: rgba(245, 158, 11, 0.16); color: #FBBF24; border-color: rgba(245, 158, 11, 0.34); }
    .poste-irm { background: rgba(168, 85, 247, 0.16); color: #C084FC; border-color: rgba(168, 85, 247, 0.34); }
    .poste-echo { background: rgba(20, 184, 166, 0.16); color: #2DD4BF; border-color: rgba(20, 184, 166, 0.34); }
    .poste-gestes { background: rgba(244, 63, 94, 0.16); color: #FB7185; border-color: rgba(244, 63, 94, 0.34); }
    .poste-cs { background: rgba(59, 130, 246, 0.16); color: #60A5FA; border-color: rgba(59, 130, 246, 0.34); }
    .poste-off { background: rgba(100, 116, 139, 0.16); color: #94A3B8; border-color: rgba(100, 116, 139, 0.3); }
    .poste-vac { background: rgba(16, 185, 129, 0.18); color: #34D399; border-color: rgba(16, 185, 129, 0.38); }
    .poste-rg { background: rgba(239, 68, 68, 0.18); color: #F87171; border-color: rgba(239, 68, 68, 0.38); }

    /* Cards & Tables */
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 15px;
      padding: 14px;
      margin-bottom: 12px;
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }

    .card-title {
      font-size: 14px;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 7px;
    }

    /* Week Matrix Table (like Planning des Chefs) */
    .week-table-wrap {
      overflow-x: auto;
      border-radius: 12px;
      border: 1px solid var(--border);
    }

    table.planning-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 680px;
      background: var(--bg-card);
    }

    table.planning-table th,
    table.planning-table td {
      border-bottom: 1px solid var(--border);
      border-right: 1px solid var(--border);
      padding: 8px 9px;
      text-align: left;
      vertical-align: top;
      font-size: 12px;
    }

    table.planning-table th {
      background: rgba(30, 41, 59, 0.85);
      color: var(--text-muted);
      font-weight: 800;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    table.planning-table tr.period-divider td {
      background: rgba(56, 189, 248, 0.09);
      color: var(--primary);
      font-weight: 800;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 6px 10px;
    }

    .interne-badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 3px 8px;
      border-radius: 7px;
      font-size: 11.5px;
      font-weight: 700;
      margin: 2px 3px 2px 0;
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid rgba(148, 163, 184, 0.25);
      cursor: pointer;
    }

    .interne-badge.highlight-me {
      box-shadow: 0 0 0 2px var(--primary);
      background: rgba(56, 189, 248, 0.22);
      color: #fff;
    }

    /* Month Grid */
    .month-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
    }

    @media (max-width: 760px) {
      .month-grid {
        grid-template-columns: repeat(2, 1fr);
      }
      .main-tabs {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .month-cell {
      background: rgba(19, 28, 49, 0.9);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 9px;
      min-height: 110px;
      display: flex;
      flex-direction: column;
      gap: 5px;
      cursor: pointer;
      transition: border-color 0.15s ease;
    }

    .month-cell:hover {
      border-color: var(--primary);
    }

    .month-cell.today {
      border-color: var(--primary);
      box-shadow: 0 0 0 1px var(--primary);
    }

    /* Balance Table */
    .balance-bar-bg {
      width: 100%;
      height: 7px;
      background: rgba(148, 163, 184, 0.15);
      border-radius: 99px;
      overflow: hidden;
    }

    .balance-bar-fill {
      height: 100%;
      border-radius: 99px;
    }

    /* Modals */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(2, 6, 23, 0.78);
      backdrop-filter: blur(6px);
      z-index: 300;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }

    .modal-backdrop.open {
      display: flex;
    }

    .modal-box {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 18px;
      width: 100%;
      max-width: 520px;
      max-height: 90vh;
      overflow-y: auto;
      padding: 18px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    }

    .form-group {
      margin-bottom: 12px;
    }

    .form-group label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 5px;
    }

    .form-control {
      width: 100%;
      padding: 9px 11px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
      font-family: inherit;
    }

    .alert-box {
      padding: 10px 12px;
      border-radius: 11px;
      font-size: 12px;
      margin-bottom: 12px;
      border: 1px solid transparent;
    }

    .alert-info {
      background: rgba(56, 189, 248, 0.12);
      border-color: rgba(56, 189, 248, 0.3);
      color: #BAE6FD;
    }

    .alert-warn {
      background: rgba(245, 158, 11, 0.14);
      border-color: rgba(245, 158, 11, 0.35);
      color: #FDE68A;
    }

    .toast {
      position: fixed;
      bottom: calc(var(--safe-bottom) + 20px);
      left: 50%;
      transform: translateX(-50%);
      background: #10B981;
      color: #052E16;
      font-weight: 800;
      font-size: 12.5px;
      padding: 9px 16px;
      border-radius: 999px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
      z-index: 400;
      display: none;
    }
  </style>
</head>
<body>

  <header class="app-header">
    <div class="header-top">
      <div class="brand">
        <div class="brand-logo">RI·B</div>
        <div>
          <div class="brand-title">Cochin Radio B — Espace Internes & Chefs</div>
          <div class="brand-sub">
            <span>Semestre Hiver 2026–2027 (Pr A. Feydy)</span>
            <span class="privacy-pill">🛡️ Zéro donnée patient</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-icon" onclick="syncWithCloud(true)" id="syncBtn" title="Synchroniser avec Google Sheet Internes & Cloud">
          🔄 <span id="syncStatusText">Sync Cloud</span>
        </button>
        <a class="btn-icon" href="https://docs.google.com/spreadsheets/d/10sPMOg9GPXqsSItnUfuYn2Ke0im34p5EEyKk5A0hEF8/edit" target="_blank" rel="noopener">
          📊 Sheet Hiver 26
        </a>
      </div>
    </div>

    <!-- Sélecteur d'espace personnel par interne -->
    <div class="interne-selector-wrap" id="interneSelectorBar"></div>
  </header>

  <main class="container">
    <!-- Bandeau Espace Personnel / Résumé d'équité -->
    <section class="personal-banner" id="personalBanner"></section>

    <!-- Onglets Principaux -->
    <nav class="main-tabs">
      <button class="tab-btn active" data-tab="planning" onclick="switchTab('planning')">
        📅 Planning & Vacations
      </button>
      <button class="tab-btn" data-tab="vacances" onclick="switchTab('vacances')">
        🌴 Vacances & RG
      </button>
      <button class="tab-btn" data-tab="presentations" onclick="switchTab('presentations')">
        🎓 Mardi (Cas) & Vendredi (Biblio)
      </button>
      <button class="tab-btn" data-tab="reunions" onclick="switchTab('reunions')">
        🏛️ Réunions Service (Anne-Marie)
      </button>
      <button class="tab-btn" data-tab="annuaire" onclick="switchTab('annuaire')">
        ☎️ Annuaire Cochin
      </button>
    </nav>

    <!-- Contenu dynamique de l'onglet actif -->
    <div id="tabContent"></div>
  </main>

  <!-- Modal : Poser des Vacances / Congés / RG -->
  <div class="modal-backdrop" id="modalAbsence">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">🌴 Poser des Vacances / Congés / RG</div>
        <button class="btn-icon" onclick="closeModal('modalAbsence')">✕</button>
      </div>
      <div class="alert-box alert-info">
        <strong>Règles du service (Dr F. Mihoubi Bouvier & Anne-Marie Fortin) :</strong><br/>
        • Maximum <strong>2 internes absents</strong> en même temps.<br/>
        • Pour les jours isolés (CF, récupération), <strong>éviter les mardis et vendredis</strong> (staffs & présentations).
      </div>
      <div class="form-group">
        <label>Interne concerné</label>
        <select id="absInterneSelect" class="form-control"></select>
      </div>
      <div class="form-group">
        <label>Type d'absence</label>
        <select id="absTypeSelect" class="form-control">
          <option value="CA 1">CA 1 — Congés Annuels (1er choix)</option>
          <option value="CA 2">CA 2 — Congés Annuels (2e choix)</option>
          <option value="CF">CF — Congé Formation / Congrès</option>
          <option value="Repos de garde">RG — Repos de garde</option>
          <option value="Autre">Autre absence</option>
        </select>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Date de début</label>
          <input type="date" id="absStartDate" class="form-control" min="2026-11-02" max="2027-05-02" />
        </div>
        <div class="form-group">
          <label>Date de fin (incluse)</label>
          <input type="date" id="absEndDate" class="form-control" min="2026-11-02" max="2027-05-02" />
        </div>
      </div>
      <div class="form-group">
        <label>Commentaire (optionnel — sans aucune donnée patient)</label>
        <input type="text" id="absComment" class="form-control" placeholder="Ex: Semaine ski, JFR, Garde du dimanche..." />
      </div>
      <div id="absRuleWarning" class="alert-box alert-warn" style="display:none;"></div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:14px;">
        <button class="btn-icon" onclick="closeModal('modalAbsence')">Annuler</button>
        <button class="btn-icon btn-primary" onclick="saveAbsenceForm()">Enregistrer & Synchroniser</button>
      </div>
    </div>
  </div>

  <!-- Modal : S'inscrire / Modifier une présentation Mardi (Cas) ou Vendredi (Biblio) -->
  <div class="modal-backdrop" id="modalPresentation">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title" id="presModalTitle">🎓 Présentation Mardi / Vendredi</div>
        <button class="btn-icon" onclick="closeModal('modalPresentation')">✕</button>
      </div>
      <div class="alert-box alert-info">
        🛡️ <strong>Rappel confidentialité :</strong> Indiquez uniquement la pathologie ou le titre de l'article scientifique. Ne mentionnez jamais de nom de patient ni d'IPP.
      </div>
      <input type="hidden" id="presIdInput" />
      <div class="form-group">
        <label>Date & Créneau</label>
        <input type="text" id="presDateDisplay" class="form-control" readonly />
      </div>
      <div class="form-group">
        <label>Interne présentateur</label>
        <select id="presInterneSelect" class="form-control"></select>
      </div>
      <div class="form-group">
        <label>Titre du Cas Clinique (Mardi) ou de l'Article Biblio / DOI (Vendredi)</label>
        <textarea id="presSujetInput" class="form-control" rows="3" placeholder="Ex: Neuropathie de Baxter en IRM / Article European Radiology 2026 sur les tumeurs cartilagineuses..."></textarea>
      </div>
      <div class="form-group">
        <label>Cours du Chef associé / Thème de la semaine</label>
        <input type="text" id="presChefInput" class="form-control" placeholder="Ex: Dr T. Lefèvre — Analyse d'une PTH" />
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:14px;">
        <button class="btn-icon" onclick="closeModal('modalPresentation')">Annuler</button>
        <button class="btn-icon btn-primary" onclick="savePresentationForm()">Enregistrer & Sync Sheet</button>
      </div>
    </div>
  </div>

  <!-- Modal : Modifier / Échanger une vacation d'interne -->
  <div class="modal-backdrop" id="modalVacationEdit">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">🔄 Modifier / Échanger une vacation</div>
        <button class="btn-icon" onclick="closeModal('modalVacationEdit')">✕</button>
      </div>
      <input type="hidden" id="vacEditDate" />
      <input type="hidden" id="vacEditInterneId" />
      <div class="form-group">
        <label>Interne & Jour</label>
        <input type="text" id="vacEditHeader" class="form-control" readonly />
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Poste du Matin (AM)</label>
          <select id="vacEditAm" class="form-control"></select>
        </div>
        <div class="form-group">
          <label>Poste de l'Après-midi (PM)</label>
          <select id="vacEditPm" class="form-control"></select>
        </div>
      </div>
      <div class="form-group">
        <label>Note (ex: Échange avec Noé, Garde de nuit Cochin...)</label>
        <input type="text" id="vacEditNote" class="form-control" placeholder="Note interne (sans donnée patient)" />
      </div>
      <div style="display:flex; justify-content:space-between; gap:8px; margin-top:14px;">
        <button class="btn-icon" onclick="resetSingleVacation()">Réinitialiser trame</button>
        <div style="display:flex; gap:8px;">
          <button class="btn-icon" onclick="closeModal('modalVacationEdit')">Annuler</button>
          <button class="btn-icon btn-primary" onclick="saveSingleVacation()">Valider</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal : Ajouter une Réunion / Info Service (Anne-Marie / Chefs) -->
  <div class="modal-backdrop" id="modalMeeting">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">🏛️ Ajouter une Réunion / Info du Service</div>
        <button class="btn-icon" onclick="closeModal('modalMeeting')">✕</button>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Date</label>
          <input type="date" id="meetDate" class="form-control" value="2026-11-04" />
        </div>
        <div class="form-group">
          <label>Horaire</label>
          <input type="text" id="meetHoraire" class="form-control" placeholder="Ex: 17h00 – 18h00" />
        </div>
      </div>
      <div class="form-group">
        <label>Intitulé de la réunion</label>
        <input type="text" id="meetTitle" class="form-control" placeholder="Ex: Réunion plénière Internes / Chefs, Confrontation Anapath..." />
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Organisateur / Envoyé par</label>
          <input type="text" id="meetSender" class="form-control" value="Anne-Marie FORTIN" />
        </div>
        <div class="form-group">
          <label>Lieu / Salle</label>
          <input type="text" id="meetLocation" class="form-control" value="Salle de Staff Radio B (Albarran -1)" />
        </div>
      </div>
      <div class="form-group">
        <label>Détails / Ordre du jour (sans donnée patient)</label>
        <textarea id="meetDesc" class="form-control" rows="3"></textarea>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:14px;">
        <button class="btn-icon" onclick="closeModal('modalMeeting')">Annuler</button>
        <button class="btn-icon btn-primary" onclick="saveMeetingForm()">Ajouter au calendrier</button>
      </div>
    </div>
  </div>

  <!-- Modal : Ajouter un numéro dans l'Annuaire Cochin -->
  <div class="modal-backdrop" id="modalPhoneContact">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">☎️ Ajouter un Poste / Numéro Cochin</div>
        <button class="btn-icon" onclick="closeModal('modalPhoneContact')">✕</button>
      </div>
      <div class="form-group">
        <label>Catégorie</label>
        <select id="phoneCatInput" class="form-control">
          <option value="Radiologie B — Secrétariats & Consoles">Radiologie B — Secrétariats & Consoles</option>
          <option value="Radiologie B — Équipe Médicale (Chefs & Seniors)">Radiologie B — Équipe Médicale (Chefs & Seniors)</option>
          <option value="Services Partenaires (Ortho, Rhumato, Anesth, Anapath)">Services Partenaires (Ortho, Rhumato, Anesth, Anapath)</option>
          <option value="Laboratoires, Pharmacie & Administration (DAM)">Laboratoires, Pharmacie & Administration (DAM)</option>
        </select>
      </div>
      <div class="form-group">
        <label>Nom du contact / Secteur / Console</label>
        <input type="text" id="phoneNameInput" class="form-control" placeholder="Ex: Console IRM 3T, Salle Allura, Garde Ortho..." />
      </div>
      <div class="form-group">
        <label>Fonction / Détail</label>
        <input type="text" id="phoneRoleInput" class="form-control" placeholder="Ex: Manipulateurs IRM / Poste de garde..." />
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Poste interne / DECT (5 chiffres)</label>
          <input type="text" id="phonePosteInput" class="form-control" placeholder="Ex: 12483 ou DECT 12504" />
        </div>
        <div class="form-group">
          <label>Ligne directe (01 58 41 XX XX)</label>
          <input type="text" id="phoneNumInput" class="form-control" placeholder="Ex: 01 58 41 24 83" />
        </div>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Bâtiment / Localisation</label>
          <input type="text" id="phoneBldgInput" class="form-control" placeholder="Ex: Bâtiment Ollier -1" />
        </div>
        <div class="form-group">
          <label>Fax (optionnel)</label>
          <input type="text" id="phoneFaxInput" class="form-control" placeholder="Ex: 01 58 41 24 55" />
        </div>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:14px;">
        <button class="btn-icon" onclick="closeModal('modalPhoneContact')">Annuler</button>
        <button class="btn-icon btn-primary" onclick="savePhoneContactForm()">Enregistrer dans l'annuaire</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toastBox">Enregistré !</div>

  <script>
    const INITIAL_DATA = __INITIAL_DATA_JSON__;
    const WEBHOOK_URL = __WEBHOOK_URL_JSON__;
    const INTERNES_SHEET_ID = __INTERNES_SHEET_ID_JSON__;
    const CLOUD_PROP_KEY = __CLOUD_PROP_KEY_JSON__;
    const LOCAL_STORAGE_KEY = "cochin_internes_app_state_v1";
    const SELECTED_INTERNE_KEY = "cochin_internes_selected_id_v1";

    let STATE = loadInitialState();
    let currentTab = "planning";
    let selectedInterneId = localStorage.getItem(SELECTED_INTERNE_KEY) || "gabriel"; // 'all' ou id d'un interne
    let planningScope = "internes"; // 'internes' | 'perso' | 'chefs'
    let planningMode = "week";      // 'day' | 'week' | 'month'
    let currentDateIso = "2026-11-02";
    let presFilter = "all";         // 'all' | 'cas_mardi' | 'biblio_vendredi' | 'mine'
    let annuaireSearch = "";
    let annuaireCategory = "all";

    function loadInitialState() {
      const base = JSON.parse(JSON.stringify(INITIAL_DATA));
      try {
        const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (raw) {
          const saved = JSON.parse(raw);
          if (Array.isArray(saved.absences)) base.absences = saved.absences;
          if (saved.customVacations) base.customVacations = saved.customVacations;
          if (Array.isArray(saved.presentations) && saved.presentations.length > 0) base.presentations = saved.presentations;
          if (Array.isArray(saved.meetings) && saved.meetings.length > 0) base.meetings = saved.meetings;
          if (Array.isArray(saved.phoneDirectory) && saved.phoneDirectory.length > 0) {
            const map = {};
            (base.phoneDirectory || []).forEach(c => { map[c.id] = c; });
            saved.phoneDirectory.forEach(c => { if (c && c.id) map[c.id] = c; });
            base.phoneDirectory = Object.values(map);
          }
        }
      } catch (e) {}
      recomputeScheduleInPlace(base);
      return base;
    }

    function saveStateLocal() {
      recomputeScheduleInPlace(STATE);
      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify({
          updatedAt: new Date().toISOString(),
          absences: STATE.absences,
          customVacations: STATE.customVacations || {},
          presentations: STATE.presentations,
          meetings: STATE.meetings,
          phoneDirectory: STATE.phoneDirectory || []
        }));
      } catch (e) {}
    }

    function showToast(msg) {
      const el = document.getElementById("toastBox");
      el.textContent = msg;
      el.style.display = "block";
      clearTimeout(window.__toastTimer);
      window.__toastTimer = setTimeout(() => { el.style.display = "none"; }, 2800);
    }

    function getInterneById(iid) {
      return STATE.internes.find(x => x.id === iid) || STATE.internes[0];
    }

    function getPosteClass(poste) {
      const p = String(poste || "").toUpperCase();
      if (p.includes("VACANCES") || p.includes("CA") || p.includes("CF")) return "poste-vac";
      if (p === "RG" || p.includes("REPOS") || p.includes("GARDE") || p.includes("FÉRIÉ")) return "poste-rg";
      if (p.includes("LIBRE")) return "poste-off";
      if (p.includes("IRM")) return "poste-irm";
      if (p.includes("ECHO") || p.includes("ÉCHO")) return "poste-echo";
      if (p.includes("GESTES") || p.includes("ACHARD") || p.includes("ALLURA")) return "poste-gestes";
      if (p.includes("LECTURE") || p.includes("CS") || p.includes("CONSULT")) return "poste-cs";
      return "poste-tdm";
    }

    // Recalcule dynamiquement les vacations (absences + modifications manuelles)
    function recomputeScheduleInPlace(st) {
      const baseSched = INITIAL_DATA.schedule;
      const absLookup = {};
      (st.absences || []).forEach(a => {
        if (a && a.date && a.interneId) absLookup[a.date + "__" + a.interneId] = a.type || "CA 1";
      });
      const custom = st.customVacations || {};

      Object.keys(baseSched).forEach(iso => {
        const dayObj = JSON.parse(JSON.stringify(baseSched[iso]));
        if (!dayObj.holiday && dayObj.byInterne) {
          dayObj.am = [];
          dayObj.pm = [];
          Object.keys(dayObj.byInterne).forEach(iid => {
            const intObj = st.internes.find(x => x.id === iid);
            const cKey = iso + "__" + iid;
            let am = dayObj.byInterne[iid].am;
            let pm = dayObj.byInterne[iid].pm;
            let note = "";

            if (custom[cKey]) {
              if (custom[cKey].am) am = custom[cKey].am;
              if (custom[cKey].pm) pm = custom[cKey].pm;
              if (custom[cKey].note) note = custom[cKey].note;
            }

            if (absLookup[cKey]) {
              const at = absLookup[cKey];
              const badge = (at.toLowerCase().includes("garde") || at.toUpperCase() === "RG") ? "RG" : "VACANCES";
              am = badge;
              pm = badge;
              note = at;
            }

            dayObj.byInterne[iid] = { am, pm, note };
            dayObj.am.push({ poste: am, interneId: iid, interne: intObj ? intObj.shortName : iid });
            dayObj.pm.push({ poste: pm, interneId: iid, interne: intObj ? intObj.shortName : iid });
          });
        }
        st.schedule[iso] = dayObj;
      });
    }

    // Calcul des statistiques et de l'équité des vacations pour chaque interne
    function computeStatsByInterne() {
      const stats = {};
      STATE.internes.forEach(i => {
        stats[i.id] = {
          activeHalfDays: 0,
          freeHalfDays: 0,
          vacHalfDays: 0,
          rgHalfDays: 0,
          casMardi: 0,
          biblioVendredi: 0,
          byModality: { TDM: 0, IRM: 0, ECHO: 0, RI_GESTES: 0, LECTURE_CS: 0 }
        };
      });

      Object.keys(STATE.schedule).forEach(iso => {
        const d = STATE.schedule[iso];
        if (!d || d.holiday || !d.byInterne) return;
        Object.keys(d.byInterne).forEach(iid => {
          if (!stats[iid]) return;
          const slots = [d.byInterne[iid].am, d.byInterne[iid].pm];
          slots.forEach(p => {
            const up = String(p || "").toUpperCase();
            if (up.includes("LIBRE")) {
              stats[iid].freeHalfDays++;
            } else if (up === "VACANCES") {
              stats[iid].vacHalfDays++;
            } else if (up === "RG") {
              stats[iid].rgHalfDays++;
            } else if (up !== "FÉRIÉ") {
              stats[iid].activeHalfDays++;
              if (up.includes("IRM")) stats[iid].byModality.IRM++;
              else if (up.includes("ECHO")) stats[iid].byModality.ECHO++;
              else if (up.includes("GESTES") || up.includes("ACHARD") || up.includes("ALLURA")) stats[iid].byModality.RI_GESTES++;
              else if (up.includes("LECTURE") || up.includes("CS")) stats[iid].byModality.LECTURE_CS++;
              else stats[iid].byModality.TDM++;
            }
          });
        });
      });

      (STATE.presentations || []).forEach(pr => {
        if (pr.interneId && stats[pr.interneId]) {
          if (pr.type === "cas_mardi") stats[pr.interneId].casMardi++;
          if (pr.type === "biblio_vendredi") stats[pr.interneId].biblioVendredi++;
        }
      });

      return stats;
    }

    function formatDateFr(iso, withYear = false) {
      if (!iso) return "";
      const [y, m, d] = iso.split("-").map(Number);
      const dt = new Date(y, m - 1, d);
      const days = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
      const months = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
      return `${days[dt.getDay()]} ${d} ${months[m - 1]}${withYear ? " " + y : ""}`;
    }

    function getMondayOfWeek(iso) {
      const [y, m, d] = iso.split("-").map(Number);
      const dt = new Date(y, m - 1, d);
      const day = dt.getDay();
      const diff = (day === 0 ? -6 : 1 - day);
      dt.setDate(dt.getDate() + diff);
      return dt.toISOString().slice(0, 10);
    }

    function addDaysIso(iso, delta) {
      const [y, m, d] = iso.split("-").map(Number);
      const dt = new Date(y, m - 1, d);
      dt.setDate(dt.getDate() + delta);
      const yy = dt.getFullYear();
      const mm = String(dt.getMonth() + 1).padStart(2, "0");
      const dd = String(dt.getDate()).padStart(2, "0");
      return `${yy}-${mm}-${dd}`;
    }

    // Rendu de la barre de sélection d'espace (Internes vs Chefs & Seniors)
    function isChefId(id) {
      return String(id || "").startsWith("chef_");
    }

    function getChefById(cid) {
      const list = STATE.chefs || [];
      return list.find(c => c.id === cid) || list[0] || {
        id: "chef_tl", code: "TL", prenom: "Thomas", nom: "LEFÈVRE",
        fullName: "Dr Thomas LEFÈVRE", shortName: "Dr T. Lefèvre (TL)",
        initials: "TL", color: "#38BDF8", role: "Chef de Clinique / Assistant"
      };
    }

    function doesDocMatchChef(docStr, chef) {
      if (!docStr || !chef) return false;
      const up = String(docStr).toUpperCase();
      const code = String(chef.code || "").toUpperCase();
      const nom = String(chef.nom || "").toUpperCase();
      const re = new RegExp("(^|[^A-Z])" + code + "([^A-Z]|$)");
      if (re.test(up)) return true;
      if (nom && up.includes(nom)) return true;
      if (code === "MIHOUBI" && (up.includes("MD") || up.includes("MIHOUBI"))) return true;
      return false;
    }

    function getChefSlotsForDate(iso, chef) {
      const ch = (STATE.chefsPlanning && STATE.chefsPlanning[iso]) ? STATE.chefsPlanning[iso] : { am: [], pm: [] };
      const am = (ch.am || []).filter(x => doesDocMatchChef(x.doc, chef)).map(x => x.poste);
      const pm = (ch.pm || []).filter(x => doesDocMatchChef(x.doc, chef)).map(x => x.poste);
      const g = (STATE.chefsGardes && STATE.chefsGardes[iso]) ? STATE.chefsGardes[iso] : null;
      let isGarde = false;
      if (g && Array.isArray(g.noms)) {
        const matches = chef.gardeMatch || [chef.nom];
        isGarde = g.noms.some(n => matches.some(m => String(n).toUpperCase().includes(String(m).toUpperCase())));
      }
      return { am, pm, isGarde, gardeNature: g ? g.nature : "" };
    }

    function computeChefStats(chef) {
      let totalHalfDays = 0;
      let gardesCount = 0;
      let coursMardiCount = 0;
      const byMod = { TDM: 0, IRM: 0, ECHO: 0, RI_GESTES: 0, CS_STAFF: 0 };

      Object.keys(STATE.chefsPlanning || {}).forEach(iso => {
        const sl = getChefSlotsForDate(iso, chef);
        if (sl.am.length > 0) {
          totalHalfDays++;
          const joined = sl.am.join(" ").toUpperCase();
          if (joined.includes("IRM")) byMod.IRM++;
          else if (joined.includes("ECHO")) byMod.ECHO++;
          else if (joined.includes("GESTES") || joined.includes("ACHARD") || joined.includes("ALLURA")) byMod.RI_GESTES++;
          else if (joined.includes("CONSULT") || joined.includes("UCSA") || joined.includes("STAFF")) byMod.CS_STAFF++;
          else byMod.TDM++;
        }
        if (sl.pm.length > 0) {
          totalHalfDays++;
          const joined = sl.pm.join(" ").toUpperCase();
          if (joined.includes("IRM")) byMod.IRM++;
          else if (joined.includes("ECHO")) byMod.ECHO++;
          else if (joined.includes("GESTES") || joined.includes("ACHARD") || joined.includes("ALLURA")) byMod.RI_GESTES++;
          else if (joined.includes("CONSULT") || joined.includes("UCSA") || joined.includes("STAFF")) byMod.CS_STAFF++;
          else byMod.TDM++;
        }
      });

      Object.keys(STATE.chefsGardes || {}).forEach(iso => {
        const g = STATE.chefsGardes[iso];
        if (g && Array.isArray(g.noms)) {
          const matches = chef.gardeMatch || [chef.nom];
          if (g.noms.some(n => matches.some(m => String(n).toUpperCase().includes(String(m).toUpperCase())))) {
            gardesCount++;
          }
        }
      });

      (STATE.presentations || []).forEach(p => {
        if (p.chefIntervenant && String(p.chefIntervenant).toUpperCase().includes(String(chef.nom).toUpperCase())) {
          coursMardiCount++;
        }
      });

      return { totalHalfDays, gardesCount, coursMardiCount, byMod };
    }

    function renderInterneSelector() {
      const bar = document.getElementById("interneSelectorBar");
      const inChefSpace = (selectedInterneId === "all_chefs" || isChefId(selectedInterneId));
      let html = `
        <div style="display:flex; flex-direction:column; gap:6px; width:100%;">
          <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">
            <div style="display:inline-flex; background:rgba(15,23,42,0.85); border:1px solid var(--border); border-radius:999px; padding:3px; gap:4px;">
              <button class="interne-chip ${!inChefSpace ? 'active' : ''}" style="border:none; padding:5px 12px;" onclick="switchRoleSpace('internes')">
                🎓 Espace Internes (${STATE.internes.length})
              </button>
              <button class="interne-chip ${inChefSpace ? 'active' : ''}" style="border:none; padding:5px 12px;" onclick="switchRoleSpace('chefs')">
                🩺 Espace Chefs & Seniors (${(STATE.chefs || []).length})
              </button>
            </div>
            <div style="font-size:11px; color:var(--text-muted);">
              🔄 Accès croisé permanent : <strong>Planning Internes ⇄ Planning Chefs</strong>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:6px; overflow-x:auto; padding-bottom:2px; scrollbar-width:none;">
      `;

      if (!inChefSpace) {
        html += `
          <button class="interne-chip ${selectedInterneId === 'all' ? 'active' : ''}" onclick="selectInterne('all')">
            👥 Tous les Internes (6)
          </button>
        `;
        STATE.internes.forEach(i => {
          const active = (selectedInterneId === i.id) ? "active" : "";
          html += `
            <button class="interne-chip ${active}" onclick="selectInterne('${i.id}')">
              <span class="dot" style="background:${i.color}"></span>
              <span>${i.shortName} ${i.nom}</span>
            </button>
          `;
        });
      } else {
        html += `
          <button class="interne-chip ${selectedInterneId === 'all_chefs' ? 'active' : ''}" onclick="selectInterne('all_chefs')">
            🩺 Tous les Chefs & Seniors
          </button>
        `;
        (STATE.chefs || []).forEach(c => {
          const active = (selectedInterneId === c.id) ? "active" : "";
          html += `
            <button class="interne-chip ${active}" onclick="selectInterne('${c.id}')">
              <span class="dot" style="background:${c.color}"></span>
              <span>${c.shortName}</span>
            </button>
          `;
        });
      }

      html += `</div></div>`;
      bar.innerHTML = html;
    }

    function switchRoleSpace(space) {
      if (space === "chefs") {
        if (!isChefId(selectedInterneId) && selectedInterneId !== "all_chefs") {
          selectedInterneId = "chef_tl";
        }
        planningScope = "perso";
      } else {
        if (isChefId(selectedInterneId) || selectedInterneId === "all_chefs") {
          selectedInterneId = "gabriel";
        }
        if (planningScope === "chefs") planningScope = "internes";
      }
      localStorage.setItem(SELECTED_INTERNE_KEY, selectedInterneId);
      renderAll();
    }

    function selectInterne(iid) {
      selectedInterneId = iid;
      if (iid === "all_chefs") {
        planningScope = "chefs";
      } else if (isChefId(iid)) {
        if (planningScope === "internes") planningScope = "perso";
      } else if (iid === "all") {
        if (planningScope === "perso") planningScope = "internes";
      }
      localStorage.setItem(SELECTED_INTERNE_KEY, iid);
      renderAll();
    }

    // Rendu du bandeau Espace Personnel & KPIs (Internes ET Chefs)
    function renderPersonalBanner() {
      const el = document.getElementById("personalBanner");

      // CAS 1 : ESPACE TOUS LES CHEFS & SENIORS
      if (selectedInterneId === "all_chefs") {
        el.innerHTML = `
          <div class="personal-top">
            <div class="personal-identity">
              <div class="avatar-circle" style="background:linear-gradient(135deg,#0284C7,#10B981)">🩺</div>
              <div>
                <div class="personal-name">Espace Chefs de Clinique, Assistants & Seniors — Radiologie B</div>
                <div class="personal-meta">Planning officiel des Chefs (Anne-Marie Fortin), Gardes Seniors, Cours du Mardi & Accès direct au Planning des Internes</div>
              </div>
            </div>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              <button class="btn-icon ${planningScope === 'chefs' ? 'btn-primary' : ''}" onclick="setPlanningScope('chefs')">🩺 Grille des Chefs</button>
              <button class="btn-icon ${planningScope === 'internes' ? 'btn-primary' : ''}" onclick="setPlanningScope('internes')">👥 Voir Planning Internes</button>
              <button class="btn-icon ${planningScope === 'combined' ? 'btn-primary' : ''}" onclick="setPlanningScope('combined')">🔄 Vue Croisée Chefs + Internes</button>
            </div>
          </div>
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-val" style="color:#38BDF8">${(STATE.chefs || []).length} Seniors</div>
              <div class="kpi-lbl">Chefs de Clinique, Assistants & PH/PU-PH</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#14B8A6">6 Internes DES</div>
              <div class="kpi-lbl">Gabriel, Noé, Marwane, Milan, Nathanaël, Oussama</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#A855F7">${STATE.presentations.filter(p => p.type === 'cas_mardi').length} Mardis</div>
              <div class="kpi-lbl">Cours des Chefs + Cas cliniques</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#F59E0B">${STATE.absences.length / 1} demi-j. / j.</div>
              <div class="kpi-lbl">Congés & RG internes suivis en direct</div>
            </div>
          </div>
        `;
        return;
      }

      // CAS 2 : ESPACE PERSONNEL D'UN CHEF (ex: Dr Thomas Lefèvre, Dr H. Monnier, Dr M. Hamadouche, Dr S. Lusi, Dr Y. Allel, Dr M-P. Talabard...)
      if (isChefId(selectedInterneId)) {
        const chef = getChefById(selectedInterneId);
        const cStats = computeChefStats(chef);
        const todaySlots = getChefSlotsForDate(currentDateIso, chef);
        const todayIntSched = STATE.schedule[currentDateIso] || { am: [], pm: [] };
        const todayAmTxt = todaySlots.am.length ? todaySlots.am.join(" + ") : "Hors trame / Libre";
        const todayPmTxt = todaySlots.pm.length ? todaySlots.pm.join(" + ") : "Hors trame / Libre";

        // Trouver quels internes travaillent sur les mêmes secteurs aujourd'hui
        const binomeInternes = [];
        [...todaySlots.am, ...todaySlots.pm].forEach(cPost => {
          const pUp = cPost.toUpperCase();
          [...(todayIntSched.am || []), ...(todayIntSched.pm || [])].forEach(it => {
            const iPost = String(it.poste || "").toUpperCase();
            if (
              (pUp.includes("ACHARD") && iPost.includes("ACHARD")) ||
              (pUp.includes("GESTES") && iPost.includes("GESTES")) ||
              (pUp.includes("SAU") && iPost.includes("SAU")) ||
              (pUp.includes("IRM") && iPost.includes("IRM")) ||
              (pUp.includes("ECHO") && iPost.includes("ECHO")) ||
              (pUp.includes("ALLURA") && iPost.includes("ALLURA"))
            ) {
              const label = `${it.interne} (${it.poste})`;
              if (!binomeInternes.includes(label)) binomeInternes.push(label);
            }
          });
        });

        el.innerHTML = `
          <div class="personal-top">
            <div class="personal-identity">
              <div class="avatar-circle" style="background:${chef.color}">${chef.initials}</div>
              <div>
                <div class="personal-name">Espace Chef — ${chef.fullName}</div>
                <div class="personal-meta">
                  ${chef.role} • ☎️ Poste : <strong>${chef.posteTel || "12483"}</strong> • Aujourd'hui (${formatDateFr(currentDateIso)}) :
                  <span class="poste-pill ${getPosteClass(todayAmTxt)}" style="padding:2px 7px; font-size:11px;">Matin : ${todayAmTxt}</span>
                  <span class="poste-pill ${getPosteClass(todayPmTxt)}" style="padding:2px 7px; font-size:11px;">PM : ${todayPmTxt}</span>
                  ${todaySlots.isGarde ? `<span class="poste-pill poste-rg" style="padding:2px 7px; font-size:11px;">🚨 DE GARDE (${todaySlots.gardeNature})</span>` : ""}
                </div>
                ${binomeInternes.length ? `<div style="font-size:11.5px; color:#38BDF8; margin-top:4px;">🎓 <strong>Internes en binôme sur vos postes ce jour :</strong> ${binomeInternes.join(" • ")}</div>` : ""}
              </div>
            </div>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              <button class="btn-icon ${planningScope === 'perso' ? 'btn-primary' : ''}" onclick="setPlanningScope('perso')">
                👤 Mon Planning Chef (${chef.code})
              </button>
              <button class="btn-icon ${planningScope === 'internes' ? 'btn-primary' : ''}" onclick="setPlanningScope('internes')">
                🎓 Voir Planning Internes
              </button>
              <button class="btn-icon ${planningScope === 'combined' ? 'btn-primary' : ''}" onclick="setPlanningScope('combined')">
                🔄 Vue Croisée Chefs + Internes
              </button>
              ${chef.code === "TL" ? `<a class="btn-icon" href="https://mrthomaslef.github.io/agenda-cochin/" target="_blank" rel="noopener">🔒 Mon App RI Perso (Patients)</a>` : ""}
            </div>
          </div>
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-val" style="color:${chef.color}">${cStats.totalHalfDays} demi-j.</div>
              <div class="kpi-lbl">Vacations Semestre (${chef.code})</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#F59E0B">${cStats.byMod.RI_GESTES} Gestes/Achard • ${cStats.byMod.TDM} TDM</div>
              <div class="kpi-lbl">${cStats.byMod.IRM} IRM • ${cStats.byMod.ECHO} Écho • ${cStats.byMod.CS_STAFF} CS/Staff</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#EF4444">${cStats.gardesCount} Gardes</div>
              <div class="kpi-lbl">Gardes Senior Hiver 2026–2027</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#A855F7">${cStats.coursMardiCount} Cours Mardi</div>
              <div class="kpi-lbl">Enseignement aux internes (12h30)</div>
            </div>
            <div class="kpi-card" style="cursor:pointer;" onclick="setPlanningScope('internes')">
              <div class="kpi-val" style="color:#22C55E">6 Internes ↗</div>
              <div class="kpi-lbl">Accès direct au planning & congés internes</div>
            </div>
          </div>
        `;
        return;
      }

      const statsAll = computeStatsByInterne();

      if (selectedInterneId === "all") {
        // Vue synthèse d'équité de toute la promotion
        const mainCounts = ["gabriel", "noe", "marwane", "milan", "nathanael", "oussama"].map(id => statsAll[id].activeHalfDays);
        const avgVac = Math.round(mainCounts.reduce((a, b) => a + b, 0) / mainCounts.length);
        el.innerHTML = `
          <div class="personal-top">
            <div class="personal-identity">
              <div class="avatar-circle" style="background:linear-gradient(135deg,#38BDF8,#6366F1)">👥</div>
              <div>
                <div class="personal-name">Promotion Internes Radio B — Hiver 2026–2027</div>
                <div class="personal-meta">6 Internes DES (Gabriel, Noé, Marwane, Milan, Nathanaël, Oussama) • Accès direct au Planning des Chefs</div>
              </div>
            </div>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              <button class="btn-icon ${planningScope === 'chefs' ? 'btn-primary' : ''}" onclick="setPlanningScope('chefs')">🩺 Voir Planning des Chefs</button>
              <button class="btn-icon ${planningScope === 'combined' ? 'btn-primary' : ''}" onclick="setPlanningScope('combined')">🔄 Vue Croisée Chefs + Internes</button>
              <button class="btn-icon btn-primary" onclick="openAbsenceModal()">+ Poser Vacances / RG</button>
              <button class="btn-icon" onclick="switchTab('presentations')">+ S'inscrire Cas / Biblio</button>
            </div>
          </div>
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-val" style="color:#38BDF8">${avgVac} demi-j.</div>
              <div class="kpi-lbl">Vacations actives / interne (équilibré)</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#14B8A6">8 / sem.</div>
              <div class="kpi-lbl">+ 2 demi-journées libres / sem.</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#A855F7">${STATE.presentations.filter(p => p.type === 'cas_mardi').length} Mardis</div>
              <div class="kpi-lbl">Cas cliniques + Cours des chefs</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-val" style="color:#F59E0B">${STATE.presentations.filter(p => p.type === 'biblio_vendredi').length} Vendredis</div>
              <div class="kpi-lbl">Séances de Bibliographie</div>
            </div>
            <div class="kpi-card" style="cursor:pointer;" onclick="setPlanningScope('chefs')">
              <div class="kpi-val" style="color:#22C55E">Planning Chefs ↗</div>
              <div class="kpi-lbl">Voir quel Chef est sur chaque poste</div>
            </div>
          </div>
        `;
        return;
      }

      const me = getInterneById(selectedInterneId);
      const st = statsAll[me.id];
      const daySched = (STATE.schedule[currentDateIso] && STATE.schedule[currentDateIso].byInterne)
        ? STATE.schedule[currentDateIso].byInterne[me.id]
        : null;

      const todayAm = daySched ? daySched.am : "—";
      const todayPm = daySched ? daySched.pm : "—";

      // Trouver le(s) Chef(s) référent(s) sur le poste de l'interne aujourd'hui
      const chToday = (STATE.chefsPlanning && STATE.chefsPlanning[currentDateIso]) ? STATE.chefsPlanning[currentDateIso] : { am: [], pm: [] };
      function findChefForInternePoste(slots, iPoste) {
        const up = String(iPoste || "").toUpperCase();
        if (!up || up.includes("LIBRE") || up === "RG" || up === "VACANCES") return "";
        const m = (slots || []).filter(s => {
          const p = String(s.poste || "").toUpperCase();
          if (up.includes("SAU")) return p.includes("SAU");
          if (up.includes("ACHARD")) return p.includes("ACHARD");
          if (up.includes("GESTES")) return p.includes("GESTES");
          if (up.includes("ALLURA")) return p.includes("ALLURA");
          if (up.includes("IRM 3T")) return p.includes("IRM 3T") || p === "IRM";
          if (up.includes("IRM 1,5T")) return p.includes("IRM 1,5T") || p === "IRM";
          if (up === "IRM") return p.includes("IRM");
          if (up.includes("ECHO")) return p.includes("ECHO");
          if (up.includes("OLLIER DIAG")) return p.includes("OLLIER 3") || p.includes("SAU");
          if (up.includes("LECTURE") || up.includes("CS")) return p.includes("CONSULT");
          return false;
        });
        return m.map(x => x.doc).join(" / ");
      }
      const chefAm = findChefForInternePoste(chToday.am, todayAm);
      const chefPm = findChefForInternePoste(chToday.pm, todayPm);

      el.innerHTML = `
        <div class="personal-top">
          <div class="personal-identity">
            <div class="avatar-circle" style="background:${me.color}">${me.initials}</div>
            <div>
              <div class="personal-name">Espace personnel — ${me.fullName}</div>
              <div class="personal-meta">
                ${me.role} • Aujourd'hui (${formatDateFr(currentDateIso)}) :
                <span class="poste-pill ${getPosteClass(todayAm)}" style="padding:2px 7px; font-size:11px;">Matin : ${todayAm}${chefAm ? ` (Chef: ${chefAm})` : ''}</span>
                <span class="poste-pill ${getPosteClass(todayPm)}" style="padding:2px 7px; font-size:11px;">PM : ${todayPm}${chefPm ? ` (Chef: ${chefPm})` : ''}</span>
              </div>
            </div>
          </div>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <button class="btn-icon ${planningScope === 'perso' ? 'btn-primary' : ''}" onclick="togglePersoOnly()">
              ${planningScope === 'perso' ? '👁️ Voir tout le service' : '🎯 Mon planning seul'}
            </button>
            <button class="btn-icon ${planningScope === 'chefs' ? 'btn-primary' : ''}" onclick="setPlanningScope('chefs')">
              🩺 Planning des Chefs
            </button>
            <button class="btn-icon ${planningScope === 'combined' ? 'btn-primary' : ''}" onclick="setPlanningScope('combined')">
              🔄 Vue Croisée
            </button>
            <button class="btn-icon btn-primary" onclick="openAbsenceModal('${me.id}')">+ Mes Vacances / RG</button>
          </div>
        </div>
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-val" style="color:${me.color}">${st.activeHalfDays}</div>
            <div class="kpi-lbl">Mes vacations actives (Semestre)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color:#F59E0B">${st.byModality.TDM} TDM • ${st.byModality.IRM} IRM</div>
            <div class="kpi-lbl">${st.byModality.ECHO} Écho • ${st.byModality.RI_GESTES} Gestes RI</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color:#94A3B8">${st.freeHalfDays} demi-j.</div>
            <div class="kpi-lbl">1/2 journées libres (2 / sem.)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color:#10B981">${Math.round(st.vacHalfDays / 2)} j. CA/CF</div>
            <div class="kpi-lbl">+ ${Math.round(st.rgHalfDays / 2)} j. Repos de garde</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color:#A855F7">${st.casMardi} Cas • ${st.biblioVendredi} Biblio</div>
            <div class="kpi-lbl">Mes présentations Mardi & Vendredi</div>
          </div>
        </div>
      `;
    }

    function togglePersoOnly() {
      if (planningScope === "perso") {
        planningScope = isChefId(selectedInterneId) ? "chefs" : "internes";
      } else {
        if (selectedInterneId === "all") selectedInterneId = "gabriel";
        if (selectedInterneId === "all_chefs") selectedInterneId = "chef_tl";
        planningScope = "perso";
      }
      switchTab("planning");
    }

    function switchTab(tab) {
      currentTab = tab;
      document.querySelectorAll(".tab-btn").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-tab") === tab);
      });
      renderTabContent();
    }

    function renderAll() {
      renderInterneSelector();
      renderPersonalBanner();
      renderTabContent();
    }

    function renderTabContent() {
      const container = document.getElementById("tabContent");
      if (currentTab === "planning") {
        container.innerHTML = renderPlanningTab();
      } else if (currentTab === "vacances") {
        container.innerHTML = renderVacancesTab();
      } else if (currentTab === "presentations") {
        container.innerHTML = renderPresentationsTab();
      } else if (currentTab === "reunions") {
        container.innerHTML = renderReunionsTab();
      } else if (currentTab === "annuaire") {
        container.innerHTML = renderAnnuaireTab();
      }
    }

    /* =========================================================================
     * ONGLET 1 : PLANNING & VACATIONS (INTERNES ⇄ CHEFS + VUE CROISÉE)
     * ========================================================================= */
    function renderPlanningTab() {
      const monIso = getMondayOfWeek(currentDateIso);
      const friIso = addDaysIso(monIso, 4);

      let headerLabel = "";
      if (planningMode === "day") {
        headerLabel = formatDateFr(currentDateIso, true);
      } else if (planningMode === "week") {
        headerLabel = `Semaine du ${formatDateFr(monIso)} au ${formatDateFr(friIso, true)}`;
      } else {
        const [y, m] = currentDateIso.split("-").map(Number);
        const mNames = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
        headerLabel = `${mNames[m - 1]} ${y}`;
      }

      // Bandeau des jours de la semaine (style Chefs)
      let dayStripHtml = `<div class="day-strip">`;
      for (let offset = 0; offset < 5; offset++) {
        const dIso = addDaysIso(monIso, offset);
        const [yy, mm, dd] = dIso.split("-").map(Number);
        const dNames = ["Lun", "Mar", "Mer", "Jeu", "Ven"];
        const isAct = (dIso === currentDateIso) ? "active" : "";
        const hasMeet = STATE.meetings.some(m => m.date === dIso);
        const hasPres = STATE.presentations.some(p => p.date === dIso);
        dayStripHtml += `
          <div class="day-pill ${isAct}" onclick="setCurrentDate('${dIso}')">
            <span class="dow">${dNames[offset]}</span>
            <span class="dom">${dd}/${mm}</span>
            <div class="dots">
              <span class="mini-dot" style="background:#38BDF8"></span>
              ${hasPres ? '<span class="mini-dot" style="background:#A855F7"></span>' : ''}
              ${hasMeet ? '<span class="mini-dot" style="background:#22C55E"></span>' : ''}
            </div>
          </div>
        `;
      }
      dayStripHtml += `</div>`;

      let bodyHtml = "";
      if (planningScope === "chefs") {
        bodyHtml = renderChefsPlanningView(monIso);
      } else if (planningScope === "combined") {
        bodyHtml = renderCombinedChefsInternesView(monIso);
      } else if (planningScope === "perso" && isChefId(selectedInterneId)) {
        bodyHtml = renderSingleChefPersoView(monIso, getChefById(selectedInterneId));
      } else if (planningMode === "day") {
        bodyHtml = renderDayPlanningView(currentDateIso);
      } else if (planningMode === "week") {
        bodyHtml = renderWeekPlanningView(monIso);
      } else {
        bodyHtml = renderMonthPlanningView(currentDateIso);
      }

      const persoBtnLabel = isChefId(selectedInterneId)
        ? `👤 Mon Planning (${getChefById(selectedInterneId).code})`
        : `👤 Mon Planning`;

      return `
        <div class="planning-toolbar">
          <div class="segmented">
            <button class="seg-btn ${planningScope === 'internes' ? 'active' : ''}" onclick="setPlanningScope('internes')">🎓 Grille Internes</button>
            <button class="seg-btn ${planningScope === 'chefs' ? 'active' : ''}" onclick="setPlanningScope('chefs')">🩺 Grille Chefs</button>
            <button class="seg-btn ${planningScope === 'combined' ? 'active' : ''}" onclick="setPlanningScope('combined')">🔄 Chefs + Internes</button>
            <button class="seg-btn ${planningScope === 'perso' ? 'active' : ''}" onclick="setPlanningScope('perso')">${persoBtnLabel}</button>
          </div>

          <div class="date-nav">
            <button class="btn-icon" onclick="shiftPlanningDate(-1)">◀</button>
            <div class="date-label">${headerLabel}</div>
            <button class="btn-icon" onclick="shiftPlanningDate(1)">▶</button>
            <button class="btn-icon" onclick="setCurrentDate('2026-11-02')">Début Semestre</button>
          </div>

          <div class="segmented">
            <button class="seg-btn ${planningMode === 'day' ? 'active' : ''}" onclick="setPlanningMode('day')">Jour</button>
            <button class="seg-btn ${planningMode === 'week' ? 'active' : ''}" onclick="setPlanningMode('week')">Semaine</button>
            <button class="seg-btn ${planningMode === 'month' ? 'active' : ''}" onclick="setPlanningMode('month')">Mois</button>
          </div>
        </div>

        ${dayStripHtml}
        ${bodyHtml}
        ${renderBalanceSummaryCard()}
      `;
    }

    function setPlanningScope(sc) {
      planningScope = sc;
      if (sc === "perso") {
        if (selectedInterneId === "all") selectedInterneId = "gabriel";
        if (selectedInterneId === "all_chefs") selectedInterneId = "chef_tl";
      }
      renderAll();
    }

    function setPlanningMode(md) {
      planningMode = md;
      renderTabContent();
    }

    function setCurrentDate(iso) {
      currentDateIso = iso;
      renderAll();
    }

    function shiftPlanningDate(dir) {
      if (planningMode === "day") {
        let next = addDaysIso(currentDateIso, dir);
        const [y, m, d] = next.split("-").map(Number);
        const wd = new Date(y, m - 1, d).getDay();
        if (wd === 6) next = addDaysIso(next, dir > 0 ? 2 : -1);
        if (wd === 0) next = addDaysIso(next, dir > 0 ? 1 : -2);
        currentDateIso = next;
      } else if (planningMode === "week") {
        currentDateIso = addDaysIso(currentDateIso, dir * 7);
      } else {
        const [y, m] = currentDateIso.split("-").map(Number);
        const dt = new Date(y, m - 1 + dir, 2);
        currentDateIso = dt.toISOString().slice(0, 10);
      }
      renderAll();
    }

    // Vue personnelle d'un Chef (Semaine ou Mois avec les internes en binôme sur ses postes)
    function renderSingleChefPersoView(monIso, chef) {
      if (planningMode === "month") {
        const ym = currentDateIso.slice(0, 7);
        const allDates = Object.keys(STATE.chefsPlanning || {}).filter(k => k.startsWith(ym)).sort();
        let cells = "";
        allDates.forEach(dIso => {
          const sl = getChefSlotsForDate(dIso, chef);
          cells += `
            <div class="month-cell ${dIso === currentDateIso ? 'today' : ''}" onclick="setCurrentDate('${dIso}'); setPlanningMode('day');">
              <div style="display:flex; justify-content:space-between; font-weight:800; font-size:12px;">
                <span>${formatDateFr(dIso)}</span>
                ${sl.isGarde ? '<span title="De Garde Senior">🚨</span>' : ''}
              </div>
              <div style="font-size:10px; color:var(--text-muted);">Matin :</div>
              ${sl.am.length ? sl.am.map(p => `<span class="poste-pill ${getPosteClass(p)}" style="font-size:10px; padding:2px 6px;">${p}</span>`).join(" ") : `<span style="font-size:10.5px; color:var(--text-muted);">—</span>`}
              <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">Après-midi :</div>
              ${sl.pm.length ? sl.pm.map(p => `<span class="poste-pill ${getPosteClass(p)}" style="font-size:10px; padding:2px 6px;">${p}</span>`).join(" ") : `<span style="font-size:10.5px; color:var(--text-muted);">—</span>`}
            </div>
          `;
        });
        return `
          <div class="card">
            <div class="card-header">
              <div class="card-title">🗓️ Vue Mensuelle — ${chef.fullName}</div>
              <button class="btn-icon" onclick="setPlanningScope('internes')">🎓 Voir le mois des Internes</button>
            </div>
            <div class="month-grid">${cells}</div>
          </div>
        `;
      }

      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      let cardsHtml = `
        <div class="card">
          <div class="card-header">
            <div class="card-title">🩺 Semaine de ${chef.fullName} — Vacations & Internes affectés sur vos postes</div>
            <button class="btn-icon" onclick="setPlanningScope('internes')">🎓 Ouvrir Grille complète des Internes</button>
          </div>
          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:10px;">
      `;
      days.forEach(dIso => {
        const sl = getChefSlotsForDate(dIso, chef);
        const intDay = STATE.schedule[dIso] || { am: [], pm: [] };
        const presList = STATE.presentations.filter(p => p.date === dIso);

        // Internes en binôme le matin et l'après-midi
        function findMatchingInternes(chefPostes, intPeriodList) {
          const out = [];
          (chefPostes || []).forEach(cp => {
            const pUp = cp.toUpperCase();
            (intPeriodList || []).forEach(it => {
              const iUp = String(it.poste || "").toUpperCase();
              if (
                (pUp.includes("ACHARD") && iUp.includes("ACHARD")) ||
                (pUp.includes("GESTES") && iUp.includes("GESTES")) ||
                (pUp.includes("SAU") && iUp.includes("SAU")) ||
                (pUp.includes("OLLIER 3") && iUp.includes("OLLIER DIAG")) ||
                (pUp.includes("IRM") && iUp.includes("IRM")) ||
                (pUp.includes("ECHO") && iUp.includes("ECHO")) ||
                (pUp.includes("ALLURA") && iUp.includes("ALLURA")) ||
                (pUp.includes("CONSULT") && iUp.includes("LECTURE"))
              ) {
                const tag = `${it.interne} (${it.poste})`;
                if (!out.includes(tag)) out.push(tag);
              }
            });
          });
          return out;
        }
        const intAm = findMatchingInternes(sl.am, intDay.am);
        const intPm = findMatchingInternes(sl.pm, intDay.pm);

        cardsHtml += `
          <div class="card" style="margin:0; background:rgba(11,17,32,0.78); border-color:${sl.isGarde ? 'rgba(239,68,68,0.5)' : 'var(--border)'};">
            <div style="font-weight:800; font-size:13px; margin-bottom:8px; color:${chef.color}; display:flex; justify-content:space-between; align-items:center;">
              <span>${formatDateFr(dIso)}</span>
              ${sl.isGarde ? `<span class="poste-pill poste-rg" style="font-size:10px;">🚨 GARDE</span>` : ``}
            </div>
            <div style="margin-bottom:8px;">
              <div style="font-size:10px; color:var(--text-muted); font-weight:700;">MATIN (08h30 – 13h00)</div>
              <div style="margin-top:3px; display:flex; flex-wrap:wrap; gap:4px;">
                ${sl.am.length ? sl.am.map(p => `<span class="poste-pill ${getPosteClass(p)}">${p}</span>`).join("") : `<span class="poste-pill poste-off">Hors trame / Libre</span>`}
              </div>
              ${intAm.length ? `<div style="font-size:11px; color:#38BDF8; margin-top:4px;">🎓 Internes : <strong>${intAm.join(", ")}</strong></div>` : ``}
            </div>
            <div style="margin-bottom:6px;">
              <div style="font-size:10px; color:var(--text-muted); font-weight:700;">APRÈS-MIDI (13h30 – 18h30)</div>
              <div style="margin-top:3px; display:flex; flex-wrap:wrap; gap:4px;">
                ${sl.pm.length ? sl.pm.map(p => `<span class="poste-pill ${getPosteClass(p)}">${p}</span>`).join("") : `<span class="poste-pill poste-off">Hors trame / Libre</span>`}
              </div>
              ${intPm.length ? `<div style="font-size:11px; color:#C084FC; margin-top:4px;">🎓 Internes : <strong>${intPm.join(", ")}</strong></div>` : ``}
            </div>
            ${presList.map(p => `<div style="font-size:11px; color:#FBBF24; margin-top:5px; padding-top:5px; border-top:1px dashed var(--border);">🎓 12h30 : ${p.typeLabel} — <strong>${p.interneName}</strong>${p.chefIntervenant ? `<br/>🩺 Cours : ${p.chefIntervenant}` : ''}</div>`).join("")}
          </div>
        `;
      });
      cardsHtml += `</div></div>`;
      return cardsHtml;
    }

    // Vue Croisée Chefs + Internes côte à côte sur chaque poste de la semaine
    function renderCombinedChefsInternesView(monIso) {
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      const sectors = [
        { label: "ECHO", chefMatch: ["ECHO"], intMatch: ["ECHO"] },
        { label: "GESTES (C)", chefMatch: ["GESTES"], intMatch: ["GESTES (C)"] },
        { label: "TDM SAU (Ollier 4)", chefMatch: ["SAU", "OLLIER 4"], intMatch: ["TDM SAU"] },
        { label: "TDM ACHARD 1 (RI)", chefMatch: ["ACHARD"], intMatch: ["SCAN ACHARD"] },
        { label: "ALLURA (Vasculaire/Os)", chefMatch: ["ALLURA"], intMatch: ["ALLURA"] },
        { label: "IRM 3T & 1,5T", chefMatch: ["IRM"], intMatch: ["IRM 3T", "IRM 1,5T", "IRM"] },
        { label: "TDM OLLIER 3 / DIAG", chefMatch: ["OLLIER 3"], intMatch: ["TDM OLLIER DIAG"] },
        { label: "CONSULTATION / LECTURE", chefMatch: ["CONSULT", "UCSA"], intMatch: ["LECTURE/CS"] }
      ];

      function buildCombinedPeriodRows(periodKey) {
        let rows = "";
        sectors.forEach(sec => {
          rows += `<tr><td><span class="poste-pill ${getPosteClass(sec.label)}">${sec.label}</span></td>`;
          days.forEach(dIso => {
            const chDay = (STATE.chefsPlanning && STATE.chefsPlanning[dIso]) ? (STATE.chefsPlanning[dIso][periodKey] || []) : [];
            const intDay = (STATE.schedule && STATE.schedule[dIso]) ? (STATE.schedule[dIso][periodKey] || []) : [];

            const matchedChefs = chDay.filter(x => sec.chefMatch.some(m => String(x.poste || "").toUpperCase().includes(m)));
            const matchedInts = intDay.filter(x => sec.intMatch.includes(x.poste));

            let cellHtml = "";
            if (matchedChefs.length > 0) {
              cellHtml += `<div style="margin-bottom:4px;">` + matchedChefs.map(c =>
                `<span style="display:inline-block; font-size:11px; font-weight:800; color:#38BDF8; background:rgba(56,189,248,0.14); border:1px solid rgba(56,189,248,0.35); border-radius:6px; padding:1px 6px; margin:1px;">🩺 ${c.doc}</span>`
              ).join("") + `</div>`;
            }
            if (matchedInts.length > 0) {
              cellHtml += `<div>` + matchedInts.map(m => {
                const iObj = getInterneById(m.interneId);
                return `<span class="interne-badge" onclick="openVacationEditModal('${dIso}', '${m.interneId}')" style="margin:1px;">
                  <span style="width:6px;height:6px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                  🎓 ${iObj.shortName}
                </span>`;
              }).join("") + `</div>`;
            }
            rows += `<td>${cellHtml || '<span style="color:rgba(148,163,184,0.3)">—</span>'}</td>`;
          });
          rows += `</tr>`;
        });
        return rows;
      }

      return `
        <div class="card" style="padding:0; overflow:hidden;">
          <div style="padding:12px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div class="card-title">🔄 Vue Croisée Semaine — Binômes Chefs (🩺) & Internes (🎓) par Secteur</div>
            <div style="font-size:11.5px; color:var(--text-muted);">Visualisez simultanément le Senior/Chef et l'Interne affectés sur chaque poste</div>
          </div>
          <div class="week-table-wrap" style="border:none; border-radius:0;">
            <table class="planning-table">
              <thead>
                <tr>
                  <th style="width:175px;">SECTEUR / POSTE</th>
                  ${days.map(d => `<th>${formatDateFr(d)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr class="period-divider"><td colspan="6">☀️ MATIN (08h30 – 13h00) — 🩺 CHEFS & 🎓 INTERNES</td></tr>
                ${buildCombinedPeriodRows("am")}
                <tr class="period-divider"><td colspan="6">🌤️ APRÈS-MIDI (13h30 – 18h30) — 🩺 CHEFS & 🎓 INTERNES</td></tr>
                ${buildCombinedPeriodRows("pm")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // Vue Semaine — Grille par Poste (exactement comme le Planning des Chefs)
    function renderWeekPlanningView(monIso) {
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      const postesAm = ["ECHO", "GESTES (C)", "TDM SAU", "TDM OLLIER DIAG", "IRM 3T", "IRM 1,5T", "SCAN ACHARD", "LECTURE/CS", "1/2 journée libre", "RG", "VACANCES"];
      const postesPm = ["GESTES (C)", "TDM OLLIER DIAG", "TDM SAU", "IRM", "ECHO", "ALLURA", "SCAN ACHARD", "LECTURE/CS", "1/2 journée libre", "RG", "VACANCES"];

      if (planningScope === "perso") {
        const me = getInterneById(selectedInterneId === "all" ? "gabriel" : selectedInterneId);
        let cardsHtml = `<div class="card"><div class="card-header"><div class="card-title">👤 Semaine de ${me.fullName} (cliquez sur une demi-journée pour échanger/modifier)</div></div><div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px;">`;
        days.forEach(dIso => {
          const dObj = STATE.schedule[dIso] || {};
          const slot = (dObj.byInterne && dObj.byInterne[me.id]) ? dObj.byInterne[me.id] : { am: "—", pm: "—", note: "" };
          const presList = STATE.presentations.filter(p => p.date === dIso);
          const meetList = STATE.meetings.filter(m => m.date === dIso);
          cardsHtml += `
            <div class="card" style="margin:0; background:rgba(11,17,32,0.75); cursor:pointer;" onclick="openVacationEditModal('${dIso}', '${me.id}')">
              <div style="font-weight:800; font-size:13px; margin-bottom:8px; color:var(--primary); display:flex; justify-content:space-between;">
                <span>${formatDateFr(dIso)}</span>
                <span style="font-size:11px; color:var(--text-muted);">✎</span>
              </div>
              <div style="margin-bottom:6px;">
                <div style="font-size:10px; color:var(--text-muted); font-weight:700;">MATIN (08h30 – 13h00)</div>
                <span class="poste-pill ${getPosteClass(slot.am)}" style="margin-top:3px;">${slot.am}</span>
              </div>
              <div style="margin-bottom:6px;">
                <div style="font-size:10px; color:var(--text-muted); font-weight:700;">APRÈS-MIDI (13h30 – 18h30)</div>
                <span class="poste-pill ${getPosteClass(slot.pm)}" style="margin-top:3px;">${slot.pm}</span>
              </div>
              ${slot.note ? `<div style="font-size:11px; color:#FBBF24; margin-top:4px;">📌 ${slot.note}</div>` : ''}
              ${presList.map(p => `<div style="font-size:11px; color:#C084FC; margin-top:4px;">🎓 12h30 : ${p.typeLabel} (${p.interneName})</div>`).join("")}
              ${meetList.map(m => `<div style="font-size:11px; color:#34D399; margin-top:4px;">🏛️ ${m.horaire} : ${m.title}</div>`).join("")}
            </div>
          `;
        });
        cardsHtml += `</div></div>`;
        return cardsHtml;
      }

      function renderPeriodRows(postesList, periodKey) {
        let rowsHtml = "";
        postesList.forEach(posteName => {
          // Vérifier si au moins un interne est sur ce poste dans la semaine
          const hasAny = days.some(dIso => {
            const dObj = STATE.schedule[dIso];
            if (!dObj || !dObj[periodKey]) return false;
            return dObj[periodKey].some(x => x.poste === posteName);
          });
          if (!hasAny && (posteName === "RG" || posteName === "VACANCES")) return;

          rowsHtml += `<tr><td><span class="poste-pill ${getPosteClass(posteName)}">${posteName}</span></td>`;
          days.forEach(dIso => {
            const dObj = STATE.schedule[dIso];
            if (!dObj) {
              rowsHtml += `<td>—</td>`;
              return;
            }
            if (dObj.holiday) {
              rowsHtml += `<td><span class="poste-pill poste-rg">FÉRIÉ (${dObj.holiday})</span></td>`;
              return;
            }
            const matches = (dObj[periodKey] || []).filter(x => x.poste === posteName);
            if (matches.length === 0) {
              rowsHtml += `<td style="color:rgba(148,163,184,0.35)">—</td>`;
            } else {
              const badges = matches.map(m => {
                const iObj = getInterneById(m.interneId);
                const isMe = (selectedInterneId !== "all" && m.interneId === selectedInterneId) ? "highlight-me" : "";
                return `<span class="interne-badge ${isMe}" onclick="openVacationEditModal('${dIso}', '${m.interneId}')" title="Cliquer pour modifier ou échanger la vacation">
                  <span style="width:7px;height:7px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                  ${iObj.shortName}
                </span>`;
              }).join("");
              rowsHtml += `<td>${badges}</td>`;
            }
          });
          rowsHtml += `</tr>`;
        });
        return rowsHtml;
      }

      // Ligne des présentations Midi & Réunions de la semaine
      let staffRowHtml = `<tr><td><span class="poste-pill poste-irm">🎓 STAFF 12h30 & RÉUNIONS</span></td>`;
      days.forEach(dIso => {
        const pres = STATE.presentations.filter(p => p.date === dIso);
        const meets = STATE.meetings.filter(m => m.date === dIso);
        let cell = "";
        pres.forEach(p => {
          cell += `<div style="font-size:11px; margin-bottom:4px; padding:4px 6px; border-radius:6px; background:rgba(168,85,247,0.14); border:1px solid rgba(168,85,247,0.3); cursor:pointer;" onclick="openPresentationModal('${p.id}')">
            <strong style="color:#C084FC">${p.type === 'cas_mardi' ? 'Cas Mardi' : (p.type === 'biblio_vendredi' ? 'Biblio Ven.' : p.typeLabel)} :</strong> ${p.interneName}
            ${p.sujet ? `<div style="color:var(--text-muted); font-size:10.5px;">« ${p.sujet} »</div>` : `<div style="color:#FBBF24; font-size:10px;">+ Remplir le sujet</div>`}
            ${p.coursChef ? `<div style="color:#38BDF8; font-size:10px;">🩺 Cours : ${p.chefIntervenant}</div>` : ''}
          </div>`;
        });
        meets.forEach(m => {
          cell += `<div style="font-size:11px; margin-bottom:4px; padding:4px 6px; border-radius:6px; background:rgba(34,197,94,0.14); border:1px solid rgba(34,197,94,0.3);">
            <strong style="color:#4ADE80">🏛️ ${m.horaire} :</strong> ${m.title}
          </div>`;
        });
        staffRowHtml += `<td>${cell || '<span style="color:rgba(148,163,184,0.35)">—</span>'}</td>`;
      });
      staffRowHtml += `</tr>`;

      // Ligne Garde Senior Cochin (référence)
      let gardeRowHtml = `<tr><td><span class="poste-pill poste-rg">🚨 GARDE SENIOR</span></td>`;
      days.forEach(dIso => {
        const g = STATE.chefsGardes ? STATE.chefsGardes[dIso] : null;
        gardeRowHtml += `<td>${g && g.noms ? `<span style="font-weight:700; color:#F87171;">Dr ${g.noms.join(", ")}</span>` : '—'}</td>`;
      });
      gardeRowHtml += `</tr>`;

      return `
        <div class="card" style="padding:0; overflow:hidden;">
          <div style="padding:12px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div class="card-title">📋 Trame Hebdomadaire des Internes — Radiologie B (style Planning des Chefs)</div>
            <div style="font-size:11.5px; color:var(--text-muted);">💡 Cliquez sur le prénom d'un interne pour échanger ou adapter sa demi-journée</div>
          </div>
          <div class="week-table-wrap" style="border:none; border-radius:0;">
            <table class="planning-table">
              <thead>
                <tr>
                  <th style="width:170px;">POSTE / SECTEUR</th>
                  ${days.map(d => `<th>${formatDateFr(d)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr class="period-divider"><td colspan="6">☀️ MATIN (08h30 – 13h00)</td></tr>
                ${renderPeriodRows(postesAm, "am")}
                <tr class="period-divider"><td colspan="6">🎓 MIDI (12h30 – 13h30) — CAS DU MARDI, BIBLIO DU VENDREDI & RÉUNIONS</td></tr>
                ${staffRowHtml}
                <tr class="period-divider"><td colspan="6">🌤️ APRÈS-MIDI (13h30 – 18h30)</td></tr>
                ${renderPeriodRows(postesPm, "pm")}
                <tr class="period-divider"><td colspan="6">🌙 GARDE SENIOR DE RÉFÉRENCE (COCHIN)</td></tr>
                ${gardeRowHtml}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // Vue Jour détaillée (affiche à la fois les Internes ET les Chefs du jour !)
    function renderDayPlanningView(iso) {
      const dObj = STATE.schedule[iso];
      if (!dObj) {
        return `<div class="card">Aucune vacation programmée ce jour (${formatDateFr(iso, true)}).</div>`;
      }
      const pres = STATE.presentations.filter(p => p.date === iso);
      const meets = STATE.meetings.filter(m => m.date === iso);
      const gSenior = STATE.chefsGardes ? STATE.chefsGardes[iso] : null;
      const chDay = (STATE.chefsPlanning && STATE.chefsPlanning[iso]) ? STATE.chefsPlanning[iso] : { am: [], pm: [] };

      let rows = "";
      STATE.internes.forEach(i => {
        if (planningScope === "perso" && !isChefId(selectedInterneId) && selectedInterneId !== "all" && i.id !== selectedInterneId) return;
        const slot = (dObj.byInterne && dObj.byInterne[i.id]) ? dObj.byInterne[i.id] : null;
        if (!slot) return;
        rows += `
          <tr onclick="openVacationEditModal('${iso}', '${i.id}')" style="cursor:pointer;">
            <td>
              <div style="display:flex; align-items:center; gap:8px; font-weight:800;">
                <span style="width:10px;height:10px;border-radius:50%;background:${i.color};display:inline-block;"></span>
                ${i.fullName}
              </div>
            </td>
            <td><span class="poste-pill ${getPosteClass(slot.am)}">${slot.am}</span></td>
            <td><span class="poste-pill ${getPosteClass(slot.pm)}">${slot.pm}</span></td>
            <td style="color:var(--text-muted); font-size:12px;">${slot.note || "—"} <span style="float:right;opacity:0.6;">✎</span></td>
          </tr>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">📅 Détail du ${formatDateFr(iso, true)} — Internes & Chefs</div>
            ${gSenior && gSenior.noms ? `<span class="poste-pill poste-rg">🚨 Garde Senior : Dr ${gSenior.noms.join(", ")}</span>` : ''}
          </div>
          ${pres.map(p => `
            <div class="alert-box alert-info" style="cursor:pointer;" onclick="openPresentationModal('${p.id}')">
              🎓 <strong>${p.horaire} — ${p.typeLabel} :</strong> présenté par <strong>${p.interneName}</strong>
              ${p.sujet ? `<br/>Sujet : <em>« ${p.sujet} »</em>` : `<br/><span style="color:#FBBF24">Cliquez pour renseigner le titre du cas ou de l'article</span>`}
              ${p.coursChef ? `<br/>🩺 Cours des Chefs : <strong>${p.chefIntervenant}</strong> — ${p.coursChef}` : ''}
            </div>
          `).join("")}
          ${meets.map(m => `
            <div class="alert-box" style="background:rgba(34,197,94,0.12); border-color:rgba(34,197,94,0.3); color:#BBF7D0;">
              🏛️ <strong>${m.horaire} — ${m.title}</strong> (${m.location})<br/>
              <span style="font-size:11.5px;">Envoyé par ${m.sender} : ${m.description}</span>
            </div>
          `).join("")}
          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:12px;">
            <div>
              <div style="font-size:12px; font-weight:800; color:var(--primary); margin-bottom:6px;">🎓 VACATIONS DES 6 INTERNES</div>
              <div class="week-table-wrap">
                <table class="planning-table" style="min-width:340px;">
                  <thead>
                    <tr>
                      <th>Interne</th>
                      <th>Matin</th>
                      <th>Après-midi</th>
                      <th>Note</th>
                    </tr>
                  </thead>
                  <tbody>${rows}</tbody>
                </table>
              </div>
            </div>
            <div>
              <div style="font-size:12px; font-weight:800; color:#38BDF8; margin-bottom:6px;">🩺 VACATIONS DES CHEFS & SENIORS CE JOUR</div>
              <div class="card" style="margin:0; background:rgba(11,17,32,0.75);">
                <div style="font-size:11px; font-weight:800; color:var(--text-muted); margin-bottom:4px;">☀️ MATIN</div>
                ${(chDay.am || []).map(x => `<div style="font-size:12px; margin-bottom:4px;">• <strong>${x.poste}</strong> : <span style="color:#38BDF8; font-weight:700;">${x.doc}</span></div>`).join("") || '<div style="font-size:12px; color:var(--text-muted);">—</div>'}
                <div style="font-size:11px; font-weight:800; color:var(--text-muted); margin:10px 0 4px;">🌤️ APRÈS-MIDI</div>
                ${(chDay.pm || []).map(x => `<div style="font-size:12px; margin-bottom:4px;">• <strong>${x.poste}</strong> : <span style="color:#C084FC; font-weight:700;">${x.doc}</span></div>`).join("") || '<div style="font-size:12px; color:var(--text-muted);">—</div>'}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // Vue Mois
    function renderMonthPlanningView(iso) {
      if (isChefId(selectedInterneId)) {
        return renderSingleChefPersoView(getMondayOfWeek(iso), getChefById(selectedInterneId));
      }
      const ym = iso.slice(0, 7);
      const daysInMonth = Object.keys(STATE.schedule).filter(k => k.startsWith(ym)).sort();
      const targetId = (selectedInterneId === "all" || selectedInterneId === "all_chefs") ? "gabriel" : selectedInterneId;
      const targetInterne = getInterneById(targetId);

      let cells = "";
      daysInMonth.forEach(dIso => {
        const dObj = STATE.schedule[dIso];
        const slot = (dObj.byInterne && dObj.byInterne[targetId]) ? dObj.byInterne[targetId] : null;
        const pres = STATE.presentations.filter(p => p.date === dIso);
        const meets = STATE.meetings.filter(m => m.date === dIso);
        cells += `
          <div class="month-cell ${dIso === currentDateIso ? 'today' : ''}" onclick="setCurrentDate('${dIso}'); setPlanningMode('day');">
            <div style="display:flex; justify-content:space-between; font-weight:800; font-size:12px;">
              <span>${formatDateFr(dIso)}</span>
              ${pres.length ? '<span title="Présentation Mardi/Vendredi">🎓</span>' : ''}
            </div>
            ${dObj.holiday ? `<span class="poste-pill poste-rg">FÉRIÉ</span>` : (slot ? `
              <div style="font-size:10px; color:var(--text-muted);">Matin :</div>
              <span class="poste-pill ${getPosteClass(slot.am)}" style="font-size:10.5px; padding:2px 6px;">${slot.am}</span>
              <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">Après-midi :</div>
              <span class="poste-pill ${getPosteClass(slot.pm)}" style="font-size:10.5px; padding:2px 6px;">${slot.pm}</span>
            ` : `<span style="font-size:11px; color:var(--text-muted);">—</span>`)}
            ${meets.length ? `<div style="font-size:10px; color:#4ADE80; font-weight:700;">🏛️ ${meets.length} réunion(s)</div>` : ''}
          </div>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">🗓️ Vue Mensuelle — Vacations de ${targetInterne.fullName}</div>
            <div style="font-size:12px; color:var(--text-muted);">Sélectionnez un interne ou un chef en haut pour voir son mois complet</div>
          </div>
          <div class="month-grid">${cells}</div>
        </div>
      `;
    }

    // Vue Planning des Chefs (Grille Hebdomadaire complète par Poste + Cartes par Chef)
    function renderChefsPlanningView(monIso) {
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      const chefPostesAm = ["ECHO", "GESTES (C)", "TDM OLLIER 4 (SAU)", "TDM OLLIER 3", "TDM ACHARD 1", "IRM 3T", "IRM 1,5T", "CONSULTATION", "UCSA", "STAFF"];
      const chefPostesPm = ["GESTES (C)", "TDM OLLIER 4 (SAU)", "TDM OLLIER 3", "TDM ACHARD 1", "IRM", "ECHO", "ALLURA", "CONSULTATION", "UCSA", "STAFF"];

      const activeChef = isChefId(selectedInterneId) ? getChefById(selectedInterneId) : null;

      function renderChefRows(postesList, periodKey) {
        let rows = "";
        postesList.forEach(pName => {
          const hasAny = days.some(dIso => {
            const ch = STATE.chefsPlanning ? STATE.chefsPlanning[dIso] : null;
            return ch && ch[periodKey] && ch[periodKey].some(x => x.poste === pName);
          });
          if (!hasAny) return;
          rows += `<tr><td><span class="poste-pill ${getPosteClass(pName)}">${pName}</span></td>`;
          days.forEach(dIso => {
            const ch = STATE.chefsPlanning ? STATE.chefsPlanning[dIso] : null;
            const matches = (ch && ch[periodKey]) ? ch[periodKey].filter(x => x.poste === pName) : [];
            if (!matches.length) {
              rows += `<td style="color:rgba(148,163,184,0.3)">—</td>`;
            } else {
              const badges = matches.map(m => {
                const isHighlighted = activeChef && doesDocMatchChef(m.doc, activeChef);
                return `<span class="interne-badge ${isHighlighted ? 'highlight-me' : ''}" style="cursor:pointer;" onclick="selectChefByDocString('${m.doc.replace(/'/g, "\\'")}')">
                  🩺 <strong>${m.doc}</strong>
                </span>`;
              }).join(" ");
              rows += `<td>${badges}</td>`;
            }
          });
          rows += `</tr>`;
        });
        return rows;
      }

      let gardeRowHtml = `<tr><td><span class="poste-pill poste-rg">🚨 GARDE SENIOR</span></td>`;
      days.forEach(dIso => {
        const g = STATE.chefsGardes ? STATE.chefsGardes[dIso] : null;
        gardeRowHtml += `<td>${g && g.noms ? `<span style="font-weight:800; color:#F87171;">Dr ${g.noms.join(", ")}</span>` : '—'}</td>`;
      });
      gardeRowHtml += `</tr>`;

      return `
        <div class="card" style="padding:0; overflow:hidden;">
          <div style="padding:12px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div class="card-title">🩺 Grille Hebdomadaire des Chefs & Seniors — Radiologie B (Anne-Marie Fortin)</div>
            <div style="display:flex; gap:6px;">
              <button class="btn-icon" onclick="setPlanningScope('internes')">🎓 Basculer sur Grille Internes</button>
              <button class="btn-icon" onclick="setPlanningScope('combined')">🔄 Voir Binômes Chefs + Internes</button>
            </div>
          </div>
          <div class="week-table-wrap" style="border:none; border-radius:0;">
            <table class="planning-table">
              <thead>
                <tr>
                  <th style="width:170px;">POSTE SENIOR</th>
                  ${days.map(d => `<th>${formatDateFr(d)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr class="period-divider"><td colspan="6">☀️ MATIN (08h30 – 13h00) — CHEFS & SENIORS</td></tr>
                ${renderChefRows(chefPostesAm, "am")}
                <tr class="period-divider"><td colspan="6">🌤️ APRÈS-MIDI (13h30 – 18h30) — CHEFS & SENIORS</td></tr>
                ${renderChefRows(chefPostesPm, "pm")}
                <tr class="period-divider"><td colspan="6">🌙 GARDE SENIOR DE RÉFÉRENCE (COCHIN)</td></tr>
                ${gardeRowHtml}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    function selectChefByDocString(docStr) {
      const found = (STATE.chefs || []).find(c => doesDocMatchChef(docStr, c));
      if (found) {
        selectInterne(found.id);
      }
    }

    // Tableau d'équilibrage du nombre de vacations entre les internes
    function renderBalanceSummaryCard() {
      const statsAll = computeStatsByInterne();
      let rows = "";
      STATE.internes.forEach(i => {
        const s = statsAll[i.id];
        const pct = Math.min(100, Math.round((s.activeHalfDays / 210) * 100));
        rows += `
          <tr>
            <td>
              <div style="display:flex; align-items:center; gap:7px; font-weight:800;">
                <span style="width:9px;height:9px;border-radius:50%;background:${i.color};display:inline-block;"></span>
                ${i.fullName}
              </div>
            </td>
            <td>
              <div style="font-weight:800; color:${i.color}; margin-bottom:3px;">${s.activeHalfDays} vacations</div>
              <div class="balance-bar-bg"><div class="balance-bar-fill" style="width:${pct}%; background:${i.color};"></div></div>
            </td>
            <td><span class="poste-pill poste-tdm">${s.byModality.TDM}</span></td>
            <td><span class="poste-pill poste-irm">${s.byModality.IRM}</span></td>
            <td><span class="poste-pill poste-echo">${s.byModality.ECHO}</span></td>
            <td><span class="poste-pill poste-gestes">${s.byModality.RI_GESTES}</span></td>
            <td><span class="poste-pill poste-cs">${s.byModality.LECTURE_CS}</span></td>
            <td><span class="poste-pill poste-off">${s.freeHalfDays}</span></td>
            <td><span class="poste-pill poste-vac">${Math.round(s.vacHalfDays / 2)} j.</span></td>
            <td><strong>${s.casMardi}</strong> Cas / <strong>${s.biblioVendredi}</strong> Biblio</td>
          </tr>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">⚖️ Équilibre des Vacations & Présentations sur le Semestre (Hiver 2026–2027)</div>
            <span style="font-size:11.5px; color:var(--text-muted);">Rotation hebdomadaire équitable : chaque interne effectue le même nombre de vacations</span>
          </div>
          <div class="week-table-wrap">
            <table class="planning-table">
              <thead>
                <tr>
                  <th>Interne</th>
                  <th>Total Vacations Actives</th>
                  <th>TDM SAU / Diag</th>
                  <th>IRM 3T / 1,5T</th>
                  <th>Échographie</th>
                  <th>Gestes (C / Achard / Allura)</th>
                  <th>Lecture / CS</th>
                  <th>1/2 j. libres</th>
                  <th>Congés posés</th>
                  <th>Mardi / Vendredi</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    }

    /* =========================================================================
     * ONGLET 2 : VACANCES, CONGÉS (CA / CF) & REPOS DE GARDE (RG)
     * ========================================================================= */
    function renderVacancesTab() {
      const absences = (STATE.absences || []).slice().sort((a, b) => a.date.localeCompare(b.date));
      const filtered = (selectedInterneId === "all")
        ? absences
        : absences.filter(a => a.interneId === selectedInterneId);

      // Regrouper par date pour vérifier la règle "Max 2 absents simultanés"
      const countByDate = {};
      absences.forEach(a => {
        if (a.type !== "Repos de garde") {
          countByDate[a.date] = (countByDate[a.date] || 0) + 1;
        }
      });

      let rowsHtml = "";
      if (filtered.length === 0) {
        rowsHtml = `<tr><td colspan="6" style="text-align:center; padding:18px; color:var(--text-muted);">Aucune absence enregistrée pour ce filtre. Cliquez sur « + Poser des Vacances / RG » pour en ajouter.</td></tr>`;
      } else {
        filtered.forEach(a => {
          const iObj = getInterneById(a.interneId);
          const simCount = countByDate[a.date] || 1;
          const isOverLimit = simCount > 2;
          const [y, m, d] = a.date.split("-").map(Number);
          const wd = new Date(y, m - 1, d).getDay();
          const isTueOrFri = (wd === 2 || wd === 5);

          rowsHtml += `
            <tr>
              <td style="font-weight:800;">${formatDateFr(a.date, true)}</td>
              <td>
                <span class="interne-badge">
                  <span style="width:8px;height:8px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                  ${iObj.fullName}
                </span>
              </td>
              <td><span class="poste-pill ${a.type.includes('garde') ? 'poste-rg' : 'poste-vac'}">${a.type}</span></td>
              <td style="color:var(--text-muted);">${a.comment || "—"}</td>
              <td>
                ${isOverLimit
                  ? `<span class="poste-pill poste-rg">⚠️ ${simCount} absents ce jour (max 2)</span>`
                  : `<span class="poste-pill poste-vac">✅ OK (${simCount}/2 absents)</span>`}
                ${(isTueOrFri && a.type === "CF") ? `<span class="poste-pill poste-tdm" style="margin-left:4px;">⚠️ Mardi/Vendredi (Staff)</span>` : ''}
              </td>
              <td>
                <button class="btn-icon" onclick="deleteAbsence('${a.id}')" style="color:#F87171;">🗑️ Supprimer</button>
              </td>
            </tr>
          `;
        });
      }

      return `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">🌴 Gestion des Vacances (CA 1, CA 2), Congés Formation (CF) & Repos de Garde (RG)</div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                Synchronisé avec l'onglet <strong>Planning Absence</strong> du Google Sheet officiel des internes Hiver 2026–2027.
              </div>
            </div>
            <button class="btn-icon btn-primary" onclick="openAbsenceModal()">+ Poser des Vacances / RG</button>
          </div>

          <div class="alert-box alert-info">
            📌 <strong>Règles de congés du service (Anne-Marie Fortin & Dr F. Mihoubi Bouvier) :</strong><br/>
            1. <strong>Pas plus de 2 internes absents (CA/CF) en même temps</strong> pour garantir la continuité des postes TDM SAU, IRM et Gestes.<br/>
            2. Pour les jours isolés (CF, récupération), <strong>éviter les mardis et les vendredis</strong> (jours de cas cliniques, cours des chefs et biblio).<br/>
            3. Vacances de Noël / Jour de l'An (semaines du 21/12 et 28/12/2026) : répartition équitable en 2 groupes.
          </div>

          <div class="week-table-wrap">
            <table class="planning-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Interne</th>
                  <th>Type de congé</th>
                  <th>Commentaire</th>
                  <th>Validation Règles Service</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          </div>
        </div>
      `;
    }

    function openAbsenceModal(defaultInterneId) {
      const sel = document.getElementById("absInterneSelect");
      const target = defaultInterneId || (selectedInterneId !== "all" ? selectedInterneId : "gabriel");
      sel.innerHTML = STATE.internes.map(i => `<option value="${i.id}" ${i.id === target ? 'selected' : ''}>${i.fullName}</option>`).join("");
      document.getElementById("absStartDate").value = currentDateIso;
      document.getElementById("absEndDate").value = currentDateIso;
      document.getElementById("absComment").value = "";
      document.getElementById("absRuleWarning").style.display = "none";
      document.getElementById("modalAbsence").classList.add("open");
    }

    function saveAbsenceForm() {
      const iid = document.getElementById("absInterneSelect").value;
      const iObj = getInterneById(iid);
      const type = document.getElementById("absTypeSelect").value;
      const startIso = document.getElementById("absStartDate").value;
      const endIso = document.getElementById("absEndDate").value || startIso;
      const comment = document.getElementById("absComment").value.trim();

      if (!startIso || endIso < startIso) {
        alert("Veuillez vérifier les dates de début et de fin.");
        return;
      }

      let cur = startIso;
      const addedDates = [];
      while (cur <= endIso) {
        const id = `abs-${iid}-${cur}`;
        STATE.absences = (STATE.absences || []).filter(x => x.id !== id);
        STATE.absences.push({
          id,
          date: cur,
          interneId: iid,
          interneName: iObj.fullName,
          type,
          comment,
          createdAt: new Date().toISOString()
        });
        addedDates.push(cur);
        cur = addDaysIso(cur, 1);
      }

      saveStateLocal();
      closeModal("modalAbsence");
      renderAll();
      showToast(`Vacances / ${type} enregistrées (${addedDates.length} j.)`);
      pushStateToCloud({ syncAbsenceSheet: true, addedDates, interneName: iObj.fullName, absType: type });
    }

    function deleteAbsence(absId) {
      const target = (STATE.absences || []).find(x => x.id === absId);
      STATE.absences = (STATE.absences || []).filter(x => x.id !== absId);
      saveStateLocal();
      renderAll();
      showToast("Absence supprimée");
      pushStateToCloud({ syncAbsenceSheet: true, deletedAbsence: target });
    }

    /* =========================================================================
     * ONGLET 3 : PRÉSENTATIONS MARDI (CAS) & VENDREDI (BIBLIO)
     * ========================================================================= */
    function renderPresentationsTab() {
      const statsAll = computeStatsByInterne();
      let list = (STATE.presentations || []).slice().sort((a, b) => a.date.localeCompare(b.date));

      if (presFilter === "cas_mardi") list = list.filter(p => p.type === "cas_mardi");
      else if (presFilter === "biblio_vendredi") list = list.filter(p => p.type === "biblio_vendredi");
      else if (presFilter === "mine" && selectedInterneId !== "all") list = list.filter(p => p.interneId === selectedInterneId);
      else if (selectedInterneId !== "all" && presFilter === "all") {
        // Garde tout mais met en surbrillance l'interne sélectionné
      }

      let counterBadges = STATE.internes.map(i => {
        const s = statsAll[i.id];
        return `
          <div class="kpi-card" style="padding:8px 10px;">
            <div style="display:flex; align-items:center; gap:6px; font-weight:800; font-size:12.5px;">
              <span style="width:8px;height:8px;border-radius:50%;background:${i.color};display:inline-block;"></span>
              ${i.shortName}
            </div>
            <div style="font-size:12px; margin-top:3px;">
              <span style="color:#C084FC; font-weight:800;">${s.casMardi}</span> Cas Mardi •
              <span style="color:#FBBF24; font-weight:800;">${s.biblioVendredi}</span> Biblio Ven.
            </div>
          </div>
        `;
      }).join("");

      let rowsHtml = "";
      list.forEach(p => {
        const iObj = getInterneById(p.interneId);
        const isMe = (selectedInterneId !== "all" && p.interneId === selectedInterneId);
        const badgeClass = p.type === "cas_mardi" ? "poste-irm" : (p.type === "biblio_vendredi" ? "poste-tdm" : "poste-echo");
        rowsHtml += `
          <tr style="${isMe ? 'background:rgba(56,189,248,0.09);' : ''}">
            <td style="font-weight:800; white-space:nowrap;">${formatDateFr(p.date, true)}<div style="font-size:10.5px; color:var(--text-muted);">${p.horaire || '12h30 – 13h30'}</div></td>
            <td><span class="poste-pill ${badgeClass}">${p.typeLabel}</span></td>
            <td>
              <span class="interne-badge ${isMe ? 'highlight-me' : ''}" onclick="openPresentationModal('${p.id}')">
                <span style="width:8px;height:8px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                ${p.interneName || iObj.shortName}
              </span>
            </td>
            <td>
              ${p.sujet
                ? `<div style="font-weight:700; color:#F8FAFC;">« ${p.sujet} »</div>`
                : `<span style="color:#FBBF24; font-size:12px; cursor:pointer;" onclick="openPresentationModal('${p.id}')">+ Renseigner le sujet du cas / l'article biblio</span>`}
              ${p.themeSemaine ? `<div style="font-size:11px; color:var(--text-muted); margin-top:2px;">📚 Thème DES : ${p.themeSemaine}</div>` : ''}
            </td>
            <td>
              ${p.coursChef
                ? `<div style="font-size:12px; color:#38BDF8; font-weight:700;">${p.chefIntervenant}</div><div style="font-size:11px; color:var(--text-muted);">${p.coursChef}</div>`
                : `<span style="color:var(--text-muted); font-size:11.5px;">${p.notes || '—'}</span>`}
            </td>
            <td>
              <button class="btn-icon" onclick="openPresentationModal('${p.id}')">✎ Remplir / Changer</button>
            </td>
          </tr>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">🎓 Présentations du Mardi (Cas Clinique + Cours des Chefs) & du Vendredi (Biblio)</div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                Chaque interne peut s'inscrire, échanger sa date ou renseigner le sujet de son cas clinique (mardi) et son article (vendredi).
              </div>
            </div>
            <div class="segmented">
              <button class="seg-btn ${presFilter === 'all' ? 'active' : ''}" onclick="setPresFilter('all')">Tout (${STATE.presentations.length})</button>
              <button class="seg-btn ${presFilter === 'cas_mardi' ? 'active' : ''}" onclick="setPresFilter('cas_mardi')">Cas du Mardi</button>
              <button class="seg-btn ${presFilter === 'biblio_vendredi' ? 'active' : ''}" onclick="setPresFilter('biblio_vendredi')">Biblio Vendredi</button>
              <button class="seg-btn ${presFilter === 'mine' ? 'active' : ''}" onclick="setPresFilter('mine')">Mes présentations</button>
            </div>
          </div>

          <div class="kpi-grid" style="margin-bottom:12px;">${counterBadges}</div>

          <div class="week-table-wrap">
            <table class="planning-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type de Staff</th>
                  <th>Interne inscrit</th>
                  <th>Sujet du Cas Clinique / Référence Article Biblio</th>
                  <th>Cours des Chefs (Mardi) / Notes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          </div>
        </div>
      `;
    }

    function setPresFilter(f) {
      presFilter = f;
      if (f === "mine" && selectedInterneId === "all") selectedInterneId = "gabriel";
      renderAll();
    }

    function openPresentationModal(presId) {
      const p = (STATE.presentations || []).find(x => x.id === presId);
      if (!p) return;
      document.getElementById("presIdInput").value = p.id;
      document.getElementById("presModalTitle").textContent = `🎓 ${p.typeLabel} — ${formatDateFr(p.date, true)}`;
      document.getElementById("presDateDisplay").value = `${formatDateFr(p.date, true)} (${p.horaire || '12h30 – 13h30'})`;

      const sel = document.getElementById("presInterneSelect");
      sel.innerHTML = STATE.internes.map(i => `<option value="${i.id}" ${i.id === p.interneId ? 'selected' : ''}>${i.fullName}</option>`).join("");
      document.getElementById("presSujetInput").value = p.sujet || "";
      document.getElementById("presChefInput").value = p.coursChef ? `${p.chefIntervenant ? p.chefIntervenant + ' — ' : ''}${p.coursChef}` : "";
      document.getElementById("modalPresentation").classList.add("open");
    }

    function savePresentationForm() {
      const pid = document.getElementById("presIdInput").value;
      const p = (STATE.presentations || []).find(x => x.id === pid);
      if (!p) return;

      const iid = document.getElementById("presInterneSelect").value;
      const iObj = getInterneById(iid);
      const sujet = document.getElementById("presSujetInput").value.trim();
      const chefRaw = document.getElementById("presChefInput").value.trim();

      p.interneId = iid;
      p.interneName = iObj.shortName;
      p.sujet = sujet;
      if (chefRaw) {
        const parts = chefRaw.split("—");
        if (parts.length > 1) {
          p.chefIntervenant = parts[0].trim();
          p.coursChef = parts.slice(1).join("—").trim();
        } else {
          p.coursChef = chefRaw;
        }
      }

      saveStateLocal();
      closeModal("modalPresentation");
      renderAll();
      showToast("Présentation mise à jour !");
      pushStateToCloud({ syncStaffSheet: true });
    }

    /* =========================================================================
     * ONGLET 4 : RÉUNIONS DU SERVICE (ANNE-MARIE FORTIN & CHEFS)
     * ========================================================================= */
    function renderReunionsTab() {
      const meets = (STATE.meetings || []).slice().sort((a, b) => a.date.localeCompare(b.date));
      const recurring = STATE.recurringStaffs || [];

      let meetsHtml = meets.map(m => `
        <div class="card" style="background:rgba(11,17,32,0.75); margin-bottom:10px;">
          <div class="card-header" style="margin-bottom:6px;">
            <div>
              <span class="poste-pill ${m.mandatory ? 'poste-gestes' : 'poste-echo'}" style="margin-right:6px;">
                ${m.mandatory ? '📌 Présence requise' : m.category}
              </span>
              <strong style="font-size:14px;">${m.title}</strong>
            </div>
            <div style="font-weight:800; color:var(--primary); font-size:12.5px;">
              📅 ${formatDateFr(m.date, true)} • 🕒 ${m.horaire}
            </div>
          </div>
          <div style="font-size:12.5px; color:#E2E8F0; white-space:pre-line; margin-bottom:8px;">${m.description}</div>
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-size:11.5px; color:var(--text-muted);">
            <span>📍 <strong>Lieu :</strong> ${m.location}</span>
            <span>✉️ <strong>Transmis par :</strong> ${m.sender}</span>
          </div>
        </div>
      `).join("");

      let recHtml = recurring.map(r => `
        <div class="kpi-card" style="padding:11px;">
          <div style="font-weight:800; color:var(--primary); font-size:13px; margin-bottom:6px;">📅 Tous les ${r.day}s</div>
          ${r.items.map(it => `
            <div style="margin-bottom:6px; font-size:12px;">
              <span style="color:#FBBF24; font-weight:700;">${it.horaire} :</span> <strong>${it.title}</strong>
              <div style="font-size:11px; color:var(--text-muted);">Référent : ${it.referent}</div>
            </div>
          `).join("")}
        </div>
      `).join("");

      return `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">🏛️ Réunions & Informations du Service (Anne-Marie Fortin & Chefs)</div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                Formations obligatoires, réunion d'accueil, confrontations anatomo-pathologiques, séminaire DMU Imagina et staffs hebdomadaires.
              </div>
            </div>
            <button class="btn-icon btn-primary" onclick="openMeetingModal()">+ Ajouter une réunion</button>
          </div>
          ${meetsHtml}
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">🔄 Staffs & Réunions Hebdomadaires Récurrents de Radiologie B</div>
          </div>
          <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit,minmax(210px,1fr));">${recHtml}</div>
        </div>
      `;
    }

    function openMeetingModal() {
      document.getElementById("meetDate").value = currentDateIso;
      document.getElementById("meetHoraire").value = "17h00 – 18h00";
      document.getElementById("meetTitle").value = "";
      document.getElementById("meetDesc").value = "";
      document.getElementById("modalMeeting").classList.add("open");
    }

    function saveMeetingForm() {
      const date = document.getElementById("meetDate").value;
      const horaire = document.getElementById("meetHoraire").value.trim() || "Journée";
      const title = document.getElementById("meetTitle").value.trim();
      const sender = document.getElementById("meetSender").value.trim() || "Anne-Marie FORTIN";
      const location = document.getElementById("meetLocation").value.trim() || "Salle de Staff Radio B";
      const description = document.getElementById("meetDesc").value.trim();

      if (!date || !title) {
        alert("Veuillez renseigner la date et l'intitulé de la réunion.");
        return;
      }

      STATE.meetings.push({
        id: "reunion-" + Date.now(),
        date,
        horaire,
        title,
        category: "Réunion Service",
        sender,
        location,
        description,
        mandatory: true
      });

      saveStateLocal();
      closeModal("modalMeeting");
      renderAll();
      showToast("Réunion ajoutée !");
      pushStateToCloud({});
    }

    /* =========================================================================
     * ONGLET 5 : ANNUAIRE TÉLÉPHONIQUE & DECT (HÔPITAL COCHIN — RADIO B & SERVICES)
     * ========================================================================= */
    function renderAnnuaireTab() {
      const list = (STATE.phoneDirectory || []).slice();
      const q = (annuaireSearch || "").toLowerCase().trim();
      const categories = [
        "Radiologie B — Secrétariats & Consoles",
        "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "Laboratoires, Pharmacie & Administration (DAM)"
      ];

      const filtered = list.filter(c => {
        if (annuaireCategory !== "all" && c.category !== annuaireCategory) return false;
        if (!q) return true;
        const blob = `${c.name || ""} ${c.role || ""} ${c.poste || ""} ${c.phone || ""} ${c.building || ""} ${c.category || ""}`.toLowerCase();
        return blob.includes(q);
      });

      let groupsHtml = "";
      categories.forEach(cat => {
        const items = filtered.filter(x => x.category === cat);
        if (items.length === 0) return;

        let rows = items.map(c => {
          const telHref = (c.phone || "").replace(/[^0-9+]/g, "");
          return `
            <tr>
              <td>
                <div style="font-weight:800; color:#F8FAFC; font-size:13px;">${c.name}</div>
                <div style="font-size:11.5px; color:var(--text-muted);">${c.role || ""}</div>
              </td>
              <td>
                <span class="poste-pill poste-irm" style="font-size:12.5px; font-weight:800;">📟 ${c.poste || "—"}</span>
              </td>
              <td>
                ${c.phone
                  ? `<a href="tel:${telHref}" class="poste-pill poste-echo" style="text-decoration:none; font-size:12.5px; font-weight:800;">📞 ${c.phone}</a>`
                  : "—"}
                ${c.fax ? `<div style="font-size:10.5px; color:var(--text-muted); margin-top:3px;">📠 Fax : ${c.fax}</div>` : ""}
              </td>
              <td style="font-size:12px; color:#CBD5E1;">📍 ${c.building || "Hôpital Cochin"}</td>
            </tr>
          `;
        }).join("");

        groupsHtml += `
          <div class="card" style="margin-bottom:12px;">
            <div class="card-header">
              <div class="card-title">📂 ${cat} (${items.length})</div>
            </div>
            <div class="week-table-wrap">
              <table class="planning-table" style="min-width:520px;">
                <thead>
                  <tr>
                    <th>Contact / Secteur / Médecin</th>
                    <th style="width:155px;">Poste Interne / DECT</th>
                    <th style="width:175px;">Téléphone Direct (Appel 1 clic)</th>
                    <th style="width:175px;">Bâtiment / Lieu</th>
                  </tr>
                </thead>
                <tbody>${rows}</tbody>
              </table>
            </div>
          </div>
        `;
      });

      if (!groupsHtml) {
        groupsHtml = `<div class="card" style="text-align:center; color:var(--text-muted); padding:24px;">Aucun numéro ne correspond à votre recherche « ${annuaireSearch} ».</div>`;
      }

      return `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">☎️ Annuaire Téléphonique & DECT — Hôpital Cochin (Radiologie B & Services)</div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                Astuce : Depuis un poste interne Cochin, composez les <strong>5 chiffres du poste</strong> (ex: <strong>12483</strong> pour le ` + "`" + `01 58 41 24 83` + "`" + `). Sur smartphone, cliquez sur un numéro pour appeler directement.
              </div>
            </div>
            <button class="btn-icon btn-primary" onclick="openPhoneContactModal()">+ Ajouter un numéro</button>
          </div>

          <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
            <input
              type="text"
              class="form-control"
              style="flex:1; min-width:240px;"
              placeholder="🔍 Rechercher un nom, service, console, DECT, 12483, Ollier, Achard, Ortho, Anesth..."
              value="${annuaireSearch.replace(/"/g, '&quot;')}"
              oninput="onAnnuaireSearch(this.value)"
            />
            <div class="segmented" style="flex-wrap:wrap;">
              <button class="seg-btn ${annuaireCategory === 'all' ? 'active' : ''}" onclick="setAnnuaireCategory('all')">Tous (${list.length})</button>
              <button class="seg-btn ${annuaireCategory === 'Radiologie B — Secrétariats & Consoles' ? 'active' : ''}" onclick="setAnnuaireCategory('Radiologie B — Secrétariats & Consoles')">Radio B Secr.</button>
              <button class="seg-btn ${annuaireCategory === 'Radiologie B — Équipe Médicale (Chefs & Seniors)' ? 'active' : ''}" onclick="setAnnuaireCategory('Radiologie B — Équipe Médicale (Chefs & Seniors)')">Médecins Radio B</button>
              <button class="seg-btn ${annuaireCategory === 'Services Partenaires (Ortho, Rhumato, Anesth, Anapath)' ? 'active' : ''}" onclick="setAnnuaireCategory('Services Partenaires (Ortho, Rhumato, Anesth, Anapath)')">Ortho / Rhumato / Anesth</button>
              <button class="seg-btn ${annuaireCategory === 'Laboratoires, Pharmacie & Administration (DAM)' ? 'active' : ''}" onclick="setAnnuaireCategory('Laboratoires, Pharmacie & Administration (DAM)')">Labos / Pharma / DAM</button>
            </div>
          </div>
        </div>
        ${groupsHtml}
      `;
    }

    function onAnnuaireSearch(val) {
      annuaireSearch = val;
      renderTabContent();
      const inputs = document.querySelectorAll('input[oninput*="onAnnuaireSearch"]');
      if (inputs.length) {
        const inp = inputs[0];
        inp.focus();
        inp.setSelectionRange(inp.value.length, inp.value.length);
      }
    }

    function setAnnuaireCategory(cat) {
      annuaireCategory = cat;
      renderTabContent();
    }

    function openPhoneContactModal() {
      document.getElementById("phoneNameInput").value = "";
      document.getElementById("phoneRoleInput").value = "";
      document.getElementById("phonePosteInput").value = "";
      document.getElementById("phoneNumInput").value = "01 58 41 ";
      document.getElementById("phoneBldgInput").value = "Bâtiment Ollier";
      document.getElementById("phoneFaxInput").value = "";
      document.getElementById("modalPhoneContact").classList.add("open");
    }

    function savePhoneContactForm() {
      const category = document.getElementById("phoneCatInput").value;
      const name = document.getElementById("phoneNameInput").value.trim();
      const role = document.getElementById("phoneRoleInput").value.trim();
      const poste = document.getElementById("phonePosteInput").value.trim();
      const phone = document.getElementById("phoneNumInput").value.trim();
      const building = document.getElementById("phoneBldgInput").value.trim() || "Hôpital Cochin";
      const fax = document.getElementById("phoneFaxInput").value.trim();

      if (!name || (!poste && !phone)) {
        alert("Veuillez indiquer au moins le nom et un numéro ou poste interne.");
        return;
      }

      if (!STATE.phoneDirectory) STATE.phoneDirectory = [];
      STATE.phoneDirectory.unshift({
        id: "tel-custom-" + Date.now(),
        category,
        name,
        role,
        poste,
        phone,
        fax,
        building
      });

      saveStateLocal();
      closeModal("modalPhoneContact");
      renderAll();
      showToast("Numéro ajouté à l'annuaire Cochin !");
      pushStateToCloud({});
    }

    /* =========================================================================
     * MODIFICATION / ÉCHANGE D'UNE VACATION D'INTERNE
     * ========================================================================= */
    function openVacationEditModal(iso, iid) {
      const iObj = getInterneById(iid);
      const dObj = STATE.schedule[iso];
      if (!dObj || !dObj.byInterne || !dObj.byInterne[iid]) return;
      const slot = dObj.byInterne[iid];

      document.getElementById("vacEditDate").value = iso;
      document.getElementById("vacEditInterneId").value = iid;
      document.getElementById("vacEditHeader").value = `${iObj.fullName} — ${formatDateFr(iso, true)}`;

      const options = STATE.postesMeta.map(p => p.code);
      document.getElementById("vacEditAm").innerHTML = options.map(c => `<option value="${c}" ${c === slot.am ? 'selected' : ''}>${c}</option>`).join("");
      document.getElementById("vacEditPm").innerHTML = options.map(c => `<option value="${c}" ${c === slot.pm ? 'selected' : ''}>${c}</option>`).join("");
      document.getElementById("vacEditNote").value = slot.note || "";

      document.getElementById("modalVacationEdit").classList.add("open");
    }

    function saveSingleVacation() {
      const iso = document.getElementById("vacEditDate").value;
      const iid = document.getElementById("vacEditInterneId").value;
      const am = document.getElementById("vacEditAm").value;
      const pm = document.getElementById("vacEditPm").value;
      const note = document.getElementById("vacEditNote").value.trim();

      if (!STATE.customVacations) STATE.customVacations = {};
      STATE.customVacations[iso + "__" + iid] = { am, pm, note };

      saveStateLocal();
      closeModal("modalVacationEdit");
      renderAll();
      showToast("Vacation mise à jour !");
      pushStateToCloud({});
    }

    function resetSingleVacation() {
      const iso = document.getElementById("vacEditDate").value;
      const iid = document.getElementById("vacEditInterneId").value;
      if (STATE.customVacations) delete STATE.customVacations[iso + "__" + iid];
      saveStateLocal();
      closeModal("modalVacationEdit");
      renderAll();
      showToast("Vacation réinitialisée sur la trame équilibrée");
      pushStateToCloud({});
    }

    function closeModal(id) {
      document.getElementById(id).classList.remove("open");
    }

    /* =========================================================================
     * SYNCHRONISATION CLOUD & GOOGLE SHEET OFFICIEL (10sPMOg9GPXqsSItnUfuYn2Ke0im34p5EEyKk5A0hEF8)
     * ========================================================================= */
    async function pushStateToCloud(opts = {}) {
      const statusEl = document.getElementById("syncStatusText");
      if (statusEl) statusEl.textContent = "Sync...";

      const compact = {
        updatedAt: new Date().toISOString(),
        absences: STATE.absences || [],
        customVacations: STATE.customVacations || {},
        presentations: STATE.presentations || [],
        meetings: STATE.meetings || [],
        phoneDirectory: STATE.phoneDirectory || []
      };

      const evalCode = `
        var props = PropertiesService.getScriptProperties();
        var incoming = ${JSON.stringify(compact)};
        props.setProperty('${CLOUD_PROP_KEY}', JSON.stringify(incoming));

        // Synchronisation optionnelle vers le Google Sheet officiel 'Planning Interne CCH - Hiver 26'
        var syncOpts = ${JSON.stringify(opts)};
        if (syncOpts.syncAbsenceSheet) {
          try {
            var ssInt = SpreadsheetApp.openById('${INTERNES_SHEET_ID}');
            var shAbs = ssInt.getSheetByName('Planning Absence');
            if (shAbs) {
              var data = shAbs.getDataRange().getDisplayValues();
              var colMap = { 'Repos de garde': 2, 'CA 1': 3, 'CA 2': 4, 'CF': 5, 'Autre': 6 };
              // Map date DD/MM/YY -> row index (1-based)
              var rowByDate = {};
              for (var r = 1; r < data.length; r++) {
                var dStr = String(data[r][0] || '').trim();
                if (dStr) rowByDate[dStr] = r + 1;
              }
              function isoToSheetDate(iso) {
                var p = iso.split('-');
                return p[2] + '/' + p[1] + '/' + p[0].slice(2);
              }
              if (Array.isArray(syncOpts.addedDates)) {
                var cIdx = colMap[syncOpts.absType] || 3;
                syncOpts.addedDates.forEach(function(iso) {
                  var k = isoToSheetDate(iso);
                  if (rowByDate[k]) {
                    var cell = shAbs.getRange(rowByDate[k], cIdx);
                    var curVal = String(cell.getDisplayValue() || '').trim();
                    if (curVal.indexOf(syncOpts.interneName) === -1) {
                      cell.setValue(curVal ? (curVal + ' / ' + syncOpts.interneName) : syncOpts.interneName);
                    }
                  }
                });
              }
            }
          } catch (sheetErr) {}
        }
        return { status: 'saved', updatedAt: incoming.updatedAt };
      `;

      try {
        await fetch(WEBHOOK_URL, {
          method: "POST",
          headers: { "Content-Type": "text/plain;charset=utf-8" },
          body: JSON.stringify({ eval_code: evalCode })
        });
        if (statusEl) statusEl.textContent = "Synchronisé ✓";
      } catch (err) {
        if (statusEl) statusEl.textContent = "Mode local";
      }
    }

    async function syncWithCloud(manual = false) {
      const statusEl = document.getElementById("syncStatusText");
      if (statusEl) statusEl.textContent = "Sync...";
      const evalCode = `
        var props = PropertiesService.getScriptProperties();
        var raw = props.getProperty('${CLOUD_PROP_KEY}');
        var cloudState = raw ? JSON.parse(raw) : null;
        var sheetAbs = [];
        try {
          var ssInt = SpreadsheetApp.openById('${INTERNES_SHEET_ID}');
          var shAbs = ssInt.getSheetByName('Planning Absence');
          if (shAbs) {
            var rows = shAbs.getDataRange().getDisplayValues();
            for (var r = 1; r < rows.length; r++) {
              var dStr = String(rows[r][0] || '').trim();
              if (!dStr) continue;
              var cols = [
                { idx: 1, type: 'Repos de garde' },
                { idx: 2, type: 'CA 1' },
                { idx: 3, type: 'CA 2' },
                { idx: 4, type: 'CF' },
                { idx: 5, type: 'Autre' }
              ];
              for (var c = 0; c < cols.length; c++) {
                var val = String(rows[r][cols[c].idx] || '').trim();
                if (val) {
                  sheetAbs.push({ dateStr: dStr, name: val, type: cols[c].type });
                }
              }
            }
          }
        } catch (e) {}
        return { cloudState: cloudState, sheetAbs: sheetAbs };
      `;
      try {
        const resp = await fetch(WEBHOOK_URL, {
          method: "POST",
          headers: { "Content-Type": "text/plain;charset=utf-8" },
          body: JSON.stringify({ eval_code: evalCode })
        });
        const res = await resp.json();
        if (res && res.evalResult) {
          const remote = res.evalResult.cloudState;
          if (remote) {
            if (Array.isArray(remote.absences) && remote.absences.length >= (STATE.absences || []).length) {
              STATE.absences = remote.absences;
            }
            if (remote.customVacations) {
              STATE.customVacations = Object.assign({}, STATE.customVacations, remote.customVacations);
            }
            if (Array.isArray(remote.presentations) && remote.presentations.length > 0) {
              STATE.presentations = remote.presentations;
            }
            if (Array.isArray(remote.meetings) && remote.meetings.length > 0) {
              STATE.meetings = remote.meetings;
            }
            if (Array.isArray(remote.phoneDirectory) && remote.phoneDirectory.length > 0) {
              const map = {};
              (STATE.phoneDirectory || []).forEach(c => { map[c.id] = c; });
              remote.phoneDirectory.forEach(c => { if (c && c.id) map[c.id] = c; });
              STATE.phoneDirectory = Object.values(map);
            }
          }
          // Fusionner aussi les absences lues depuis le Google Sheet 'Planning Interne CCH - Hiver 26'
          const sheetAbs = res.evalResult.sheetAbs || [];
          sheetAbs.forEach(sa => {
            const parts = sa.dateStr.split("/");
            if (parts.length === 3) {
              const yr = parts[2].length === 2 ? "20" + parts[2] : parts[2];
              const iso = `${yr}-${parts[1].padStart(2, "0")}-${parts[0].padStart(2, "0")}`;
              const low = sa.name.toLowerCase();
              const matched = STATE.internes.find(i => low.includes(i.prenom.toLowerCase()) || low.includes(i.nom.toLowerCase()));
              if (matched) {
                const id = `abs-${matched.id}-${iso}`;
                if (!STATE.absences.some(x => x.id === id)) {
                  STATE.absences.push({
                    id,
                    date: iso,
                    interneId: matched.id,
                    interneName: matched.fullName,
                    type: sa.type,
                    comment: "Importé depuis Google Sheet Planning Interne CCH"
                  });
                }
              }
            }
          });
          saveStateLocal();
          renderAll();
        }
        if (statusEl) statusEl.textContent = "Synchronisé ✓";
        if (manual) showToast("Synchronisé avec le Cloud & Google Sheet Internes !");
      } catch (e) {
        if (statusEl) statusEl.textContent = "Hors-ligne";
      }
    }

    // Initialisation au chargement
    window.addEventListener("DOMContentLoaded", () => {
      renderAll();
      syncWithCloud(false);
    });
  </script>
</body>
</html>
"""


def generate_pwa_files(dataset: dict):
    html_out = (
        HTML_TEMPLATE
        .replace("__INITIAL_DATA_JSON__", js_json(dataset))
        .replace("__WEBHOOK_URL_JSON__", js_json(WEBHOOK_URL))
        .replace("__INTERNES_SHEET_ID_JSON__", js_json(INTERNES_SHEET_ID))
        .replace("__CLOUD_PROP_KEY_JSON__", js_json(CLOUD_PROP_KEY))
    )

    # Vérification stricte : aucune donnée patient
    assert_zero_patient_data(html_out)

    INDEX_FILE.write_text(html_out, encoding="utf-8")

    manifest = {
        "name": "Cochin Radio B — Espace Internes (Hiver 2026–2027)",
        "short_name": "Internes Radio B",
        "description": "Planning des vacations, espace personnel, congés, cas du mardi, biblio du vendredi et réunions du service de Radiologie B (Hôpital Cochin).",
        "start_url": "./index.html",
        "display": "standalone",
        "background_color": "#0B1120",
        "theme_color": "#0B1120",
        "icons": [
            {
                "src": "icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            }
        ],
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    sw_code = """const CACHE_NAME = 'cochin-internes-v1';
const ASSETS = ['./index.html', './manifest.json', './icon.svg'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
"""
    SW_FILE.write_text(sw_code, encoding="utf-8")

    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284C7"/>
      <stop offset="50%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#9333EA"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="56" fill="#0B1120"/>
  <rect x="16" y="16" width="224" height="224" rx="44" fill="url(#g)" opacity="0.22"/>
  <text x="128" y="118" text-anchor="middle" fill="#38BDF8" font-family="-apple-system, sans-serif" font-weight="800" font-size="52">RI·B</text>
  <text x="128" y="172" text-anchor="middle" fill="#F8FAFC" font-family="-apple-system, sans-serif" font-weight="700" font-size="28">INTERNES</text>
  <text x="128" y="206" text-anchor="middle" fill="#34D399" font-family="-apple-system, sans-serif" font-weight="600" font-size="18">COCHIN 26-27</text>
</svg>
"""
    ICON_FILE.write_text(svg_icon, encoding="utf-8")

    launcher_code = """#!/bin/zsh
cd "$(dirname "$0")"
open "./index.html"
"""
    LAUNCHER_FILE.write_text(launcher_code, encoding="utf-8")
    LAUNCHER_FILE.chmod(LAUNCHER_FILE.stat().st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    dataset = build_full_dataset()
    DATA_FILE.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    generate_pwa_files(dataset)
    print(f"Generated {INDEX_FILE} ({INDEX_FILE.stat().st_size} bytes) successfully with ZERO patient data!")
    try:
        res = sync_initial_state_to_cloud(dataset)
        print("Synced initial state to cloud:", res)
    except Exception as exc:
        print("Cloud sync warning:", exc)
