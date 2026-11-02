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
  <meta name="apple-mobile-web-app-status-bar-style" content="default" />
  <meta name="apple-mobile-web-app-title" content="Planning Radio B" />
  <meta name="application-name" content="Planning Radio B — Cochin" />
  <meta name="theme-color" content="#F8FAFC" />
  <link rel="manifest" href="manifest.json?v=3" />
  <link rel="icon" type="image/svg+xml" href="icon.svg?v=3" />
  <link rel="apple-touch-icon" href="icon.svg?v=3" />
  <title>Radio B Cochin — Planning Internes & Chefs</title>
  <style>
    :root {
      --bg: #F8FAFC;
      --bg-card: #FFFFFF;
      --bg-elevated: #F1F5F9;
      --border: #E2E8F0;
      --text: #0F172A;
      --text-muted: #64748B;
      --primary: #0284C7;
      --primary-dark: #0369A1;
      --tdm: #D97706;
      --irm: #7C3AED;
      --echo: #0D9488;
      --gestes: #E11D48;
      --cs: #2563EB;
      --off: #64748B;
      --vac: #16A34A;
      --rg: #DC2626;
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
      line-height: 1.4;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* En-tête épuré */
    .app-header {
      position: sticky;
      top: 0;
      z-index: 100;
      padding: calc(var(--safe-top) + 10px) 16px 10px;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }

    .header-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      max-width: 1120px;
      margin: 0 auto;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .brand-logo {
      width: 34px;
      height: 34px;
      border-radius: 9px;
      background: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 13px;
      color: #fff;
      flex-shrink: 0;
    }

    .brand-title {
      font-size: 15px;
      font-weight: 800;
      color: #0F172A;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .brand-sub {
      font-size: 11.5px;
      color: var(--text-muted);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    .btn {
      border: 1px solid #CBD5E1;
      background: #FFFFFF;
      color: #0F172A;
      padding: 8px 13px;
      border-radius: 9px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      text-decoration: none;
      transition: background 0.15s ease, border-color 0.15s ease;
    }

    .btn:hover {
      background: #F1F5F9;
      border-color: #94A3B8;
    }

    .btn-sm {
      padding: 5px 10px;
      font-size: 12px;
      border-radius: 7px;
    }

    .btn-primary {
      background: var(--primary);
      border-color: var(--primary);
      color: #FFFFFF;
      font-weight: 700;
    }
    .btn-primary:hover {
      background: var(--primary-dark);
      border-color: var(--primary-dark);
      color: #FFFFFF;
    }

    /* Barre de sélection simple (2 listes déroulantes ou boutons clairs) */
    .selector-bar {
      max-width: 1120px;
      margin: 10px auto 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }

    .person-chips {
      display: flex;
      align-items: center;
      gap: 5px;
      overflow-x: auto;
      padding-bottom: 2px;
      scrollbar-width: none;
      flex: 1;
    }
    .person-chips::-webkit-scrollbar { display: none; }

    .chip {
      border: 1px solid #CBD5E1;
      background: #FFFFFF;
      color: #334155;
      padding: 5px 11px;
      border-radius: 999px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .chip:hover {
      background: #F1F5F9;
    }

    .chip .dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .chip.active {
      background: #E0F2FE;
      color: #0369A1;
      border-color: #0284C7;
      font-weight: 700;
    }

    /* Conteneur principal */
    .container {
      max-width: 1120px;
      margin: 0 auto;
      padding: 12px 16px calc(var(--safe-bottom) + 80px);
    }

    /* Bandeau résumé compact */
    .summary-strip {
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 14px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .summary-left {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .avatar-sm {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 12px;
      color: #fff;
      flex-shrink: 0;
    }

    .summary-title {
      font-size: 14px;
      font-weight: 800;
      color: #0F172A;
    }

    .summary-sub {
      font-size: 12.5px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .summary-stats {
      display: flex;
      align-items: center;
      gap: 14px;
      font-size: 12.5px;
      color: var(--text-muted);
      flex-wrap: wrap;
    }

    .summary-stats strong {
      color: #0F172A;
      font-weight: 800;
    }

    /* Onglets principaux courts et lisibles */
    .main-tabs {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 4px;
      background: #E2E8F0;
      padding: 4px;
      border-radius: 11px;
      margin-bottom: 12px;
    }

    .tab-btn {
      border: none;
      background: transparent;
      color: #475569;
      padding: 8px 6px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s ease;
    }

    .tab-btn.active {
      background: #FFFFFF;
      color: #0F172A;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
    }

    /* Barre d'outils du planning */
    .planning-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }

    .segmented {
      display: inline-flex;
      background: #E2E8F0;
      border-radius: 9px;
      padding: 3px;
      gap: 2px;
    }

    .seg-btn {
      border: none;
      background: transparent;
      color: #475569;
      padding: 6px 11px;
      border-radius: 7px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
    }

    .seg-btn.active {
      background: #FFFFFF;
      color: #0F172A;
      font-weight: 700;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
    }

    .date-nav {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .date-label {
      font-size: 13.5px;
      font-weight: 800;
      min-width: 150px;
      text-align: center;
    }

    /* Jours de la semaine : Lun-Ven en grand + Sam/Dim en petit avec juste les gardes */
    .day-strip {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr)) repeat(2, minmax(0, 0.74fr));
      gap: 5px;
      margin-bottom: 10px;
      align-items: stretch;
    }

    .day-pill {
      padding: 6px 4px;
      border-radius: 9px;
      background: #FFFFFF;
      border: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 2px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 700;
      text-align: center;
      min-width: 0;
    }

    .day-pill .dp-top {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 3px;
      white-space: nowrap;
      line-height: 1.15;
    }

    .day-pill .dp-dow {
      font-weight: 800;
      color: #0F172A;
    }

    .day-pill .dp-date {
      font-weight: 700;
      color: #475569;
      font-size: 11px;
    }

    .day-pill .dp-sub {
      font-size: 9.5px;
      font-weight: 700;
      color: #64748B;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
      line-height: 1.1;
    }

    .day-pill.weekend-pill {
      padding: 4px 2px;
      background: #FFF5F5;
      border: 1px dashed #FCA5A5;
      border-radius: 8px;
    }

    .day-pill.weekend-pill .dp-dow {
      font-size: 9.5px;
      color: #991B1B;
      text-transform: uppercase;
    }

    .day-pill.weekend-pill .dp-date {
      font-size: 9px;
      color: #B91C1C;
    }

    .day-pill.weekend-pill .dp-garde {
      font-size: 9.5px;
      font-weight: 800;
      color: #B91C1C;
      background: #FEE2E2;
      border-radius: 4px;
      padding: 1px 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
      line-height: 1.15;
    }

    .day-pill.active {
      background: #E0F2FE;
      border-color: var(--primary);
      border-style: solid;
      color: #0369A1;
      box-shadow: 0 0 0 1px var(--primary);
    }

    .day-pill.active .dp-dow,
    .day-pill.active .dp-date {
      color: #0369A1;
    }

    /* Bandeau compact Samedi & Dimanche (Gardes uniquement) */
    .weekend-gardes-compact {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      padding: 7px 10px;
      background: #FFF5F5;
      border-top: 1px dashed #FCA5A5;
    }

    .weekend-garde-mini {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 7px;
      background: #FFFFFF;
      border: 1px solid #FECACA;
      font-size: 11px;
      cursor: pointer;
      min-width: 0;
    }

    .weekend-garde-mini .wg-day {
      font-weight: 800;
      color: #7F1D1D;
      font-size: 10.5px;
      white-space: nowrap;
    }

    .weekend-garde-mini .wg-doc {
      font-weight: 800;
      color: #B91C1C;
      background: #FEE2E2;
      padding: 1px 6px;
      border-radius: 5px;
      font-size: 10.5px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Grille 5 colonnes Lun-Ven pour Mon Planning */
    .perso-week-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
    }

    /* Badges de postes */
    .poste-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .poste-tdm { background: #FEF3C7; color: #B45309; border-color: #FCD34D; }
    .poste-irm { background: #F3E8FF; color: #6D28D9; border-color: #D8B4FE; }
    .poste-echo { background: #CCFBF1; color: #0F766E; border-color: #5EEAD4; }
    .poste-gestes { background: #FFE4E6; color: #BE123C; border-color: #FDA4AF; }
    .poste-cs { background: #DBEAFE; color: #1D4ED8; border-color: #93C5FD; }
    .poste-off { background: #F1F5F9; color: #475569; border-color: #CBD5E1; }
    .poste-vac { background: #DCFCE7; color: #15803D; border-color: #86EFAC; }
    .poste-rg { background: #FEE2E2; color: #B91C1C; border-color: #FCA5A5; }
    .poste-closed {
      background: #FEF2F2;
      color: #B91C1C;
      border: 1px dashed #EF4444;
      font-weight: 700;
    }

    .tag-sm {
      display: inline-block;
      padding: 1px 5px;
      border-radius: 4px;
      font-size: 9.5px;
      font-weight: 800;
      background: #EDE9FE;
      color: #6D28D9;
      text-transform: uppercase;
    }

    .tag-dj {
      display: inline-block;
      padding: 1px 5px;
      border-radius: 4px;
      font-size: 9.5px;
      font-weight: 800;
      background: #DCFCE7;
      color: #15803D;
      border: 1px solid #86EFAC;
      text-transform: uppercase;
    }

    .pres-type-switcher {
      display: inline-flex;
      background: #F1F5F9;
      border: 1px solid #CBD5E1;
      border-radius: 7px;
      padding: 2px;
      gap: 2px;
      margin-top: 4px;
    }

    .pres-type-btn {
      border: none;
      background: transparent;
      color: #475569;
      padding: 3px 7px;
      border-radius: 5px;
      font-size: 10.5px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.12s ease;
    }

    .pres-type-btn:hover {
      background: #E2E8F0;
      color: #0F172A;
    }

    .pres-type-btn.active-cas {
      background: #F3E8FF;
      color: #6D28D9;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }

    .pres-type-btn.active-biblio {
      background: #FEF3C7;
      color: #B45309;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }

    .pres-type-btn.active-cours {
      background: #DBEAFE;
      color: #1D4ED8;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }

    .tag-binome {
      display: inline-block;
      padding: 1px 5px;
      border-radius: 4px;
      font-size: 9.5px;
      font-weight: 700;
      background: #FEF3C7;
      color: #B45309;
    }

    /* Cartes & Tableaux */
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 12px;
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }

    .card-title {
      font-size: 14px;
      font-weight: 800;
      color: #0F172A;
    }

    .week-table-wrap {
      overflow-x: auto;
      border-radius: 10px;
      border: 1px solid var(--border);
    }

    table.planning-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 640px;
      background: #FFFFFF;
    }

    table.planning-table.week-5col {
      table-layout: fixed;
      min-width: 0;
      width: 100%;
    }

    table.planning-table.week-5col th.col-poste {
      width: 140px;
    }

    table.planning-table th,
    table.planning-table td {
      border-bottom: 1px solid var(--border);
      border-right: 1px solid var(--border);
      padding: 7px 9px;
      text-align: left;
      vertical-align: top;
      font-size: 12px;
    }

    table.planning-table th {
      background: #F8FAFC;
      color: #475569;
      font-weight: 700;
      font-size: 11px;
      text-transform: uppercase;
    }

    table.planning-table tr.period-divider td {
      background: #F1F5F9;
      color: #0F172A;
      font-weight: 800;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding: 5px 10px;
    }

    .interne-badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 3px 7px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 600;
      margin: 2px 3px 2px 0;
      background: #F8FAFC;
      color: #0F172A;
      border: 1px solid #CBD5E1;
      cursor: pointer;
    }
    .interne-badge:hover {
      background: #E2E8F0;
    }

    .interne-badge.highlight-me {
      background: #E0F2FE;
      color: #0369A1;
      border-color: var(--primary);
      font-weight: 800;
    }

    /* Grille mois */
    .month-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
    }

    /* ADAPTATION MOBILE : Semaine Lun-Ven entière à l'écran + Sam/Dim en petit avec juste les gardes */
    @media (max-width: 768px) {
      .container {
        padding: 8px 6px calc(var(--safe-bottom) + 74px);
      }
      .top-header {
        padding: 8px 10px;
      }
      .brand-title {
        font-size: 13.5px;
      }
      .brand-sub {
        font-size: 10.5px;
      }
      .summary-strip {
        padding: 8px 10px;
        gap: 8px;
      }
      .main-tabs {
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 2px;
        padding: 3px;
      }
      .tab-btn {
        font-size: 11px;
        padding: 6px 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .planning-toolbar {
        gap: 5px;
      }
      .seg-btn {
        padding: 5px 7px;
        font-size: 11px;
      }
      .date-label {
        font-size: 12px;
        min-width: 115px;
      }
      .day-strip {
        grid-template-columns: repeat(5, minmax(0, 1fr)) repeat(2, minmax(0, 0.72fr));
        gap: 3px;
        margin-bottom: 8px;
      }
      .day-pill {
        padding: 4px 2px;
        border-radius: 7px;
        font-size: 10.5px;
      }
      .day-pill .dp-top {
        flex-direction: column;
        gap: 0px;
      }
      .day-pill .dp-dow {
        font-size: 10px;
      }
      .day-pill .dp-date {
        font-size: 9.5px;
      }
      .day-pill .dp-sub {
        font-size: 8px;
      }
      .day-pill.weekend-pill {
        padding: 3px 1px;
      }
      .day-pill.weekend-pill .dp-dow {
        font-size: 8.5px;
      }
      .day-pill.weekend-pill .dp-date {
        font-size: 8px;
      }
      .day-pill.weekend-pill .dp-garde {
        font-size: 8px;
        padding: 1px 2px;
      }
      table.planning-table.week-5col th.col-poste {
        width: 58px;
      }
      table.planning-table.week-5col th,
      table.planning-table.week-5col td {
        padding: 4px 2.5px;
        font-size: 9.5px;
        word-break: break-word;
      }
      table.planning-table.week-5col th {
        font-size: 9.5px;
        text-align: center;
      }
      table.planning-table.week-5col tr.period-divider td {
        font-size: 9.5px;
        padding: 4px 6px;
      }
      table.planning-table.week-5col .poste-pill {
        font-size: 8.5px;
        padding: 2px 3.5px;
        white-space: normal;
        line-height: 1.1;
      }
      table.planning-table.week-5col .poste-horaire-sub {
        font-size: 7.5px !important;
        line-height: 1.05;
      }
      table.planning-table.week-5col .interne-badge {
        font-size: 9px;
        padding: 1.5px 3px;
        gap: 2.5px;
        margin: 1px 1px 1px 0;
        max-width: 100%;
        white-space: normal;
        line-height: 1.1;
      }
      table.planning-table.week-5col .interne-badge .tag-sm,
      table.planning-table.week-5col .interne-badge .tag-dj,
      table.planning-table.week-5col .interne-badge .tag-binome {
        font-size: 7.5px;
        padding: 0px 2.5px;
      }
      .perso-week-grid {
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 3px;
      }
      .perso-week-grid .perso-day-card {
        padding: 5px 3px !important;
        border-radius: 8px !important;
      }
      .perso-week-grid .perso-day-card .poste-pill {
        font-size: 8.5px !important;
        padding: 2px 3px !important;
        white-space: normal !important;
        line-height: 1.1 !important;
      }
      .weekend-gardes-compact {
        padding: 5px 6px;
        gap: 4px;
      }
      .weekend-garde-mini {
        padding: 3px 6px;
        font-size: 9.5px;
      }
      .weekend-garde-mini .wg-day,
      .weekend-garde-mini .wg-doc {
        font-size: 9.5px;
      }
      .month-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .month-cell {
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px;
      min-height: 92px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      cursor: pointer;
    }

    .month-cell:hover {
      border-color: var(--primary);
    }

    .month-cell.today {
      border-color: var(--primary);
      background: #F0F9FF;
    }

    /* Modales */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.45);
      backdrop-filter: blur(3px);
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
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 14px;
      width: 100%;
      max-width: 480px;
      max-height: 90vh;
      overflow-y: auto;
      padding: 16px;
      box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
    }

    .action-choice-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }

    .choice-btn {
      border: 1px solid var(--border);
      background: #F8FAFC;
      border-radius: 10px;
      padding: 12px 10px;
      text-align: left;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .choice-btn:hover {
      background: #E0F2FE;
      border-color: var(--primary);
    }

    .choice-btn strong {
      display: block;
      font-size: 13px;
      color: #0F172A;
      margin-bottom: 2px;
    }

    .choice-btn span {
      font-size: 11.5px;
      color: var(--text-muted);
    }

    .form-group {
      margin-bottom: 10px;
    }

    .form-group label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 4px;
    }

    .form-control {
      width: 100%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid #CBD5E1;
      background: #F8FAFC;
      color: #0F172A;
      font-size: 13px;
      font-family: inherit;
    }

    .note-box {
      padding: 8px 11px;
      border-radius: 8px;
      font-size: 12px;
      margin-bottom: 10px;
      background: #F1F5F9;
      color: #334155;
      border: 1px solid #CBD5E1;
    }

    .toast {
      position: fixed;
      bottom: calc(var(--safe-bottom) + 18px);
      left: 50%;
      transform: translateX(-50%);
      background: #0F172A;
      color: #FFFFFF;
      font-weight: 700;
      font-size: 12.5px;
      padding: 8px 16px;
      border-radius: 999px;
      z-index: 400;
      display: none;
    }

    /* Mode Chef de Planning & Drag and Drop */
    .btn-chef-lock {
      border-color: #CBD5E1;
      background: #F8FAFC;
      color: #334155;
    }
    .btn-chef-lock.unlocked {
      background: #FEF3C7;
      border-color: #F59E0B;
      color: #92400E;
      font-weight: 800;
      box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
    }

    .chef-mode-banner {
      background: linear-gradient(90deg, #FEF3C7 0%, #FFFBEB 100%);
      border: 1.5px solid #F59E0B;
      border-radius: 12px;
      padding: 10px 14px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .chef-mode-title {
      font-size: 13.5px;
      font-weight: 800;
      color: #92400E;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .chef-mode-sub {
      font-size: 12px;
      color: #B45309;
      margin-top: 2px;
    }

    .chef-mode-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .interne-badge.draggable-interne {
      cursor: grab;
      border: 1.5px solid #94A3B8;
      background: #FFFFFF;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
      user-select: none;
      -webkit-user-select: none;
      transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
    }
    .interne-badge.draggable-interne:hover {
      border-color: var(--primary);
      background: #F0F9FF;
      transform: translateY(-1px);
      box-shadow: 0 3px 6px rgba(2, 132, 199, 0.16);
    }
    .interne-badge.draggable-interne:active {
      cursor: grabbing;
    }
    .interne-badge.dragging {
      opacity: 0.45;
      transform: scale(0.96);
      border-style: dashed;
    }
    .interne-badge.selected-for-move {
      background: #FEF3C7 !important;
      border: 2px solid #D97706 !important;
      color: #92400E !important;
      box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.28);
      font-weight: 800;
    }

    .drag-grip {
      font-size: 11px;
      color: #64748B;
      margin-right: 1px;
      letter-spacing: -1px;
      font-weight: 900;
    }

    td.drop-zone-cell {
      transition: background 0.12s ease, outline 0.12s ease;
      position: relative;
      min-height: 38px;
    }
    td.drop-zone-cell.drag-over {
      background: #E0F2FE !important;
      outline: 2px dashed #0284C7;
      outline-offset: -2px;
    }
    td.drop-zone-cell.tap-target-ready {
      cursor: pointer;
    }
    td.drop-zone-cell.tap-target-ready:hover {
      background: #FEF3C7 !important;
      outline: 1.5px dashed #D97706;
      outline-offset: -2px;
    }
  </style>
</head>
<body>

  <header class="app-header">
    <div class="header-top">
      <div class="brand">
        <div class="brand-logo">RB</div>
        <div>
          <div class="brand-title">Radio B Cochin</div>
          <div class="brand-sub">Hiver 2026–2027 • Sans donnée patient</div>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-sm btn-chef-lock" onclick="toggleChefPlanningMode()" id="chefModeBtn" title="Mode Chef de Planning (code requis)">
          <span id="chefModeBtnText">🔒 Mode Chef</span>
        </button>
        <button class="btn btn-sm" onclick="syncWithCloud(true)" id="syncBtn">
          <span id="syncStatusText">Synchroniser</span>
        </button>
        <button class="btn btn-primary" onclick="openQuickAddModal()">
          + Ajouter
        </button>
      </div>
    </div>

    <!-- Sélection rapide de la personne -->
    <div class="selector-bar" id="interneSelectorBar"></div>
  </header>

  <main class="container">
    <!-- Bandeau Mode Chef de Planning (visible uniquement quand déverrouillé) -->
    <div id="chefPlanningBanner" style="display:none;"></div>

    <!-- Bandeau résumé sur 1 ligne -->
    <section class="summary-strip" id="personalBanner"></section>

    <!-- 5 Onglets au texte court et sans icône -->
    <nav class="main-tabs">
      <button class="tab-btn active" data-tab="planning" onclick="switchTab('planning')">Planning</button>
      <button class="tab-btn" data-tab="vacances" onclick="switchTab('vacances')">Congés</button>
      <button class="tab-btn" data-tab="presentations" onclick="switchTab('presentations')">Cours & Cas</button>
      <button class="tab-btn" data-tab="reunions" onclick="switchTab('reunions')">Réunions</button>
      <button class="tab-btn" data-tab="annuaire" onclick="switchTab('annuaire')">Annuaire</button>
    </nav>

    <!-- Contenu de l'onglet -->
    <div id="tabContent"></div>
  </main>

  <!-- Modal : Déverrouillage Mode Chef de Planning (code cocochin) -->
  <div class="modal-backdrop" id="modalChefAuth">
    <div class="modal-box" style="max-width:400px;">
      <div class="card-header">
        <div class="card-title">🔓 Mode Chef de Planning</div>
        <button class="btn btn-sm" onclick="closeModal('modalChefAuth')">Fermer</button>
      </div>
      <div class="note-box">
        Entrez le code d'accès Chef de Planning pour activer le déplacement direct des internes par glisser-déposer (Drag & Drop).
      </div>
      <div class="form-group">
        <label>Code d'accès</label>
        <input
          type="password"
          id="chefCodeInput"
          class="form-control"
          placeholder="Code chef de planning..."
          autocomplete="off"
          onkeydown="if(event.key==='Enter') submitChefAuth()"
        />
      </div>
      <div id="chefCodeError" class="note-box" style="display:none; background:#FEE2E2; border-color:#FCA5A5; color:#B91C1C; font-weight:700;">
        Code incorrect. Veuillez réessayer.
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
        <button class="btn" onclick="closeModal('modalChefAuth')">Annuler</button>
        <button class="btn btn-primary" onclick="submitChefAuth()">Déverrouiller</button>
      </div>
    </div>
  </div>

  <!-- Menu unique "+ Ajouter" regroupant toutes les actions -->
  <div class="modal-backdrop" id="modalQuickAdd">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">Que souhaitez-vous ajouter ?</div>
        <button class="btn btn-sm" onclick="closeModal('modalQuickAdd')">Fermer</button>
      </div>
      <div class="action-choice-grid">
        <button class="choice-btn" onclick="closeModal('modalQuickAdd'); openAbsenceModal();">
          <strong>Poser un congé / RG</strong>
          <span>Vacances, formation ou repos de garde</span>
        </button>
        <button class="choice-btn" onclick="closeModal('modalQuickAdd'); openNextPresentationModal();">
          <strong>S'inscrire à un cours</strong>
          <span>Cas du mardi ou biblio du vendredi</span>
        </button>
        <button class="choice-btn" onclick="closeModal('modalQuickAdd'); openQuickVacationPicker();">
          <strong>Échanger un poste</strong>
          <span>Modifier une demi-journée du planning</span>
        </button>
        <button class="choice-btn" onclick="closeModal('modalQuickAdd'); openMeetingModal();">
          <strong>Ajouter une réunion</strong>
          <span>Staff ou information du service</span>
        </button>
        <button class="choice-btn" onclick="closeModal('modalQuickAdd'); openPhoneContactModal();">
          <strong>Ajouter un numéro à l'annuaire</strong>
          <span>Poste interne Cochin, DECT ou secrétariat</span>
        </button>
        <button class="choice-btn" style="background:#FFFBEB; border-color:#FCD34D;" onclick="closeModal('modalQuickAdd'); toggleChefPlanningMode();">
          <strong style="color:#92400E;">🔓 Mode Chef de Planning</strong>
          <span>Glisser-déposer les internes (code requis)</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Modal : Poser un congé / RG -->
  <div class="modal-backdrop" id="modalAbsence">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">Poser un congé ou repos de garde</div>
        <button class="btn btn-sm" onclick="closeModal('modalAbsence')">Fermer</button>
      </div>
      <div class="note-box">
        Règle : max 2 internes absents en même temps. Éviter mardi/vendredi pour les jours isolés.
      </div>
      <div class="form-group">
        <label>Interne</label>
        <select id="absInterneSelect" class="form-control"></select>
      </div>
      <div class="form-group">
        <label>Motif</label>
        <select id="absTypeSelect" class="form-control">
          <option value="CA 1">Congés Annuels (CA 1)</option>
          <option value="CA 2">Congés Annuels (CA 2)</option>
          <option value="CF">Congé Formation / Congrès (CF)</option>
          <option value="Repos de garde">Repos de garde (RG)</option>
          <option value="Autre">Autre absence</option>
        </select>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Début</label>
          <input type="date" id="absStartDate" class="form-control" min="2026-11-02" max="2027-05-02" />
        </div>
        <div class="form-group">
          <label>Fin (incluse)</label>
          <input type="date" id="absEndDate" class="form-control" min="2026-11-02" max="2027-05-02" />
        </div>
      </div>
      <div class="form-group">
        <label>Note (optionnel)</label>
        <input type="text" id="absComment" class="form-control" placeholder="Ex: Garde du dimanche, JFR..." />
      </div>
      <div id="absRuleWarning" class="note-box" style="display:none;"></div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
        <button class="btn" onclick="closeModal('modalAbsence')">Annuler</button>
        <button class="btn btn-primary" onclick="saveAbsenceForm()">Enregistrer</button>
      </div>
    </div>
  </div>

  <!-- Modal : Cours Mardi / Vendredi -->
  <div class="modal-backdrop" id="modalPresentation">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title" id="presModalTitle">Présentation Mardi / Vendredi</div>
        <button class="btn btn-sm" onclick="closeModal('modalPresentation')">Fermer</button>
      </div>
      <div class="note-box">
        Indiquez uniquement la pathologie, le thème du cours ou le titre de l'article (aucun nom de patient).
      </div>
      <input type="hidden" id="presIdInput" />
      <input type="hidden" id="presTypeInput" value="cas_mardi" />
      <div class="form-group">
        <label>Date</label>
        <select id="presDateSelect" class="form-control" onchange="onPresDateChange(this.value)"></select>
        <input type="text" id="presDateDisplay" class="form-control" readonly style="display:none;" />
      </div>
      <div class="form-group" id="presTypeGroup">
        <label>Format de la séance</label>
        <div class="segmented" style="width:100%; display:grid; grid-template-columns:repeat(3, 1fr);">
          <button type="button" class="seg-btn" id="modalTypeBtnBiblio" onclick="setModalPresType('biblio_vendredi')">Biblio</button>
          <button type="button" class="seg-btn" id="modalTypeBtnCas" onclick="setModalPresType('cas_mardi')">Cas</button>
          <button type="button" class="seg-btn" id="modalTypeBtnCours" onclick="setModalPresType('cours_internes')">Cours aux internes</button>
        </div>
      </div>
      <div class="form-group">
        <label>Interne / DJ</label>
        <select id="presInterneSelect" class="form-control"></select>
      </div>
      <div class="form-group">
        <label>Sujet (cas, article biblio ou cours aux internes)</label>
        <textarea id="presSujetInput" class="form-control" rows="2" placeholder="Ex: Tumeur cartilagineuse en IRM..."></textarea>
      </div>
      <div class="form-group">
        <label>Cours du Chef / Intervenant associé</label>
        <input type="text" id="presChefInput" class="form-control" placeholder="Ex: Dr T. Lefèvre — PTH" />
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
        <button class="btn" onclick="closeModal('modalPresentation')">Annuler</button>
        <button class="btn btn-primary" onclick="savePresentationForm()">Enregistrer</button>
      </div>
    </div>
  </div>

  <!-- Modal : Modifier / Échanger un poste -->
  <div class="modal-backdrop" id="modalVacationEdit">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">Modifier un poste</div>
        <button class="btn btn-sm" onclick="closeModal('modalVacationEdit')">Fermer</button>
      </div>
      <div class="note-box">
        Règle : 2 demi-offs (1/2 journée libre) par semaine maximum par interne.
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Date</label>
          <input type="date" id="vacEditDate" class="form-control" onchange="refreshVacationModalFields()" />
        </div>
        <div class="form-group">
          <label>Interne</label>
          <select id="vacEditInterneId" class="form-control" onchange="refreshVacationModalFields()"></select>
        </div>
      </div>
      <input type="hidden" id="vacEditHeader" />
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Matin</label>
          <select id="vacEditAm" class="form-control"></select>
        </div>
        <div class="form-group">
          <label>Après-midi</label>
          <select id="vacEditPm" class="form-control"></select>
        </div>
      </div>
      <div class="form-group">
        <label>Note</label>
        <input type="text" id="vacEditNote" class="form-control" placeholder="Ex: Échange avec Noé..." />
      </div>
      <div style="display:flex; justify-content:space-between; gap:8px; margin-top:12px;">
        <button class="btn btn-sm" onclick="resetSingleVacation()">Par défaut</button>
        <div style="display:flex; gap:8px;">
          <button class="btn" onclick="closeModal('modalVacationEdit')">Annuler</button>
          <button class="btn btn-primary" onclick="saveSingleVacation()">Valider</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal : Ajouter une réunion -->
  <div class="modal-backdrop" id="modalMeeting">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">Nouvelle réunion</div>
        <button class="btn btn-sm" onclick="closeModal('modalMeeting')">Fermer</button>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Date</label>
          <input type="date" id="meetDate" class="form-control" value="2026-11-04" />
        </div>
        <div class="form-group">
          <label>Horaire</label>
          <input type="text" id="meetHoraire" class="form-control" placeholder="17h00 – 18h00" />
        </div>
      </div>
      <div class="form-group">
        <label>Titre</label>
        <input type="text" id="meetTitle" class="form-control" placeholder="Ex: Réunion Internes / Chefs" />
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Organisateur</label>
          <input type="text" id="meetSender" class="form-control" value="Anne-Marie FORTIN" />
        </div>
        <div class="form-group">
          <label>Salle</label>
          <input type="text" id="meetLocation" class="form-control" value="Salle de Staff Radio B" />
        </div>
      </div>
      <div class="form-group">
        <label>Détails</label>
        <textarea id="meetDesc" class="form-control" rows="2"></textarea>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
        <button class="btn" onclick="closeModal('modalMeeting')">Annuler</button>
        <button class="btn btn-primary" onclick="saveMeetingForm()">Enregistrer</button>
      </div>
    </div>
  </div>

  <!-- Modal : Ajouter un numéro -->
  <div class="modal-backdrop" id="modalPhoneContact">
    <div class="modal-box">
      <div class="card-header">
        <div class="card-title">Nouveau numéro Cochin</div>
        <button class="btn btn-sm" onclick="closeModal('modalPhoneContact')">Fermer</button>
      </div>
      <div class="form-group">
        <label>Catégorie</label>
        <select id="phoneCatInput" class="form-control">
          <option value="Radiologie B — Secrétariats & Consoles">Radio B — Secrétariats & Consoles</option>
          <option value="Radiologie B — Équipe Médicale (Chefs & Seniors)">Radio B — Médecins</option>
          <option value="Services Partenaires (Ortho, Rhumato, Anesth, Anapath)">Services (Ortho, Rhumato, Anesth)</option>
          <option value="Laboratoires, Pharmacie & Administration (DAM)">Labos & Administration</option>
        </select>
      </div>
      <div class="form-group">
        <label>Nom / Console</label>
        <input type="text" id="phoneNameInput" class="form-control" placeholder="Ex: Console IRM 3T" />
      </div>
      <div class="form-group">
        <label>Précision</label>
        <input type="text" id="phoneRoleInput" class="form-control" placeholder="Ex: Manipulateurs IRM" />
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Poste à 5 chiffres / DECT</label>
          <input type="text" id="phonePosteInput" class="form-control" placeholder="Ex: 12483" />
        </div>
        <div class="form-group">
          <label>Ligne directe</label>
          <input type="text" id="phoneNumInput" class="form-control" placeholder="01 58 41 24 83" />
        </div>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
        <div class="form-group">
          <label>Localisation</label>
          <input type="text" id="phoneBldgInput" class="form-control" placeholder="Bâtiment Ollier" />
        </div>
        <div class="form-group">
          <label>Fax (optionnel)</label>
          <input type="text" id="phoneFaxInput" class="form-control" />
        </div>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
        <button class="btn" onclick="closeModal('modalPhoneContact')">Annuler</button>
        <button class="btn btn-primary" onclick="savePhoneContactForm()">Enregistrer</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toastBox">Enregistré</div>

  <script>
    const INITIAL_DATA = __INITIAL_DATA_JSON__;
    const WEBHOOK_URL = __WEBHOOK_URL_JSON__;
    const INTERNES_SHEET_ID = __INTERNES_SHEET_ID_JSON__;
    const CLOUD_PROP_KEY = __CLOUD_PROP_KEY_JSON__;
    const LOCAL_STORAGE_KEY = "cochin_internes_app_state_v2";
    const SELECTED_INTERNE_KEY = "cochin_internes_selected_id_v1";
    const CHEF_MODE_STORAGE_KEY = "cochin_chef_planning_unlocked_v1";
    const CHEF_SECRET_CODE = "cocochin";

    let STATE = loadInitialState();
    let currentTab = "planning";
    let selectedInterneId = localStorage.getItem(SELECTED_INTERNE_KEY) || "gabriel";
    let planningScope = "internes"; // 'internes' | 'perso' | 'chefs' | 'combined'
    let planningMode = "week";      // 'day' | 'week' | 'month'
    let currentDateIso = "2026-11-02";
    let presFilter = "all";
    let annuaireSearch = "";
    let annuaireCategory = "all";
    let showStatsTable = false;
    let isChefPlanningMode = sessionStorage.getItem(CHEF_MODE_STORAGE_KEY) === "1";
    let activeDragPayload = null;
    let selectedForMove = null; // { dIso, periodKey, interneId, fromPoste }
    let chefHistoryStack = [];

    function mergePresentationsList(baseList, savedList) {
      const obsoleteIds = new Set(["boneclub-2026-12-10", "cra-2027-01-29"]);
      const map = {};
      (baseList || []).forEach(p => { if (p && p.id) map[p.id] = Object.assign({}, p); });
      (savedList || []).forEach(p => {
        if (!p || !p.id || obsoleteIds.has(p.id)) return;
        if (map[p.id] && (p.type === "bone_club" || p.type === "confrontation_anapath")) {
          // Conserver les métadonnées officielles (horaire, salle, modérateurs) tout en gardant un éventuel sujet personnalisé
          if (p.sujet && p.sujet !== map[p.id].sujet) map[p.id].sujet = p.sujet;
          if (p.interneId) {
            map[p.id].interneId = p.interneId;
            map[p.id].interneName = p.interneName || map[p.id].interneName;
          }
        } else {
          map[p.id] = p;
        }
      });
      return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
    }

    function mergeMeetingsList(baseList, savedList) {
      const obsoleteTitles = new Set(["Bone Club — Novembre", "Bone Club — Janvier", "Confrontation Radio-Anatomo-Pathologique (Janvier)"]);
      const map = {};
      (baseList || []).forEach(m => { if (m && m.id) map[m.id] = Object.assign({}, m); });
      (savedList || []).forEach(m => {
        if (!m || !m.id || obsoleteTitles.has(m.title)) return;
        // Si l'ID existe dans baseList (ex: mtg-1..12), privilégier la définition officielle à jour
        if (!map[m.id]) map[m.id] = m;
      });
      return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
    }

    function loadInitialState() {
      const base = JSON.parse(JSON.stringify(INITIAL_DATA));
      try {
        const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (raw) {
          const saved = JSON.parse(raw);
          if (Array.isArray(saved.absences)) base.absences = saved.absences;
          if (saved.customVacations) base.customVacations = saved.customVacations;
          if (Array.isArray(saved.presentations) && saved.presentations.length > 0) {
            base.presentations = mergePresentationsList(base.presentations, saved.presentations);
          }
          if (Array.isArray(saved.meetings) && saved.meetings.length > 0) {
            base.meetings = mergeMeetingsList(base.meetings, saved.meetings);
          }
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
      window.__toastTimer = setTimeout(() => { el.style.display = "none"; }, 2500);
    }

    function getInterneById(iid) {
      return STATE.internes.find(x => x.id === iid) || STATE.internes[0];
    }

    function getPosteClass(poste) {
      const p = String(poste || "").toUpperCase();
      if (p.includes("FERMÉ") || p.includes("FERME") || p.includes("MAINTENANCE")) return "poste-closed";
      if (p.includes("VACANCES") || p.includes("CA") || p.includes("CF")) return "poste-vac";
      if (p === "RG" || p.includes("REPOS") || p.includes("GARDE") || p.includes("FÉRIÉ")) return "poste-rg";
      if (p.includes("LIBRE")) return "poste-off";
      if (p.includes("IRM")) return "poste-irm";
      if (p.includes("ECHO") || p.includes("ÉCHO")) return "poste-echo";
      if (p.includes("GESTES") || p.includes("ACHARD") || p.includes("ALLURA")) return "poste-gestes";
      if (p.includes("LECTURE") || p.includes("CS") || p.includes("CONSULT")) return "poste-cs";
      return "poste-tdm";
    }

    function getPosteHoraire(poste, periodKey) {
      const p = String(poste || "").toUpperCase();
      if (p.includes("IRM")) {
        return periodKey === "am" ? "dès 07h45" : (periodKey === "pm" ? "dès 07h45 (matin)" : "dès 07h45");
      }
      if (p.includes("ECHO") || p.includes("ÉCHO") || p.includes("GESTES")) {
        return periodKey === "am" ? "dès 09h00" : (periodKey === "pm" ? "dès 09h00 (matin)" : "dès 09h00");
      }
      if (p.includes("SAU") || p.includes("OLLIER 4")) {
        return periodKey === "am" ? "08h00 – 13h00" : (periodKey === "pm" ? "fin à 18h30" : "08h00 – 18h30");
      }
      return "";
    }

    function getPosteWithTimeLabel(poste, periodKey) {
      const shortName = poste === "1/2 journée libre" ? "Demi-off" : poste;
      const p = String(poste || "").toUpperCase();
      let h = "";
      if (p.includes("IRM")) h = periodKey === "am" ? "7h45" : "";
      else if (p.includes("ECHO") || p.includes("ÉCHO") || p.includes("GESTES")) h = periodKey === "am" ? "9h00" : "";
      else if (p.includes("SAU") || p.includes("OLLIER 4")) h = periodKey === "am" ? "dès 8h00" : (periodKey === "pm" ? "fin 18h30" : "8h00–18h30");
      return h ? `${shortName} <span style="opacity:0.85; font-weight:600; font-size:10px;">(${h})</span>` : shortName;
    }

    function renderPosteCellLabel(poste, periodKey) {
      let shortName = poste === "1/2 journée libre" ? "Demi-off" : poste;
      if (shortName === "TDM OLLIER DIAG") shortName = "TDM OLLIER";
      if (shortName === "TDM OLLIER 4 (SAU)") shortName = "TDM SAU";
      if (shortName === "TDM ACHARD 1") shortName = "ACHARD 1";
      if (shortName === "CONSULT / LECTURE") shortName = "CS / LECT.";
      const p = String(poste || "").toUpperCase();
      let h = "";
      if (p.includes("IRM")) h = periodKey === "am" ? "07h45" : "Mat. 07h45";
      else if (p.includes("ECHO") || p.includes("ÉCHO")) h = periodKey === "am" ? "09h00" : "Mat. 09h00";
      else if (p.includes("GESTES")) h = periodKey === "am" ? "09h00" : "Mat. 09h00";
      else if (p.includes("SAU") || p.includes("OLLIER 4")) h = periodKey === "am" ? "08h00–18h30" : "fin 18h30";
      else if (p.includes("LECTURE") || p.includes("CONSULT")) h = periodKey === "pm" ? "Mar : Pr Drapé • Ven : CS" : "";
      return `<div style="display:flex; flex-direction:column; align-items:flex-start; gap:1px;">
        <span class="poste-pill ${getPosteClass(poste)}">${shortName}</span>
        ${h ? `<span class="poste-horaire-sub" style="font-size:9.5px; font-weight:700; color:var(--text-muted); padding-left:1px;">🕒 ${h}</span>` : ""}
      </div>`;
    }

    function recomputeScheduleInPlace(st) {
      const baseSched = INITIAL_DATA.schedule;
      const absLookup = {};
      (st.absences || []).forEach(a => {
        if (a && a.date && a.interneId) absLookup[a.date + "__" + a.interneId] = a.type || "CA 1";
      });
      const custom = st.customVacations || {};
      const seniorIds = ["gabriel", "marwane", "milan", "nathanael", "oussama"];

      // 1. Appliquer customVacations et absences jour par jour
      const weeksMap = {};
      Object.keys(baseSched).sort().forEach(iso => {
        const dayObj = JSON.parse(JSON.stringify(baseSched[iso]));
        const [yy, mm, dd] = iso.split("-").map(Number);
        const dt = new Date(yy, mm - 1, dd);
        const jsDay = dt.getDay(); // 1=Mon, 2=Tue, ..., 5=Fri
        const monIso = getMondayOfWeek(iso);
        if (!weeksMap[monIso]) weeksMap[monIso] = [];
        weeksMap[monIso].push(iso);

        if (!dayObj.holiday && dayObj.byInterne) {
          Object.keys(dayObj.byInterne).forEach(iid => {
            const intObj = st.internes.find(x => x.id === iid);
            const origSlot = dayObj.byInterne[iid] || {};
            const cKey = iso + "__" + iid;
            let am = origSlot.am;
            let pm = origSlot.pm;
            let noteAm = origSlot.noteAm || "";
            let notePm = origSlot.notePm || "";
            let note = origSlot.note || noteAm || notePm || "";
            const isSocle = Boolean(origSlot.isSocle || (intObj && intObj.isSocle));

            if (custom[cKey]) {
              if (custom[cKey].am) am = custom[cKey].am;
              if (custom[cKey].pm) pm = custom[cKey].pm;
              if (custom[cKey].note !== undefined) {
                note = custom[cKey].note;
                noteAm = custom[cKey].note;
              }
            }

            if (absLookup[cKey]) {
              const at = absLookup[cKey];
              const badge = (at.toLowerCase().includes("garde") || at.toUpperCase() === "RG") ? "RG" : "VACANCES";
              am = badge;
              pm = badge;
              note = at;
              noteAm = at;
              notePm = at;
            }

            dayObj.byInterne[iid] = { am, pm, note, noteAm, notePm, isSocle };
          });

          // Garantie systématique : Relecture avec Pr Drapé le Mardi après-midi (jsDay === 2)
          if (jsDay === 2) {
            const hasTueCs = Object.keys(dayObj.byInterne).some(iid => dayObj.byInterne[iid].pm === "LECTURE/CS");
            if (!hasTueCs) {
              const donorPostes = ["ECHO", "GESTES (C)", "SCAN ACHARD"];
              let replaced = false;
              for (const dp of donorPostes) {
                for (const iid of seniorIds) {
                  const cKey = iso + "__" + iid;
                  if (dayObj.byInterne[iid] && dayObj.byInterne[iid].pm === dp && !(custom[cKey] && custom[cKey].pm)) {
                    dayObj.byInterne[iid].pm = "LECTURE/CS";
                    dayObj.byInterne[iid].notePm = "Relecture avec Pr Drapé (systématique)";
                    if (!dayObj.byInterne[iid].note) {
                      dayObj.byInterne[iid].note = "Relecture avec Pr Drapé (systématique)";
                    }
                    replaced = true;
                    break;
                  }
                }
                if (replaced) break;
              }
            }
          }
        }
        st.schedule[iso] = dayObj;
      });

      // 2. Garantie hebdomadaire : si les demi-offs ne sont pas suffisants (< 2 demi-offs / sem pour un interne présent),
      //    les autres créneaux ne sont pas obligatoires (hors TDM SAU et hors Relecture Pr Drapé du mardi PM)
      const nonMandatoryPriority = [
        "LECTURE/CS", // Vendredi PM uniquement (Mardi PM protégé)
        "ALLURA",
        "TDM OLLIER DIAG",
        "IRM 1,5T",
        "ECHO",
        "GESTES (C)",
        "SCAN ACHARD",
        "IRM 3T",
        "IRM"
      ];
      Object.keys(weeksMap).forEach(monIso => {
        const activeIsos = weeksMap[monIso].filter(dIso => st.schedule[dIso] && !st.schedule[dIso].holiday && st.schedule[dIso].byInterne);
        (st.internes || []).forEach(intObj => {
          const iid = intObj.id;
          let vacHalfDays = 0;
          let offCnt = 0;
          activeIsos.forEach(dIso => {
            const slot = st.schedule[dIso].byInterne[iid];
            if (!slot) return;
            ["am", "pm"].forEach(h => {
              if (slot[h] === "VACANCES" || slot[h] === "RG") vacHalfDays++;
              else if (slot[h] === "1/2 journée libre") offCnt++;
            });
          });
          if (vacHalfDays >= 6) return;
          while (offCnt < 2) {
            let freed = false;
            for (const candPoste of nonMandatoryPriority) {
              for (let i = activeIsos.length - 1; i >= 0; i--) {
                const dIso = activeIsos[i];
                const [yy, mm, dd] = dIso.split("-").map(Number);
                const jsDay = new Date(yy, mm - 1, dd).getDay();
                const cKey = dIso + "__" + iid;
                for (const h of ["pm", "am"]) {
                  // Ne jamais supprimer la Relecture systématique avec Pr Drapé du mardi après-midi
                  if (jsDay === 2 && h === "pm" && candPoste === "LECTURE/CS") continue;
                  // Respecter un choix manuel explicite dans customVacations
                  if (custom[cKey] && custom[cKey][h]) continue;
                  const slot = st.schedule[dIso].byInterne[iid];
                  if (slot && slot[h] === candPoste) {
                    const nk = h === "am" ? "noteAm" : "notePm";
                    slot[h] = "1/2 journée libre";
                    slot[nk] = "Créneau non obligatoire libéré (quota 2 demi-offs / sem)";
                    if (!slot.note) slot.note = slot[nk];
                    offCnt++;
                    freed = true;
                    break;
                  }
                }
                if (freed) break;
              }
              if (freed) break;
            }
            if (!freed) break;
          }
        });
      });

      // 3. Reconstruire dayObj.am, dayObj.pm et dayObj.slots
      Object.keys(st.schedule).forEach(iso => {
        const dayObj = st.schedule[iso];
        if (!dayObj || dayObj.holiday || !dayObj.byInterne) return;
        dayObj.am = [];
        dayObj.pm = [];
        Object.keys(dayObj.byInterne).forEach(iid => {
          const intObj = st.internes.find(x => x.id === iid);
          const slot = dayObj.byInterne[iid];
          const isSocle = Boolean(slot.isSocle || (intObj && intObj.isSocle));
          dayObj.am.push({
            poste: slot.am,
            interneId: iid,
            interne: intObj ? intObj.shortName : iid,
            isSocle,
            binome: isSocle && slot.am === "TDM SAU",
            note: slot.noteAm || ""
          });
          dayObj.pm.push({
            poste: slot.pm,
            interneId: iid,
            interne: intObj ? intObj.shortName : iid,
            isSocle,
            binome: isSocle && slot.pm === "TDM SAU",
            note: slot.notePm || ""
          });
        });
        (dayObj.closedAm || []).forEach(cl => {
          dayObj.am.push({
            poste: cl.poste,
            interneId: null,
            interne: cl.reason || cl.status || "FERMÉ",
            closed: true,
            reason: cl.reason || cl.status || "FERMÉ"
          });
        });
        (dayObj.closedPm || []).forEach(cl => {
          dayObj.pm.push({
            poste: cl.poste,
            interneId: null,
            interne: cl.reason || cl.status || "FERMÉ",
            closed: true,
            reason: cl.reason || cl.status || "FERMÉ"
          });
        });
        dayObj.slots = dayObj.byInterne;
      });
    }

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
          coursInternes: 0,
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
          if (pr.type === "cours_internes") stats[pr.interneId].coursInternes++;
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

    function formatShortDayHeader(iso) {
      if (!iso) return "";
      const [y, m, d] = iso.split("-").map(Number);
      const dt = new Date(y, m - 1, d);
      const days = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
      const dd = String(d).padStart(2, "0");
      const mm = String(m).padStart(2, "0");
      return `${days[dt.getDay()]} ${dd}/${mm}`;
    }

    function getMondayOfWeek(iso) {
      const [y, m, d] = iso.split("-").map(Number);
      const dt = new Date(y, m - 1, d, 12, 0, 0);
      const day = dt.getDay();
      const diff = (day === 0 ? -6 : 1 - day);
      dt.setDate(dt.getDate() + diff);
      const yy = dt.getFullYear();
      const mm = String(dt.getMonth() + 1).padStart(2, "0");
      const dd = String(dt.getDate()).padStart(2, "0");
      return `${yy}-${mm}-${dd}`;
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

    function isChefId(id) {
      return String(id || "").startsWith("chef_");
    }

    function getChefById(cid) {
      const list = STATE.chefs || [];
      return list.find(c => c.id === cid) || list[0] || {
        id: "chef_tl", code: "TL", prenom: "Thomas", nom: "LEFÈVRE",
        fullName: "Dr Thomas LEFÈVRE", shortName: "Dr T. Lefèvre",
        initials: "TL", color: "#0284C7", role: "Chef de Clinique"
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
      Object.keys(STATE.chefsPlanning || {}).forEach(iso => {
        const sl = getChefSlotsForDate(iso, chef);
        if (sl.am.length > 0) totalHalfDays++;
        if (sl.pm.length > 0) totalHalfDays++;
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
      return { totalHalfDays, gardesCount, coursMardiCount };
    }

    /* =========================================================================
     * MODE CHEF DE PLANNING (CODE: cocochin) & DRAG-AND-DROP DES INTERNES
     * ========================================================================= */
    function toggleChefPlanningMode() {
      if (isChefPlanningMode) {
        isChefPlanningMode = false;
        selectedForMove = null;
        activeDragPayload = null;
        sessionStorage.removeItem(CHEF_MODE_STORAGE_KEY);
        renderAll();
        showToast("Mode Chef de Planning verrouillé");
      } else {
        const inp = document.getElementById("chefCodeInput");
        const err = document.getElementById("chefCodeError");
        if (inp) inp.value = "";
        if (err) err.style.display = "none";
        document.getElementById("modalChefAuth").classList.add("open");
        setTimeout(() => { if (inp) inp.focus(); }, 60);
      }
    }

    function submitChefAuth() {
      const inp = document.getElementById("chefCodeInput");
      const err = document.getElementById("chefCodeError");
      const val = String((inp && inp.value) || "").trim().toLowerCase();
      if (val === CHEF_SECRET_CODE) {
        isChefPlanningMode = true;
        selectedForMove = null;
        sessionStorage.setItem(CHEF_MODE_STORAGE_KEY, "1");
        closeModal("modalChefAuth");
        currentTab = "planning";
        if (planningScope === "chefs" || planningScope === "perso") {
          planningScope = "internes";
        }
        renderAll();
        showToast("🔓 Mode Chef de Planning activé !");
      } else {
        if (err) err.style.display = "block";
        if (inp) inp.select();
      }
    }

    function renderChefModeUI() {
      const btn = document.getElementById("chefModeBtn");
      const btnTxt = document.getElementById("chefModeBtnText");
      const banner = document.getElementById("chefPlanningBanner");

      if (btn && btnTxt) {
        if (isChefPlanningMode) {
          btn.classList.add("unlocked");
          btnTxt.textContent = "🔓 Mode Chef actif";
        } else {
          btn.classList.remove("unlocked");
          btnTxt.textContent = "🔒 Mode Chef";
        }
      }

      if (!banner) return;
      if (!isChefPlanningMode) {
        banner.style.display = "none";
        banner.innerHTML = "";
        return;
      }

      const selInfo = selectedForMove
        ? `<span class="poste-pill poste-tdm">Sélectionné : ${getInterneById(selectedForMove.interneId).shortName} (${formatDateFr(selectedForMove.dIso)} • ${selectedForMove.periodKey === 'am' ? 'Matin' : 'PM'}) — Cliquez sur un autre interne ou poste pour déplacer/échanger</span>`
        : `Glissez-déposez un interne vers un autre poste (déplacement) ou sur un autre interne (échange automatique). Sur mobile/tablette : touchez un interne puis touchez la case cible.`;

      banner.style.display = "block";
      banner.innerHTML = `
        <div class="chef-mode-banner">
          <div>
            <div class="chef-mode-title">
              <span>🔓 Mode Chef de Planning — Édition directe par Drag & Drop</span>
            </div>
            <div class="chef-mode-sub">${selInfo}</div>
          </div>
          <div class="chef-mode-actions">
            ${selectedForMove ? `<button class="btn btn-sm" onclick="cancelSelectedForMove()">Annuler sélection</button>` : ""}
            ${chefHistoryStack.length > 0 ? `<button class="btn btn-sm" onclick="undoLastChefMove()">↩ Annuler (${chefHistoryStack.length})</button>` : ""}
            <button class="btn btn-sm" onclick="resetCurrentWeekVacations()" style="color:#B45309; border-color:#F59E0B;">Réinitialiser la semaine</button>
            <button class="btn btn-sm" onclick="toggleChefPlanningMode()" style="background:#92400E; color:#FFF; border-color:#92400E;">Verrouiller</button>
          </div>
        </div>
      `;
    }

    function cancelSelectedForMove() {
      selectedForMove = null;
      renderAll();
    }

    function pushChefHistorySnapshot() {
      chefHistoryStack.push(JSON.parse(JSON.stringify(STATE.customVacations || {})));
      if (chefHistoryStack.length > 30) chefHistoryStack.shift();
    }

    function undoLastChefMove() {
      if (!chefHistoryStack.length) return;
      STATE.customVacations = chefHistoryStack.pop();
      selectedForMove = null;
      saveStateLocal();
      renderAll();
      showToast("Modification annulée");
      pushStateToCloud({});
    }

    function resetCurrentWeekVacations() {
      const monIso = getMondayOfWeek(currentDateIso);
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      if (!STATE.customVacations) return;
      pushChefHistorySnapshot();
      days.forEach(dIso => {
        STATE.internes.forEach(i => {
          delete STATE.customVacations[dIso + "__" + i.id];
        });
      });
      selectedForMove = null;
      saveStateLocal();
      renderAll();
      showToast("Semaine réinitialisée par défaut");
      pushStateToCloud({});
    }

    function applyInterneSlotChange(dIso, periodKey, interneId, newPoste, customNote) {
      const dObj = STATE.schedule[dIso];
      if (!dObj || !dObj.byInterne || !dObj.byInterne[interneId]) return;
      const curSlot = dObj.byInterne[interneId];
      if (!STATE.customVacations) STATE.customVacations = {};
      const cKey = dIso + "__" + interneId;
      const existing = STATE.customVacations[cKey] || {
        am: curSlot.am,
        pm: curSlot.pm,
        note: curSlot.note || ""
      };
      existing[periodKey] = newPoste;
      if (customNote !== undefined) existing.note = customNote;
      STATE.customVacations[cKey] = existing;
    }

    function executeChefMoveOrSwap(source, target) {
      // source: { dIso, periodKey, interneId, fromPoste }
      // target: { dIso, periodKey, toPoste, targetInterneId (optional) }
      if (!source || !target) return;

      const srcInterne = getInterneById(source.interneId);

      // Si on dépose directement sur un autre interne (ou si on échange deux internes, même jour ou autre jour)
      if (target.targetInterneId && (target.targetInterneId !== source.interneId || target.dIso !== source.dIso || target.periodKey !== source.periodKey)) {
        const tgtInterne = getInterneById(target.targetInterneId);
        const srcDayObj = STATE.schedule[source.dIso];
        const tgtDayObj = STATE.schedule[target.dIso];
        const srcPoste = srcDayObj && srcDayObj.byInterne && srcDayObj.byInterne[source.interneId]
          ? srcDayObj.byInterne[source.interneId][source.periodKey]
          : source.fromPoste;
        const tgtPoste = tgtDayObj && tgtDayObj.byInterne && tgtDayObj.byInterne[target.targetInterneId]
          ? tgtDayObj.byInterne[target.targetInterneId][target.periodKey]
          : target.toPoste;

        pushChefHistorySnapshot();
        applyInterneSlotChange(source.dIso, source.periodKey, source.interneId, tgtPoste);
        applyInterneSlotChange(target.dIso, target.periodKey, target.targetInterneId, srcPoste);
        selectedForMove = null;
        saveStateLocal();
        renderAll();
        showToast(`🔄 Échange : ${srcInterne.shortName} (${tgtPoste}) ↔ ${tgtInterne.shortName} (${srcPoste})`);
        pushStateToCloud({});
        return;
      }

      if (source.dIso !== target.dIso || source.periodKey !== target.periodKey) {
        showToast("Pour changer de poste vers une case vide, déposez sur le même jour/demi-journée (ou sur un interne pour échanger).");
        return;
      }

      // Déplacement vers une ligne de poste
      if (!target.toPoste || target.toPoste === source.fromPoste) {
        selectedForMove = null;
        renderAll();
        return;
      }

      pushChefHistorySnapshot();
      applyInterneSlotChange(source.dIso, source.periodKey, source.interneId, target.toPoste);
      selectedForMove = null;
      saveStateLocal();
      renderAll();
      showToast(`✅ ${srcInterne.shortName} déplacé sur ${target.toPoste} (${source.periodKey === 'am' ? 'Matin' : 'PM'})`);
      pushStateToCloud({});
    }

    function onInterneDragStart(ev, dIso, periodKey, interneId, fromPoste) {
      if (!isChefPlanningMode) return;
      activeDragPayload = { dIso, periodKey, interneId, fromPoste };
      if (ev.dataTransfer) {
        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", JSON.stringify(activeDragPayload));
      }
      setTimeout(() => {
        if (ev.target && ev.target.classList) ev.target.classList.add("dragging");
      }, 0);
    }

    function onInterneDragEnd(ev) {
      if (ev.target && ev.target.classList) ev.target.classList.remove("dragging");
      document.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"));
    }

    function onCellDragOver(ev, dIso, periodKey) {
      if (!isChefPlanningMode || !activeDragPayload) return;
      ev.preventDefault();
      if (ev.dataTransfer) ev.dataTransfer.dropEffect = "move";
      const td = ev.currentTarget;
      if (td && !td.classList.contains("drag-over")) {
        td.classList.add("drag-over");
      }
    }

    function onCellDragLeave(ev) {
      const td = ev.currentTarget;
      if (td) td.classList.remove("drag-over");
    }

    function onCellDrop(ev, dIso, periodKey, toPoste) {
      if (!isChefPlanningMode) return;
      ev.preventDefault();
      ev.stopPropagation();
      const td = ev.currentTarget;
      if (td) td.classList.remove("drag-over");

      let payload = activeDragPayload;
      if (!payload && ev.dataTransfer) {
        try { payload = JSON.parse(ev.dataTransfer.getData("text/plain")); } catch (e) {}
      }
      activeDragPayload = null;
      if (!payload) return;

      executeChefMoveOrSwap(payload, { dIso, periodKey, toPoste });
    }

    function onBadgeDrop(ev, dIso, periodKey, targetInterneId, toPoste) {
      if (!isChefPlanningMode) return;
      ev.preventDefault();
      ev.stopPropagation();
      document.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"));

      let payload = activeDragPayload;
      if (!payload && ev.dataTransfer) {
        try { payload = JSON.parse(ev.dataTransfer.getData("text/plain")); } catch (e) {}
      }
      activeDragPayload = null;
      if (!payload) return;

      executeChefMoveOrSwap(payload, { dIso, periodKey, toPoste, targetInterneId });
    }

    function onInterneBadgeClick(ev, dIso, periodKey, interneId, posteName) {
      ev.stopPropagation();
      if (!isChefPlanningMode) {
        openVacationEditModal(dIso, interneId);
        return;
      }
      // En mode Chef de Planning : clic 1 sélectionne l'interne, clic 2 sur un autre interne les échange
      if (!selectedForMove) {
        selectedForMove = { dIso, periodKey, interneId, fromPoste: posteName };
        renderAll();
        return;
      }
      if (selectedForMove.interneId === interneId && selectedForMove.dIso === dIso && selectedForMove.periodKey === periodKey) {
        selectedForMove = null;
        renderAll();
        return;
      }
      executeChefMoveOrSwap(selectedForMove, {
        dIso,
        periodKey,
        toPoste: posteName,
        targetInterneId: interneId
      });
    }

    function onChefCellClick(ev, dIso, periodKey, toPoste) {
      if (!isChefPlanningMode || !selectedForMove) return;
      ev.stopPropagation();
      executeChefMoveOrSwap(selectedForMove, { dIso, periodKey, toPoste });
    }

    // Barre de sélection simplifiée
    function renderInterneSelector() {
      const bar = document.getElementById("interneSelectorBar");
      const inChefSpace = (selectedInterneId === "all_chefs" || isChefId(selectedInterneId));
      let html = `
        <div class="segmented">
          <button class="seg-btn ${!inChefSpace ? 'active' : ''}" onclick="switchRoleSpace('internes')">Internes</button>
          <button class="seg-btn ${inChefSpace ? 'active' : ''}" onclick="switchRoleSpace('chefs')">Chefs</button>
        </div>
        <div class="person-chips">
      `;

      if (!inChefSpace) {
        html += `<button class="chip ${selectedInterneId === 'all' ? 'active' : ''}" onclick="selectInterne('all')">Tous</button>`;
        STATE.internes.forEach(i => {
          const active = (selectedInterneId === i.id) ? "active" : "";
          const isDJ = Boolean(i.isDJ || i.id === "oussama");
          html += `
            <button class="chip ${active}" onclick="selectInterne('${i.id}')">
              <span class="dot" style="background:${i.color}"></span>
              <span>${i.shortName}</span>
              ${i.isSocle ? `<span class="tag-sm">Socle</span>` : ""}
              ${isDJ ? `<span class="tag-dj">DJ</span>` : ""}
            </button>
          `;
        });
      } else {
        html += `<button class="chip ${selectedInterneId === 'all_chefs' ? 'active' : ''}" onclick="selectInterne('all_chefs')">Tous</button>`;
        (STATE.chefs || []).forEach(c => {
          const active = (selectedInterneId === c.id) ? "active" : "";
          html += `
            <button class="chip ${active}" onclick="selectInterne('${c.id}')">
              <span class="dot" style="background:${c.color}"></span>
              <span>${c.code} · ${c.nom}</span>
            </button>
          `;
        });
      }

      html += `</div>`;
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

    // Bandeau résumé épuré sur une seule barre lisible
    function renderPersonalBanner() {
      const el = document.getElementById("personalBanner");

      if (selectedInterneId === "all_chefs") {
        el.innerHTML = `
          <div class="summary-left">
            <div class="avatar-sm" style="background:#0284C7">CH</div>
            <div>
              <div class="summary-title">Équipe Chefs & Seniors</div>
              <div class="summary-sub">${(STATE.chefs || []).length} médecins • Vacations, gardes et fermetures</div>
            </div>
          </div>
          <div class="summary-stats">
            <span><strong>6</strong> Internes / DJ</span>
            <span><strong>${STATE.presentations.filter(p => p.type === 'cas_mardi').length}</strong> Mardis</span>
          </div>
        `;
        return;
      }

      if (isChefId(selectedInterneId)) {
        const chef = getChefById(selectedInterneId);
        const cStats = computeChefStats(chef);
        const todaySlots = getChefSlotsForDate(currentDateIso, chef);
        const todayAmTxt = todaySlots.am.length ? todaySlots.am.join(" + ") : "Libre";
        const todayPmTxt = todaySlots.pm.length ? todaySlots.pm.join(" + ") : "Libre";
        const todayAmHtml = todaySlots.am.length ? todaySlots.am.map(p => getPosteWithTimeLabel(p, "am")).join(" + ") : "Libre";
        const todayPmHtml = todaySlots.pm.length ? todaySlots.pm.map(p => getPosteWithTimeLabel(p, "pm")).join(" + ") : "Libre";

        el.innerHTML = `
          <div class="summary-left">
            <div class="avatar-sm" style="background:${chef.color}">${chef.initials}</div>
            <div>
              <div class="summary-title">${chef.fullName}</div>
              <div class="summary-sub">
                <span>${formatDateFr(currentDateIso)} :</span>
                <span class="poste-pill ${getPosteClass(todayAmTxt)}">Matin : ${todayAmHtml}</span>
                <span class="poste-pill ${getPosteClass(todayPmTxt)}">PM : ${todayPmHtml}</span>
                ${todaySlots.isGarde ? `<span class="poste-pill poste-rg">Garde</span>` : ""}
              </div>
            </div>
          </div>
          <div class="summary-stats">
            <span>Poste <strong>${chef.posteTel || "12483"}</strong></span>
            <span><strong>${cStats.totalHalfDays}</strong> vac.</span>
            <span><strong>${cStats.gardesCount}</strong> gardes</span>
            ${chef.code === "TL" ? `<a class="btn btn-sm" href="https://mrthomaslef.github.io/agenda-cochin/" target="_blank" rel="noopener">App RI</a>` : ""}
          </div>
        `;
        return;
      }

      const statsAll = computeStatsByInterne();

      if (selectedInterneId === "all") {
        const mainCounts = ["gabriel", "noe", "marwane", "milan", "nathanael", "oussama"].map(id => statsAll[id].activeHalfDays);
        const avgVac = Math.round(mainCounts.reduce((a, b) => a + b, 0) / mainCounts.length);
        el.innerHTML = `
          <div class="summary-left">
            <div class="avatar-sm" style="background:#0284C7">6</div>
            <div>
              <div class="summary-title">Tous les internes & DJ (6)</div>
              <div class="summary-sub">Oussama Docteur Junior (DJ) • Noé en Phase Socle (doublé aux Urgences TDM SAU, avec Macil les 3 premiers mardis)</div>
            </div>
          </div>
          <div class="summary-stats">
            <span>Moyenne : <strong>${avgVac}</strong> postes</span>
            <span>Demi-offs : <strong>max 2 / sem.</strong></span>
          </div>
        `;
        return;
      }

      const me = getInterneById(selectedInterneId);
      const isDJ = Boolean(me.isDJ || me.id === "oussama");
      const st = statsAll[me.id];
      const daySched = (STATE.schedule[currentDateIso] && STATE.schedule[currentDateIso].byInterne)
        ? STATE.schedule[currentDateIso].byInterne[me.id]
        : null;

      const todayAm = daySched ? daySched.am : "—";
      const todayPm = daySched ? daySched.pm : "—";

      el.innerHTML = `
        <div class="summary-left">
          <div class="avatar-sm" style="background:${me.color}">${me.initials}</div>
          <div>
            <div class="summary-title">
              ${me.fullName}
              ${me.isSocle ? `<span class="tag-sm">Socle</span>` : ""}
              ${isDJ ? `<span class="tag-dj">Docteur Junior (DJ)</span>` : ""}
            </div>
            <div class="summary-sub">
              <span>${formatDateFr(currentDateIso)} :</span>
              <span class="poste-pill ${getPosteClass(todayAm)}">Matin : ${getPosteWithTimeLabel(todayAm, "am")}</span>
              <span class="poste-pill ${getPosteClass(todayPm)}">PM : ${getPosteWithTimeLabel(todayPm, "pm")}</span>
              ${daySched && daySched.note ? `<span class="tag-binome">${daySched.note}</span>` : ""}
            </div>
          </div>
        </div>
        <div class="summary-stats">
          <span><strong>${st.activeHalfDays}</strong> postes</span>
          <span><strong>${st.freeHalfDays}</strong> demi-offs</span>
          <span><strong>${Math.round(st.vacHalfDays / 2)}j</strong> congés</span>
          <span><strong>${st.casMardi + st.biblioVendredi + (st.coursInternes || 0)}</strong> cours</span>
        </div>
      `;
    }

    function switchTab(tab) {
      currentTab = tab;
      document.querySelectorAll(".tab-btn").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-tab") === tab);
      });
      renderTabContent();
    }

    function renderAll() {
      renderChefModeUI();
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
     * BOUTON UNIQUE "+ AJOUTER"
     * ========================================================================= */
    function openQuickAddModal() {
      document.getElementById("modalQuickAdd").classList.add("open");
    }

    function openNextPresentationModal() {
      const upcoming = (STATE.presentations || []).find(p => p.date >= currentDateIso) || (STATE.presentations || [])[0];
      if (upcoming) openPresentationModal(upcoming.id);
    }

    function openQuickVacationPicker() {
      const iid = (!isChefId(selectedInterneId) && selectedInterneId !== "all" && selectedInterneId !== "all_chefs")
        ? selectedInterneId
        : "gabriel";
      openVacationEditModal(currentDateIso, iid);
    }

    /* =========================================================================
     * ONGLET 1 : PLANNING
     * ========================================================================= */
    function renderWeekendGardesCompactBar(monIso) {
      const satIso = addDaysIso(monIso, 5);
      const sunIso = addDaysIso(monIso, 6);
      const [sy, sm, sd] = satIso.split("-").map(Number);
      const [uy, um, ud] = sunIso.split("-").map(Number);
      const gSat = (STATE.chefsGardes && STATE.chefsGardes[satIso] && STATE.chefsGardes[satIso].noms)
        ? `Dr ${STATE.chefsGardes[satIso].noms.join(", ")}`
        : "—";
      const gSun = (STATE.chefsGardes && STATE.chefsGardes[sunIso] && STATE.chefsGardes[sunIso].noms)
        ? `Dr ${STATE.chefsGardes[sunIso].noms.join(", ")}`
        : "—";
      return `
        <div class="weekend-gardes-compact">
          <div class="weekend-garde-mini" onclick="setCurrentDate('${satIso}'); setPlanningMode('day');">
            <span class="wg-day">Sam. ${String(sd).padStart(2, "0")}/${String(sm).padStart(2, "0")} <span style="font-weight:600; color:#991B1B;">(Garde)</span></span>
            <span class="wg-doc">🚨 ${gSat}</span>
          </div>
          <div class="weekend-garde-mini" onclick="setCurrentDate('${sunIso}'); setPlanningMode('day');">
            <span class="wg-day">Dim. ${String(ud).padStart(2, "0")}/${String(um).padStart(2, "0")} <span style="font-weight:600; color:#991B1B;">(Garde)</span></span>
            <span class="wg-doc">🚨 ${gSun}</span>
          </div>
        </div>
      `;
    }

    function renderPlanningTab() {
      const monIso = getMondayOfWeek(currentDateIso);
      const friIso = addDaysIso(monIso, 4);

      let headerLabel = "";
      if (planningMode === "day") {
        headerLabel = formatDateFr(currentDateIso, true);
      } else if (planningMode === "week") {
        headerLabel = `${formatDateFr(monIso)} – ${formatDateFr(friIso)}`;
      } else {
        const [y, m] = currentDateIso.split("-").map(Number);
        const mNames = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
        headerLabel = `${mNames[m - 1]} ${y}`;
      }

      const dNames = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
      let dayStripHtml = `<div class="day-strip">`;
      // Lundi à Vendredi (5 jours principaux)
      for (let offset = 0; offset < 5; offset++) {
        const dIso = addDaysIso(monIso, offset);
        const [yy, mm, dd] = dIso.split("-").map(Number);
        const isAct = (dIso === currentDateIso) ? "active" : "";
        const g = (STATE.chefsGardes && STATE.chefsGardes[dIso] && STATE.chefsGardes[dIso].noms)
          ? STATE.chefsGardes[dIso].noms.join("/")
          : "";
        dayStripHtml += `
          <div class="day-pill ${isAct}" onclick="setCurrentDate('${dIso}')">
            <div class="dp-top">
              <span class="dp-dow">${dNames[offset]}</span>
              <span class="dp-date">${String(dd).padStart(2, "0")}/${String(mm).padStart(2, "0")}</span>
            </div>
            ${g ? `<div class="dp-sub">Garde: ${g}</div>` : ``}
          </div>
        `;
      }
      // Samedi et Dimanche en petit avec juste les gardes
      for (let offset = 5; offset < 7; offset++) {
        const dIso = addDaysIso(monIso, offset);
        const [yy, mm, dd] = dIso.split("-").map(Number);
        const isAct = (dIso === currentDateIso) ? "active" : "";
        const g = (STATE.chefsGardes && STATE.chefsGardes[dIso] && STATE.chefsGardes[dIso].noms)
          ? STATE.chefsGardes[dIso].noms.join("/")
          : "—";
        dayStripHtml += `
          <div class="day-pill weekend-pill ${isAct}" onclick="setCurrentDate('${dIso}')" title="Garde ${dNames[offset]} ${dd}/${mm} : Dr ${g}">
            <div class="dp-top">
              <span class="dp-dow">${dNames[offset]}</span>
              <span class="dp-date">${String(dd).padStart(2, "0")}/${String(mm).padStart(2, "0")}</span>
            </div>
            <div class="dp-garde">🚨 ${g}</div>
          </div>
        `;
      }
      dayStripHtml += `</div>`;

      const horairesStripHtml = `
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:5px; margin-bottom:8px; font-size:11px;">
          <span style="font-weight:700; color:var(--text-muted); margin-right:2px;">🕒 Horaires :</span>
          <span class="poste-pill poste-irm">IRM : 07h45</span>
          <span class="poste-pill poste-tdm">TDM SAU : 08h00 – 18h30</span>
          <span class="poste-pill poste-echo">Écho : 09h00</span>
          <span class="poste-pill poste-gestes">Poste C : 09h00</span>
          <span class="poste-pill poste-cs">Consult. Internes : Mar PM (Relecture Pr Drapé) & Ven PM</span>
        </div>
      `;

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

      return `
        <div class="planning-toolbar">
          <div class="segmented">
            <button class="seg-btn ${planningScope === 'internes' ? 'active' : ''}" onclick="setPlanningScope('internes')">Internes</button>
            <button class="seg-btn ${planningScope === 'chefs' ? 'active' : ''}" onclick="setPlanningScope('chefs')">Chefs</button>
            <button class="seg-btn ${planningScope === 'combined' ? 'active' : ''}" onclick="setPlanningScope('combined')">Croisé</button>
            <button class="seg-btn ${planningScope === 'perso' ? 'active' : ''}" onclick="setPlanningScope('perso')">Mon planning</button>
          </div>

          <div class="date-nav">
            <button class="btn btn-sm" onclick="shiftPlanningDate(-1)">Préc.</button>
            <div class="date-label">${headerLabel}</div>
            <button class="btn btn-sm" onclick="shiftPlanningDate(1)">Suiv.</button>
          </div>

          <div class="segmented">
            <button class="seg-btn ${planningMode === 'day' ? 'active' : ''}" onclick="setPlanningMode('day')">Jour</button>
            <button class="seg-btn ${planningMode === 'week' ? 'active' : ''}" onclick="setPlanningMode('week')">Semaine</button>
            <button class="seg-btn ${planningMode === 'month' ? 'active' : ''}" onclick="setPlanningMode('month')">Mois</button>
          </div>
        </div>

        ${dayStripHtml}
        ${horairesStripHtml}
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
        currentDateIso = addDaysIso(currentDateIso, dir);
      } else if (planningMode === "week") {
        currentDateIso = addDaysIso(currentDateIso, dir * 7);
      } else {
        const [y, m] = currentDateIso.split("-").map(Number);
        const dt = new Date(y, m - 1 + dir, 2, 12, 0, 0);
        const yy = dt.getFullYear();
        const mm = String(dt.getMonth() + 1).padStart(2, "0");
        const dd = String(dt.getDate()).padStart(2, "0");
        currentDateIso = `${yy}-${mm}-${dd}`;
      }
      renderAll();
    }

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
                ${sl.isGarde ? '<span class="tag-sm">Garde</span>' : ''}
              </div>
              <div style="font-size:10px; color:var(--text-muted);">Matin</div>
              ${sl.am.length ? sl.am.map(p => `<span class="poste-pill ${getPosteClass(p)}" style="font-size:10px; padding:2px 6px;">${getPosteWithTimeLabel(p, "am")}</span>`).join(" ") : `<span style="font-size:10.5px; color:var(--text-muted);">—</span>`}
              <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">Après-midi</div>
              ${sl.pm.length ? sl.pm.map(p => `<span class="poste-pill ${getPosteClass(p)}" style="font-size:10px; padding:2px 6px;">${getPosteWithTimeLabel(p, "pm")}</span>`).join(" ") : `<span style="font-size:10.5px; color:var(--text-muted);">—</span>`}
            </div>
          `;
        });
        return `
          <div class="card">
            <div class="card-header">
              <div class="card-title">Mois — ${chef.fullName}</div>
            </div>
            <div class="month-grid">${cells}</div>
          </div>
        `;
      }

      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      let cardsHtml = `
        <div class="card" style="padding:12px 10px 0; overflow:hidden;">
          <div class="card-header" style="padding:0 4px;">
            <div class="card-title">Semaine (Lun–Ven) — ${chef.fullName}</div>
          </div>
          <div class="perso-week-grid" style="margin-bottom:10px;">
      `;
      days.forEach(dIso => {
        const sl = getChefSlotsForDate(dIso, chef);
        const intDay = STATE.schedule[dIso] || { am: [], pm: [] };

        function findMatchingInternes(chefPostes, intPeriodList) {
          const out = [];
          (chefPostes || []).forEach(cp => {
            const pUp = cp.toUpperCase();
            (intPeriodList || []).forEach(it => {
              if (it.closed) return;
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
                const tag = `${it.interne}`;
                if (!out.includes(tag)) out.push(tag);
              }
            });
          });
          return out;
        }
        const intAm = findMatchingInternes(sl.am, intDay.am);
        const intPm = findMatchingInternes(sl.pm, intDay.pm);

        cardsHtml += `
          <div class="card perso-day-card" style="margin:0; padding:8px 6px; background:#F8FAFC;">
            <div style="font-weight:800; font-size:11.5px; margin-bottom:6px; color:${chef.color}; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:2px;">
              <span>${formatShortDayHeader(dIso)}</span>
              ${sl.isGarde ? `<span class="poste-pill poste-rg" style="font-size:9px; padding:1px 4px;">Garde</span>` : ``}
            </div>
            <div style="margin-bottom:6px;">
              <div style="font-size:9px; color:var(--text-muted); font-weight:700;">MATIN</div>
              <div style="margin-top:2px; display:flex; flex-wrap:wrap; gap:3px;">
                ${sl.am.length ? sl.am.map(p => `<span class="poste-pill ${getPosteClass(p)}">${getPosteWithTimeLabel(p, "am")}</span>`).join("") : `<span class="poste-pill poste-off">Libre</span>`}
              </div>
              ${intAm.length ? `<div style="font-size:9.5px; color:#0284C7; margin-top:3px;">Int: <strong>${intAm.join(", ")}</strong></div>` : ``}
            </div>
            <div>
              <div style="font-size:9px; color:var(--text-muted); font-weight:700;">APRÈS-MIDI</div>
              <div style="margin-top:2px; display:flex; flex-wrap:wrap; gap:3px;">
                ${sl.pm.length ? sl.pm.map(p => `<span class="poste-pill ${getPosteClass(p)}">${getPosteWithTimeLabel(p, "pm")}</span>`).join("") : `<span class="poste-pill poste-off">Libre</span>`}
              </div>
              ${intPm.length ? `<div style="font-size:9.5px; color:#7C3AED; margin-top:3px;">Int: <strong>${intPm.join(", ")}</strong></div>` : ``}
            </div>
          </div>
        `;
      });
      cardsHtml += `</div>${renderWeekendGardesCompactBar(monIso)}</div>`;
      return cardsHtml;
    }

    function renderCombinedChefsInternesView(monIso) {
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      const sectors = [
        { label: "ECHO", chefMatch: ["ECHO"], intMatch: ["ECHO"], defaultPosteAm: "ECHO", defaultPostePm: "ECHO" },
        { label: "GESTES (C)", chefMatch: ["GESTES"], intMatch: ["GESTES (C)"], defaultPosteAm: "GESTES (C)", defaultPostePm: "GESTES (C)" },
        { label: "TDM SAU", chefMatch: ["SAU", "OLLIER 4"], intMatch: ["TDM SAU"], defaultPosteAm: "TDM SAU", defaultPostePm: "TDM SAU" },
        { label: "SCAN ACHARD", chefMatch: ["ACHARD"], intMatch: ["SCAN ACHARD"], defaultPosteAm: "SCAN ACHARD", defaultPostePm: "SCAN ACHARD" },
        { label: "ALLURA", chefMatch: ["ALLURA"], intMatch: ["ALLURA"], defaultPosteAm: "ALLURA", defaultPostePm: "ALLURA" },
        { label: "IRM", chefMatch: ["IRM"], intMatch: ["IRM 3T", "IRM 1,5T", "IRM"], defaultPosteAm: "IRM 3T", defaultPostePm: "IRM" },
        { label: "TDM OLLIER", chefMatch: ["OLLIER 3"], intMatch: ["TDM OLLIER DIAG"], defaultPosteAm: "TDM OLLIER DIAG", defaultPostePm: "TDM OLLIER DIAG" },
        { label: "CONSULT / LECTURE", chefMatch: ["CONSULT", "UCSA"], intMatch: ["LECTURE/CS"], defaultPosteAm: "LECTURE/CS", defaultPostePm: "LECTURE/CS" },
        { label: "DEMI-OFF", chefMatch: ["LIBRE"], intMatch: ["1/2 journée libre"], defaultPosteAm: "1/2 journée libre", defaultPostePm: "1/2 journée libre" }
      ];

      function buildCombinedPeriodRows(periodKey) {
        let rows = "";
        sectors.forEach(sec => {
          const targetPoste = periodKey === "am" ? sec.defaultPosteAm : sec.defaultPostePm;
          const escPoste = targetPoste.replace(/'/g, "\\'");
          rows += `<tr><td>${renderPosteCellLabel(sec.label, periodKey)}</td>`;
          days.forEach(dIso => {
            const chDay = (STATE.chefsPlanning && STATE.chefsPlanning[dIso]) ? (STATE.chefsPlanning[dIso][periodKey] || []) : [];
            const intDay = (STATE.schedule && STATE.schedule[dIso]) ? (STATE.schedule[dIso][periodKey] || []) : [];

            const matchedChefs = chDay.filter(x => sec.chefMatch.some(m => String(x.poste || "").toUpperCase().includes(m)));
            const matchedInts = intDay.filter(x => sec.intMatch.includes(x.poste));

            let cellHtml = "";
            if (matchedChefs.length > 0) {
              cellHtml += `<div style="margin-bottom:2px;">` + matchedChefs.map(c => {
                const isClosedDoc = (c.doc === "FERMÉ" || c.doc === "MAINTENANCE" || c.closed);
                if (isClosedDoc) {
                  return `<span class="poste-pill poste-closed" style="margin:1px; font-size:9px;">Fermé</span>`;
                }
                return `<span style="display:inline-block; font-size:9.5px; font-weight:700; color:#0369A1; background:#E0F2FE; border-radius:4px; padding:1px 4px; margin:1px;">${c.doc}</span>`;
              }).join("") + `</div>`;
            }
            if (matchedInts.length > 0) {
              cellHtml += `<div>` + matchedInts.map(m => {
                if (m.closed) {
                  return `<span class="poste-pill poste-closed" style="margin:1px; font-size:9px;">${m.reason || 'Fermé'}</span>`;
                }
                const iObj = getInterneById(m.interneId);
                const isSelectedMove = isChefPlanningMode && selectedForMove && selectedForMove.interneId === m.interneId && selectedForMove.dIso === dIso && selectedForMove.periodKey === periodKey;
                const dragClass = isChefPlanningMode ? `draggable-interne ${isSelectedMove ? 'selected-for-move' : ''}` : "";
                const mPosteEsc = String(m.poste || targetPoste).replace(/'/g, "\\'");
                const dragAttrs = isChefPlanningMode
                  ? `draggable="true" ondragstart="onInterneDragStart(event, '${dIso}', '${periodKey}', '${m.interneId}', '${mPosteEsc}')" ondragend="onInterneDragEnd(event)" ondragover="onCellDragOver(event, '${dIso}', '${periodKey}')" ondrop="onBadgeDrop(event, '${dIso}', '${periodKey}', '${m.interneId}', '${mPosteEsc}')"`
                  : "";
                return `<span class="interne-badge ${dragClass}" ${dragAttrs} onclick="onInterneBadgeClick(event, '${dIso}', '${periodKey}', '${m.interneId}', '${mPosteEsc}')" style="margin:1px;">
                  ${isChefPlanningMode ? `<span class="drag-grip">⋮⋮</span>` : ""}
                  <span style="width:6px;height:6px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                  ${iObj.shortName}
                </span>`;
              }).join("") + `</div>`;
            }
            const canDrop = isChefPlanningMode;
            const isTapTarget = canDrop && selectedForMove && selectedForMove.dIso === dIso && selectedForMove.periodKey === periodKey;
            const tdClass = canDrop ? `drop-zone-cell ${isTapTarget ? 'tap-target-ready' : ''}` : "";
            const tdAttrs = canDrop
              ? `ondragover="onCellDragOver(event, '${dIso}', '${periodKey}')" ondragleave="onCellDragLeave(event)" ondrop="onCellDrop(event, '${dIso}', '${periodKey}', '${escPoste}')" onclick="onChefCellClick(event, '${dIso}', '${periodKey}', '${escPoste}')"`
              : "";
            rows += `<td class="${tdClass}" ${tdAttrs}>${cellHtml || '<span style="color:#CBD5E1">—</span>'}</td>`;
          });
          rows += `</tr>`;
        });
        return rows;
      }

      let gardeRowHtml = `<tr><td><span class="poste-pill poste-rg">GARDE</span></td>`;
      days.forEach(dIso => {
        const g = STATE.chefsGardes ? STATE.chefsGardes[dIso] : null;
        gardeRowHtml += `<td>${g && g.noms ? `<span style="font-weight:700; color:#B91C1C;">Dr ${g.noms.join(", ")}</span>` : '—'}</td>`;
      });
      gardeRowHtml += `</tr>`;

      return `
        <div class="card" style="padding:0; overflow:hidden;">
          <div class="week-table-wrap" style="border:none; border-radius:0;">
            <table class="planning-table week-5col">
              <thead>
                <tr>
                  <th class="col-poste">POSTE</th>
                  ${days.map(d => `<th>${formatShortDayHeader(d)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr class="period-divider"><td colspan="6">MATIN — IRM 07h45 • TDM SAU 08h00 • Écho & Poste C 09h00</td></tr>
                ${buildCombinedPeriodRows("am")}
                <tr class="period-divider"><td colspan="6">APRÈS-MIDI — TDM SAU fin 18h30</td></tr>
                ${buildCombinedPeriodRows("pm")}
                <tr class="period-divider"><td colspan="6">GARDE SENIOR (LUN–VEN)</td></tr>
                ${gardeRowHtml}
              </tbody>
            </table>
          </div>
          ${renderWeekendGardesCompactBar(monIso)}
        </div>
      `;
    }

    function renderWeekPlanningView(monIso) {
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      const postesAm = ["ECHO", "GESTES (C)", "TDM SAU", "TDM OLLIER DIAG", "IRM 3T", "IRM 1,5T", "SCAN ACHARD", "LECTURE/CS", "1/2 journée libre", "RG", "VACANCES"];
      const postesPm = ["GESTES (C)", "TDM OLLIER DIAG", "TDM SAU", "IRM", "ECHO", "ALLURA", "SCAN ACHARD", "LECTURE/CS", "1/2 journée libre", "RG", "VACANCES"];

      if (planningScope === "perso") {
        const me = getInterneById(selectedInterneId === "all" ? "gabriel" : selectedInterneId);
        let cardsHtml = `
          <div class="card" style="padding:12px 10px 0; overflow:hidden;">
            <div class="card-header" style="padding:0 4px;">
              <div class="card-title">Semaine (Lun–Ven) — ${me.fullName}</div>
              <span style="font-size:11px; color:var(--text-muted);">Touchez un jour pour modifier</span>
            </div>
            <div class="perso-week-grid" style="margin-bottom:10px;">
        `;
        days.forEach(dIso => {
          const dObj = STATE.schedule[dIso] || {};
          const slot = (dObj.byInterne && dObj.byInterne[me.id]) ? dObj.byInterne[me.id] : { am: "—", pm: "—", note: "" };
          const presList = STATE.presentations.filter(p => p.date === dIso);
          cardsHtml += `
            <div class="card perso-day-card" style="margin:0; padding:8px 6px; background:#F8FAFC; cursor:pointer;" onclick="openVacationEditModal('${dIso}', '${me.id}')">
              <div style="font-weight:800; font-size:11.5px; margin-bottom:6px; color:var(--primary); display:flex; justify-content:space-between; align-items:center;">
                <span>${formatShortDayHeader(dIso)}</span>
              </div>
              <div style="margin-bottom:5px;">
                <div style="font-size:8.5px; color:var(--text-muted); font-weight:700;">MATIN</div>
                <span class="poste-pill ${getPosteClass(slot.am)}" style="margin-top:2px;">${getPosteWithTimeLabel(slot.am, "am")}</span>
              </div>
              <div>
                <div style="font-size:8.5px; color:var(--text-muted); font-weight:700;">APRÈS-MIDI</div>
                <span class="poste-pill ${getPosteClass(slot.pm)}" style="margin-top:2px;">${getPosteWithTimeLabel(slot.pm, "pm")}</span>
              </div>
              ${slot.note ? `<div style="font-size:9.5px; color:#0369A1; font-weight:700; margin-top:4px;">${slot.note}</div>` : ''}
              ${presList.map(p => `<div style="font-size:9.5px; color:#6D28D9; margin-top:3px;">12h30: ${p.interneName}</div>`).join("")}
            </div>
          `;
        });
        cardsHtml += `</div>${renderWeekendGardesCompactBar(monIso)}</div>`;
        return cardsHtml;
      }

      function renderPeriodRows(postesList, periodKey) {
        let rowsHtml = "";
        postesList.forEach(posteName => {
          const hasAny = days.some(dIso => {
            const dObj = STATE.schedule[dIso];
            if (!dObj || !dObj[periodKey]) return false;
            return dObj[periodKey].some(x => x.poste === posteName);
          });
          if (periodKey === "am" && posteName === "LECTURE/CS" && !hasAny && !isChefPlanningMode) return;
          if (!isChefPlanningMode && !hasAny && (posteName === "RG" || posteName === "VACANCES")) return;

          const escPoste = posteName.replace(/'/g, "\\'");
          rowsHtml += `<tr><td>${renderPosteCellLabel(posteName, periodKey)}</td>`;
          days.forEach(dIso => {
            const dObj = STATE.schedule[dIso];
            if (!dObj) {
              rowsHtml += `<td>—</td>`;
              return;
            }
            if (dObj.holiday) {
              rowsHtml += `<td><span class="poste-pill poste-rg">Férié</span></td>`;
              return;
            }
            const matches = (dObj[periodKey] || []).filter(x => x.poste === posteName);
            const canDrop = isChefPlanningMode;
            const isTapTarget = canDrop && selectedForMove && selectedForMove.dIso === dIso && selectedForMove.periodKey === periodKey;
            const tdClass = canDrop ? `drop-zone-cell ${isTapTarget ? 'tap-target-ready' : ''}` : "";
            const tdAttrs = canDrop
              ? `ondragover="onCellDragOver(event, '${dIso}', '${periodKey}')" ondragleave="onCellDragLeave(event)" ondrop="onCellDrop(event, '${dIso}', '${periodKey}', '${escPoste}')" onclick="onChefCellClick(event, '${dIso}', '${periodKey}', '${escPoste}')"`
              : "";

            if (matches.length === 0) {
              rowsHtml += `<td class="${tdClass}" ${tdAttrs} style="color:#CBD5E1">—</td>`;
            } else {
              const [yy, mm, dd] = dIso.split("-").map(Number);
              const jsDay = new Date(yy, mm - 1, dd).getDay();
              const badges = matches.map(m => {
                if (m.closed) {
                  return `<span class="poste-pill poste-closed">${m.reason === "MAINTENANCE" ? "Maint." : "Fermé"}</span>`;
                }
                const iObj = getInterneById(m.interneId);
                const isMe = (selectedInterneId !== "all" && m.interneId === selectedInterneId) ? "highlight-me" : "";
                const isSelectedMove = isChefPlanningMode && selectedForMove && selectedForMove.interneId === m.interneId && selectedForMove.dIso === dIso && selectedForMove.periodKey === periodKey;
                const dragClass = isChefPlanningMode ? `draggable-interne ${isSelectedMove ? 'selected-for-move' : ''}` : "";
                const socleHtml = iObj.isSocle ? `<span class="tag-sm">Socle</span>` : "";
                const djHtml = (iObj.isDJ || iObj.id === "oussama") ? `<span class="tag-dj">DJ</span>` : "";
                let binomeHtml = "";
                if (posteName === "LECTURE/CS" && periodKey === "pm" && jsDay === 2) {
                  binomeHtml = `<span class="tag-binome">Relecture Pr Drapé</span>`;
                } else if (posteName === "LECTURE/CS" && periodKey === "pm" && jsDay === 5) {
                  binomeHtml = `<span class="tag-binome">Consult.</span>`;
                } else if (m.note && m.note.includes("Macil")) {
                  binomeHtml = `<span class="tag-binome">+Macil</span>`;
                } else if (m.binome) {
                  binomeHtml = `<span class="tag-binome">Binôme</span>`;
                }
                const dragAttrs = isChefPlanningMode
                  ? `draggable="true" ondragstart="onInterneDragStart(event, '${dIso}', '${periodKey}', '${m.interneId}', '${escPoste}')" ondragend="onInterneDragEnd(event)" ondragover="onCellDragOver(event, '${dIso}', '${periodKey}')" ondrop="onBadgeDrop(event, '${dIso}', '${periodKey}', '${m.interneId}', '${escPoste}')"`
                  : "";
                return `<span class="interne-badge ${isMe} ${dragClass}" ${dragAttrs} onclick="onInterneBadgeClick(event, '${dIso}', '${periodKey}', '${m.interneId}', '${escPoste}')">
                  ${isChefPlanningMode ? `<span class="drag-grip">⋮⋮</span>` : ""}
                  <span style="width:6px;height:6px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                  ${iObj.shortName}
                  ${socleHtml}
                  ${djHtml}
                  ${binomeHtml}
                </span>`;
              }).join(" ");
              rowsHtml += `<td class="${tdClass}" ${tdAttrs}>${badges}</td>`;
            }
          });
          rowsHtml += `</tr>`;
        });
        return rowsHtml;
      }

      let staffRowHtml = `<tr><td><span class="poste-pill poste-irm">COURS</span></td>`;
      days.forEach(dIso => {
        const pres = STATE.presentations.filter(p => p.date === dIso);
        const meets = STATE.meetings.filter(m => m.date === dIso);
        let cell = "";
        pres.forEach(p => {
          const isBone = p.type === "bone_club";
          const isCra = p.type === "confrontation_anapath";
          const isCoursInt = p.type === "cours_internes";
          const bg = isBone ? "#FEF2F2" : (isCra ? "#FEF3C7" : (isCoursInt ? "#DBEAFE" : "#F3E8FF"));
          const fg = isBone ? "#B91C1C" : (isCra ? "#B45309" : (isCoursInt ? "#1D4ED8" : "#6D28D9"));
          const lbl = isBone
            ? `Bone Club`
            : (isCra
              ? `CRA Anapath`
              : (isCoursInt
                ? `Cours 12h30`
                : (p.type === 'cas_mardi' ? 'Cas 12h30' : 'Biblio 12h30')));
          cell += `<div style="font-size:9.5px; margin-bottom:2px; padding:2px 4px; border-radius:4px; background:${bg}; cursor:pointer; line-height:1.15;" onclick="openPresentationModal('${p.id}')">
            <strong style="color:${fg}">${lbl} :</strong> ${p.interneName}
          </div>`;
        });
        meets.forEach(m => {
          if (pres.some(p => (p.type === "bone_club" && m.category === "Bone Club") || (p.type === "confrontation_anapath" && m.category === "Anapath"))) return;
          cell += `<div style="font-size:9.5px; margin-bottom:2px; padding:2px 4px; border-radius:4px; background:#DCFCE7; line-height:1.15;">
            <strong style="color:#15803D">${m.horaire} :</strong> ${m.title}
          </div>`;
        });
        staffRowHtml += `<td>${cell || '<span style="color:#CBD5E1">—</span>'}</td>`;
      });
      staffRowHtml += `</tr>`;

      let gardeRowHtml = `<tr><td><span class="poste-pill poste-rg">GARDE</span></td>`;
      days.forEach(dIso => {
        const g = STATE.chefsGardes ? STATE.chefsGardes[dIso] : null;
        gardeRowHtml += `<td>${g && g.noms ? `<span style="font-weight:700; color:#B91C1C;">Dr ${g.noms.join(", ")}</span>` : '—'}</td>`;
      });
      gardeRowHtml += `</tr>`;

      return `
        <div class="card" style="padding:0; overflow:hidden;">
          <div class="week-table-wrap" style="border:none; border-radius:0;">
            <table class="planning-table week-5col">
              <thead>
                <tr>
                  <th class="col-poste">POSTE</th>
                  ${days.map(d => `<th>${formatShortDayHeader(d)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr class="period-divider"><td colspan="6">MATIN — IRM 07h45 • TDM SAU 08h00 • Écho & Poste C 09h00</td></tr>
                ${renderPeriodRows(postesAm, "am")}
                <tr class="period-divider"><td colspan="6">COURS & RÉUNIONS (12h30)</td></tr>
                ${staffRowHtml}
                <tr class="period-divider"><td colspan="6">APRÈS-MIDI — TDM SAU fin 18h30</td></tr>
                ${renderPeriodRows(postesPm, "pm")}
                <tr class="period-divider"><td colspan="6">GARDE SENIOR (LUN–VEN)</td></tr>
                ${gardeRowHtml}
              </tbody>
            </table>
          </div>
          ${renderWeekendGardesCompactBar(monIso)}
        </div>
      `;
    }

    function renderDayPlanningView(iso) {
      const dObj = STATE.schedule[iso];
      const gSenior = STATE.chefsGardes ? STATE.chefsGardes[iso] : null;
      if (!dObj) {
        return `
          <div class="card">
            <div class="card-header">
              <div class="card-title">${formatDateFr(iso, true)} — Week-end / Garde</div>
              ${gSenior && gSenior.noms ? `<span class="poste-pill poste-rg">🚨 Garde : Dr ${gSenior.noms.join(", ")}</span>` : ''}
            </div>
            <div style="font-size:13px; color:var(--text-muted);">
              ${gSenior && gSenior.noms
                ? `Médecin senior de garde ce jour : <strong style="color:#B91C1C;">Dr ${gSenior.noms.join(", ")}</strong> (${gSenior.nature || "Garde Week-end"}).`
                : `Aucune vacation ordinaire programmée pour le ${formatDateFr(iso, true)}.`}
            </div>
          </div>
        `;
      }
      const chDay = (STATE.chefsPlanning && STATE.chefsPlanning[iso]) ? STATE.chefsPlanning[iso] : { am: [], pm: [] };

      let rows = "";
      STATE.internes.forEach(i => {
        if (planningScope === "perso" && !isChefId(selectedInterneId) && selectedInterneId !== "all" && i.id !== selectedInterneId) return;
        const slot = (dObj.byInterne && dObj.byInterne[i.id]) ? dObj.byInterne[i.id] : null;
        if (!slot) return;
        const amEsc = String(slot.am || "").replace(/'/g, "\\'");
        const pmEsc = String(slot.pm || "").replace(/'/g, "\\'");
        const isSelAm = isChefPlanningMode && selectedForMove && selectedForMove.interneId === i.id && selectedForMove.dIso === iso && selectedForMove.periodKey === "am";
        const isSelPm = isChefPlanningMode && selectedForMove && selectedForMove.interneId === i.id && selectedForMove.dIso === iso && selectedForMove.periodKey === "pm";
        const isDJ = Boolean(i.isDJ || i.id === "oussama");

        const amDragAttrs = isChefPlanningMode
          ? `draggable="true" ondragstart="onInterneDragStart(event, '${iso}', 'am', '${i.id}', '${amEsc}')" ondragend="onInterneDragEnd(event)" ondragover="onCellDragOver(event, '${iso}', 'am')" ondrop="onBadgeDrop(event, '${iso}', 'am', '${i.id}', '${amEsc}')" onclick="onInterneBadgeClick(event, '${iso}', 'am', '${i.id}', '${amEsc}')"`
          : "";
        const pmDragAttrs = isChefPlanningMode
          ? `draggable="true" ondragstart="onInterneDragStart(event, '${iso}', 'pm', '${i.id}', '${pmEsc}')" ondragend="onInterneDragEnd(event)" ondragover="onCellDragOver(event, '${iso}', 'pm')" ondrop="onBadgeDrop(event, '${iso}', 'pm', '${i.id}', '${pmEsc}')" onclick="onInterneBadgeClick(event, '${iso}', 'pm', '${i.id}', '${pmEsc}')"`
          : "";

        rows += `
          <tr onclick="openVacationEditModal('${iso}', '${i.id}')" style="cursor:pointer;">
            <td>
              <div style="display:flex; align-items:center; gap:7px; font-weight:700;">
                <span style="width:8px;height:8px;border-radius:50%;background:${i.color};display:inline-block;"></span>
                ${i.shortName}
                ${i.isSocle ? `<span class="tag-sm">Socle</span>` : ""}
                ${isDJ ? `<span class="tag-dj">DJ</span>` : ""}
              </div>
            </td>
            <td class="${isChefPlanningMode ? 'drop-zone-cell' : ''}" ${amDragAttrs}>
              <span class="poste-pill ${getPosteClass(slot.am)} ${isChefPlanningMode ? 'draggable-interne' : ''} ${isSelAm ? 'selected-for-move' : ''}">
                ${isChefPlanningMode ? `<span class="drag-grip">⋮⋮</span>` : ""}
                ${getPosteWithTimeLabel(slot.am, "am")}
              </span>
            </td>
            <td class="${isChefPlanningMode ? 'drop-zone-cell' : ''}" ${pmDragAttrs}>
              <span class="poste-pill ${getPosteClass(slot.pm)} ${isChefPlanningMode ? 'draggable-interne' : ''} ${isSelPm ? 'selected-for-move' : ''}">
                ${isChefPlanningMode ? `<span class="drag-grip">⋮⋮</span>` : ""}
                ${getPosteWithTimeLabel(slot.pm, "pm")}
              </span>
            </td>
            <td style="color:var(--text-muted); font-size:12px;">${slot.note || "—"}</td>
          </tr>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">${formatDateFr(iso, true)}</div>
            ${gSenior && gSenior.noms ? `<span class="poste-pill poste-rg">Garde : Dr ${gSenior.noms.join(", ")}</span>` : ''}
          </div>
          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px;">
            <div>
              <div style="font-size:12px; font-weight:800; margin-bottom:6px;">${isChefPlanningMode ? "Internes & DJ (glissez-déposez un créneau sur un autre interne pour échanger)" : "Internes & DJ (cliquez pour modifier)"}</div>
              <div class="week-table-wrap">
                <table class="planning-table" style="min-width:280px;">
                  <thead>
                    <tr>
                      <th>Interne / DJ</th>
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
              <div style="font-size:12px; font-weight:800; margin-bottom:6px;">Chefs & Seniors</div>
              <div class="card" style="margin:0; background:#F8FAFC;">
                <div style="font-size:11px; font-weight:700; color:var(--text-muted); margin-bottom:4px;">MATIN (IRM 7h45 • TDM SAU 8h • Écho/Poste C 9h)</div>
                ${(chDay.am || []).map(x => {
                  const isCl = (x.doc === "FERMÉ" || x.doc === "MAINTENANCE" || x.closed);
                  return `<div style="font-size:12px; margin-bottom:3px;"><strong>${getPosteWithTimeLabel(x.poste, "am")}</strong> : ${isCl ? `<span class="poste-pill poste-closed">${x.doc}</span>` : `<span style="color:#0284C7; font-weight:700;">${x.doc}</span>`}</div>`;
                }).join("") || '—'}
                <div style="font-size:11px; font-weight:700; color:var(--text-muted); margin:10px 0 4px;">APRÈS-MIDI (TDM SAU fin 18h30)</div>
                ${(chDay.pm || []).map(x => {
                  const isCl = (x.doc === "FERMÉ" || x.doc === "MAINTENANCE" || x.closed);
                  return `<div style="font-size:12px; margin-bottom:3px;"><strong>${getPosteWithTimeLabel(x.poste, "pm")}</strong> : ${isCl ? `<span class="poste-pill poste-closed">${x.doc}</span>` : `<span style="color:#6D28D9; font-weight:700;">${x.doc}</span>`}</div>`;
                }).join("") || '—'}
              </div>
            </div>
          </div>
        </div>
      `;
    }

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
        cells += `
          <div class="month-cell ${dIso === currentDateIso ? 'today' : ''}" onclick="setCurrentDate('${dIso}'); setPlanningMode('day');">
            <div style="font-weight:800; font-size:12px;">${formatDateFr(dIso)}</div>
            ${dObj.holiday ? `<span class="poste-pill poste-rg">Férié</span>` : (slot ? `
              <span class="poste-pill ${getPosteClass(slot.am)}" style="font-size:10.5px; padding:2px 6px;">M: ${getPosteWithTimeLabel(slot.am, "am")}</span>
              <span class="poste-pill ${getPosteClass(slot.pm)}" style="font-size:10.5px; padding:2px 6px;">PM: ${getPosteWithTimeLabel(slot.pm, "pm")}</span>
            ` : `—`)}
          </div>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Mois — ${targetInterne.fullName}</div>
          </div>
          <div class="month-grid">${cells}</div>
        </div>
      `;
    }

    function renderChefsPlanningView(monIso) {
      const days = [0, 1, 2, 3, 4].map(off => addDaysIso(monIso, off));
      const chefPostesAm = ["ECHO", "GESTES (C)", "TDM OLLIER 4 (SAU)", "TDM OLLIER 3", "TDM ACHARD 1", "IRM 3T", "IRM 1,5T", "CONSULTATION", "UCSA", "STAFF", "1/2 journée libre"];
      const chefPostesPm = ["GESTES (C)", "TDM OLLIER 4 (SAU)", "TDM OLLIER 3", "TDM ACHARD 1", "IRM", "ECHO", "ALLURA", "CONSULTATION", "UCSA", "STAFF", "1/2 journée libre"];

      const activeChef = isChefId(selectedInterneId) ? getChefById(selectedInterneId) : null;

      function renderChefRows(postesList, periodKey) {
        let rows = "";
        postesList.forEach(pName => {
          const hasAny = days.some(dIso => {
            const ch = STATE.chefsPlanning ? STATE.chefsPlanning[dIso] : null;
            return ch && ch[periodKey] && ch[periodKey].some(x => x.poste === pName);
          });
          if (!hasAny) return;
          rows += `<tr><td>${renderPosteCellLabel(pName, periodKey)}</td>`;
          days.forEach(dIso => {
            const ch = STATE.chefsPlanning ? STATE.chefsPlanning[dIso] : null;
            const matches = (ch && ch[periodKey]) ? ch[periodKey].filter(x => x.poste === pName) : [];
            if (!matches.length) {
              rows += `<td style="color:#CBD5E1">—</td>`;
            } else {
              const badges = matches.map(m => {
                if (m.doc === "FERMÉ" || m.doc === "MAINTENANCE" || m.closed) {
                  return `<span class="poste-pill poste-closed">${m.doc === "MAINTENANCE" ? "Maint." : "Fermé"}</span>`;
                }
                const isHighlighted = activeChef && doesDocMatchChef(m.doc, activeChef);
                return `<span class="interne-badge ${isHighlighted ? 'highlight-me' : ''}" onclick="selectChefByDocString('${m.doc.replace(/'/g, "\\'")}')">
                  <strong>${m.doc}</strong>
                </span>`;
              }).join(" ");
              rows += `<td>${badges}</td>`;
            }
          });
          rows += `</tr>`;
        });
        return rows;
      }

      let gardeRowHtml = `<tr><td><span class="poste-pill poste-rg">GARDE</span></td>`;
      days.forEach(dIso => {
        const g = STATE.chefsGardes ? STATE.chefsGardes[dIso] : null;
        gardeRowHtml += `<td>${g && g.noms ? `<span style="font-weight:700; color:#B91C1C;">Dr ${g.noms.join(", ")}</span>` : '—'}</td>`;
      });
      gardeRowHtml += `</tr>`;

      return `
        <div class="card" style="padding:0; overflow:hidden;">
          <div class="week-table-wrap" style="border:none; border-radius:0;">
            <table class="planning-table week-5col">
              <thead>
                <tr>
                  <th class="col-poste">POSTE</th>
                  ${days.map(d => `<th>${formatShortDayHeader(d)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr class="period-divider"><td colspan="6">MATIN — IRM 07h45 • TDM SAU 08h00 • Écho & Poste C 09h00</td></tr>
                ${renderChefRows(chefPostesAm, "am")}
                <tr class="period-divider"><td colspan="6">APRÈS-MIDI — TDM SAU fin 18h30</td></tr>
                ${renderChefRows(chefPostesPm, "pm")}
                <tr class="period-divider"><td colspan="6">GARDE SENIOR (LUN–VEN)</td></tr>
                ${gardeRowHtml}
              </tbody>
            </table>
          </div>
          ${renderWeekendGardesCompactBar(monIso)}
        </div>
      `;
    }

    function selectChefByDocString(docStr) {
      const found = (STATE.chefs || []).find(c => doesDocMatchChef(docStr, c));
      if (found) selectInterne(found.id);
    }

    function toggleStatsTable() {
      showStatsTable = !showStatsTable;
      renderTabContent();
    }

    function renderBalanceSummaryCard() {
      if (!showStatsTable) {
        return `
          <div style="text-align:center; margin-top:8px;">
            <button class="btn btn-sm" onclick="toggleStatsTable()">Afficher le décompte des postes par interne</button>
          </div>
        `;
      }

      const statsAll = computeStatsByInterne();
      let rows = "";
      STATE.internes.forEach(i => {
        const s = statsAll[i.id];
        const isDJ = Boolean(i.isDJ || i.id === "oussama");
        rows += `
          <tr>
            <td style="font-weight:700;">
              ${i.shortName}
              ${i.isSocle ? `<span class="tag-sm">Socle</span>` : ""}
              ${isDJ ? `<span class="tag-dj">DJ</span>` : ""}
            </td>
            <td><strong>${s.activeHalfDays}</strong></td>
            <td>${s.byModality.TDM}</td>
            <td>${s.byModality.IRM}</td>
            <td>${s.byModality.ECHO}</td>
            <td>${s.byModality.RI_GESTES}</td>
            <td>${s.byModality.LECTURE_CS}</td>
            <td>${s.freeHalfDays}</td>
            <td>${Math.round(s.vacHalfDays / 2)} j.</td>
            <td>${s.casMardi} / ${s.biblioVendredi}${s.coursInternes ? ` / ${s.coursInternes}` : ""}</td>
          </tr>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Répartition des postes sur le semestre</div>
            <button class="btn btn-sm" onclick="toggleStatsTable()">Masquer</button>
          </div>
          <div class="week-table-wrap">
            <table class="planning-table">
              <thead>
                <tr>
                  <th>Interne / DJ</th>
                  <th>Total</th>
                  <th>TDM</th>
                  <th>IRM</th>
                  <th>Écho</th>
                  <th>Gestes</th>
                  <th>CS</th>
                  <th>Demi-offs</th>
                  <th>Congés</th>
                  <th>Cas / Biblio / Cours</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    }

    /* =========================================================================
     * ONGLET 2 : CONGÉS & RG
     * ========================================================================= */
    function renderVacancesTab() {
      const absences = (STATE.absences || []).slice().sort((a, b) => a.date.localeCompare(b.date));
      const filtered = (selectedInterneId === "all" || isChefId(selectedInterneId) || selectedInterneId === "all_chefs")
        ? absences
        : absences.filter(a => a.interneId === selectedInterneId);

      const countByDate = {};
      absences.forEach(a => {
        if (a.type !== "Repos de garde") {
          countByDate[a.date] = (countByDate[a.date] || 0) + 1;
        }
      });

      let rowsHtml = "";
      if (filtered.length === 0) {
        rowsHtml = `<tr><td colspan="6" style="text-align:center; padding:18px; color:var(--text-muted);">Aucun congé enregistré. Utilisez le bouton "+ Ajouter" en haut à droite.</td></tr>`;
      } else {
        filtered.forEach(a => {
          const iObj = getInterneById(a.interneId);
          const simCount = countByDate[a.date] || 1;
          const isOverLimit = simCount > 2;

          rowsHtml += `
            <tr>
              <td style="font-weight:700;">${formatDateFr(a.date, true)}</td>
              <td>${iObj.shortName}</td>
              <td><span class="poste-pill ${a.type.includes('garde') ? 'poste-rg' : 'poste-vac'}">${a.type}</span></td>
              <td style="color:var(--text-muted);">${a.comment || "—"}</td>
              <td>
                ${isOverLimit
                  ? `<span class="poste-pill poste-rg">${simCount} absents (max 2)</span>`
                  : `<span class="poste-pill poste-vac">OK (${simCount}/2)</span>`}
              </td>
              <td>
                <button class="btn btn-sm" onclick="deleteAbsence('${a.id}')" style="color:#DC2626;">Supprimer</button>
              </td>
            </tr>
          `;
        });
      }

      return `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Congés & Repos de garde</div>
              <div style="font-size:12px; color:var(--text-muted);">Maximum 2 internes absents en même temps • Éviter mardi et vendredi pour les jours isolés</div>
            </div>
            <button class="btn btn-sm btn-primary" onclick="openAbsenceModal()">+ Poser un congé</button>
          </div>

          <div class="week-table-wrap">
            <table class="planning-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Interne</th>
                  <th>Type</th>
                  <th>Note</th>
                  <th>Statut</th>
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
      const target = defaultInterneId || ((!isChefId(selectedInterneId) && selectedInterneId !== "all" && selectedInterneId !== "all_chefs") ? selectedInterneId : "gabriel");
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
        alert("Vérifiez les dates.");
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
      showToast(`Congé enregistré (${addedDates.length} j.)`);
      pushStateToCloud({ syncAbsenceSheet: true, addedDates, interneName: iObj.fullName, absType: type });
    }

    function deleteAbsence(absId) {
      const target = (STATE.absences || []).find(x => x.id === absId);
      STATE.absences = (STATE.absences || []).filter(x => x.id !== absId);
      saveStateLocal();
      renderAll();
      showToast("Congé supprimé");
      pushStateToCloud({ syncAbsenceSheet: true, deletedAbsence: target });
    }

    /* =========================================================================
     * ONGLET 3 : COURS & CAS (BIBLIO / CAS / COURS AUX INTERNES / BONE CLUB / CRA)
     * ========================================================================= */
    function getPresTypeMeta(p) {
      if (p.type === "cas_mardi") {
        return { badgeClass: "poste-irm", shortType: "Cas • 12h30", modalLabel: "Cas clinique (12h30)", typeLabel: "Cas Clinique" };
      }
      if (p.type === "cours_internes") {
        return { badgeClass: "poste-cs", shortType: "Cours aux internes • 12h30", modalLabel: "Cours aux internes (12h30)", typeLabel: "Cours aux internes" };
      }
      if (p.type === "bone_club") {
        return { badgeClass: "poste-gestes", shortType: `Bone Club • ${p.horaire || "18h–20h"}`, modalLabel: `Bone Club (${p.horaire || "18h00–20h00"})`, typeLabel: "Bone Club Cochin" };
      }
      if (p.type === "confrontation_anapath") {
        return { badgeClass: "poste-echo", shortType: `CRA Anapath • ${p.horaire || "14h15"}`, modalLabel: `Confrontation Radio-Anapath (${p.horaire || "14h15–16h00"})`, typeLabel: "CRA Anapath" };
      }
      return { badgeClass: "poste-tdm", shortType: "Biblio • 12h30", modalLabel: "Biblio (12h30)", typeLabel: "Biblio" };
    }

    function isSwitchablePresType(type) {
      return type === "cas_mardi" || type === "biblio_vendredi" || type === "cours_internes";
    }

    function switchPresentationType(presId, newType, ev) {
      if (ev && ev.stopPropagation) ev.stopPropagation();
      const p = (STATE.presentations || []).find(x => x.id === presId);
      if (!p) return;
      p.type = newType;
      const meta = getPresTypeMeta(p);
      p.typeLabel = meta.typeLabel;
      saveStateLocal();
      renderAll();
      showToast(`Format changé : ${meta.typeLabel}`);
      pushStateToCloud({ syncStaffSheet: true });
    }

    function cyclePresentationType(presId, ev) {
      if (ev && ev.stopPropagation) ev.stopPropagation();
      const p = (STATE.presentations || []).find(x => x.id === presId);
      if (!p) return;
      const order = ["biblio_vendredi", "cas_mardi", "cours_internes"];
      const idx = order.indexOf(p.type);
      const nextType = order[(idx + 1) % order.length];
      switchPresentationType(presId, nextType);
    }

    function renderPresentationsTab() {
      let list = (STATE.presentations || []).slice().sort((a, b) => a.date.localeCompare(b.date));

      if (presFilter === "cas_mardi") list = list.filter(p => p.type === "cas_mardi");
      else if (presFilter === "biblio_vendredi") list = list.filter(p => p.type === "biblio_vendredi");
      else if (presFilter === "cours_internes") list = list.filter(p => p.type === "cours_internes");
      else if (presFilter === "bone_club") list = list.filter(p => p.type === "bone_club");
      else if (presFilter === "confrontation_anapath") list = list.filter(p => p.type === "confrontation_anapath");
      else if (presFilter === "mine" && selectedInterneId !== "all" && !isChefId(selectedInterneId)) {
        const myObj = getInterneById(selectedInterneId);
        list = list.filter(p => p.interneId === selectedInterneId || (p.interneName && myObj && p.interneName.toLowerCase().includes(myObj.shortName.toLowerCase())));
      }

      let rowsHtml = "";
      list.forEach(p => {
        const iObj = getInterneById(p.interneId);
        const isDJ = Boolean(iObj.isDJ || iObj.id === "oussama");
        const isMe = (selectedInterneId !== "all" && (p.interneId === selectedInterneId || (p.interneName && iObj && p.interneName.toLowerCase().includes(getInterneById(selectedInterneId).shortName.toLowerCase()))));
        const meta = getPresTypeMeta(p);
        const lieuHtml = p.salle ? `<div style="font-size:11px; color:var(--text-muted); margin-top:2px;">📍 ${p.salle}</div>` : "";
        const canSwitch = isSwitchablePresType(p.type);
        const switcherHtml = canSwitch ? `
          <div>
            <div class="pres-type-switcher" title="Changer entre Biblio, Cas et Cours aux internes">
              <button type="button" class="pres-type-btn ${p.type === 'biblio_vendredi' ? 'active-biblio' : ''}" onclick="switchPresentationType('${p.id}', 'biblio_vendredi', event)">Biblio</button>
              <button type="button" class="pres-type-btn ${p.type === 'cas_mardi' ? 'active-cas' : ''}" onclick="switchPresentationType('${p.id}', 'cas_mardi', event)">Cas</button>
              <button type="button" class="pres-type-btn ${p.type === 'cours_internes' ? 'active-cours' : ''}" onclick="switchPresentationType('${p.id}', 'cours_internes', event)">Cours aux internes</button>
            </div>
          </div>
        ` : "";

        rowsHtml += `
          <tr style="${isMe ? 'background:#EFF6FF;' : ''}">
            <td style="font-weight:700; white-space:nowrap;">${formatDateFr(p.date, true)}</td>
            <td>
              <span class="poste-pill ${meta.badgeClass}">${meta.shortType}</span>
              ${switcherHtml}
            </td>
            <td>
              <span class="interne-badge ${isMe ? 'highlight-me' : ''}" onclick="openPresentationModal('${p.id}')">
                <span style="width:7px;height:7px;border-radius:50%;background:${iObj.color};display:inline-block;"></span>
                ${p.interneName || iObj.shortName}
                ${iObj.isSocle && (!p.interneName || p.interneName === iObj.shortName) ? `<span class="tag-sm">Socle</span>` : ""}
                ${isDJ && (!p.interneName || p.interneName === iObj.shortName) ? `<span class="tag-dj">DJ</span>` : ""}
              </span>
            </td>
            <td>
              ${p.sujet
                ? `<strong>${p.sujet}</strong>`
                : `<span style="color:#B45309; font-weight:600; cursor:pointer;" onclick="openPresentationModal('${p.id}')">+ Ajouter le sujet</span>`}
              ${lieuHtml}
            </td>
            <td>
              ${p.coursChef
                ? `<span style="color:#0284C7; font-weight:700;">${p.chefIntervenant || ''}</span> ${p.coursChef}`
                : `<span style="color:var(--text-muted);">${p.notes || '—'}</span>`}
            </td>
            <td>
              <div style="display:flex; gap:5px; flex-wrap:wrap;">
                ${canSwitch ? `<button class="btn btn-sm" onclick="cyclePresentationType('${p.id}', event)" title="Basculer entre Biblio, Cas et Cours aux internes">⇄ Format</button>` : ""}
                <button class="btn btn-sm" onclick="openPresentationModal('${p.id}')">Modifier</button>
              </div>
            </td>
          </tr>
        `;
      });

      return `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Cas, Biblio, Cours aux internes, Bone Club & CRA Anapath</div>
              <div style="font-size:12px; color:var(--text-muted);">Cliquez sur <strong>Biblio / Cas / Cours aux internes</strong> (ou ⇄ Format) sur une ligne pour changer le type de séance en 1 clic</div>
            </div>
            <div class="segmented" style="flex-wrap:wrap;">
              <button class="seg-btn ${presFilter === 'all' ? 'active' : ''}" onclick="setPresFilter('all')">Tous</button>
              <button class="seg-btn ${presFilter === 'cas_mardi' ? 'active' : ''}" onclick="setPresFilter('cas_mardi')">Cas</button>
              <button class="seg-btn ${presFilter === 'biblio_vendredi' ? 'active' : ''}" onclick="setPresFilter('biblio_vendredi')">Biblio</button>
              <button class="seg-btn ${presFilter === 'cours_internes' ? 'active' : ''}" onclick="setPresFilter('cours_internes')">Cours aux internes</button>
              <button class="seg-btn ${presFilter === 'bone_club' ? 'active' : ''}" onclick="setPresFilter('bone_club')">Bone Club (18h)</button>
              <button class="seg-btn ${presFilter === 'confrontation_anapath' ? 'active' : ''}" onclick="setPresFilter('confrontation_anapath')">CRA Anapath (14h15)</button>
              <button class="seg-btn ${presFilter === 'mine' ? 'active' : ''}" onclick="setPresFilter('mine')">Mes dates</button>
            </div>
          </div>

          <div class="week-table-wrap">
            <table class="planning-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Créneau / Format</th>
                  <th>Interne / DJ</th>
                  <th>Sujet / Lieu</th>
                  <th>Cours Chef / Modérateurs</th>
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
      if (f === "mine" && (selectedInterneId === "all" || isChefId(selectedInterneId))) selectedInterneId = "gabriel";
      renderAll();
    }

    function setModalPresType(newType) {
      const inp = document.getElementById("presTypeInput");
      if (inp) inp.value = newType;
      const btnBiblio = document.getElementById("modalTypeBtnBiblio");
      const btnCas = document.getElementById("modalTypeBtnCas");
      const btnCours = document.getElementById("modalTypeBtnCours");
      if (btnBiblio) btnBiblio.classList.toggle("active", newType === "biblio_vendredi");
      if (btnCas) btnCas.classList.toggle("active", newType === "cas_mardi");
      if (btnCours) btnCours.classList.toggle("active", newType === "cours_internes");
    }

    function openPresentationModal(presId) {
      const list = (STATE.presentations || []).slice().sort((a, b) => a.date.localeCompare(b.date));
      const p = list.find(x => x.id === presId) || list[0];
      if (!p) return;

      const dateSel = document.getElementById("presDateSelect");
      dateSel.innerHTML = list.map(item => {
        const meta = getPresTypeMeta(item);
        const lbl = `${formatDateFr(item.date, true)} — ${meta.shortType} (${item.interneName})`;
        return `<option value="${item.id}" ${item.id === p.id ? 'selected' : ''}>${lbl}</option>`;
      }).join("");

      populatePresentationModalFields(p);
      document.getElementById("modalPresentation").classList.add("open");
    }

    function onPresDateChange(presId) {
      const p = (STATE.presentations || []).find(x => x.id === presId);
      if (p) populatePresentationModalFields(p);
    }

    function populatePresentationModalFields(p) {
      const meta = getPresTypeMeta(p);
      document.getElementById("presIdInput").value = p.id;
      document.getElementById("presModalTitle").textContent = `${meta.modalLabel} — ${formatDateFr(p.date)}`;
      document.getElementById("presDateDisplay").value = formatDateFr(p.date, true);

      const typeGroup = document.getElementById("presTypeGroup");
      if (typeGroup) {
        if (isSwitchablePresType(p.type)) {
          typeGroup.style.display = "block";
          setModalPresType(p.type);
        } else {
          typeGroup.style.display = "none";
          document.getElementById("presTypeInput").value = p.type;
        }
      }

      const sel = document.getElementById("presInterneSelect");
      sel.innerHTML = STATE.internes.map(i => `<option value="${i.id}" ${i.id === p.interneId ? 'selected' : ''}>${i.fullName}${i.isDJ || i.id === 'oussama' ? ' (DJ)' : (i.isSocle ? ' (Socle)' : '')}</option>`).join("");
      document.getElementById("presSujetInput").value = p.sujet || "";
      document.getElementById("presChefInput").value = p.coursChef ? `${p.chefIntervenant ? p.chefIntervenant + ' — ' : ''}${p.coursChef}` : "";
    }

    function savePresentationForm() {
      const pid = document.getElementById("presIdInput").value;
      const p = (STATE.presentations || []).find(x => x.id === pid);
      if (!p) return;

      const iid = document.getElementById("presInterneSelect").value;
      const iObj = getInterneById(iid);
      const sujet = document.getElementById("presSujetInput").value.trim();
      const chefRaw = document.getElementById("presChefInput").value.trim();
      const chosenType = document.getElementById("presTypeInput") ? document.getElementById("presTypeInput").value : p.type;

      if (chosenType && isSwitchablePresType(p.type)) {
        p.type = chosenType;
        p.typeLabel = getPresTypeMeta(p).typeLabel;
      }

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
      showToast("Séance enregistrée");
      pushStateToCloud({ syncStaffSheet: true });
    }

    /* =========================================================================
     * ONGLET 4 : RÉUNIONS
     * ========================================================================= */
    function renderReunionsTab() {
      const meets = (STATE.meetings || []).slice().sort((a, b) => a.date.localeCompare(b.date));
      const recurring = STATE.recurringStaffs || [];

      let meetsHtml = meets.map(m => `
        <div class="card" style="background:#F8FAFC; margin-bottom:8px; padding:11px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:4px;">
            <div>
              <span class="poste-pill ${m.mandatory ? 'poste-gestes' : 'poste-echo'}" style="margin-right:6px;">
                ${m.mandatory ? 'Obligatoire' : m.category}
              </span>
              <strong>${m.title}</strong>
            </div>
            <div style="font-weight:700; color:var(--primary); font-size:12px;">
              ${formatDateFr(m.date, true)} • ${m.horaire}
            </div>
          </div>
          <div style="font-size:12px; color:#334155; margin-bottom:4px;">${m.description}</div>
          <div style="font-size:11.5px; color:var(--text-muted);">
            Lieu : ${m.location} • Par ${m.sender}
          </div>
        </div>
      `).join("");

      let recHtml = recurring.map(r => `
        <div class="card" style="margin:0; padding:10px; background:#F8FAFC;">
          <div style="font-weight:800; color:var(--primary); font-size:12.5px; margin-bottom:6px;">${r.day}</div>
          ${r.items.map(it => `
            <div style="margin-bottom:5px; font-size:12px;">
              <strong>${it.horaire} :</strong> ${it.title}
              <div style="font-size:11px; color:var(--text-muted);">${it.referent}</div>
            </div>
          `).join("")}
        </div>
      `).join("");

      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Réunions du service</div>
            <button class="btn btn-sm btn-primary" onclick="openMeetingModal()">+ Réunion</button>
          </div>
          ${meetsHtml}
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Staffs hebdomadaires</div>
          </div>
          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:8px;">${recHtml}</div>
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
        alert("Indiquez la date et le titre.");
        return;
      }

      STATE.meetings.push({
        id: "reunion-" + Date.now(),
        date,
        horaire,
        title,
        category: "Réunion",
        sender,
        location,
        description,
        mandatory: true
      });

      saveStateLocal();
      closeModal("modalMeeting");
      renderAll();
      showToast("Réunion ajoutée");
      pushStateToCloud({});
    }

    /* =========================================================================
     * ONGLET 5 : ANNUAIRE COCHIN
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
                <div style="font-weight:700; color:#0F172A;">${c.name}</div>
                <div style="font-size:11px; color:var(--text-muted);">${c.role || ""}</div>
              </td>
              <td><span class="poste-pill poste-irm">${c.poste || "—"}</span></td>
              <td>
                ${c.phone
                  ? `<a href="tel:${telHref}" class="poste-pill poste-echo" style="text-decoration:none;">${c.phone}</a>`
                  : "—"}
              </td>
              <td style="font-size:12px; color:#475569;">${c.building || "Cochin"}</td>
            </tr>
          `;
        }).join("");

        groupsHtml += `
          <div class="card" style="margin-bottom:10px;">
            <div class="card-header">
              <div class="card-title">${cat}</div>
            </div>
            <div class="week-table-wrap">
              <table class="planning-table" style="min-width:480px;">
                <thead>
                  <tr>
                    <th>Contact</th>
                    <th style="width:130px;">Poste / DECT</th>
                    <th style="width:150px;">Ligne directe</th>
                    <th style="width:150px;">Lieu</th>
                  </tr>
                </thead>
                <tbody>${rows}</tbody>
              </table>
            </div>
          </div>
        `;
      });

      if (!groupsHtml) {
        groupsHtml = `<div class="card" style="text-align:center; color:var(--text-muted); padding:20px;">Aucun numéro trouvé.</div>`;
      }

      return `
        <div class="card">
          <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
            <input
              type="text"
              class="form-control"
              style="flex:1; min-width:200px;"
              placeholder="Rechercher un nom, poste (ex: 12483), console, service..."
              value="${annuaireSearch.replace(/"/g, '&quot;')}"
              oninput="onAnnuaireSearch(this.value)"
            />
            <div class="segmented" style="flex-wrap:wrap;">
              <button class="seg-btn ${annuaireCategory === 'all' ? 'active' : ''}" onclick="setAnnuaireCategory('all')">Tous</button>
              <button class="seg-btn ${annuaireCategory === 'Radiologie B — Secrétariats & Consoles' ? 'active' : ''}" onclick="setAnnuaireCategory('Radiologie B — Secrétariats & Consoles')">Consoles</button>
              <button class="seg-btn ${annuaireCategory === 'Radiologie B — Équipe Médicale (Chefs & Seniors)' ? 'active' : ''}" onclick="setAnnuaireCategory('Radiologie B — Équipe Médicale (Chefs & Seniors)')">Médecins</button>
              <button class="seg-btn ${annuaireCategory === 'Services Partenaires (Ortho, Rhumato, Anesth, Anapath)' ? 'active' : ''}" onclick="setAnnuaireCategory('Services Partenaires (Ortho, Rhumato, Anesth, Anapath)')">Services</button>
            </div>
            <button class="btn btn-sm btn-primary" onclick="openPhoneContactModal()">+ Numéro</button>
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
        alert("Indiquez le nom et le numéro.");
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
      showToast("Numéro ajouté");
      pushStateToCloud({});
    }

    /* =========================================================================
     * MODIFICATION D'UNE VACATION D'INTERNE
     * ========================================================================= */
    function openVacationEditModal(iso, iid) {
      const targetIso = STATE.schedule[iso] ? iso : "2026-11-02";
      const targetIid = getInterneById(iid).id;

      document.getElementById("vacEditDate").value = targetIso;
      const intSelect = document.getElementById("vacEditInterneId");
      intSelect.innerHTML = STATE.internes.map(i => `<option value="${i.id}" ${i.id === targetIid ? 'selected' : ''}>${i.fullName}</option>`).join("");

      refreshVacationModalFields();
      document.getElementById("modalVacationEdit").classList.add("open");
    }

    function refreshVacationModalFields() {
      const iso = document.getElementById("vacEditDate").value;
      const iid = document.getElementById("vacEditInterneId").value;
      const iObj = getInterneById(iid);
      const dObj = STATE.schedule[iso];
      const slot = (dObj && dObj.byInterne && dObj.byInterne[iid]) ? dObj.byInterne[iid] : { am: "TDM SAU", pm: "TDM SAU", note: "" };

      document.getElementById("vacEditHeader").value = `${iObj.fullName} — ${formatDateFr(iso, true)}`;
      const options = STATE.postesMeta.map(p => p.code);
      document.getElementById("vacEditAm").innerHTML = options.map(c => `<option value="${c}" ${c === slot.am ? 'selected' : ''}>${c}</option>`).join("");
      document.getElementById("vacEditPm").innerHTML = options.map(c => `<option value="${c}" ${c === slot.pm ? 'selected' : ''}>${c}</option>`).join("");
      document.getElementById("vacEditNote").value = slot.note || "";
    }

    function saveSingleVacation() {
      const iso = document.getElementById("vacEditDate").value;
      const iid = document.getElementById("vacEditInterneId").value;
      const am = document.getElementById("vacEditAm").value;
      const pm = document.getElementById("vacEditPm").value;
      const note = document.getElementById("vacEditNote").value.trim();

      // Vérification stricte : maximum 2 demi-offs ('1/2 journée libre') par semaine par interne
      const monIso = getMondayOfWeek(iso);
      let weekDemiOffs = 0;
      for (let d = 0; d < 5; d++) {
        const curIso = addDaysIso(monIso, d);
        if (curIso === iso) {
          if (am === "1/2 journée libre") weekDemiOffs++;
          if (pm === "1/2 journée libre") weekDemiOffs++;
        } else {
          const dayObj = STATE.schedule[curIso];
          if (dayObj && !dayObj.holiday && dayObj.byInterne && dayObj.byInterne[iid]) {
            if (dayObj.byInterne[iid].am === "1/2 journée libre") weekDemiOffs++;
            if (dayObj.byInterne[iid].pm === "1/2 journée libre") weekDemiOffs++;
          }
        }
      }
      if (weekDemiOffs > 2) {
        alert(`Règle du service : 2 demi-offs par semaine maximum par interne (${weekDemiOffs} demi-offs sur cette semaine).`);
        return;
      }

      if (!STATE.customVacations) STATE.customVacations = {};
      STATE.customVacations[iso + "__" + iid] = { am, pm, note };

      saveStateLocal();
      closeModal("modalVacationEdit");
      renderAll();
      showToast("Poste mis à jour");
      pushStateToCloud({});
    }

    function resetSingleVacation() {
      const iso = document.getElementById("vacEditDate").value;
      const iid = document.getElementById("vacEditInterneId").value;
      if (STATE.customVacations) delete STATE.customVacations[iso + "__" + iid];
      saveStateLocal();
      closeModal("modalVacationEdit");
      renderAll();
      showToast("Poste réinitialisé");
      pushStateToCloud({});
    }

    function closeModal(id) {
      document.getElementById(id).classList.remove("open");
    }

    /* =========================================================================
     * SYNCHRONISATION CLOUD & GOOGLE SHEET
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

        var syncOpts = ${JSON.stringify(opts)};
        if (syncOpts.syncAbsenceSheet) {
          try {
            var ssInt = SpreadsheetApp.openById('${INTERNES_SHEET_ID}');
            var shAbs = ssInt.getSheetByName('Planning Absence');
            if (shAbs) {
              var data = shAbs.getDataRange().getDisplayValues();
              var colMap = { 'Repos de garde': 2, 'CA 1': 3, 'CA 2': 4, 'CF': 5, 'Autre': 6 };
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
        if (statusEl) statusEl.textContent = "Synchronisé";
      } catch (err) {
        if (statusEl) statusEl.textContent = "Local";
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
              STATE.presentations = mergePresentationsList(INITIAL_DATA.presentations, remote.presentations);
            }
            if (Array.isArray(remote.meetings) && remote.meetings.length > 0) {
              STATE.meetings = mergeMeetingsList(INITIAL_DATA.meetings, remote.meetings);
            }
            if (Array.isArray(remote.phoneDirectory) && remote.phoneDirectory.length > 0) {
              const map = {};
              (STATE.phoneDirectory || []).forEach(c => { map[c.id] = c; });
              remote.phoneDirectory.forEach(c => { if (c && c.id) map[c.id] = c; });
              STATE.phoneDirectory = Object.values(map);
            }
          }
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
                    comment: "Google Sheet"
                  });
                }
              }
            }
          });
          saveStateLocal();
          renderAll();
        }
        if (statusEl) statusEl.textContent = "Synchronisé";
        if (manual) showToast("Synchronisé");
      } catch (e) {
        if (statusEl) statusEl.textContent = "Hors-ligne";
      }
    }

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

    assert_zero_patient_data(html_out)

    INDEX_FILE.write_text(html_out, encoding="utf-8")

    manifest = {
        "name": "Radio B Cochin — Planning Internes & Chefs",
        "short_name": "Radio B Cochin",
        "description": "Planning des internes et chefs de Radiologie B à Cochin.",
        "start_url": "./index.html",
        "display": "standalone",
        "background_color": "#F8FAFC",
        "theme_color": "#F8FAFC",
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

    sw_code = """const CACHE_NAME = 'cochin-internes-v4';
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
  <rect width="256" height="256" rx="56" fill="#0284C7"/>
  <text x="128" y="148" text-anchor="middle" fill="#FFFFFF" font-family="-apple-system, sans-serif" font-weight="800" font-size="84">RB</text>
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
