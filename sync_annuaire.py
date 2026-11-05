#!/usr/bin/env python3
"""
Synchronisation systématique et détection automatique des mises à jour de numéros
pour l'Annuaire Téléphonique de l'Hôpital Cochin (Agendainterventionnel & Cochin OS).

Sources synchronisées automatiquement :
1. Base locale : /Users/thomaslefevre/Documents/Agendainterventionnel/cochin_annuaire.json
2. Portail Cochin OS : /Users/thomaslefevre/.t3/projects/guide-interne-cochin-os/annuaire/annuaire-data.json
3. Annuaire Général : /Users/thomaslefevre/.t3/projects/projet-regroup/ANNUAIRE_CONTACTS_IMPORTANTS.md
4. Flux entrants (Emails, iMessages, WhatsApp, personal_data.json) : détection automatique
   des changements de DECT / postes à 5 chiffres (1XXXX) et numéros Cochin (01 58 41 XX XX)
   pour les médecins seniors/chefs, secrétariats, consoles et services partenaires (hors internes).
5. Cloud Google Apps Script : récupération et fusion des ajouts/modifications faits depuis l'app web.

Sécurité : aucun email (@) ni numéro de portable (06/07) n'est inclus dans cochin_annuaire.json
afin de respecter assert_no_sensitive_data() sur la page publique GitHub Pages.
"""
import argparse
import json
from pathlib import Path
import re
import urllib.request

BASE_DIR = Path("/Users/thomaslefevre/Documents/Agendainterventionnel")
LOCAL_ANNUAIRE_PATH = BASE_DIR / "cochin_annuaire.json"
COCHIN_OS_ANNUAIRE_PATH = Path("/Users/thomaslefevre/.t3/projects/guide-interne-cochin-os/annuaire/annuaire-data.json")
ENV_PATH = BASE_DIR / ".env"

# Base de référence consolidée (MAJ Novembre 2026 — Signatures Radio B / RI Onco + Téléphones Imagerie Cochin)
BASELINE_ENTRIES = [
    # --- RADIOLOGIE B : SECRÉTARIATS, CONSOLES & LOGISTIQUE ---
    {
        "id": "tel-ri-direct",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Salle / Coordination Radiologie Interventionnelle (RI)",
        "role": "Ligne directe RI (Ollier / Achard) • DECT RI OS : 12404",
        "poste": "12163 / DECT 12404",
        "phone": "01 58 41 21 63",
        "fax": "",
        "building": "Bâtiment Ollier / Achard",
        "pinnedDefault": True,
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
        "pinnedDefault": True,
    },
    {
        "id": "tel-fortin",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Anne-Marie FORTIN-COZIC",
        "role": "Secrétariat Chef de Service (Pr Antoine FEYDY) — Bât. Albarran",
        "poste": "12483 / 13788",
        "phone": "01 58 41 24 83",
        "fax": "01 58 41 24 55",
        "building": "Albarran / Ollier",
        "pinnedDefault": True,
    },
    {
        "id": "tel-accueil-ollier",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Accueil & Bureau des RDV Radio B (Ollier -1)",
        "role": "Accueil examens TDM / IRM / Écho / Biopsies (Fax 12493)",
        "poste": "12360 / 12350 / 19135",
        "phone": "01 58 41 23 60",
        "fax": "01 58 41 24 49",
        "building": "Bâtiment Ollier (1er sous-sol)",
        "pinnedDefault": True,
    },
    {
        "id": "tel-mouyoungui",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Andress Gyslève MOUYOUNGUI",
        "role": "AMA Secrétariat Radio B (Demandes RDV / Vertébro / Cimento)",
        "poste": "12684",
        "phone": "01 58 41 26 84",
        "fax": "01 58 41 24 55",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-gameiro",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Mariana GAMEIRO JORGE",
        "role": "AMA Secrétariat Radio B (Consultations, TéléCS & Convocations)",
        "poste": "11788",
        "phone": "01 58 41 17 88",
        "fax": "01 58 41 24 55",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-orak",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Ania DWORAK (Secrétariat Pr Jean-Luc DRAPÉ)",
        "role": "Assistante Médico-Administrative — Radio B",
        "poste": "12502",
        "phone": "01 58 41 25 02",
        "fax": "01 58 41 21 51",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-camblong-pouget",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Sandrine CAMBLONG & Christelle POUGET",
        "role": "Secrétariat Médical Radiologie B (Postes 12481 & 12507)",
        "poste": "12481 / 12507",
        "phone": "01 58 41 24 81",
        "fax": "01 58 41 21 51",
        "building": "Bâtiment Ollier / Albarran",
    },
    {
        "id": "tel-menage",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Isabelle MENAGE MARACHE",
        "role": "Cadre Médico-Technique — Service de Radiologie B",
        "poste": "DECT 12484",
        "phone": "01 58 41 24 84",
        "fax": "",
        "building": "Bâtiment Ollier (1er sous-sol)",
    },
    {
        "id": "tel-cadres-rxb",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Cadres Radiologie B (C. Fischer / V. Nitsche / K. Pretzner)",
        "role": "Encadrement Médico-Technique Radio B (DECT 13424 / 12284 / 14752)",
        "poste": "DECT 13424 / 12284 / 14752",
        "phone": "01 58 41 34 24",
        "fax": "",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-sellami",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Laila SELLAMI (Référente PACS Carestream)",
        "role": "Informatique Imagerie / PACS Carestream & Syngo.via (CCH, HTD, BRC)",
        "poste": "DECT 12197",
        "phone": "01 58 41 21 97",
        "fax": "",
        "building": "Imagerie Cochin",
        "pinnedDefault": True,
    },
    {
        "id": "tel-logistique-matos",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Logisticiens / Matériel RI (O. Peaudecerf / D. Van Nifterik)",
        "role": "Commandes & Matériel Interventionnel Radio B",
        "poste": "DECT 12183 / 12984",
        "phone": "01 58 41 21 83",
        "fax": "",
        "building": "Radiologie B",
    },
    {
        "id": "tel-pcr-radioprotection",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Radioprotection / PCR (S. Le Gall & C. Stainmesse)",
        "role": "Personnes Compétentes en Radioprotection — Imagerie Cochin",
        "poste": "DECT 14782 / 11267",
        "phone": "01 58 41 47 82",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-consoles-tdm",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Consoles Scanners Cochin (Ollier, Sc3, Sc4 SAU, Achard)",
        "role": "Ollier : 12266 • Sc3 : 18383 • Sc4 Urg : 12285 • Lecture : 18384 • Sc1/Sc2 RxA : 18978 / 18656",
        "poste": "12266 / 18383 / 12285",
        "phone": "01 58 41 22 66",
        "fax": "",
        "building": "Ollier / Achard",
        "pinnedDefault": True,
    },
    {
        "id": "tel-consoles-irm",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Consoles IRM Cochin (IRM 1 3T, IRM 2 1.5T & Lecture)",
        "role": "IRM 1 (3T) : 12492 • IRM 2 (1.5T) : 12798 • Salle d'interprétation : 18715",
        "poste": "12492 / 12798 / 18715",
        "phone": "01 58 41 24 92",
        "fax": "",
        "building": "Imagerie Cochin",
    },
    {
        "id": "tel-consoles-echo",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Consoles Échographie Radio B & Rhumato",
        "role": "Écho 1 : 13510 • Écho 2 : 18599 • Écho Rhumato : 19905 • DECT Écho : 12504 • Écho SAU : 12513",
        "poste": "13510 / 18599 / DECT 12504",
        "phone": "01 58 41 35 10",
        "fax": "",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-manip-bloc-salles",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Manipulateur Bloc Radio B, Salles RxB & Staff Albarran",
        "role": "Manip Bloc : 12498 • Staff Albarran : 12508 • Salle A : 18982 • B : 18983 • C : 18984 • EOS : 18985",
        "poste": "12498 / 12508",
        "phone": "01 58 41 24 98",
        "fax": "",
        "building": "Ollier / Albarran",
    },
    {
        "id": "tel-gardes-imagerie",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "DECT Gardes d'Imagerie Cochin (Sénior & SAU)",
        "role": "Garde Sénior / SAU : 12621 • DECT Radio B : 15314 • Garde Interne : 15095",
        "poste": "DECT 12621 / 15314",
        "phone": "01 58 41 26 21",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-allura-rxa",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Salle Allura & Bureau RDV Radio A / Vasculaire",
        "role": "Allura Manip : 14254 / 12454 • Accueil RxA : 12463 / 19146 / 19147 (Fax 12874)",
        "poste": "14254 / 12463 / 19146",
        "phone": "01 58 41 42 54",
        "fax": "01 58 41 28 74",
        "building": "Radiologie A",
    },
    # --- RADIOLOGIE B : ÉQUIPE MÉDICALE (CHEFS & SENIORS) ---
    {
        "id": "tel-bureau-cca",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Bureau des CCA / Assistants Radio B",
        "role": "Ligne directe Bureau CCA (Dr Lefèvre, Dr Talabard, Dr Monnier, Dr Hamadouche, Dr Lusi, Dr Allel)",
        "poste": "12488 / 12489",
        "phone": "01 58 41 24 88",
        "fax": "",
        "building": "Bâtiment Albarran / Ollier",
        "pinnedDefault": True,
    },
    {
        "id": "tel-feydy",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Pr Antoine FEYDY",
        "role": "PU-PH, Chef de Service — Radiologie B (Ostéo-Articulaire) • DECT 12487",
        "poste": "DECT 12487 / Secr. 12483 & 12481",
        "phone": "01 58 41 24 83",
        "fax": "01 58 41 24 55",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-drape",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Pr Jean-Luc DRAPÉ",
        "role": "PU-PH — Radiologie B • DECT 12494",
        "poste": "DECT 12494 / Secr. 12502 & 12480",
        "phone": "01 58 41 25 02",
        "fax": "01 58 41 21 51",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-lefevre",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Thomas LEFÈVRE",
        "role": "Chef de Clinique / Assistant — RI Onco & Avis Radio B",
        "poste": "DECT 12489 / Salle RI 12163",
        "phone": "01 58 41 24 89",
        "fax": "",
        "building": "Albarran / Ollier / Achard",
        "pinnedDefault": True,
    },
    {
        "id": "tel-talabard",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Marie-Pauline TALABARD",
        "role": "Chef de Clinique Assistant — RI Onco & Avis Radio B",
        "poste": "DECT 12489",
        "phone": "01 58 41 24 89",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-hamadouche",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Macil HAMADOUCHE",
        "role": "Assistant Spécialiste — Imagerie Ostéo-Articulaire & RI",
        "poste": "DECT 12504 / 12404",
        "phone": "01 58 41 25 04",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-monnier",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Hippolyte MONNIER",
        "role": "Chef de Clinique Assistant — Radio B & Staff CIRTAL",
        "poste": "DECT 12503 / 12404 / 12488",
        "phone": "01 58 41 25 03",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-lusi",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Stefano LUSI",
        "role": "Chef de Clinique / Assistant — Radiologie B",
        "poste": "DECT 12488",
        "phone": "01 58 41 24 88",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-allel",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Yazid ALLEL",
        "role": "Chef de Clinique Assistant — Radiologie B",
        "poste": "DECT 12404 / 12488",
        "phone": "01 58 41 24 04",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-laporte",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Amandine LAPORTE",
        "role": "PH / Senior — Référente Sarcomes & Radiologie B",
        "poste": "DECT 11399 / Secr. 12483",
        "phone": "01 58 41 13 99",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-mihoubi",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Fadila MIHOUBI BOUVIER",
        "role": "Praticien Hospitalier (PH) — Responsable Pédagogique & Staffs",
        "poste": "DECT 12480 / Secr. 12483",
        "phone": "01 58 41 24 80",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-costea",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Adina COSTEA",
        "role": "Praticien Hospitalier — Radiologie B",
        "poste": "12483",
        "phone": "01 58 41 24 83",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-yang",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Malika YANG",
        "role": "Praticien — IRM, Écho & Staff Rachis/Rhumato",
        "poste": "12483",
        "phone": "01 58 41 24 83",
        "fax": "",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-guerini-thevenin",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Henri GUERINI & Dr Fabrice THEVENIN",
        "role": "Praticiens Attachés — Radiologie Ostéo-Articulaire (Guerini : 18987 • Thevenin : 11339)",
        "poste": "DECT 18987 / 11339",
        "phone": "01 58 41 89 87",
        "fax": "",
        "building": "Bâtiment Ollier / Albarran",
    },
    {
        "id": "tel-burns-idier",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Robert Edward BURNS & Dr Louis IDIER",
        "role": "Chefs de Clinique (CCA) — Radiologie Cochin (Burns : 12488 • Idier : 13101)",
        "poste": "12488 / 13101",
        "phone": "01 58 41 24 88",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-radio-a",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Service de Radiologie A (Pr A. Dohan / Pr M. Barat)",
        "role": "Secrétariat Radio A & Gardes d'Imagerie (Secrétariat Universitaire : Mme Marie Masson)",
        "poste": "12490 / 14612",
        "phone": "01 58 41 24 90",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    # --- SERVICES PARTENAIRES (ORTHO, RHUMATO, ANESTH, ANAPATH, URGENCES) ---
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
        "poste": "13077 / 13041 / 13104",
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
        "role": "Médecine Péri-Opératoire & Programmation AG • SSPI / UCA : 3131 / 3232 / 13691",
        "poste": "11563 / 11566 / 11528 / 13691",
        "phone": "01 58 41 15 63",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-uca",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Unité de Chirurgie Ambulatoire (UCA — Mme S. Azzopardi)",
        "role": "Cadre de santé IBODE / Ambulatoire • Médecin UCA/SSPI : 3131 / 3232 / 13691",
        "poste": "14022 / 13691",
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
        "id": "tel-urgences-hucd",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Urgences / HUCD Cochin — SOS Rachis (Dr François LECOMTE)",
        "role": "Hospitalisation Unité Courte Durée (HUCD) & Urgences Cochin",
        "poste": "14091",
        "phone": "01 58 41 40 91",
        "fax": "",
        "building": "Urgences / HUCD Cochin",
    },
    {
        "id": "tel-onco-thorax",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Oncologie Thoracique & Pneumologie",
        "role": "DECT Oncologie 14352 / Secrétariats 12349 & 13099",
        "poste": "DECT 14352 / 12349 / 13099",
        "phone": "01 58 41 23 49",
        "fax": "01 58 41 23 85",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-med-interne",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service de Médecine Interne",
        "role": "Secrétariat 12103 / DECT Garde 18184",
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
        "poste": "11878 / 11888 / 13940",
        "phone": "01 58 41 18 88",
        "fax": "01 58 41 18 10",
        "building": "Pavillon Copernic",
    },
    # --- LABORATOIRES, PHARMACIE & ADMINISTRATION (DAM) ---
    {
        "id": "tel-hemostase",
        "category": "Laboratoires, Pharmacie & Administration (DAM)",
        "name": "Consultation & Laboratoire d'Hémostase / Hématologie Biologique",
        "role": "Bilan d'hémostase pré-geste (13445) / Labo Hémato J. Dausset (14141 / 13520)",
        "poste": "13445 / 14141 / 13520",
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
        "role": "Gestion du Personnel Médical Cochin (12295 / 11014 / 11071)",
        "poste": "12295 / 11014 / 11071",
        "phone": "01 58 41 22 95",
        "fax": "",
        "building": "Port-Royal — Pavillon de Chasse",
    },
    {
        "id": "tel-depannage-info-biomed",
        "category": "Laboratoires, Pharmacie & Administration (DAM)",
        "name": "Dépannage Informatique (*75) & Ingénierie Biomédicale",
        "role": "Assistance Informatique AP-HP : *75 • Biomédical Cochin : 11276",
        "poste": "*75 / 11276",
        "phone": "01 58 41 12 76",
        "fax": "",
        "building": "Hôpital Cochin",
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

# Correspondance entre noms/emails des seniors/contacts et leur ID d'annuaire pour auto-mise à jour depuis les mails/messages
CONTACT_MATCH_RULES = [
    ("tel-lefevre", ["thomas-jean.lefevre", "thomas lefevre", "thomas lefèvre"]),
    ("tel-talabard", ["marie.talabard", "talabard"]),
    ("tel-hamadouche", ["macil.hamadouche", "hamadouche"]),
    ("tel-monnier", ["hippolyte.monnier", "monnier"]),
    ("tel-lusi", ["stefano.lusi", "stéphano lusi", "stefano lusi"]),
    ("tel-allel", ["yazid.allel", "allel"]),
    ("tel-laporte", ["amandine.laporte", "laporte"]),
    ("tel-mihoubi", ["fadila.mihoubi", "mihoubi"]),
    ("tel-feydy", ["antoine.feydy", "feydy"]),
    ("tel-drape", ["secretariat.drape", "jean-luc drape", "jean-luc drapé"]),
    ("tel-fortin", ["anne-marie.fortin", "fortin-cozic"]),
    ("tel-mouyoungui", ["gysleve.mouyoungui", "mouyoungui"]),
    ("tel-gameiro", ["mariana.gameiro", "gameiro"]),
    ("tel-sellami", ["laila.sellami", "sellami"]),
]


def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def poste_to_cochin_phone(poste_5digits: str) -> str:
    """Convertit un poste Cochin 5 chiffres (1XXXX) en numéro 01 58 41 XX XX."""
    m = re.match(r"^1(\d{2})(\d{2})$", str(poste_5digits).strip())
    if not m:
        return ""
    return f"01 58 41 {m.group(1)} {m.group(2)}"


def sanitize_public_str(s: str) -> str:
    """Retire tout email (@) ou mobile (06/07) pour respecter assert_no_sensitive_data()."""
    if not s:
        return ""
    out = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+[.][A-Za-z.]{2,}", "", str(s))
    out = re.sub(r"\b0[67](?:[ .]?[0-9]{2}){4}\b", "", out)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" •-—")
    return out.strip()


def load_json_list(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def scan_messages_for_number_updates(entries_by_id: dict) -> list:
    """
    Analyse personal_data.json, processed_emails.json, processed_imessages.json et processed_whatsapp.json
    pour détecter automatiquement un changement de DECT / poste (1XXXX) ou de ligne Cochin (01 58 41 XX XX)
    concernant un contact de l'annuaire.
    """
    updates_log = []
    sources = ["personal_data.json", "processed_emails.json", "processed_imessages.json", "processed_whatsapp.json"]
    blobs = []
    for src in sources:
        p = BASE_DIR / src
        if p.exists():
            try:
                blobs.append(p.read_text(encoding="utf-8"))
            except Exception:
                pass

    full_text = "\n".join(blobs)
    if not full_text:
        return updates_log

    for entry_id, patterns in CONTACT_MATCH_RULES:
        entry = entries_by_id.get(entry_id)
        if not entry:
            continue
        for pat in patterns:
            regex = re.compile(
                re.escape(pat) + r"[^\n,;•]{0,65}?(?:DECT|poste)\s*[:\-]?\s*(1\d{4})\b",
                re.IGNORECASE,
            )
            for m in regex.finditer(full_text):
                new_dect = m.group(1)
                current_poste = str(entry.get("poste") or "")
                if new_dect not in current_poste:
                    entry["poste"] = f"DECT {new_dect}" + (f" / {current_poste}" if current_poste else "")
                    new_phone = poste_to_cochin_phone(new_dect)
                    if new_phone:
                        entry["phone"] = new_phone
                    updates_log.append(f"{entry['name']} -> DECT {new_dect} ({new_phone})")

    return updates_log


def fetch_cloud_annuaire_overrides() -> list:
    """Récupère les éventuels numéros ajoutés ou modifiés depuis l'interface web (Google Apps Script)."""
    env = load_env()
    webhook_url = env.get("SHEETS_WEBHOOK_URL")
    admin_token = env.get("ADMIN_TOKEN")
    if not webhook_url or not admin_token:
        return []
    eval_js = """
    var raw = PropertiesService.getScriptProperties().getProperty('cochin_annuaire_custom_v1');
    try { return raw ? JSON.parse(raw) : []; } catch (e) { return []; }
    """
    body = json.dumps({"action": "read_tabs", "admin_token": admin_token, "eval_code": eval_js}).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        res = data.get("evalResult")
        return res if isinstance(res, list) else []
    except Exception:
        return []


def sync_annuaire(fetch_cloud: bool = False) -> tuple[list, list]:
    """
    Fusionne toutes les sources de l'annuaire Cochin et met à jour les fichiers JSON locaux.
    Retourne (liste_finale, journal_modifications).
    """
    changes = []
    entries_by_id = {}
    order_ids = []

    def upsert(item: dict, source_label: str = "", overwrite_existing: bool = True):
        if not isinstance(item, dict):
            return
        iid = str(item.get("id") or "").strip()
        name = sanitize_public_str(item.get("name") or "")
        if not name:
            return
        if not iid:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:32]
            iid = f"tel-{slug}"
            item["id"] = iid

        poste_val = sanitize_public_str(item.get("poste") or item.get("short") or "")
        phone_val = sanitize_public_str(item.get("phone") or "")
        if not phone_val and poste_val:
            m5 = re.search(r"\b(1\d{4})\b", poste_val)
            if m5:
                phone_val = poste_to_cochin_phone(m5.group(1))

        normalized = {
            "id": iid,
            "category": sanitize_public_str(item.get("category") or "Radiologie B — Secrétariats & Consoles"),
            "name": name,
            "role": sanitize_public_str(item.get("role") or ""),
            "poste": poste_val,
            "phone": phone_val,
            "fax": sanitize_public_str(item.get("fax") or ""),
            "building": sanitize_public_str(item.get("building") or "Hôpital Cochin"),
        }
        if item.get("pinnedDefault"):
            normalized["pinnedDefault"] = True
        if item.get("custom"):
            normalized["custom"] = True

        if iid not in entries_by_id:
            entries_by_id[iid] = normalized
            order_ids.append(iid)
            if source_label:
                changes.append(f"[{source_label}] Ajout : {name} ({poste_val or phone_val})")
        elif overwrite_existing:
            prev = entries_by_id[iid]
            updated_fields = []
            prev.pop("email", None)
            for k in ("category", "name", "role", "poste", "phone", "fax", "building"):
                new_v = normalized.get(k, "")
                old_v = prev.get(k, "")
                if new_v and new_v != old_v:
                    prev[k] = new_v
                    updated_fields.append(k)
            if normalized.get("pinnedDefault"):
                prev["pinnedDefault"] = True
            if updated_fields and source_label:
                changes.append(f"[{source_label}] MAJ {name} ({', '.join(updated_fields)})")

    # 1. Charger les entrées existantes de cochin_annuaire.json et guide-interne-cochin-os
    for item in load_json_list(LOCAL_ANNUAIRE_PATH):
        upsert(item, "")
    for item in load_json_list(COCHIN_OS_ANNUAIRE_PATH):
        upsert(item, "cochin-os", overwrite_existing=False)

    # 2. Appliquer la base consolidée de référence (écrase les anciens postes obsolètes)
    for item in BASELINE_ENTRIES:
        upsert(item, "baseline-2026-11", overwrite_existing=True)

    # 3. Réordonner pour mettre les entrées de BASELINE_ENTRIES en tête dans leur ordre logique
    baseline_order = [x["id"] for x in BASELINE_ENTRIES]
    extra_ids = [x for x in order_ids if x not in baseline_order]
    order_ids = baseline_order + extra_ids

    # 4. Scanner automatiquement les messages/emails pour tout nouveau DECT/numéro
    msg_updates = scan_messages_for_number_updates(entries_by_id)
    changes.extend([f"[auto-scan] {u}" for u in msg_updates])

    # 5. Fusionner les éventuelles modifications faites dans l'app web (Cloud)
    if fetch_cloud:
        for c_item in fetch_cloud_annuaire_overrides():
            if c_item.get("deleted") and c_item.get("id") in entries_by_id:
                del entries_by_id[c_item["id"]]
                order_ids = [x for x in order_ids if x != c_item["id"]]
                changes.append(f"[cloud] Suppression : {c_item.get('id')}")
            else:
                upsert(c_item, "cloud", overwrite_existing=True)

    final_list = [entries_by_id[iid] for iid in order_ids if iid in entries_by_id]

    new_json = json.dumps(final_list, indent=2, ensure_ascii=False) + "\n"
    old_local = LOCAL_ANNUAIRE_PATH.read_text(encoding="utf-8") if LOCAL_ANNUAIRE_PATH.exists() else ""
    if new_json != old_local:
        LOCAL_ANNUAIRE_PATH.write_text(new_json, encoding="utf-8")

    if COCHIN_OS_ANNUAIRE_PATH.parent.exists():
        old_os = COCHIN_OS_ANNUAIRE_PATH.read_text(encoding="utf-8") if COCHIN_OS_ANNUAIRE_PATH.exists() else ""
        if new_json != old_os:
            COCHIN_OS_ANNUAIRE_PATH.write_text(new_json, encoding="utf-8")

    return final_list, changes


def main():
    parser = argparse.ArgumentParser(description="Synchronise et met à jour l'annuaire téléphonique Cochin")
    parser.add_argument("--cloud", action="store_true", help="Interroge aussi Google Apps Script pour les ajouts web")
    args = parser.parse_args()

    final_list, changes = sync_annuaire(fetch_cloud=args.cloud)
    print(f"Annuaire synchronisé : {len(final_list)} entrées.")
    if changes:
        print("Mises à jour appliquées :")
        for c in changes:
            print("  -", c)


if __name__ == "__main__":
    main()
