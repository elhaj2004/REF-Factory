"""
Crée des fiches REF exemples dans data/reference_library/ quand
O:\\ConseiletAudit n'est pas accessible (Linux, hors réseau Orange).
Les fiches sont anonymisées et couvrent les principaux domaines OCD.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

DEST = Path(__file__).resolve().parents[1] / "data" / "reference_library"
DEST.mkdir(parents=True, exist_ok=True)

FICHES = [
    {
        "filename": "REF_Audit_Gouvernance_Secteur_Bancaire.json",
        "data": {
            "titre": "Audit de gouvernance SSI - Groupe Bancaire",
            "client": "Banque régionale française (anonymisé)",
            "secteur": "Banque / Finance",
            "duree": "8 semaines",
            "equipe": "1 manager senior, 2 consultants",
            "confidentialite": "Confidentiel",
            "mots_cles": ["gouvernance", "audit", "DORA", "ISO 27001", "RSSI", "banque"],
            "contexte": "Évaluation de maturité SSI dans le cadre de la mise en conformité DORA. Entité sans politique SSI formalisée ni processus de gestion des risques documenté.",
            "mission": "Audit de gouvernance couvrant les 5 domaines DORA. Rapport et roadmap de conformité sur 18 mois.",
            "livrables": ["Rapport d'audit gouvernance SSI", "Cartographie des écarts DORA", "Roadmap conformité 18 mois"],
            "resultats": ["Maturité mesurée 2.1/5 avant intervention", "32 recommandations priorisées", "Validation AMF du plan"]
        }
    },
    {
        "filename": "REF_SOC_Industrie_Energie.json",
        "data": {
            "titre": "Mise en place SOC managé - Opérateur énergie OIV",
            "client": "Opérateur national infrastructure énergie (anonymisé)",
            "secteur": "Énergie / Infrastructure critique / OIV",
            "duree": "6 mois puis support récurrent",
            "equipe": "1 architecte sécurité, 2 analystes SOC, 1 chef de projet",
            "confidentialite": "Confidentiel",
            "mots_cles": ["SOC", "SIEM", "OIV", "NIS2", "détection", "OT/IT", "énergie"],
            "contexte": "OIV soumis aux obligations NIS2/LPM. Aucune capacité de détection centralisée. Systèmes OT/SCADA et IT sans supervision unifiée.",
            "mission": "Déploiement SOC managé IT/OT. Configuration SIEM Splunk, 120 règles de détection, runbooks astreinte 24/7.",
            "livrables": ["Architecture SOC IT/OT", "120 règles détection SIEM", "Runbooks incident response", "Tableau de bord SLA"],
            "resultats": ["MTTD réduit de 48h à <2h", "Couverture OT/IT sur 3 sites", "Certification NIS2 obtenue"]
        }
    },
    {
        "filename": "REF_Tests_Intrusion_Retail.json",
        "data": {
            "titre": "Tests d'intrusion e-commerce et cloud - Groupe Retail",
            "client": "Groupe distribution retail multicanal (anonymisé)",
            "secteur": "Retail / Distribution / E-commerce",
            "duree": "3 semaines",
            "equipe": "2 pentesters certifiés OSCP/GPEN",
            "confidentialite": "Confidentiel",
            "mots_cles": ["pentest", "intrusion", "e-commerce", "cloud", "AWS", "PCI-DSS", "API"],
            "contexte": "Préparation à la certification PCI-DSS v4.0. Plateforme traitant 2M transactions/an. Périmètre : app web, API REST, AWS, DMZ.",
            "mission": "Tests d'intrusion boîte grise sur 4 vecteurs : web OWASP, API e-commerce, cloud AWS, réseau interne.",
            "livrables": ["Rapport pentest avec PoC", "Matrice criticité CVSS 47 vulnérabilités", "Plan remédiation priorisé"],
            "resultats": ["4 vulnérabilités critiques identifiées dont 1 RCE", "Certification PCI-DSS v4.0 obtenue"]
        }
    },
    {
        "filename": "REF_PSSI_Hopital_Sante.json",
        "data": {
            "titre": "Élaboration PSSI et plan de sécurisation - CHU",
            "client": "Centre Hospitalier Universitaire régional (anonymisé)",
            "secteur": "Santé / Hôpital / Service public",
            "duree": "12 semaines",
            "equipe": "1 manager, 1 consultant senior",
            "confidentialite": "Interne",
            "mots_cles": ["PSSI", "hôpital", "HDS", "ANSSI", "RGPD", "données de santé"],
            "contexte": "Suite à cyberattaque ransomware 2023. CHU avec 1200 postes, 350 applications, 180 000 patients. Besoin de PSSI formalisée.",
            "mission": "Élaboration PSSI 17 domaines ISO 27002, analyse risques EBIOS RM, plan sécurisation pluriannuel avec budget.",
            "livrables": ["PSSI complète 17 chapitres", "Analyse EBIOS RM 12 scénarios", "PSP 2025-2027 (43 chantiers)"],
            "resultats": ["PSSI validée en 6 mois", "Score ANSSI de 15% à 42%", "Label CNIL obtenu"]
        }
    },
    {
        "filename": "REF_Cyberdiag_PME_Industrie.json",
        "data": {
            "titre": "Cyberdiagnostic et feuille de route - PME industrielle",
            "client": "Fabricant équipementier automobile (anonymisé - Grand Est)",
            "secteur": "Industrie / Manufacturing / Automobile",
            "duree": "4 semaines",
            "equipe": "1 consultant senior",
            "confidentialite": "Interne",
            "mots_cles": ["cyberdiagnostic", "PME", "feuille de route", "maturité", "TISAX", "NIS2"],
            "contexte": "PME 350 salariés, sous-traitant automobile. Exigences TISAX AL2 des donneurs d'ordre. Pas de DSI dédié.",
            "mission": "Diagnostic flash maturité 6 domaines, évaluation TISAX AL2, feuille de route pragmatique budget PME.",
            "livrables": ["Rapport cyberdiag avec scoring TISAX AL2", "Top 10 risques prioritaires", "Feuille de route 12 mois"],
            "resultats": ["Score TISAX AL2 de 28% à 61% en 8 mois", "Audit TISAX réussi", "MFA 100% accès distants"]
        }
    },
    {
        "filename": "REF_Reponse_Incident_Ransomware.json",
        "data": {
            "titre": "Réponse à incident ransomware - Groupe industriel",
            "client": "Groupe industriel européen chimie (anonymisé)",
            "secteur": "Industrie / Chimie",
            "duree": "6 semaines crise + 3 mois remédiation",
            "equipe": "CERT OCD : 1 incident commander, 3 analystes forensics, 1 threat intel",
            "confidentialite": "Confidentiel",
            "mots_cles": ["ransomware", "CERT", "réponse à incident", "forensics", "LockBit", "remédiation"],
            "contexte": "Attaque LockBit 3.0, chiffrement 40% du SI en 4h. 12 sites industriels. Demande de rançon 4M€.",
            "mission": "Engagement CERT urgence : containment, forensics, reconstruction SI, attribution, dépôt plainte, remédiation.",
            "livrables": ["Rapport forensics complet avec IoC", "Plan remédiation 62 actions", "Debriefing CODIR"],
            "resultats": ["Reprise activité critique en 72h", "Rançon non payée", "Aucune fuite de données"]
        }
    },
    {
        "filename": "REF_Conformite_RGPD_Collectivite.json",
        "data": {
            "titre": "DPO externalisé et conformité RGPD - Collectivité",
            "client": "Communauté d'agglomération 250 000 habitants (anonymisé)",
            "secteur": "Collectivité territoriale / Service public",
            "duree": "6 mois",
            "equipe": "1 DPO externalisé OCD, 1 consultant RGPD",
            "confidentialite": "Interne",
            "mots_cles": ["RGPD", "DPO", "conformité", "collectivité", "registre", "CNIL"],
            "contexte": "Collectivité sans DPO. Traitements sensibles : état civil, vidéosurveillance, données sociales. Violations non déclarées.",
            "mission": "DPO externalisé : cartographie traitements, registre RGPD, mise en conformité, formation agents.",
            "livrables": ["Registre 142 traitements", "12 PIAs réalisées", "Programme formation 320 agents"],
            "resultats": ["0 sanction CNIL sur la période", "Score RGPD de 18% à 74%"]
        }
    }
]


def main() -> int:
    created = 0
    skipped = 0
    for fiche in FICHES:
        dest_path = DEST / fiche["filename"]
        if dest_path.exists():
            skipped += 1
            print(f"  [SKIP] {fiche['filename']} (déjà présent)")
            continue
        dest_path.write_text(json.dumps(fiche["data"], indent=2, ensure_ascii=False), encoding="utf-8")
        created += 1
        print(f"  [OK]   {fiche['filename']}")

    total = sum(1 for f in DEST.rglob("*") if f.is_file())
    print(f"\nBilan : {created} créés, {skipped} ignorés | Total dans reference_library : {total} fichiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
