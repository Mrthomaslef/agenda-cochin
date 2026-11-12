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
        "role": "Ligne directe RI (Ollier / Achard) • DECT RI Onco : 12489 • DECT RI OS : 15095 / 12404",
        "poste": "12163 / DECT 12489 & 15095",
        "phone": "01 58 41 21 63",
        "fax": "",
        "email": "secretariat.radiob.cch@aphp.fr",
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
        "email": "secretariat.radiob.cch@aphp.fr",
        "building": "Bâtiment Ollier",
        "pinnedDefault": True,
    },
    {
        "id": "tel-fortin",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Anne-Marie FORTIN-COZIC",
        "role": "Secrétariat Chef de Service (Pr Antoine FEYDY) — Bât. Albarran",
        "poste": "12483",
        "phone": "01 58 41 24 83",
        "fax": "01 58 41 24 55",
        "email": "anne-marie.fortin@aphp.fr",
        "building": "Albarran / Ollier",
        "pinnedDefault": True,
    },
    {
        "id": "tel-accueil-ollier",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Accueil & Bureau des RDV Radio B (Ollier -1 — J-Y. Chastroux)",
        "role": "Accueil Radio B : 12350 • Bureau RDV : 12360 / 19135 • J-Y. Chastroux : 19134 (Fax 12493)",
        "poste": "12350 / 12360 / 19135 / 19134",
        "phone": "01 58 41 23 60",
        "fax": "01 58 41 24 93",
        "email": "rdv.radiob.cch@aphp.fr / secretariat.radiob.cch@aphp.fr",
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
        "email": "gysleve.mouyoungui@aphp.fr",
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
        "email": "mariana.gameirojorge@aphp.fr",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-orak",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Ania DWORAK (Secrétariat Pr Jean-Luc DRAPÉ)",
        "role": "Assistante Médico-Administrative — Radio B (Poste 12502 • Fax Ania & Sandrine : 12151)",
        "poste": "12502",
        "phone": "01 58 41 25 02",
        "fax": "01 58 41 21 51",
        "email": "ania.dworak@aphp.fr / secretariat.drape.cch@aphp.fr",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-camblong-pouget",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Sandrine CAMBLONG & Christelle POUGET",
        "role": "Secrétaires Radio B — S. Camblong : 12481 (Fax 12151) • C. Pouget : 12507",
        "poste": "12481 / 12507",
        "phone": "01 58 41 24 81",
        "fax": "01 58 41 21 51",
        "email": "sandrine.camblong@aphp.fr / christelle.pouget@aphp.fr",
        "building": "Bâtiment Ollier / Albarran",
    },
    {
        "id": "tel-menage",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Karine PRETZNER / Isabelle MENAGE MARACHE",
        "role": "Cadre Médico-Technique — Service de Radiologie B",
        "poste": "12484",
        "phone": "01 58 41 24 84",
        "fax": "",
        "email": "karine.pretzner@aphp.fr / isabelle.menage-marache@aphp.fr",
        "building": "Bâtiment Ollier (1er sous-sol)",
    },
    {
        "id": "tel-cadres-rxb",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Cadres Radiologie B (C. Fischer / V. Nitsche / K. Pretzner / P. Vilasèque / L. Selami)",
        "role": "C. Fischer : 13424 • V. Nitsche : 12284 • K. Pretzner : 12484 • P. Vilasèque : 14752 • L. Selami : 12197",
        "poste": "13424 / 12284 / 12484 / 14752 / 12197",
        "phone": "01 58 41 34 24",
        "fax": "",
        "email": "catherine.fischer@aphp.fr / veronique.nitsche@aphp.fr / karine.pretzner@aphp.fr / philippe.vilaseque@aphp.fr / laila.sellami@aphp.fr",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-sellami",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Laila SELAMI (Cadre Radio B & Référente PACS Carestream)",
        "role": "Cadre Radio B & Informatique Imagerie / PACS Carestream & Syngo.via (CCH, HTD, BRC)",
        "poste": "12197",
        "phone": "01 58 41 21 97",
        "fax": "",
        "email": "laila.sellami@aphp.fr",
        "building": "Imagerie Cochin",
        "pinnedDefault": True,
    },
    {
        "id": "tel-logistique-matos",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Logisticiens Radio B (O. Peaudecerf / D. Van Nifterik)",
        "role": "Commandes & Matériel Interventionnel Radio B (O. Peaudecerf : 12984 • D. Van Nifterik : 12183)",
        "poste": "12984 / 12183",
        "phone": "01 58 41 29 84",
        "fax": "",
        "email": "olivier.peaudecerf@aphp.fr / david.vannifterik@aphp.fr",
        "building": "Radiologie B",
    },
    {
        "id": "tel-pcr-radioprotection",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Radioprotection (S. Le Gall / C. Stainmesse) & Radiophysiciennes (C. Bouchard / M-J. Waryn)",
        "role": "Radioprotection : S. Le Gall (14782) & C. Stainmesse (11267) • Radiophysiciennes : C. Bouchard (11872) & M-J. Waryn (14783)",
        "poste": "14782 / 11267 / 11872 / 14783",
        "phone": "01 58 41 47 82",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-consoles-tdm",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Consoles Scanners Cochin (Ollier, Sc3, Sc4 Urgences, Lecture, Sc1/Sc2 RxA)",
        "role": "Accueil (Scanner & Écho Ollier) : 12266 • Scanner 3 : 12883 • Scanner 4 (Urgences) : 12285 • Salle de lecture : 18384 • DECT Radiologue Radio B : 15314 • Scanner 1 RxA : 18978 • Scanner 2 RxA : 18656",
        "poste": "12266 / 12883 / 12285 / 18384 / DECT 15314",
        "phone": "01 58 41 22 66",
        "fax": "",
        "building": "Ollier / Achard",
        "pinnedDefault": True,
    },
    {
        "id": "tel-consoles-irm",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Consoles IRM Cochin (IRM 1 3T, IRM 2 1.5T & Salle d'interprétation)",
        "role": "IRM 1 - CB 411 (3T) : 12492 • IRM 2 - CB 412 (1.5T) : 12798 • Salle d'interprétation IRM : 18715",
        "poste": "12492 / 12798 / 18715",
        "phone": "01 58 41 24 92",
        "fax": "",
        "building": "Imagerie Cochin",
    },
    {
        "id": "tel-consoles-echo",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Consoles Échographie Radio B, Rhumatologie, SAU & Radio A",
        "role": "Écho 1 : 13510 • Écho 2 : 18599 • DECT Écho : 12504 • Écho 3 (Rhumatologie) : 19905 • Manip SAU : 12514 • Écho SAU : 12513 • DECT SAU : 12621 • Écho RxA : 12477",
        "poste": "13510 / 18599 / 19905 / DECT 12504",
        "phone": "01 58 41 35 10",
        "fax": "",
        "building": "Bâtiment Ollier / SAU",
    },
    {
        "id": "tel-manip-bloc-salles",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Postes Radio B (A, B, C, EOS), Manip Bloc, Staff Albarran, Repos & Rx Lit",
        "role": "A - CB 121 : 18982 • B - CB 122 : 18983 • C - CB 123 : 18984 • EOS - CB 124 : 18985 • Manip Bloc : 12498 • Salle de repos RxB : 18356 • Salle de Staff Albarran RxB : 12508 • Manip Radio de Lit RxB : 15094",
        "poste": "18982 / 18983 / 18984 / 18985 / 12498 / 12508 / 18356 / 15094",
        "phone": "01 58 41 24 98",
        "fax": "",
        "building": "Ollier / Albarran",
    },
    {
        "id": "tel-gardes-imagerie",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "DECT Gardes d'Imagerie (Sénior & Radio B)",
        "role": "Radiologue de garde - Sénior / DECT SAU : 12621 • DECT Radiologue Radio B : 15314 • Radiologue interventionnel OS : 15095",
        "poste": "DECT 12621 / 15314 / 15095",
        "phone": "01 58 41 26 21",
        "fax": "",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-allura-rxa",
        "category": "Radiologie B — Secrétariats & Consoles",
        "name": "Radiologie A (Accueil, RDV, Allura, Écho, Scanners, Rx Lit) & Médecine Nucléaire",
        "role": "Accueil RxA : 12463 - 18836 • Bureau RDV RxA : 19146 - 19147 (Fax 12874) • Allura : 14254 (manip) • Écho RxA : 12477 • Sc1 : 18978 • Sc2 : 18656 • Rx Lit / Néo Nat : 15696 - 15726 • Cadres RxA : 12490-12453-14306 • Méd. Nucléaire Accueil/RDV : 12204 - 12179 • Caméra 1/2/3 : 12188-12206-12985 • Écho : 12975 - 12978 • TEP Scan : 12187 • Cadre : 12323",
        "poste": "12463 / 18836 / 19146 / 19147 / 14254 / 12187",
        "phone": "01 58 41 42 54",
        "fax": "01 58 41 28 74",
        "email": "rdv.radioa.cch@aphp.fr / radio.vasculaire.cch@aphp.fr",
        "building": "Radiologie A / Médecine Nucléaire",
    },
    # --- RADIOLOGIE B : ÉQUIPE MÉDICALE (CHEFS & SENIORS) ---
    {
        "id": "tel-bureau-cca",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Bureau des CCA / Assistants Radio B",
        "role": "Dr Lefèvre & Dr Talabard : 12489 • Dr Lusi : 12488 • Dr Monnier : 12503 • Dr Hamadouche : 12504 • Dr Allel : 12404",
        "poste": "12489 / 12488 / 12503 / 12504 / 12404",
        "phone": "01 58 41 24 89",
        "fax": "",
        "building": "Bâtiment Albarran / Ollier",
        "pinnedDefault": True,
    },
    {
        "id": "tel-feydy",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Pr Antoine FEYDY",
        "role": "PU-PH, Chef de Service — Radiologie B (Ostéo-Articulaire) • Ligne directe : 12494 • Secr. Anne-Marie Fortin : 12483",
        "poste": "12494 / Secr. 12483",
        "phone": "01 58 41 24 94",
        "fax": "01 58 41 24 55",
        "email": "antoine.feydy@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-drape",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Pr Jean-Luc DRAPÉ",
        "role": "PU-PH — Radiologie B • Secrétariat (Ania Dworak) : 12502 (Fax 12151)",
        "poste": "12502 (Ania)",
        "phone": "01 58 41 25 02",
        "fax": "01 58 41 21 51",
        "email": "jean-luc.drape@aphp.fr / secretariat.drape.cch@aphp.fr",
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
        "email": "thomas-jean.lefevre@aphp.fr",
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
        "email": "marie.talabard@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-hamadouche",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Macil HAMADOUCHE",
        "role": "Assistant Spécialiste — Imagerie Ostéo-Articulaire & RI",
        "poste": "DECT 12504",
        "phone": "01 58 41 25 04",
        "fax": "",
        "email": "macil.hamadouche@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-monnier",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Hippolyte MONNIER",
        "role": "Chef de Clinique Assistant — Radio B & Staff CIRTAL",
        "poste": "DECT 12503",
        "phone": "01 58 41 25 03",
        "fax": "",
        "email": "hippolyte.monnier@aphp.fr",
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
        "email": "stefano.lusi@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-allel",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Yazid ALLEL",
        "role": "Chef de Clinique Assistant — Radiologie B",
        "poste": "DECT 12404",
        "phone": "01 58 41 24 04",
        "fax": "",
        "email": "yazid.allel@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-laporte",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Amandine LAPORTE",
        "role": "PH / Senior — Référente Sarcomes & Radiologie B (Pas de DECT • Secr. 12483)",
        "poste": "Pas de DECT / Secr. 12483",
        "phone": "01 58 41 24 83",
        "fax": "",
        "email": "amandine.laporte@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-mihoubi",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Fadila MIHOUBI BOUVIER",
        "role": "Praticien Hospitalier (PH) — Responsable Pédagogique & Staffs (DECT 18987)",
        "poste": "DECT 18987",
        "phone": "01 58 41 89 87",
        "fax": "",
        "email": "fadila.mihoubibouvier@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-costea",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Adina COSTEA",
        "role": "Assistante Spécialiste (partagée CH Gonesse) — Radiologie B (Jeudi & Vendredi)",
        "poste": "12483",
        "phone": "01 58 41 24 83",
        "fax": "",
        "email": "secretariat.radiob.cch@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-yang",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Malika / Sisi YANG",
        "role": "Praticien — IRM, Écho & Staff Rachis/Rhumato",
        "poste": "12483",
        "phone": "01 58 41 24 83",
        "fax": "",
        "email": "sisi.yang@aphp.fr / secretariat.radiob.cch@aphp.fr",
        "building": "Albarran / Ollier",
    },
    {
        "id": "tel-guerini-thevenin",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Henri GUERINI & Dr Fabrice THEVENIN",
        "role": "Praticiens Attachés — Radiologie Ostéo-Articulaire (Pas de DECT • Secr. 12483 / 12502)",
        "poste": "Pas de DECT / Secr. 12483 & 12502",
        "phone": "01 58 41 24 83",
        "fax": "",
        "email": "henri.guerini@aphp.fr / fabrice.thevenin@aphp.fr",
        "building": "Bâtiment Ollier / Albarran",
    },
    {
        "id": "tel-burns-idier",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Dr Robert Edward BURNS (Radio) & Dr Louis IDIER (CCA Chirurgie Orthopédique)",
        "role": "Dr R. E. Burns (CCA Radiologie : 12488) • Dr L. Idier (CCA Chirurgie Orthopédique — Secr. Mme Rozenn L'Henoret : 13101 / 01 58 41 31 01)",
        "poste": "12488 / 13101",
        "phone": "01 58 41 31 01",
        "fax": "",
        "email": "robert.burns@aphp.fr / louis.idier@aphp.fr / rozenn.lhenoret@aphp.fr",
        "building": "Bâtiment Ollier — Hôpital Cochin",
    },
    {
        "id": "tel-radio-a",
        "category": "Radiologie B — Équipe Médicale (Chefs & Seniors)",
        "name": "Service de Radiologie A (Pr A. Dohan / Pr M. Barat)",
        "role": "Secrétariat Radio A & RI Paris Centre (14612 / 12476) • Gardes d'Imagerie & Secr. Universitaire (Mme Marie Masson : 12490)",
        "poste": "12490 / 14612 / 12476",
        "phone": "01 58 41 24 90",
        "fax": "",
        "email": "anthony.dohan@aphp.fr / maxime.barat@aphp.fr / marie.masson@aphp.fr / Interventionnel.pariscentre.cch@aphp.fr",
        "building": "Bâtiment Achard — Hôpital Cochin",
    },
    # --- SERVICES PARTENAIRES (ORTHO, RHUMATO, ANESTH, ANAPATH, URGENCES) ---
    {
        "id": "tel-ortho-biau",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Chirurgie Orthopédique & Oncologique — Pr David BIAU (Mme A. Tison)",
        "role": "Secrétariat Pr Biau (13037) • Bureau : 18764 • DECT : 14052",
        "poste": "13037 / 18764 / DECT 14052",
        "phone": "01 58 41 30 37",
        "fax": "01 58 41 30 60 / 01 58 41 30 16",
        "email": "secretariat.biau.cch@aphp.fr / david.biau@aphp.fr",
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
        "email": "khaoula.rahmani@aphp.fr / adjopatricia.bitty@aphp.fr / laurence.guedj@aphp.fr",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-ortho-maalouf",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Chirurgie Orthopédique — Dr V. DUMAINE (Banque Os) / Dr P. MAALOUF / Dr A. VILLARD",
        "role": "Secr. Dr V. Dumaine (Mme C. Dumousseau : 13104) • Secr. Dr A. Villard (Mme R. Rahal : 13041) • Secr. Dr P. Maalouf : 13077",
        "poste": "13104 / 13041 / 13077",
        "phone": "01 58 41 31 04",
        "fax": "",
        "email": "valerie.dumaine@aphp.fr / celine.dumousseau@aphp.fr / alexandra.villard2@aphp.fr / rachida.rahal@aphp.fr / peter.maalouf@aphp.fr",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-ortho-corsia-ruterana",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Chirurgie Orthopédique — Dr Simon CORSIA & Dr Paul RUTERANA (Mme Hélène Bard)",
        "role": "Secrétariat Dr S. Corsia & Dr P. Ruterana : 11493 • RDV CS Orthopédie : 13038",
        "poste": "11493 / 13038",
        "phone": "01 58 41 14 93",
        "fax": "",
        "email": "helene.bard@aphp.fr / simon.corsia@aphp.fr / paul.ruterana@aphp.fr",
        "building": "Bâtiment Ollier",
    },
    {
        "id": "tel-rhumato-allanore",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service de Rhumatologie (Pr Y. ALLANORE — Mme Canvel / Dr E. KOUMAKIS / Dr H. Hajji / Dr J. Pariselle / Dr A. Raymond)",
        "role": "Secrétariat Rhumatologie A/B (12606 / 12619) • Hospit Trad. : Dr A. Raymond (DECT 12500 / Secr. Mme A. Coche : 12559, Fax 12624) • HDS Rhumato / Secr. Dr H. Hajji : 13173 • CRMR MOC & Métabolisme Ca/P (Dr E. Koumakis / ARC Mme A. Camara : 13429)",
        "poste": "12606 / 12619 / 12559 / DECT 12500 / 13173 / 13429",
        "phone": "01 58 41 26 06",
        "fax": "01 58 41 40 97 / 01 58 41 26 24",
        "email": "yannick.allanore@aphp.fr / eugenie.koumakis@aphp.fr / aicha.camara@aphp.fr / haifa.hajji@aphp.fr / juliette.pariselle@aphp.fr / anna.raymond@aphp.fr",
        "building": "Bâtiment Achard / Hardy",
    },
    {
        "id": "tel-anesth",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service d'Anesthésie-Réanimation & Consultations d'Anesthésie (Pr C. Baillard / Dr M.S. Dallel / Dr W. Ouechani)",
        "role": "Médecine Péri-Opératoire & Programmation AG (Dr M.S. Dallel resp. RI • Dr W. Ouechani 11566 • SSPI / UCA : 3131 / 3232 / 13691)",
        "poste": "11563 / 11566 / 11528 / 13691",
        "phone": "01 58 41 15 63 / 01 58 41 15 66",
        "fax": "",
        "email": "mohamedsabri.dallel@aphp.fr / wisalle.ouechani@aphp.fr / christophe.baillard@aphp.fr / michele.rozet@aphp.fr / audrey.primot@aphp.fr",
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
        "email": "sandra.azzopardi@aphp.fr",
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
        "email": "elisabeth.vaugenot@aphp.fr",
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
        "email": "leslie.chanat@aphp.fr / frederique.larousserie@aphp.fr",
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
        "email": "corinne.taliercio@aphp.fr / serge.perrot@aphp.fr",
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
        "email": "francois.lecomte@aphp.fr",
        "building": "Urgences / HUCD Cochin",
    },
    {
        "id": "tel-onco-thorax",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Oncologie Thoracique & Pneumologie (Dr J. SLOMKA / Dr S. CHELABI / Programmation)",
        "role": "DECT Dr J. Slomka : 14352 (Secr. 12349) • HDS Onco Thoracique (Dr S. Chelabi — Unité Y. Pouzin : Secr. 13099) • Poste de soins HDS : 12154 • Prog. HDS : 12168 (Fax 12977) • Prog. HC : 12377 / 12159 (Fax 12352 / 12365)",
        "poste": "DECT 14352 / 12349 / 13099 / 12154 / 12168",
        "phone": "01 58 41 23 49",
        "fax": "01 58 41 23 85 / 01 58 41 22 60",
        "email": "jeremy.slomka@aphp.fr / samy.chelabi@aphp.fr / programmation.pneumologie.cch@aphp.fr",
        "building": "Bâtiment Cornil Brissaud — Hôpital Cochin",
    },
    {
        "id": "tel-med-interne",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service de Médecine Interne (Pr L. MOUTHON / Pr B. TERRIER)",
        "role": "Secrétariat 12103 • Pr B. Terrier : 11461 • DECT Garde : 18184",
        "poste": "12103 / 11461 / DECT 18184",
        "phone": "01 58 41 21 03",
        "fax": "01 58 41 15 79 / 01 58 41 14 50",
        "email": "benjamin.terrier@aphp.fr / luc.mouthon@aphp.fr",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-hemato-clin",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service d'Hématologie Clinique (Dr S. Knapp / Dr A. Fernandez • Secr. Mme V. Kerouaz)",
        "role": "Dr A. Fernandez (CCA) : 15256 (01 58 41 52 56) • Secrétariat Hématologie Clinique : 12130 / 13919 / 12110",
        "poste": "15256 / 12130 / 13919 / 12110",
        "phone": "01 58 41 21 30",
        "fax": "",
        "email": "silene.knapp@aphp.fr / alexis.fernandez@aphp.fr",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-endocrino",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service d'Endocrinologie (Pr J. BERTHERAT) & Programmation Hospit (Copernic)",
        "role": "Pr J. Bertherat : 11895 • Secr. 11878 • Programmation Hospit 11888 & 13940",
        "poste": "11895 / 11878 / 11888 / 13940",
        "phone": "01 58 41 18 95",
        "fax": "01 58 41 18 10 / 01 46 33 80 60",
        "email": "jerome.bertherat@aphp.fr",
        "building": "Pavillon Copernic",
    },
    {
        "id": "tel-onco-dig",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Oncologie Digestive & Hépato-Gastro-Entérologie (Dr Anna PELLAT)",
        "role": "Oncologie Digestive Cochin — DECT Dr A. Pellat : 15046",
        "poste": "DECT 15046",
        "phone": "01 58 41 50 46",
        "fax": "",
        "email": "anna.pellat@aphp.fr",
        "building": "Hôpital Cochin",
    },
    {
        "id": "tel-mpr-nguyen",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service MPR — Rééducation & Pathologies du Rachis (Pr Christelle NGUYEN)",
        "role": "Secrétariat MPR Hardy B1 (Laëtitia : 12945) • HDS MPR (Mme Alisa Nikolić : 13177) • Dr Alexandre Luc / Dr Quentin Lejeune",
        "poste": "12945 / 13177",
        "phone": "01 58 41 29 45",
        "fax": "01 58 41 25 38",
        "email": "reeducation.hardyb1.cch@aphp.fr / alisa.nikolic@aphp.fr / christelle.nguyen2@aphp.fr / quentin.lejeune@aphp.fr",
        "building": "Bâtiment Hardy (B1 / 1er sous-sol)",
    },
    {
        "id": "tel-dermato-kramkimel",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Service de Dermatologie & Oncologie Cutanée (Pr N. DUPIN / Dr N. KRAMKIMEL / Dr C. LHEURE / Dr J. ARCHIMBAUD)",
        "role": "Dr J. Archimbaud : DECT 14668 (Secr. 11838) • Secr. Dr C. Lheure (Mme P. Figoni) : 11789 • IDE Parcours HDJ : 11868 • RDV CS : 11919 • Secr. CS : Mme V. Bruandet",
        "poste": "DECT 14668 / 11838 / 11789 / 11868 / 11919",
        "phone": "01 58 41 18 38",
        "fax": "",
        "email": "nora.kramkimel@aphp.fr / juliette.archimbaud@aphp.fr / coralie.lheure@aphp.fr / ideparcours.dermato.cch@aphp.fr / valerie.bruandet@aphp.fr",
        "building": "Site Port-Royal — Bâtiment Copernic / Tarnier",
    },
    {
        "id": "tel-onco-goldwasser",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Cancérologie / Oncologie Médicale Port-Royal (Pr F. GOLDWASSER / Dr P. BOUDOU-ROUQUETTE / Dr J. NOËL)",
        "role": "Dr P. Boudou-Rouquette (PH) : 11439 (Fax 11434) • Secr. Pr Goldwasser / Dr J. Noël (Mme V. Solovieff) : 11454",
        "poste": "11439 / 11454",
        "phone": "01 58 41 14 39",
        "fax": "01 58 41 14 34",
        "email": "pascaline.boudou@aphp.fr / violaine.solovieff@aphp.fr",
        "building": "Site Port-Royal — 123 Boulevard de Port-Royal, 75014 Paris",
    },
    {
        "id": "tel-onco-hegp",
        "category": "Services Partenaires (Ortho, Rhumato, Anesth, Anapath)",
        "name": "Oncologie Médicale HEGP (Pr J. MEDIONI / Dr A. ROCHAND / Dr É. AUCLIN)",
        "role": "Secr. Pr Medioni (Mme S. Zion) : 01 56 09 27 81 • Secr. Dr Rochand (Mme J. Diony) : 01 56 09 51 22 • Prog. : 01 56 09 57 82",
        "poste": "HEGP 22781 / 25122 / 25782",
        "phone": "01 56 09 27 81",
        "fax": "01 56 09 35 77 / 01 56 09 51 10",
        "email": "jacques.medioni@aphp.fr / adrien.rochand@aphp.fr / edouard.auclin@aphp.fr / sandy.zion@aphp.fr / jessica.diony@aphp.fr",
        "building": "HEGP — 20 rue Leblanc, 75015 Paris",
    },
    # --- RCP & STAFFS MULTIDISCIPLINAIRES COCHIN ---
    {
        "id": "tel-rcp-meta-os",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "RCP Métastases Osseuses (Méta-Os) — Lundi 12h00 (Visio Teams)",
        "role": "Référent Radio B : Dr Thomas LEFÈVRE (DECT 12489) • Inscriptions Cochin : Aurélie TISON (13037) • Onco HEGP : Dr C. Thibault / Dr A. Rochand (Secr. J. Diony : 01 56 09 51 22) • RT : Dr Y. Meraouna / Dr S. Benichou • Ortho HEGP : Dr D. Casasola",
        "poste": "13037 / DECT 12489",
        "phone": "01 58 41 30 37",
        "fax": "01 58 41 30 60",
        "email": "secretariat.biau.cch@aphp.fr / thomas-jean.lefevre@aphp.fr / constance.thibault@aphp.fr / adrien.rochand@aphp.fr / yannis.meraouna@aphp.fr / sasha.benichou@aphp.fr",
        "building": "Visio Teams / Bureau Radio B (Albarran -1)",
        "pinnedDefault": True,
    },
    {
        "id": "tel-rcp-cirtal-ewing",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "RCP CIRTAL / Tumeurs Osseuses & Sarcomes d'Ewing — Lundi Après-midi",
        "role": "Référent Radio B : Dr Hippolyte MONNIER (DECT 12503) • Coord. Chirurgie Ortho : Pr David BIAU (Secr. Mme A. Tison : 13037)",
        "poste": "DECT 12503 / 13037",
        "phone": "01 58 41 25 03",
        "fax": "01 58 41 30 60",
        "email": "secretariat.biau.cch@aphp.fr / hippolyte.monnier@aphp.fr / david.biau@aphp.fr",
        "building": "Bâtiment Ollier / Albarran",
        "pinnedDefault": True,
    },
    {
        "id": "tel-rcp-sarcomes",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "RCP Sarcomes (Os & Tissus Mous) — Mardi 17h00",
        "role": "Référents Radio B : Dr Amandine LAPORTE (Pas de DECT • Secr. 12483) & Chefs • Ortho : Pr D. BIAU / Pr P. ANRACT (13037) • Onco Méd. Port-Royal : Pr F. GOLDWASSER / Dr P. BOUDOU-ROUQUETTE (11439) / Dr J. NOËL (Secr. V. Solovieff : 11454)",
        "poste": "13037 / 11439 / 11454 / 12483",
        "phone": "01 58 41 30 37",
        "fax": "01 58 41 30 60",
        "email": "pascaline.boudou@aphp.fr / violaine.solovieff@aphp.fr / secretariat.biau.cch@aphp.fr / amandine.laporte@aphp.fr",
        "building": "Salle de Staff Ollier (3e étage)",
        "pinnedDefault": True,
    },
    {
        "id": "tel-rcp-rachis",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "RCP Rachis & Staff Rhumatologie Osseuse — Mercredi 14h30",
        "role": "Référente Radio B : Dr Malika YANG (Secr. 12483) • MPR Rachis : Pr C. NGUYEN (12945) • Rhumatologie : 12606",
        "poste": "12945 / 12606 / 12483",
        "phone": "01 58 41 29 45",
        "fax": "01 58 41 25 38",
        "email": "reeducation.hardyb1.cch@aphp.fr / christelle.nguyen2@aphp.fr / anne-marie.fortin@aphp.fr",
        "building": "Salle de Staff MPR — Bâtiment Hardy (1er sous-sol)",
    },
    {
        "id": "tel-rcp-maladies-osseuses",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "RCP Maladies Osseuses Constitutionnelles & Métaboliques — Mercredi 16h30",
        "role": "Rhumatologie & Métabolisme Osseux (Dr E. Koumakis / Secr. 12606 / 12619 • ARC Mme A. Camara : 13429) • Radio B (Dr M. Yang / Pr A. Feydy : 12494 / 12483)",
        "poste": "12606 / 12619 / 13429 / 12483",
        "phone": "01 58 41 26 06",
        "fax": "01 58 41 40 97",
        "email": "yannick.allanore@aphp.fr / eugenie.koumakis@aphp.fr / aicha.camara@aphp.fr / antoine.feydy@aphp.fr",
        "building": "Salle de Staff — Bâtiment Hardy A (RDC)",
    },
    {
        "id": "tel-staff-protheses-sport",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "Staff Prothèse Douloureuse (Ven. 11h30) & Staff Sport Membre Sup (Ven. 14h00)",
        "role": "Mensuels (1 fois/mois) • Référent Radio B : Dr Henri GUERINI (Pas de DECT • Secr. 12483) • MPR (12945) & Ortho",
        "poste": "12945 / 12483",
        "phone": "01 58 41 29 45",
        "fax": "",
        "email": "henri.guerini@aphp.fr / reeducation.hardyb1.cch@aphp.fr",
        "building": "Salle de Staff MPR — Bâtiment Hardy (1er sous-sol)",
    },
    {
        "id": "tel-staff-mpr-rhumato",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "Staffs Radio / MPR (1er Ven. 15h30) & Radio / Rhumato (3e Ven. 15h30)",
        "role": "Référente Radio B : Dr Fadila MIHOUBI BOUVIER (DECT 18987) • Organisation : Anne-Marie FORTIN (12483) • Salle Staff Albarran : 12508",
        "poste": "12508 / DECT 18987 / 12483",
        "phone": "01 58 41 25 08",
        "fax": "01 58 41 24 55",
        "email": "fadila.mihoubibouvier@aphp.fr / anne-marie.fortin@aphp.fr",
        "building": "Salle de Staff Radio B — Pavillon Albarran (1er sous-sol)",
    },
    {
        "id": "tel-staff-cra-boneclub",
        "category": "RCP & Staffs Multidisciplinaires Cochin",
        "name": "CRA (Confrontations Radio-Anapath — Ven. 14h15) & Bone Club (Mer. 18h00)",
        "role": "CRA : Radio B & Anapath (Dr F. Larousserie / Dr V. Audard : 13542) en Salle Staff Albarran (12508) • Bone Club : Amphi Luton • Secr. Enseignement : S. Camblong (12481)",
        "poste": "12508 / 12481 / 13542",
        "phone": "01 58 41 24 81",
        "fax": "01 58 41 21 51",
        "email": "enseignement.radiob.cch@aphp.fr / sandrine.camblong@aphp.fr / frederique.larousserie@aphp.fr",
        "building": "Salle de Staff Albarran -1 / Amphithéâtre Luton",
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
        "email": "marie-laure.brandely-piat@aphp.fr / hugo.palisson@aphp.fr",
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
        "email": "lea.meyer@aphp.fr",
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
        "name": "Bureau du Personnel Médical & DAM — Pavillon de Chasse (Mme A. N'Diaye / Mme M. Lambert / Mme É. Hache)",
        "role": "Gestion du Personnel Médical Cochin & DAM (12295 / 11014 / É. Hache : 11071) • Gestionnaire Imagerie : 11058 • Présence au travail : 11573 • Relations Usagers (S. Dufay) : 11159 / 14252",
        "poste": "12295 / 11014 / 11071 / 11058 / 11573",
        "phone": "01 58 41 22 95",
        "fax": "",
        "email": "aminata.ndiaye3@aphp.fr / magalie.lambert@aphp.fr / emilie.hache@aphp.fr / isabelle.parrain@aphp.fr / cindy.besacier@aphp.fr / sandrine.dufay@aphp.fr",
        "building": "Port-Royal — Pavillon de Chasse / Cochin",
    },
    {
        "id": "tel-depannage-info-biomed",
        "category": "Laboratoires, Pharmacie & Administration (DAM)",
        "name": "Numéros Utiles Cochin : Informatique (*75), Biomédical, Sécurité & Services Techniques",
        "role": "Informatique : *75 • Biomédical : 11276 - 11271 • Service Technique : 11400 • Vaguemestre : 11156 • Sécurité Anti-Malveillances : 11138 - 14450 • Sécurité Incendie : 11152 • Broca : 01 44 08 35 14",
        "poste": "*75 / 11276 / 11271 / 11400 / 11156 / 11138 / 14450 / 11152",
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
    {
        "id": "tel-macsf-rcp",
        "category": "Laboratoires, Pharmacie & Administration (DAM)",
        "name": "MACSF — Assurance RCP & Protection Juridique (Contrat n° 7485615)",
        "role": "Assurance RCP Hospitalier + Remplacements libéraux • Référent : Tony TAHIRI / Julie ERARD • Agence Paris 12",
        "poste": "3233 / Dossier 7485615",
        "phone": "3233",
        "fax": "",
        "email": "contact@macsf.fr / societaire@macsf.fr",
        "building": "275 rue du Faubourg Saint-Antoine, 75012 Paris",
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
    ("tel-onco-dig", ["anna.pellat", "pellat"]),
    ("tel-mpr-nguyen", ["christelle.nguyen", "reeducation.hardyb1"]),
    ("tel-dermato-kramkimel", ["nora.kramkimel", "kramkimel", "ideparcours.dermato", "valerie.bruandet"]),
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

        email_val = str(item.get("email") or "").strip()
        normalized = {
            "id": iid,
            "category": sanitize_public_str(item.get("category") or "Radiologie B — Secrétariats & Consoles"),
            "name": name,
            "role": sanitize_public_str(item.get("role") or ""),
            "poste": poste_val,
            "phone": phone_val,
            "fax": sanitize_public_str(item.get("fax") or ""),
            "email": email_val,
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
            for k in ("category", "name", "role", "poste", "phone", "fax", "email", "building"):
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
