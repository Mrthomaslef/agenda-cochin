#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cochin Radio B — Espace Internes (Semestre Hiver 2026–2027)
Générateur et synchroniseur de l'application web mobile (PWA) dédiée aux internes.
APPLICATION 100% INDÉPENDANTE ET SÉPARÉE :
- Répertoire dédié : /Users/thomaslefevre/Documents/Agendainterventionnel/agenda-internes/
- ZÉRO donnée patient (vérifié automatiquement par assert_zero_patient_data).
- Synchronisation directe avec le Google Sheet officiel 'Planning Interne CCH - Hiver 26'
  (ID: 10sPMOg9GPXqsSItnUfuYn2Ke0im34p5EEyKk5A0hEF8) et PropertiesService ('cochin_internes_state_v1').
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import re
import ssl
import urllib.request

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "internes_data.json"
INDEX_FILE = BASE_DIR / "index.html"
MANIFEST_FILE = BASE_DIR / "manifest.json"
SW_FILE = BASE_DIR / "sw.js"
ICON_FILE = BASE_DIR / "icon.svg"
LAUNCHER_FILE = BASE_DIR / "Lancer_Agenda_Internes.command"

INTERNES_SHEET_ID = "10sPMOg9GPXqsSItnUfuYn2Ke0im34p5EEyKk5A0hEF8"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxLGqUevVWi36mNQ7WNoY2uhRsYLdsG_gQcscMPkP1GcQEt0LgdhGIuzYL2SM-uTcPq/exec"
CLOUD_PROP_KEY = "cochin_internes_state_v1"

# Liste officielle des internes du semestre Hiver 2026-2027 (Service de Radiologie B - Pr A. Feydy)
INTERNES_LIST = [
    {
        "id": "gabriel",
        "prenom": "Gabriel",
        "nom": "COTTIN",
        "fullName": "Gabriel COTTIN",
        "shortName": "Gabriel",
        "initials": "GC",
        "color": "#38BDF8",
        "role": "Interne DES Radiologie",
        "semestre": "Hiver 2026–2027",
        "startIso": "2026-11-02",
    },
    {
        "id": "noe",
        "prenom": "Noé",
        "nom": "GRANDVAL",
        "fullName": "Noé GRANDVAL",
        "shortName": "Noé",
        "initials": "NG",
        "color": "#A855F7",
        "role": "Interne DES Radiologie",
        "semestre": "Hiver 2026–2027",
        "startIso": "2026-11-02",
    },
    {
        "id": "marwane",
        "prenom": "Marwane",
        "nom": "HAMMAMI",
        "fullName": "Marwane HAMMAMI",
        "shortName": "Marwane",
        "initials": "MH",
        "color": "#14B8A6",
        "role": "Interne DES Radiologie",
        "semestre": "Hiver 2026–2027",
        "startIso": "2026-11-02",
    },
    {
        "id": "milan",
        "prenom": "Milan",
        "nom": "KORSEC",
        "fullName": "Milan KORSEC",
        "shortName": "Milan",
        "initials": "MK",
        "color": "#F59E0B",
        "role": "Interne DES Radiologie",
        "semestre": "Hiver 2026–2027",
        "startIso": "2026-11-02",
    },
    {
        "id": "nathanael",
        "prenom": "Nathanaël",
        "nom": "SEBBAN",
        "fullName": "Nathanaël SEBBAN",
        "shortName": "Nathanaël",
        "initials": "NS",
        "color": "#F43F5E",
        "role": "Interne DES Radiologie",
        "semestre": "Hiver 2026–2027",
        "startIso": "2026-11-02",
    },
    {
        "id": "oussama",
        "prenom": "Oussama",
        "nom": "TALIB",
        "fullName": "Oussama TALIB",
        "shortName": "Oussama",
        "initials": "OT",
        "color": "#22C55E",
        "role": "Interne DES Radiologie",
        "semestre": "Hiver 2026–2027",
        "startIso": "2026-11-02",
    },
]

# Liste officielle des Chefs de Clinique, Assistants & Seniors de Radiologie B (Cochin)
CHEFS_LIST = [
    {
        "id": "chef_tl",
        "code": "TL",
        "prenom": "Thomas",
        "nom": "LEFÈVRE",
        "fullName": "Dr Thomas LEFÈVRE",
        "shortName": "Dr T. Lefèvre (TL)",
        "initials": "TL",
        "color": "#38BDF8",
        "role": "Chef de Clinique / Assistant — RI & Ostéo-Articulaire",
        "posteTel": "12489 / 12163 (DECT 12504)",
        "gardeMatch": ["LEFEVRE", "LEFÈVRE"],
    },
    {
        "id": "chef_hm",
        "code": "HM",
        "prenom": "Hippolyte",
        "nom": "MONNIER",
        "fullName": "Dr Hippolyte MONNIER",
        "shortName": "Dr H. Monnier (HM)",
        "initials": "HM",
        "color": "#A855F7",
        "role": "Chef de Clinique Assistant — Radiologie B",
        "posteTel": "12488 / 12489",
        "gardeMatch": ["MONNIER"],
    },
    {
        "id": "chef_mh",
        "code": "MH",
        "prenom": "Macil",
        "nom": "HAMADOUCHE",
        "fullName": "Dr Macil HAMADOUCHE",
        "shortName": "Dr M. Hamadouche (MH)",
        "initials": "MH",
        "color": "#F59E0B",
        "role": "Assistant Spécialiste — Radiologie B & RI",
        "posteTel": "DECT 12504 / 12488",
        "gardeMatch": ["HAMADOUCHE"],
    },
    {
        "id": "chef_sl",
        "code": "SL",
        "prenom": "Stéphano",
        "nom": "LUSI",
        "fullName": "Dr Stéphano LUSI",
        "shortName": "Dr S. Lusi (SL)",
        "initials": "SL",
        "color": "#14B8A6",
        "role": "Chef de Clinique Assistant — Radiologie B",
        "posteTel": "12488 / 12489",
        "gardeMatch": ["LUSI"],
    },
    {
        "id": "chef_ya",
        "code": "YA",
        "prenom": "Yazid",
        "nom": "ALLEL",
        "fullName": "Dr Yazid ALLEL",
        "shortName": "Dr Y. Allel (YA)",
        "initials": "YA",
        "color": "#F43F5E",
        "role": "Chef de Clinique Assistant — Radiologie B",
        "posteTel": "12488 / 12489",
        "gardeMatch": ["ALLEL"],
    },
    {
        "id": "chef_mp",
        "code": "MP",
        "prenom": "Marie-Pauline",
        "nom": "TALABARD",
        "fullName": "Dr Marie-Pauline TALABARD",
        "shortName": "Dr M-P. Talabard (MP)",
        "initials": "MP",
        "color": "#EC4899",
        "role": "Chef de Clinique Assistant — Imagerie Ostéo-Articulaire & RI",
        "posteTel": "12489",
        "gardeMatch": ["TALABARD"],
    },
    {
        "id": "chef_al",
        "code": "AL",
        "prenom": "Amandine",
        "nom": "LAPORTE",
        "fullName": "Dr Amandine LAPORTE",
        "shortName": "Dr A. Laporte (AL)",
        "initials": "AL",
        "color": "#6366F1",
        "role": "PH / Senior — Référente Sarcomes & Radiologie B",
        "posteTel": "12483 / 12488",
        "gardeMatch": ["LAPORTE"],
    },
    {
        "id": "chef_ac",
        "code": "AC",
        "prenom": "Adina",
        "nom": "COSTEA",
        "fullName": "Dr Adina COSTEA",
        "shortName": "Dr A. Costea (AC)",
        "initials": "AC",
        "color": "#22C55E",
        "role": "Praticien — Radiologie B",
        "posteTel": "12483",
        "gardeMatch": ["COSTEA"],
    },
    {
        "id": "chef_mihoubi",
        "code": "MIHOUBI",
        "prenom": "Fadila",
        "nom": "MIHOUBI BOUVIER",
        "fullName": "Dr Fadila MIHOUBI BOUVIER",
        "shortName": "Dr F. Mihoubi",
        "initials": "FM",
        "color": "#06B6D4",
        "role": "PH — Responsable Pédagogique Internes & Staffs",
        "posteTel": "12483",
        "gardeMatch": ["MIHOUBI"],
    },
    {
        "id": "chef_feydy",
        "code": "FEYDY",
        "prenom": "Antoine",
        "nom": "FEYDY",
        "fullName": "Pr Antoine FEYDY",
        "shortName": "Pr A. Feydy",
        "initials": "AF",
        "color": "#3B82F6",
        "role": "PU-PH, Chef de Service — Radiologie B",
        "posteTel": "12483 / 12481",
        "gardeMatch": ["FEYDY"],
    },
    {
        "id": "chef_drape",
        "code": "DRAPE",
        "prenom": "Jean-Luc",
        "nom": "DRAPÉ",
        "fullName": "Pr Jean-Luc DRAPÉ",
        "shortName": "Pr J-L. Drapé",
        "initials": "JD",
        "color": "#8B5CF6",
        "role": "PU-PH — Radiologie B",
        "posteTel": "12502 / 12480",
        "gardeMatch": ["DRAPE", "DRAPÉ"],
    },
    {
        "id": "chef_yang",
        "code": "YANG",
        "prenom": "Malika",
        "nom": "YANG",
        "fullName": "Dr YANG",
        "shortName": "Dr Yang",
        "initials": "YG",
        "color": "#10B981",
        "role": "Praticien — IRM, Écho & Staff Rachis/Rhumato",
        "posteTel": "12483",
        "gardeMatch": ["YANG"],
    },
]

# Postes officiels de la trame des internes de Radiologie B (Cochin)
POSTES_META = [
    {"code": "TDM SAU", "label": "TDM SAU (Ollier)", "cat": "tdm", "color": "#F59E0B"},
    {"code": "IRM 3T", "label": "IRM 3T", "cat": "irm", "color": "#A855F7"},
    {"code": "IRM 1,5T", "label": "IRM 1,5T", "cat": "irm", "color": "#8B5CF6"},
    {"code": "IRM", "label": "IRM (Après-midi)", "cat": "irm", "color": "#A855F7"},
    {"code": "ECHO", "label": "Échographie Ostéo-Articulaire", "cat": "echo", "color": "#14B8A6"},
    {"code": "GESTES (C)", "label": "Gestes / Interventionnel (C)", "cat": "gestes", "color": "#F43F5E"},
    {"code": "SCAN ACHARD", "label": "Scanner Achard 1 (Interventionnel)", "cat": "gestes", "color": "#EC4899"},
    {"code": "ALLURA", "label": "Salle Allura (Vasculaire / Os)", "cat": "gestes", "color": "#E11D48"},
    {"code": "TDM OLLIER DIAG", "label": "TDM Ollier Diag", "cat": "tdm", "color": "#38BDF8"},
    {"code": "LECTURE/CS", "label": "Lecture / Consultation", "cat": "cs", "color": "#3B82F6"},
    {"code": "1/2 journée libre", "label": "1/2 journée libre", "cat": "off", "color": "#64748B"},
    {"code": "RG", "label": "Repos de garde (RG)", "cat": "rg", "color": "#EF4444"},
    {"code": "VACANCES", "label": "Congés / Vacances (CA/CF)", "cat": "vac", "color": "#10B981"},
]

# Programme officiel des 25 cours d'Imagerie Ostéo-Articulaire (Feuille 3 du Google Sheet)
CURRICULUM_COURS = [
    "Épaule : Pathologies de la coiffe des rotateurs",
    "Épaule : Instabilité gléno-humérale",
    "Épaule : Pathologies nerveuses de la ceinture scapulaire",
    "Épaule : Capsulite rétractile - Omarthrose - Ostéochondrite - Scapula alata - Articulation AC/SC - Grand pectoral",
    "Rachis cervical : Pathologies mécaniques",
    "Rachis thoraco-lombaire : Pathologies dégénératives (discopathie, hernie, rachialgie / radiculalgies)",
    "Rachis thoraco-lombaire : Instabilité - Ossifications ligamentaires - Fractures vertébrales et sacrum - Scoliose",
    "Coude : Pathologies du compartiment médial et latéral",
    "Coude : Pathologies du compartiment antérieur et postérieur et pathologies diverses",
    "Poignet : Pathologies osseuses dégénératives",
    "Poignet : Pathologies ligamentaires",
    "Poignet : Pathologies tendineuses et ténosynoviales",
    "Poignet : Pathologies vasculo-nerveuses",
    "Main : Pathologies dégénératives / tendineuses de la main et des doigts (I)",
    "Main : Pathologies dégénératives / tendineuses de la main et des doigts (II)",
    "Hanche : Pathologies osseuses et articulaires",
    "Hanche : Pathologies abarticulaires",
    "Ceinture pelvienne : Articulations sacro-iliaques, symphyse pubienne & plexus lombo-sacré",
    "Genou : Pathologies antérieures",
    "Genou : Ménisques et ligaments croisés",
    "Genou : Plans collatéraux et postérieurs, Gonarthrose, fractures de contrainte, ostéonécroses, SDRC1",
    "Jambe & Cheville : Pathologies de la jambe et du mollet / Tendon calcanéen & Aponévrose plantaire",
    "Pied et Cheville : Tendon Tibial postérieur + Spring - LFH - Fibulaires – Extenseurs",
    "Pied et Cheville : Ligaments & Neuropathies (Morton, Baxter, tunnel tarsien)",
    "Pied et Cheville : Statique du pied - Coalition du tarse - Ostéochondroses - Arthrose de cheville et du pied",
]

# Sujets des cours des chefs du mardi (20-30 min, organisés par Dr Fadila Mihoubi Bouvier)
CHEFS_TUESDAY_COURS = [
    ("Dr Fadila MIHOUBI BOUVIER", "Introduction à la séméiologie ostéo-articulaire & organisation du staff"),
    ("Dr Thomas LEFÈVRE", "Analyse radiologique d'une prothèse totale de hanche (PTH)"),
    ("Dr Hippolyte MONNIER", "Troubles de la statique du pied : mesures et points clés"),
    ("Dr Samuel LUSI", "Tumeurs cartilagineuses : enchondrome vs tumeur cartilagineuse atypique"),
    ("Dr Youcef ALLEL", "Urgences traumatiques du poignet et du carpe au TDM SAU"),
    ("Dr Maroua HAMMOUD", "Échographie de l'épaule : protocole standardisé et pièges"),
    ("Dr Amandine LAPORTE", "Bilan d'extension et biopsie des sarcomes des tissus mous"),
    ("Dr Henri GUÉRINI", "Imagerie des prothèses du genou et conflits péri-prothétiques"),
    ("Drmalika BOUSSAID / Dr YANG", "IRM du rachis inflammatoire vs mécanique"),
    ("Pr Antoine FEYDY", "IRM de l'épaule : instabilité et bourrelet glénoïdien"),
    ("Pr Jean-Luc DRAPÉ", "Imagerie de la main et des tendons fléchisseurs/extenseurs"),
    ("Dr Marie-Pierre TALABARD", "Radiologie interventionnelle ostéo-articulaire : infiltrations & cimentoplasties"),
]

JOURS_FERIES_HIVER = {
    "2026-11-11": "Armistice 1918",
    "2026-12-25": "Jour de Noël",
    "2027-01-01": "Jour de l'An",
    "2027-03-29": "Lundi de Pâques",
}


def build_balanced_trame() -> dict:
    """
    Construit la trame hebdomadaire équilibrée sur un cycle de 6 rôles (R0..R5) pour les 6 internes principaux
    (+ intégration d'Amal El Madani en binôme/rotation dès le 14/12/2026).
    Chaque rôle R0..R5 sur une semaine de 5 jours (10 demi-journées) comporte exactement :
    - 8 vacations actives en imagerie / interventionnel / lecture
    - 2 demi-journées libres ('1/2 journée libre')
    Et en tournant d'un cran chaque semaine (r = (interne_idx + week_num) % 6),
    les 6 internes ont EXACTEMENT le même nombre de vacations totales et par modalité !
    """
    # Pour chaque jour (0=Lundi .. 4=Vendredi), attribution du rôle (0..5) aux postes Matin et Après-midi :
    # Chaque jour, les rôles 0..5 ont chacun exactement 1 poste matin et 1 poste après-midi.
    # Total par rôle sur la semaine :
    # - TDM SAU : 2 demi-journées
    # - IRM (3T / 1,5T / PM) : 2 demi-journées
    # - ECHO : 1 à 2 demi-journées
    # - GESTES (C) / SCAN ACHARD / ALLURA : 2 demi-journées
    # - TDM OLLIER DIAG / LECTURE/CS : 1 à 2 demi-journées
    # - 1/2 journée libre : 2 demi-journées exactement !
    weekly_roles = {
        0: {  # LUNDI
            "am": {
                0: "ECHO",
                1: "GESTES (C)",
                2: "TDM SAU",
                3: "IRM 3T",
                4: "1/2 journée libre",
                5: "1/2 journée libre",
            },
            "pm": {
                0: "1/2 journée libre",
                1: "TDM OLLIER DIAG",
                2: "1/2 journée libre",
                3: "TDM SAU",
                4: "IRM",
                5: "ECHO",
            },
        },
        1: {  # MARDI (Staff Cas Clinique + Cours Chef à 12h30)
            "am": {
                0: "TDM SAU",
                1: "IRM 3T",
                2: "ECHO",
                3: "GESTES (C)",
                4: "SCAN ACHARD",
                5: "IRM 1,5T",
            },
            "pm": {
                0: "SCAN ACHARD",
                1: "1/2 journée libre",
                2: "GESTES (C)",
                3: "LECTURE/CS",
                4: "TDM SAU",
                5: "ECHO",
            },
        },
        2: {  # MERCREDI
            "am": {
                0: "IRM 1,5T",
                1: "TDM OLLIER DIAG",
                2: "IRM 3T",
                3: "ECHO",
                4: "GESTES (C)",
                5: "TDM SAU",
            },
            "pm": {
                0: "GESTES (C)",
                1: "TDM SAU",
                2: "SCAN ACHARD",
                3: "1/2 journée libre",
                4: "ECHO",
                5: "IRM",
            },
        },
        3: {  # JEUDI
            "am": {
                0: "SCAN ACHARD",
                1: "TDM SAU",
                2: "1/2 journée libre",
                3: "1/2 journée libre",
                4: "ECHO",
                5: "GESTES (C)",
            },
            "pm": {
                0: "ALLURA",
                1: "IRM",
                2: "ECHO",
                3: "SCAN ACHARD",
                4: "1/2 journée libre",
                5: "TDM SAU",
            },
        },
        4: {  # VENDREDI (Biblio du vendredi)
            "am": {
                0: "1/2 journée libre",
                1: "ECHO",
                2: "TDM SAU",
                3: "IRM 3T",
                4: "IRM 1,5T",
                5: "LECTURE/CS",
            },
            "pm": {
                0: "IRM",
                1: "GESTES (C)",
                2: "TDM SAU",
                3: "ECHO",
                4: "SCAN ACHARD",
                5: "1/2 journée libre",
            },
        },
    }
    return weekly_roles


def generate_semester_schedule(absences: list[dict]) -> dict:
    """
    Génère le planning quotidien (Matin & Après-midi) du 02/11/2026 au 02/05/2027 (26 semaines)
    pour les internes du service, en intégrant automatiquement :
    - Les jours fériés
    - Les absences posées (CA 1, CA 2, CF, Repos de garde RG, Autre)
    - L'équilibrage dynamique : chaque semaine tourne équitablement entre les internes.
    """
    weekly_roles = build_balanced_trame()
    main_ids = ["gabriel", "noe", "marwane", "milan", "nathanael", "oussama"]

    # Index absences par (date_iso, interne_id) -> type d'absence
    abs_lookup = {}
    for ab in absences:
        dt = ab.get("date")
        iid = ab.get("interneId")
        atype = ab.get("type", "CA 1")
        if dt and iid:
            abs_lookup[(dt, iid)] = atype

    start_date = datetime.date(2026, 11, 2)
    end_date = datetime.date(2027, 4, 30)
    schedule = {}

    cur = start_date
    while cur <= end_date:
        iso = cur.isoformat()
        wd = cur.weekday()  # 0=Mon .. 6=Sun
        week_idx = (cur - start_date).days // 7

        if wd >= 5:
            # Week-end : pas de vacations programmées hors garde
            cur += datetime.timedelta(days=1)
            continue

        if iso in JOURS_FERIES_HIVER:
            schedule[iso] = {
                "holiday": JOURS_FERIES_HIVER[iso],
                "am": [],
                "pm": [],
                "byInterne": {
                    i["id"]: {"am": "FÉRIÉ", "pm": "FÉRIÉ", "note": JOURS_FERIES_HIVER[iso]}
                    for i in INTERNES_LIST
                },
            }
            cur += datetime.timedelta(days=1)
            continue

        day_roles = weekly_roles[wd]
        am_list = []
        pm_list = []
        by_interne = {}

        for idx, iid in enumerate(main_ids):
            interne_obj = next(x for x in INTERNES_LIST if x["id"] == iid)
            role_idx = (idx + week_idx) % 6
            post_am = day_roles["am"][role_idx]
            post_pm = day_roles["pm"][role_idx]

            abs_type = abs_lookup.get((iso, iid))
            if abs_type:
                badge = "RG" if "garde" in abs_type.lower() or abs_type.upper() == "RG" else "VACANCES"
                post_am = badge
                post_pm = badge
                note = f"{abs_type}"
            else:
                note = ""

            by_interne[iid] = {"am": post_am, "pm": post_pm, "note": note}
            am_list.append({"poste": post_am, "interneId": iid, "interne": interne_obj["shortName"]})
            pm_list.append({"poste": post_pm, "interneId": iid, "interne": interne_obj["shortName"]})

        schedule[iso] = {
            "holiday": None,
            "am": am_list,
            "pm": pm_list,
            "byInterne": by_interne,
        }
        cur += datetime.timedelta(days=1)

    return schedule


def build_initial_presentations() -> list[dict]:
    """
    Génère le calendrier complet des présentations du semestre Hiver 2026-2027 :
    - Tous les Mardis (Cas clinique des internes + Cours des chefs)
    - Tous les Vendredis (Bibliographie des internes)
    - Les séances Bone Club & Confrontations Radio-Anatomopathologiques
    Avec répartition initiale équilibrée par roulement (modifiable en 1 clic par les internes).
    """
    start_date = datetime.date(2026, 11, 2)
    end_date = datetime.date(2027, 4, 30)
    main_ids = ["gabriel", "noe", "marwane", "milan", "nathanael", "oussama"]

    items = []
    tuesday_idx = 0
    friday_idx = 0

    cur = start_date
    while cur <= end_date:
        iso = cur.isoformat()
        wd = cur.weekday()
        if iso in JOURS_FERIES_HIVER:
            cur += datetime.timedelta(days=1)
            continue

        pool = main_ids

        if wd == 1:  # MARDI : Cas clinique + Cours des chefs
            assigned_id = pool[tuesday_idx % len(pool)]
            assigned_obj = next(x for x in INTERNES_LIST if x["id"] == assigned_id)
            chef_nom, chef_sujet = CHEFS_TUESDAY_COURS[tuesday_idx % len(CHEFS_TUESDAY_COURS)]
            cours_programme = CURRICULUM_COURS[tuesday_idx % len(CURRICULUM_COURS)]
            items.append({
                "id": f"cas-{iso}",
                "date": iso,
                "type": "cas_mardi",
                "typeLabel": "Cas Clinique du Mardi",
                "horaire": "12h30 – 13h30",
                "salle": "Salle de Staff Radio B (Albarran -1)",
                "interneId": assigned_id,
                "interneName": assigned_obj["shortName"],
                "sujet": "" if iso > "2026-11-17" else (
                    "Dossier ostéo-articulaire inaugural (choix libre)" if iso == "2026-11-03" else ""
                ),
                "chefIntervenant": chef_nom,
                "coursChef": chef_sujet,
                "themeSemaine": cours_programme,
                "notes": "Présentation d'un cas clinique (10 min) suivie du cours hebdo des chefs (20-30 min).",
            })
            tuesday_idx += 1

        elif wd == 4:  # VENDREDI : Biblio du vendredi
            assigned_id = pool[(friday_idx + 3) % len(pool)]
            assigned_obj = next(x for x in INTERNES_LIST if x["id"] == assigned_id)
            items.append({
                "id": f"biblio-{iso}",
                "date": iso,
                "type": "biblio_vendredi",
                "typeLabel": "Biblio du Vendredi",
                "horaire": "12h30 – 13h30",
                "salle": "Salle de Staff Radio B (Albarran -1)",
                "interneId": assigned_id,
                "interneName": assigned_obj["shortName"],
                "sujet": "",
                "articleRef": "",
                "notes": "Présentation critique d'un article récent d'imagerie musculo-squelettique ou interventionnelle.",
            })
            friday_idx += 1

        cur += datetime.timedelta(days=1)

    # Ajout des Confrontations Radio-Anatomopathologiques & Bone Club
    special_staffs = [
        {
            "id": "cra-2026-11-27",
            "date": "2026-11-27",
            "type": "confrontation_anapath",
            "typeLabel": "Confrontations Radio-Anatomopathologiques",
            "horaire": "14h00 – 16h00",
            "salle": "Salle de Staff Radio B (Albarran -1)",
            "interneId": "gabriel",
            "interneName": "Gabriel & Noé",
            "sujet": "Confrontations Radio-Anatomo-Pathologiques mensuelles (Service Pr Feydy / Anapath)",
            "notes": "Envoyé par Anne-Marie Fortin — présence de tous les internes disponible sur le secteur.",
        },
        {
            "id": "boneclub-2026-12-10",
            "date": "2026-12-10",
            "type": "bone_club",
            "typeLabel": "Bone Club Cochin",
            "horaire": "17h30 – 19h00",
            "salle": "Salle Chevrot / Albarran -1",
            "interneId": "marwane",
            "interneName": "Marwane & Milan",
            "sujet": "Dossiers difficiles d'imagerie osseuse — Bone Club",
            "notes": "Séance de dossiers radiologiques commentés.",
        },
        {
            "id": "cra-2027-01-29",
            "date": "2027-01-29",
            "type": "confrontation_anapath",
            "typeLabel": "Confrontations Radio-Anatomopathologiques",
            "horaire": "14h00 – 16h00",
            "salle": "Salle de Staff Radio B (Albarran -1)",
            "interneId": "nathanael",
            "interneName": "Nathanaël & Oussama",
            "sujet": "Confrontations Radio-Anatomo-Pathologiques",
            "notes": "Dossiers biopsiés au Scanner Achard / Écho.",
        },
    ]
    items.extend(special_staffs)
    items.sort(key=lambda x: (x["date"], x["type"]))
    return items


def build_service_meetings() -> list[dict]:
    """
    Réunions du service, formations obligatoires, accueils et annonces officielles
    envoyées par Anne-Marie Fortin (secrétariat du Pr A. Feydy) et l'équipe des chefs.
    """
    return [
        {
            "id": "reunion-2026-11-02-cafe",
            "date": "2026-11-02",
            "horaire": "08h15 – 08h45",
            "title": "Café d'accueil & Visite du Service de Radiologie B",
            "category": "Accueil & Vie du service",
            "sender": "Anne-Marie FORTIN / Dr M-P. TALABARD & les Chefs",
            "location": "Bâtiment Albarran (-1) — Salle de Staff Radio B",
            "description": "Accueil de la nouvelle promotion d'internes Hiver 2026–2027 autour d'un café à 8h15, suivi de la visite des différents secteurs (TDM Ollier, Achard, IRM 1.5T/3T, Écho, Salle C & Allura).",
            "mandatory": True,
        },
        {
            "id": "reunion-2026-11-02-formation",
            "date": "2026-11-02",
            "horaire": "09h00 – 11h45",
            "title": "Demi-journée de Formation obligatoire des nouveaux arrivants",
            "category": "Formation obligatoire",
            "sender": "Anne-Marie FORTIN (Secrétariat Pr A. Feydy)",
            "location": "Salle de Staff Radio B (Albarran -1 / Salle Chevrot)",
            "description": (
                "Programme officiel transmis par Anne-Marie Fortin :\n"
                "• 09h00 – 09h45 : Radioprotection (Mme Sophie LE GALL)\n"
                "• 10h00 – 10h45 : Règles d'hygiène en imagerie & interventionnel (Dr Véronique FARAUT DEROUIN)\n"
                "• 11h00 – 11h45 : Utilisation des anesthésiants locaux (Pr Anthony DOHAN / Dr Raphaël DAUTRY)"
            ),
            "mandatory": True,
        },
        {
            "id": "reunion-2026-11-04-accueil",
            "date": "2026-11-04",
            "horaire": "17h00 – 18h30",
            "title": "Réunion d'accueil Internes & Chefs de Clinique",
            "category": "Réunion Service",
            "sender": "Dr Fadila MIHOUBI BOUVIER, Dr Amandine LAPORTE & Anne-Marie FORTIN",
            "location": "Salle de Staff Radio B (Albarran -1)",
            "description": "Présentation du fonctionnement du service, des gardes, des règles de congés (max 2 absents simultanés, éviter mardi/vendredi), de la trame des vacations et du programme des présentations du mardi (cas) et vendredi (biblio).",
            "mandatory": True,
        },
        {
            "id": "reunion-2026-11-09-externes",
            "date": "2026-11-09",
            "horaire": "09h00 – 12h00",
            "title": "Arrivée des nouveaux externes & Lancement des Cours Externes Nov–Déc",
            "category": "Enseignement",
            "sender": "Anne-Marie FORTIN",
            "location": "Salle de réunion Albarran -1",
            "description": "Accueil des externes du stage de Novembre–Décembre 2026 (du 09/11/2026 au 03/01/2027) et début du planning des cours externes assurés par les CCA et internes.",
            "mandatory": False,
        },
        {
            "id": "reunion-2026-11-19-ecos",
            "date": "2026-11-19",
            "horaire": "09h00 – 12h00",
            "title": "Session ECOS Externes — Radiologie B",
            "category": "Enseignement",
            "sender": "Anne-Marie FORTIN",
            "location": "Salle de réunion Albarran -1",
            "description": "Entraînement ECOS pour les externes du service (encadrement CCA / Internes).",
            "mandatory": False,
        },
        {
            "id": "reunion-2026-11-24-dmu",
            "date": "2026-11-24",
            "horaire": "09h00 – 17h00",
            "title": "Séminaire DMU Imagina",
            "category": "Séminaire / Congrès",
            "sender": "Anne-Marie FORTIN / Direction DMU Imagina",
            "location": "Hôpital Necker-Enfants Malades",
            "description": "Journée annuelle du DMU Imagina (présentations institutionnelles et projets du DMU).",
            "mandatory": False,
        },
        {
            "id": "reunion-2026-11-27-anapath",
            "date": "2026-11-27",
            "horaire": "14h00 – 16h00",
            "title": "Confrontations Radio-Anatomo-Pathologiques",
            "category": "Staff Multidisciplinaire",
            "sender": "Anne-Marie FORTIN",
            "location": "Salle de Staff Radio B (Albarran -1)",
            "description": "Réunion mensuelle de corrélation radio-histologique sur les biopsies ostéo-articulaires et des parties molles.",
            "mandatory": True,
        },
        {
            "id": "reunion-2026-12-18-vaccin",
            "date": "2026-12-18",
            "horaire": "Toute la journée",
            "title": "Campagne de vaccination Grippe & Covid — Cochin Port-Royal",
            "category": "Infos AP-HP",
            "sender": "Anne-Marie FORTIN",
            "location": "Hôpital Cochin",
            "description": "Date limite de la campagne de vaccination annuelle pour le personnel médical et les internes du site Cochin.",
            "mandatory": False,
        },
        {
            "id": "reunion-2026-12-21-noel",
            "date": "2026-12-21",
            "horaire": "Semaines du 21/12 et 28/12/2026",
            "title": "Organisation des Congés de Fin d'Année (Noël / Nouvel An)",
            "category": "Congés & Effectifs",
            "sender": "Anne-Marie FORTIN & les Chefs",
            "location": "Service de Radiologie B",
            "description": "Répartition équitable des internes entre la semaine de Noël (21/12–25/12) et la semaine du Jour de l'An (28/12–01/01) afin d'assurer la continuité des postes prioritaires (TDM SAU, IRM, Gestes).",
            "mandatory": True,
        },
    ]


def build_recurring_staffs() -> list[dict]:
    """Staffs hebdomadaires récurrents du service de Radiologie B."""
    return [
        {
            "day": "Lundi",
            "weekday": 0,
            "items": [
                {"horaire": "Matin", "title": "Staff RCP Métastases Osseuses", "referent": "Dr T. Lefèvre"},
                {"horaire": "Après-midi", "title": "Staff CIRTAL / Sarcomes d'Ewing", "referent": "Dr H. Monnier"},
            ],
        },
        {
            "day": "Mardi",
            "weekday": 1,
            "items": [
                {"horaire": "12h30 – 13h30", "title": "Staff Internes : Cas Clinique du Mardi + Cours des Chefs", "referent": "Dr F. Mihoubi Bouvier & Tous les Chefs"},
                {"horaire": "Après-midi", "title": "Staff RCP Sarcomes des Tissus Mous", "referent": "Dr A. Laporte & Chefs"},
            ],
        },
        {
            "day": "Mercredi",
            "weekday": 2,
            "items": [
                {"horaire": "Matin", "title": "Accueil stagiaires / Enseignement externes", "referent": "CCA / Internes"},
                {"horaire": "Après-midi", "title": "Staff Rachis / Rhumatologie Osseuse", "referent": "Dr Yang"},
            ],
        },
        {
            "day": "Jeudi",
            "weekday": 3,
            "items": [
                {"horaire": "Matin / PM", "title": "Vacations Interventionnelles lourdes (Scanner Achard & Salle Allura)", "referent": "Équipe RI"},
            ],
        },
        {
            "day": "Vendredi",
            "weekday": 4,
            "items": [
                {"horaire": "Matin", "title": "Staff Prothèses & Imagerie Orthopédique", "referent": "Dr H. Guérini"},
                {"horaire": "12h30 – 13h30", "title": "Biblio du Vendredi (Article scientifique par un interne)", "referent": "Internes & Chefs"},
                {"horaire": "Après-midi", "title": "Staff MPR / Rhumatologie", "referent": "Dr F. Mihoubi Bouvier"},
            ],
        },
    ]


def get_initial_absences() -> list[dict]:
    """
    Absences déjà inscrites sur le Google Sheet officiel 'Planning Interne CCH - Hiver 26'
    (ex: Milan KORSEC du 22/03/2027 au 28/03/2027 en CA 1).
    """
    absences = []
    for day in range(22, 29):
        iso = f"2027-03-{day:02d}"
        absences.append({
            "id": f"abs-milan-{iso}",
            "date": iso,
            "interneId": "milan",
            "interneName": "Milan KORSEC",
            "type": "CA 1",
            "comment": "Congés annuels posés sur le Google Sheet Hiver 26-27",
            "createdAt": "2026-11-01T10:00:00Z",
        })
    return absences


def build_phone_directory() -> list[dict]:
    """
    Annuaire téléphonique complet de l'Hôpital Cochin (AP-HP) — Service de Radiologie B & Services partenaires.
    Numéros fixes (01 58 41 XX XX), postes internes (5 chiffres) et DECT extraits des communications officielles.
    Aucune donnée patient.
    """
    return [
        # 1. RADIOLOGIE B — SECRÉTARIATS, ENCADREMENT & CONSOLES
        {
            "id": "tel-fortin",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Anne-Marie FORTIN-COZIC",
            "role": "Secrétariat Chef de Service (Pr Antoine FEYDY) — Bât. Albarran",
            "poste": "12483 / 13788",
            "phone": "01 58 41 24 83",
            "fax": "01 58 41 24 55",
            "building": "Albarran / Ollier",
        },
        {
            "id": "tel-ri-sec",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Secrétariat Radiologie Interventionnelle (RI)",
            "role": "Programmation RI & Consultations — Bât. Ollier",
            "poste": "14612 / 12476",
            "phone": "01 58 41 46 12",
            "fax": "01 58 41 24 55",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-ri-direct",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Ligne Directe Radiologie Interventionnelle",
            "role": "Salle / Coordination RI (Ollier / Achard)",
            "poste": "12163",
            "phone": "01 58 41 21 63",
            "fax": "",
            "building": "Bâtiment Ollier / Achard",
        },
        {
            "id": "tel-mouyoungui",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Andress Gyslève MOUYOUNGUI",
            "role": "Assistante Médico-Administrative (AMA) — Radio B",
            "poste": "12684",
            "phone": "01 58 41 26 84",
            "fax": "01 58 41 24 55",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-gameiro",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Mariana GAMEIRO JORGE",
            "role": "Assistante Médico-Administrative (AMA) — Radio B",
            "poste": "11788",
            "phone": "01 58 41 17 88",
            "fax": "01 58 41 24 55",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-orak",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Secrétariat Pr Jean-Luc DRAPÉ (Mme ORAK)",
            "role": "Assistante Médico-Administrative — Radio B",
            "poste": "12502",
            "phone": "01 58 41 25 02",
            "fax": "01 58 41 21 51",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-menage",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Isabelle MENAGE",
            "role": "Cadre Médico-Technique — Service de Radiologie B",
            "poste": "12484",
            "phone": "01 58 41 24 84",
            "fax": "",
            "building": "Bâtiment Ollier (1er sous-sol)",
        },
        {
            "id": "tel-accueil-ollier",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Accueil & Rendez-vous Radio B (Ollier -1)",
            "role": "Accueil examens TDM / IRM / Écho / Biopsies",
            "poste": "12360 / 12350",
            "phone": "01 58 41 23 60",
            "fax": "01 58 41 24 49",
            "building": "Bâtiment Ollier (1er sous-sol)",
        },
        {
            "id": "tel-sellami",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Laila SELLAMI",
            "role": "Référente Informatique Imagerie / PACS Carestream (CCH, HTD, BRC)",
            "poste": "DECT 12197",
            "phone": "01 58 41 21 97",
            "fax": "",
            "building": "Imagerie Cochin",
        },
        {
            "id": "tel-logistique-matos",
            "category": "Radiologie B — Secrétariats & Consoles",
            "name": "Logisticiens / Matériel RI (O. Peaudecerf / D. Vannifterik)",
            "role": "Commandes & Matériel Interventionnel",
            "poste": "DECT 12183",
            "phone": "01 58 41 21 83",
            "fax": "",
            "building": "Radiologie B",
        },
        # 2. RADIOLOGIE B — MÉDECINS SENIORS & CHEFS DE CLINIQUE
        {
            "id": "tel-feydy",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Pr Antoine FEYDY",
            "role": "Chef de Service — Radiologie B (Ostéo-Articulaire)",
            "poste": "12483",
            "phone": "01 58 41 24 83",
            "fax": "01 58 41 24 55",
            "building": "Albarran / Ollier",
        },
        {
            "id": "tel-drape",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Pr Jean-Luc DRAPÉ",
            "role": "PU-PH — Radiologie B",
            "poste": "12502",
            "phone": "01 58 41 25 02",
            "fax": "01 58 41 21 51",
            "building": "Albarran / Ollier",
        },
        {
            "id": "tel-talabard",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Dr Marie-Pauline TALABARD",
            "role": "Chef de Clinique Assistant — Imagerie Ostéo-Articulaire & RI",
            "poste": "12489",
            "phone": "01 58 41 24 89",
            "fax": "",
            "building": "Albarran / Ollier",
        },
        {
            "id": "tel-lefevre",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Dr Thomas LEFÈVRE",
            "role": "Chef de Clinique / Assistant — Radiologie Interventionnelle & Ostéo-Articulaire",
            "poste": "12489 / 12163",
            "phone": "01 58 41 24 89",
            "fax": "",
            "building": "Albarran / Ollier / Achard",
        },
        {
            "id": "tel-hamadouche",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Dr Macil HAMADOUCHE",
            "role": "Assistant Spécialiste — Imagerie Ostéo-Articulaire & RI",
            "poste": "DECT 12504",
            "phone": "01 58 41 25 04",
            "fax": "",
            "building": "Albarran / Ollier",
        },
        {
            "id": "tel-bureau-cca",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Bureau des CCA / Assistants Radio B (Dr Monnier, Dr Lusi, Dr Allel, Dr Hammoud)",
            "role": "Ligne directe Bureau CCA Radiologie B",
            "poste": "12488 / 12489",
            "phone": "01 58 41 24 88",
            "fax": "",
            "building": "Bâtiment Albarran / Ollier",
        },
        {
            "id": "tel-radio-a",
            "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
            "name": "Service de Radiologie A (Pr A. Dohan / Pr M. Barat)",
            "role": "Secrétariat Radiologie A & Gardes d'Imagerie",
            "poste": "12490",
            "phone": "01 58 41 24 90",
            "fax": "",
            "building": "Hôpital Cochin",
        },
        # 3. SERVICES CLINIQUES PARTENAIRES (ORTHOPÉDIE, RHUMATO, ANESTH, ANAPATH)
        {
            "id": "tel-ortho-biau",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Chirurgie Orthopédique & Oncologique — Pr David BIAU (Mme A. Tison)",
            "role": "Secrétariat Pr Biau (Sarcomes & Tumeurs osseuses)",
            "poste": "13037",
            "phone": "01 58 41 30 37",
            "fax": "01 58 41 30 60",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-ortho-cca",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Secrétariat CCA Chirurgie Orthopédique (M. Rahmani / A. P. Bitty / L. Guedj)",
            "role": "Chirurgie Orthopédique et Traumatologique",
            "poste": "13130 / 13082 / 13107",
            "phone": "01 58 41 31 30",
            "fax": "01 58 41 30 60",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-ortho-maalouf",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Chirurgie Orthopédique — Dr P. MAALOUF / Dr A. VILLARD / Banque Os",
            "role": "Secrétariats Orthopédie (13077 / 13041 / 13104)",
            "poste": "13077 / 13041",
            "phone": "01 58 41 30 77",
            "fax": "",
            "building": "Bâtiment Ollier",
        },
        {
            "id": "tel-rhumato-allanore",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Service de Rhumatologie (Pr Y. ALLANORE — Mme Canvel)",
            "role": "Secrétariat Rhumatologie A/B & Demandes Cimentoplastie",
            "poste": "12606 / 12619",
            "phone": "01 58 41 26 06",
            "fax": "01 58 41 40 97",
            "building": "Bâtiment Achard / Hardy",
        },
        {
            "id": "tel-anesth",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Service d'Anesthésie-Réanimation & Consultations d'Anesthésie",
            "role": "Médecine Péri-Opératoire & Programmation AG",
            "poste": "11563 / 11566 / 11528",
            "phone": "01 58 41 15 63",
            "fax": "",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-uca",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Unité de Chirurgie Ambulatoire (UCA — Mme S. Azzopardi)",
            "role": "Cadre de santé IBODE / Ambulatoire",
            "poste": "14022",
            "phone": "01 58 41 40 22",
            "fax": "",
            "building": "Bâtiment Port-Royal",
        },
        {
            "id": "tel-achard-poly",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Polyclinique Bâtiment Achard RDC (Mme E. Vaugenot Nardy)",
            "role": "Cadre de santé — Bâtiment Achard RDC",
            "poste": "12412",
            "phone": "01 58 41 24 12",
            "fax": "",
            "building": "Bâtiment Achard",
        },
        {
            "id": "tel-anapath",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Service d'Anatomie et Cytologie Pathologiques (Anapath)",
            "role": "Secrétariat Pathologie (Mme L. Chanat) & UF CRB-Cancer",
            "poste": "13542 / 14719",
            "phone": "01 58 41 35 42",
            "fax": "",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-douleur",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Centre d'Évaluation et Traitement de la Douleur (CETD — Pr Perrot)",
            "role": "Secrétariat Douleur (Mme C. Taliercio) & UF Douleur",
            "poste": "13040 / 12704",
            "phone": "01 58 41 30 40",
            "fax": "",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-onco-thorax",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Oncologie Thoracique & Pneumologie",
            "role": "DECT Oncologie 14352 / Secrétariats 12349 & 13099",
            "poste": "DECT 14352 / 12349",
            "phone": "01 58 41 23 49",
            "fax": "01 58 41 23 85",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-med-interne",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Service de Médecine Interne",
            "role": "Secrétariat 12103 / DECT Interne 18184",
            "poste": "12103 / DECT 18184",
            "phone": "01 58 41 21 03",
            "fax": "01 58 41 15 79",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-hemato-clin",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Service d'Hématologie Clinique (Mme V. Kerouaz)",
            "role": "Secrétariat Hématologie Clinique",
            "poste": "12110 / 13919",
            "phone": "01 58 41 21 10",
            "fax": "",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-endocrino",
            "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
            "name": "Service d'Endocrinologie & Programmation Hospitalisations (Copernic)",
            "role": "Secrétariat 11878 / Programmation Hospit 11888 & 13940",
            "poste": "11878 / 11888",
            "phone": "01 58 41 18 88",
            "fax": "01 58 41 18 10",
            "building": "Pavillon Copernic",
        },
        # 4. LABORATOIRES, PHARMACIE, HYGIÈNE & AFFAIRES MÉDICALES
        {
            "id": "tel-hemostase",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "Consultation & Laboratoire d'Hémostase / Hématologie Biologique",
            "role": "Bilan d'hémostase pré-geste (13445) / Labo Hémato J. Dausset (14141 / 13520)",
            "poste": "13445 / 14141",
            "phone": "01 58 41 34 45",
            "fax": "",
            "building": "Bâtiment Jean Dausset",
        },
        {
            "id": "tel-bio-auto",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "Diagnostic Biologique Automatisé & Virologie / Parasitologie",
            "role": "Biochimie-Garde (14146) / Viro-Parasito (11547)",
            "poste": "14146 / 11547",
            "phone": "01 58 41 41 46",
            "fax": "",
            "building": "Bâtiment Jean Dausset",
        },
        {
            "id": "tel-pharmacie",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "Pharmacie Hospitalière (Dr M-L. Brandely-Piat / Dr H. Palisson)",
            "role": "Médicaments, Bléomycine ECT & Dispositifs Médicaux Stériles (MDS)",
            "poste": "14275 / 12314 / 12982",
            "phone": "01 58 41 42 75",
            "fax": "01 58 41 18 84",
            "building": "Service Pharmacie Cochin",
        },
        {
            "id": "tel-hygiene",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "Équipe Opérationnelle d'Hygiène (EOH — Mme L. Meyer)",
            "role": "Hygiène Hospitalière Cochin / Hôtel-Dieu / Broca",
            "poste": "12632",
            "phone": "01 58 41 26 32",
            "fax": "",
            "building": "Hôpital Cochin",
        },
        {
            "id": "tel-ucsa",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "UCSA — Unité de Consultations et Soins Ambulatoires (La Santé)",
            "role": "Liaison UCSA / Hôpital Cochin",
            "poste": "12700",
            "phone": "01 58 41 27 00",
            "fax": "",
            "building": "Cochin / La Santé",
        },
        {
            "id": "tel-dam",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "Bureau du Personnel Médical — Pavillon de Chasse (Mme A. N'Diaye / Mme M. Lambert)",
            "role": "Gestion des Internes & Seniors Cochin (12295 / 11014 / 11071)",
            "poste": "12295 / 11014",
            "phone": "01 58 41 22 95",
            "fax": "",
            "building": "Port-Royal — Pavillon de Chasse",
        },
        {
            "id": "tel-standard",
            "category": "Laboratoires, Pharmacie & Administration (DAM)",
            "name": "Standard Général Hôpital Cochin",
            "role": "Standard AP-HP Cochin (27 rue du Faubourg Saint-Jacques)",
            "poste": "11000 / 9",
            "phone": "01 58 41 10 00",
            "fax": "",
            "building": "Hôpital Cochin",
        },
    ]


def assert_zero_patient_data(text: str):
    """
    Vérifie de façon stricte qu'aucune donnée patient (IPP, date de naissance, nom de patient,
    numéro de téléphone, adresse email personnelle) ne figure dans le code généré.
    """
    forbidden_patterns = {
        "Numéro IPP": r"IPP[^0-9<]{0,15}[0-9]{7,10}",
        "Date de naissance patient": r"n[ée]e? le [0-9]{2}/[0-9]{2}/[0-9]{4}",
    }
    problems = []
    for label, pat in forbidden_patterns.items():
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            problems.append(f"{label}: {m.group(0)[:40]!r}")
    if problems:
        raise RuntimeError("ERREUR CRITIQUE : Donnée sensible détectée -> " + ", ".join(problems))


def expand_chefs_planning_full_semester(base_chefs_planning: dict) -> dict:
    """
    Étend le planning des Chefs & Seniors sur l'ensemble du semestre d'Hiver (02/11/2026 au 30/04/2027)
    en conservant les dates exactes du planning d'Anne-Marie V3 et en appliquant la maquette hebdomadaire
    officielle des Chefs pour toutes les autres semaines du semestre.
    """
    maquette_dow = {
        0: {  # LUNDI
            "am": [
                {"poste": "ECHO", "doc": "HAMMOUD"},
                {"poste": "GESTES (C)", "doc": "HM"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "YA"},
                {"poste": "CONSULTATION", "doc": "TL"},
                {"poste": "UCSA", "doc": "TL"},
                {"poste": "STAFF", "doc": "TL (méta OS)"},
            ],
            "pm": [
                {"poste": "GESTES (C)", "doc": "TL"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "TL"},
                {"poste": "TDM OLLIER 3", "doc": "YA"},
                {"poste": "IRM", "doc": "FEYDY"},
                {"poste": "ECHO", "doc": "HM"},
                {"poste": "STAFF", "doc": "HM (Cirtal/Ewing)"},
            ],
        },
        1: {  # MARDI
            "am": [
                {"poste": "ECHO", "doc": "YA"},
                {"poste": "GESTES (C)", "doc": "MIHOUBI"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "MH"},
                {"poste": "TDM ACHARD 1", "doc": "TL"},
                {"poste": "IRM 3T", "doc": "DRAPE/YANG"},
                {"poste": "IRM 1,5T", "doc": "AL"},
                {"poste": "CONSULTATION", "doc": "HM"},
                {"poste": "UCSA", "doc": "SL"},
            ],
            "pm": [
                {"poste": "GESTES (C)", "doc": "HM"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "SL"},
                {"poste": "TDM ACHARD 1", "doc": "TL"},
                {"poste": "ECHO", "doc": "MH"},
                {"poste": "CONSULTATION", "doc": "INTERNES"},
                {"poste": "UCSA", "doc": "YA"},
                {"poste": "STAFF", "doc": "Chef et AL Sarcomes"},
            ],
        },
        2: {  # MERCREDI
            "am": [
                {"poste": "ECHO", "doc": "THEVENIN ET SL"},
                {"poste": "GESTES (C)", "doc": "TL"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "YA"},
                {"poste": "TDM OLLIER 3", "doc": "MH"},
                {"poste": "IRM 3T", "doc": "DRAPE/YANG"},
                {"poste": "IRM 1,5T", "doc": "MOUTOUNET"},
            ],
            "pm": [
                {"poste": "GESTES (C)", "doc": "DRAPE"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "TL"},
                {"poste": "TDM ACHARD 1", "doc": "SEROR/YA"},
                {"poste": "IRM", "doc": "SL"},
                {"poste": "ECHO", "doc": "MIHOUBI"},
                {"poste": "CONSULTATION", "doc": "TL"},
                {"poste": "UCSA", "doc": "MH"},
                {"poste": "STAFF", "doc": "YANG (Rachis/Rhumato OS)"},
            ],
        },
        3: {  # JEUDI
            "am": [
                {"poste": "ECHO", "doc": "AL/AC"},
                {"poste": "GESTES (C)", "doc": "RUBINI"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "MH"},
                {"poste": "TDM ACHARD 1", "doc": "HM"},
                {"poste": "CONSULTATION", "doc": "SL"},
            ],
            "pm": [
                {"poste": "GESTES (C)", "doc": "SL"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "SL"},
                {"poste": "TDM ACHARD 1", "doc": "AL/MH"},
                {"poste": "IRM", "doc": "AC"},
                {"poste": "ECHO", "doc": "MD"},
                {"poste": "ALLURA", "doc": "HM"},
                {"poste": "CONSULTATION", "doc": "FEYDY"},
            ],
        },
        4: {  # VENDREDI
            "am": [
                {"poste": "ECHO", "doc": "TL/YANG"},
                {"poste": "GESTES (C)", "doc": "MH"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "AC"},
                {"poste": "IRM 3T", "doc": "HM"},
                {"poste": "IRM 1,5T", "doc": "YA"},
                {"poste": "STAFF", "doc": "GUERINI (prothèse)"},
            ],
            "pm": [
                {"poste": "GESTES (C)", "doc": "YA"},
                {"poste": "TDM OLLIER 4 (SAU)", "doc": "HM"},
                {"poste": "TDM ACHARD 1", "doc": "AC/SL"},
                {"poste": "IRM", "doc": "TL"},
                {"poste": "CONSULTATION", "doc": "MH/INTERNES"},
                {"poste": "STAFF", "doc": "MIHOUBI (MPR Rhumato)"},
            ],
        },
    }
    out = dict(base_chefs_planning)
    cur = datetime.date(2026, 11, 2)
    end = datetime.date(2027, 4, 30)
    while cur <= end:
        iso = cur.isoformat()
        wd = cur.weekday()
        if wd < 5 and iso not in out:
            if iso in JOURS_FERIES_HIVER:
                out[iso] = {"am": [{"poste": "FÉRIÉ", "doc": JOURS_FERIES_HIVER[iso]}], "pm": []}
            else:
                out[iso] = maquette_dow[wd]
        cur += datetime.timedelta(days=1)
    return out


def build_full_dataset() -> dict:
    chefs_gardes = {}
    chefs_planning = {}
    if (BASE_DIR / "chefs_gardes.json").exists():
        chefs_gardes = json.loads((BASE_DIR / "chefs_gardes.json").read_text(encoding="utf-8"))
    if (BASE_DIR / "chefs_planning.json").exists():
        chefs_planning = json.loads((BASE_DIR / "chefs_planning.json").read_text(encoding="utf-8"))
    chefs_planning = expand_chefs_planning_full_semester(chefs_planning)

    absences = get_initial_absences()
    if DATA_FILE.exists():
        try:
            old = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if old.get("absences"):
                abs_map = {a["id"]: a for a in absences}
                for a in old["absences"]:
                    if a.get("id"):
                        abs_map[a["id"]] = a
                absences = sorted(abs_map.values(), key=lambda x: (x["date"], x["interneId"]))
        except Exception:
            pass

    schedule = generate_semester_schedule(absences)
    presentations = build_initial_presentations()
    meetings = build_service_meetings()
    recurring_staffs = build_recurring_staffs()
    phone_directory = build_phone_directory()

    return {
        "version": "1.2.0",
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "semester": {
            "title": "Semestre d'Hiver 2026–2027",
            "hospital": "Hôpital Cochin (AP-HP) — Service de Radiologie B (Pr A. Feydy)",
            "startDate": "2026-11-02",
            "endDate": "2027-04-30",
            "secretariat": "Anne-Marie FORTIN (01 58 41 24 83 / poste 12483)",
            "rules": [
                "Pas plus de 2 internes absents (CA / CF) en même temps.",
                "Pour les jours isolés (CF, récupérations), éviter les mardis et les vendredis (jours de staff/présentations).",
                "Équité stricte du nombre de vacations et des présentations du mardi (cas) et du vendredi (biblio).",
                "Aucune donnée patient ne doit jamais être saisie sur cette application.",
            ],
        },
        "internes": INTERNES_LIST,
        "chefs": CHEFS_LIST,
        "postesMeta": POSTES_META,
        "curriculumCours": CURRICULUM_COURS,
        "absences": absences,
        "customVacations": {},
        "interneGardes": {},
        "schedule": schedule,
        "presentations": presentations,
        "meetings": meetings,
        "recurringStaffs": recurring_staffs,
        "phoneDirectory": phone_directory,
        "chefsGardes": chefs_gardes,
        "chefsPlanning": chefs_planning,
    }


def sync_initial_state_to_cloud(dataset: dict):
    """
    Sauvegarde l'état initial de l'application des internes dans PropertiesService
    sous la clé dédiée 'cochin_internes_state_v1' (sans toucher aux clés des autres applications).
    """
    compact_state = {
        "updatedAt": dataset["updatedAt"],
        "absences": dataset["absences"],
        "customVacations": dataset["customVacations"],
        "interneGardes": dataset["interneGardes"],
        "presentations": dataset["presentations"],
        "meetings": dataset["meetings"],
        "phoneDirectory": dataset["phoneDirectory"],
    }
    safe_json = json.dumps(compact_state, ensure_ascii=False)
    eval_code = f"""
    var props = PropertiesService.getScriptProperties();
    var existingRaw = props.getProperty('{CLOUD_PROP_KEY}');
    var incoming = {safe_json};
    if (!existingRaw) {{
      props.setProperty('{CLOUD_PROP_KEY}', JSON.stringify(incoming));
      return {{ status: 'initialized_cloud', presentations: incoming.presentations.length, meetings: incoming.meetings.length }};
    }}
    var cur = JSON.parse(existingRaw);
    cur.presentations = incoming.presentations;
    cur.meetings = incoming.meetings;
    cur.phoneDirectory = incoming.phoneDirectory;
    if (!cur.absences || cur.absences.length === 0) cur.absences = incoming.absences;
    props.setProperty('{CLOUD_PROP_KEY}', JSON.stringify(cur));
    return {{ status: 'verified_cloud', presentations: cur.presentations.length, absences: cur.absences.length }};
    """
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps({"eval_code": eval_code}).encode("utf-8"),
        headers={"Content-Type": "text/plain;charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    data = build_full_dataset()
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote internes_data.json successfully. Days in schedule:", len(data["schedule"]))
    try:
        res = sync_initial_state_to_cloud(data)
        print("Cloud sync result:", res)
    except Exception as e:
        print("Cloud sync warning:", e)
