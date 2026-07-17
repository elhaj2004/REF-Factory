# REF-Factory

REF-Factory génère automatiquement une **fiche REF Orange Cyberdefense** au format PowerPoint une seule slide, conforme à la charte graphique OCD, à partir d'un brief consultant et d'une base d'exemples locale (RAG).

---

## 1. Objectif

Issu du cadrage `Cadrage_IA REF Factory CU10.pdf` :

- Retrouver des fiches REF similaires déjà capitalisées
- Aider le consultant à produire une nouvelle fiche REF plus vite
- Respecter la structure et le style OCD (couleurs officielles, typo, grille)
- Ne jamais inventer les informations manquantes (`[A_COMPLETER]`)
- Livrer un fichier `.pptx` une slide directement exploitable

---

## 2. Architecture du pipeline

```
[Brief + champs UI + pièces jointes]
              │
              ▼
       collect_inputs
              │
              ▼
      retrieve_examples   ◄── RAG local (ChromaDB + local embeddings)
              │
              ▼
       structure_ref      ◄── LLM si disponible, sinon fallback heuristique
              │
              ▼
        render_pptx        ◄── python-pptx, charte OCD intégrée
              │
              ▼
       check_quality
              │
              ▼
             FIN
```

- Si aucun LLM n'est configuré : le fallback heuristique prend le relais (champs extraits du brief, mots-clés, phrases courtes).
- Si aucune fiche d'exemple n'est présente : la génération fonctionne mais le rapport le signale.

---

## 3. Conformité charte OCD

### Couleurs officielles

Extraites des fichiers de brand box :
- `Tools and templates PPT - FR/French/6. XML/Orange WHT Core.xml`
- `Tools and templates PPT - FR/French/6. XML/Orange BLK Core.xml`

| Couleur | Valeur | Rôle |
|---|---|---|
| Orange principal | `#FF7900` | Titres de section, bandeau, badge accent |
| Noir | `#000000` | Texte principal, titre slide |
| Dark grey | `#595959` | Sous-titres, texte secondaire |
| Medium grey | `#8F8F8F` | Footer, légendes |
| Light grey | `#D6D6D6` | Séparateurs, bordures |

> ⚠️ L'ancienne valeur `#FF6600` était incorrecte. La couleur officielle est `#FF7900` (source : `accent1` / `lt2` dans les XML de brand box).

### Polices

- Principale : **Source Sans Pro**
- Fallback : Calibri, Arial, Helvetica Neue

### Dimensions slide

- Largeur : **33.87 cm**
- Hauteur : **19.05 cm** (format 16:9 standard OCD)

### Grille de mise en page

```
┌─────────────────────────────────────────────────┐
│  [Bandeau orange 0.6 cm]        Orange CD       │
├─────────────────────────────────────────────────┤
│  [Titre]                              [Badge]   │
│  [Sous-titre : Client | Secteur | Durée]        │
│  ═══════════════════════════════════════════════│
│  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ MÉTADONNÉES  │  │ CONTEXTE  │  MISSION     │ │
│  │ (fond gris)  │  ├───────────┴──────────────┤ │
│  │ Client       │  │ LIVRABLES │  RÉSULTATS   │ │
│  │ Secteur      │  │ • item 1  │  • item 1    │ │
│  │ Durée        │  │ • item 2  │  • item 2    │ │
│  │ Équipe       │  │ • item 3  │  • item 3    │ │
│  │ Mots-clés    │  └──────────────────────────┘ │
│  └──────────────┘                               │
├─────────────────────────────────────────────────┤
│  Orange Cyberdefense — Conseil & Audit   [date] │
└─────────────────────────────────────────────────┘
```

---

## 4. Base d'exemples REF (RAG)

### Où déposer les fiches

```
REF-Factory/
  data/
    reference_library/
      ← déposez ici vos fiches REF existantes
```

Formats supportés : `.pptx`, `.pdf`, `.docx`, `.txt`, `.md`, `.json`

### Copier depuis O:\ConseiletAudit (Windows Orange)

```bash
python copy_ref_factory.py
```

Le script copie toutes les fiches REF depuis `O:\ConseiletAudit\Références` vers `data/reference_library/`. Ce script est conçu pour Windows avec accès au réseau Orange.

### Créer des fiches exemples (hors réseau Orange / Linux)

Quand `O:\ConseiletAudit` n'est pas accessible :

```bash
python scripts/seed_reference_library.py
```

Crée 7 fiches REF anonymisées couvrant les principaux domaines OCD :
- Audit gouvernance SSI / DORA (banque)
- SOC managé IT/OT (OIV énergie)
- Tests d'intrusion e-commerce (PCI-DSS)
- PSSI + EBIOS RM (hôpital)
- Cyberdiagnostic PME (TISAX)
- Réponse à incident ransomware (CERT)
- DPO externalisé / RGPD (collectivité)

### Indexer la base

```bash
python scripts/index_reference_library.py
```

Ou depuis l'interface UI : bouton **"Indexer la base REF"**.

---

## 5. Installation

### Prérequis

- Python 3.10+

### Environnement virtuel

```bash
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

---

## 6. Configuration

```bash
cp .env.example .env
```

Puis éditer `.env` :

```env
# LLM (optionnel — le fallback heuristique fonctionne sans)
LLM_PROVIDER=dinootoo
DINOOTOO_API_KEY=...
DINOOTOO_BASE_URL=https://llmproxy.ai.orange
DINOOTOO_MODEL=gpt-4o

# Embeddings locaux (recommandé — évite les appels API pour l'indexation)
USE_LOCAL_EMBEDDINGS=true
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Dossier fiches REF
REF_LIBRARY_DIR=data/reference_library
```

Si `REF-Factory/.env` est absent, le projet tente de charger `../Pres-Factory/.env` automatiquement.

> **Embeddings locaux** : avec `USE_LOCAL_EMBEDDINGS=true`, le modèle `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` est téléchargé une seule fois depuis HuggingFace (~120 Mo). L'indexation et la recherche ne consomment plus de budget API.

---

## 7. Lancer l'interface graphique

```bash
python ui/app.py
```

Disponible sur `http://localhost:7861`

### Utilisation

1. Remplir les champs (titre, client, secteur, durée, équipe, mots-clés, confidentialité)
2. Coller le brief consultant dans la zone de texte
3. Joindre des pièces jointes (PDF, DOCX, PPTX, TXT, MD, JSON)
4. Cliquer sur **"Indexer la base REF"** si de nouvelles fiches ont été ajoutées
5. Cliquer sur **"Générer la fiche REF"**
6. Récupérer :
   - Le rapport qualité (score sur 100)
   - Les exemples similaires utilisés
   - Le JSON structuré généré
   - Le fichier **`.pptx` une slide** à télécharger

---

## 8. Script d'indexation CLI

```bash
python scripts/index_reference_library.py
```

---

## 9. Tests

```bash
python -m pytest tests/ -v
```

### Couverture des tests (19 tests)

| Fichier | Tests |
|---|---|
| `test_charter.py` | Conformité couleurs OCD (source XML brand box), dimensions slide, font, rendu |
| `test_rendering.py` | Génération PPTX une slide, dimensions, contenu titre, badge confidentialité |
| `test_quality.py` | Score qualité, champs manquants, impact RAG, densité texte, structure rapport |

Vérification de la syntaxe complète :

```bash
python -m compileall src ui scripts tests
```

---

## 10. Structure du projet

```
REF-Factory/
├── .env                          # Configuration locale (non versionné)
├── .env.example                  # Template de configuration
├── .gitignore
├── README.md
├── requirements.txt
├── Cadrage_IA REF Factory CU10.pdf
├── analyze_charter.py            # Script d'analyse des templates .potx (Windows)
├── copy_ref_factory.py           # Copie depuis O:\ConseiletAudit (Windows)
├── data/
│   ├── reference_library/        # ← Déposer les fiches REF ici
│   ├── output/                   # Fichiers PPTX générés
│   ├── uploads/                  # Pièces jointes temporaires
│   └── chroma_db/                # Index vectoriel (local, auto-généré)
├── scripts/
│   ├── index_reference_library.py
│   └── seed_reference_library.py # Fiches exemples quand O: inaccessible
├── tests/
│   ├── conftest.py
│   ├── test_charter.py           # Tests conformité charte OCD
│   ├── test_rendering.py         # Tests génération PPTX
│   └── test_quality.py           # Tests rapport qualité
├── ui/
│   └── app.py                    # Interface Gradio
├── Tools and templates PPT - FR/ # Brand box OCD (templates, XML couleurs)
│   └── French/
│       ├── 2. Templates/French/  # .potx OFR (interne, externe, confidentiel...)
│       └── 6. XML/               # Orange WHT Core.xml, Orange BLK Core.xml
└── src/
    └── ref_factory/
        ├── __init__.py
        ├── config.py
        ├── document_parser.py
        ├── graph.py
        ├── json_utils.py
        ├── state.py
        ├── charter/
        │   └── ocd_charter.json  # Charte OCD (couleurs, polices, dimensions)
        ├── llm/
        │   └── client.py         # Client LLM (OpenAI-compat / Dinootoo)
        ├── nodes/
        │   ├── collect_inputs.py
        │   ├── retrieve_examples.py
        │   ├── structure_ref.py
        │   ├── render_pptx.py
        │   └── check_quality.py
        ├── presentation/
        │   └── rendering.py      # Rendu PPTX conforme charte OCD
        └── rag/
            └── store.py          # ChromaDB + embeddings locaux ou API
```

---

## 11. Guardrails métier

- Les exemples RAG servent d'inspiration de structure, jamais de source de faits à recopier
- Les champs absents restent `[A_COMPLETER]` (jamais inventés)
- Score qualité dégradé si champs obligatoires incomplets
- Fonctionne sans LLM (fallback heuristique) et sans API d'embeddings (`USE_LOCAL_EMBEDDINGS=true`)

---

## 12. Résumé rapide

| Besoin | Commande |
|---|---|
| Créer les fiches exemples (hors réseau Orange) | `python scripts/seed_reference_library.py` |
| Copier depuis O:\ConseiletAudit (Windows) | `python copy_ref_factory.py` |
| Indexer la base REF | `python scripts/index_reference_library.py` |
| Lancer l'interface | `python ui/app.py` → http://localhost:7861 |
| Lancer les tests | `python -m pytest tests/ -v` |
| Vérifier la syntaxe | `python -m compileall src ui scripts tests` |
