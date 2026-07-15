# REF-Factory

REF-Factory est un projet Python inspire de `Pres-Factory` pour generer automatiquement une fiche REF Orange Cyberdefense au format PowerPoint, avec une sortie finale volontairement contrainte a **une seule slide**.

Le projet implemente :

- une interface graphique Gradio
- un pipeline LangGraph
- un RAG local sur des fiches REF existantes
- une generation de contenu via LLM avec garde-fous anti-invention
- un rendu PPTX one-slide avec une grille stable inspiree des usages observes dans `Pres-Factory`
- un rapport qualite pour verifier la completude avant usage

## 1. Objectif du projet

Le besoin repris du cadrage `Cadrage_IA REF Factory CU10.pdf` est le suivant :

- retrouver des fiches REF similaires deja capitalisees
- aider le consultant a produire une nouvelle fiche REF plus vite
- respecter une structure et un style homogenes
- ne pas inventer les informations manquantes
- sortir un livrable final directement exploitable en PowerPoint

Dans cette implementation, la cible livree est volontairement focalisee sur le cas d'usage "fiche REF" :

- entree : brief consultant + champs saisis + pieces jointes eventuelles
- base d'exemples : fiches REF existantes
- sortie : **un fichier `.pptx` contenant une seule slide**

## 2. Ce qui a ete repris de Pres-Factory

Le projet a ete concu en s'inspirant directement de `C:\Users\BJPS1817\Pres-Factory`.

Elements repris ou adaptes :

- pattern d'orchestration `LangGraph`
- pattern de client LLM OpenAI-compatible / Dinootoo
- pattern de RAG local avec `Chroma`
- pattern d'interface locale `Gradio`
- philosophie Orange/OCD de production de livrables bureautiques

Elements volontairement simplifies par rapport a Pres-Factory :

- pas de transformation d'un document complet multi-slides
- pas de boucle complexe de validation humaine dans le graphe
- pas de remapping de styles a partir d'un deck existant
- rendu PPT genere from scratch pour garantir une slide unique, stable et maintenable

## 3. Reutilisation de la meme cle API que Pres-Factory

Le projet **n'ecrit pas la cle API dans le repo**.

Le chargement de configuration suit cet ordre :

1. `REF-Factory/.env`
2. a defaut, `../Pres-Factory/.env`
3. enfin, les variables d'environnement deja presentes dans la session shell

Cela permet de reutiliser la meme cle que celle deja configuree dans `Pres-Factory`, sans duplication obligatoire.

Variables supportees :

- `LLM_PROVIDER`
- `OPENAI_COMPAT_API_KEY`
- `OPENAI_COMPAT_BASE_URL`
- `OPENAI_COMPAT_MODEL`
- `OPENAI_COMPAT_EMBEDDING_MODEL`
- `DINOOTOO_API_KEY`
- `DINOOTOO_BASE_URL`
- `DINOOTOO_MODEL`
- `DINOOTOO_EMBEDDING_MODEL`
- `USE_LOCAL_EMBEDDINGS`
- `LOCAL_EMBEDDING_MODEL`

## 4. Workflow implemente

Pipeline REF-Factory :

```text
[Brief + champs UI + pieces jointes]
              |
              v
       collect_inputs
              |
              v
      retrieve_examples
              |
              v
       structure_ref
              |
              v
        render_pptx
              |
              v
       check_quality
              |
              v
             END
```

Detail des etapes :

1. `collect_inputs`
   Concatene les champs saisis dans l'interface et le texte extrait des fichiers joints.

2. `retrieve_examples`
   Interroge la base locale de fiches REF deja existantes pour retrouver les exemples les plus proches.

3. `structure_ref`
   Demande au LLM de produire un JSON "slide-ready" pour la fiche REF.
   Regle cle : une information absente doit rester `[A_COMPLETER]`.

4. `render_pptx`
   Genere un fichier `.pptx` avec **une seule slide** selon une grille fixe.

5. `check_quality`
   Calcule un score heuristique de completude, densite et ancrage sur les references.

## 5. Ou mettre les fiches REF deja faites

Les fiches REF existantes qui servent de base d'exemple doivent etre deposees ici :

`data/reference_library/`

Formats supportes dans cette base locale :

- `.pptx`
- `.docx`
- `.pdf`
- `.txt`
- `.md`
- `.json`

Le cas principal attendu est le depot de fiches REF PowerPoint deja produites.

Exemple concret :

```text
REF-Factory/
  data/
    reference_library/
      Fiche_REF_Banque_X.pptx
      Fiche_REF_Industrie_Y.pptx
      Fiche_REF_SOC_Groupe_Z.pptx
```

Une fois ces fichiers poses dans `data/reference_library/`, il faut lancer l'indexation depuis l'interface ou via le script CLI.

## 6. Structure du projet

```text
REF-Factory/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── scripts/
│   └── index_reference_library.py
├── tests/
│   ├── test_quality.py
│   └── test_rendering.py
├── ui/
│   └── app.py
└── src/
    └── ref_factory/
        ├── __init__.py
        ├── config.py
        ├── document_parser.py
        ├── graph.py
        ├── json_utils.py
        ├── state.py
        ├── llm/
        │   ├── __init__.py
        │   └── client.py
        ├── nodes/
        │   ├── __init__.py
        │   ├── check_quality.py
        │   ├── collect_inputs.py
        │   ├── render_pptx.py
        │   ├── retrieve_examples.py
        │   └── structure_ref.py
        ├── presentation/
        │   ├── __init__.py
        │   └── rendering.py
        └── rag/
            ├── __init__.py
            └── store.py
```

## 7. Installation

### Prerequis

- Python 3.10+
- acces au provider OpenAI-compatible deja configure dans `Pres-Factory` ou dans un `.env` local

### Installation des dependances

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 8. Configuration

Copier si besoin :

```bash
copy .env.example .env
```

Exemple minimal :

```env
LLM_PROVIDER=dinootoo
OPENAI_COMPAT_API_KEY=
OPENAI_COMPAT_BASE_URL=https://llmproxy.ai.orange
OPENAI_COMPAT_MODEL=gpt-4o
OPENAI_COMPAT_EMBEDDING_MODEL=text-embedding-3-small

DINOOTOO_API_KEY=
DINOOTOO_BASE_URL=https://llmproxy.ai.orange
DINOOTOO_MODEL=gpt-4o
DINOOTOO_EMBEDDING_MODEL=text-embedding-3-small

USE_LOCAL_EMBEDDINGS=false
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

REF_LIBRARY_DIR=data/reference_library
```

Si `REF-Factory/.env` est absent, l'application tentera automatiquement de reutiliser `../Pres-Factory/.env`.

## 9. Lancer l'interface graphique

```bash
python ui/app.py
```

Interface disponible sur :

`http://localhost:7861`

## 10. Utilisation de l'interface

1. Remplir les champs de contexte.
2. Coller un brief libre dans la zone de texte.
3. Joindre, si besoin, des documents source `.pdf`, `.docx`, `.pptx`, `.txt`, `.md` ou `.json`.
4. Verifier que la base d'exemples est bien peuplee dans `data/reference_library/`.
5. Cliquer sur `Indexer la base REF` si de nouveaux exemples ont ete ajoutes.
6. Cliquer sur `Generer la fiche REF`.
7. Recuperer :
   - le rapport qualite
   - les exemples similaires utilises
   - le JSON structure genere
   - le `.pptx` one-slide final

## 11. Choix de design pour la slide finale

Le rendu final est genere from scratch avec `python-pptx`, mais la direction visuelle est inspiree des assets observes dans `Pres-Factory`.

Choix retenus :

- format 16:9
- slide unique
- bandeau orange fin en tete
- titre fort et badge de confidentialite
- panneau de metadonnees a gauche
- bloc principal de synthese a droite
- sections dediees : contexte, mission, livrables, resultats
- footer avec mots-cles et references utilisees

Pourquoi from scratch :

- garantir une sortie mono-slide stable
- eviter la fragilite des `.potx` et des masters complexes
- garder un rendu maintenable et pilotable par code

## 12. Script d'indexation CLI

Pour reindexer la base REF sans lancer l'UI :

```bash
python scripts/index_reference_library.py
```

## 13. Guardrails metier integres

Les regles suivantes sont appliquees :

- les exemples retrouves servent d'inspiration de structure, pas de source de faits a recopier
- les champs absents restent `[A_COMPLETER]`
- le score final degrade si les champs obligatoires sont incomplets
- l'application fonctionne meme si aucune fiche d'exemple n'est presente, mais le rapport le signale

## 14. Validation technique realisee

Le projet inclut des tests simples pour valider :

- la generation reelle d'un `.pptx` avec une seule slide
- le calcul du rapport qualite

Commandes de verification typiques :

```bash
pytest
python -m compileall src ui scripts tests
```

## 15. Sortie attendue

La sortie finale du projet est un fichier PowerPoint :

- extension : `.pptx`
- nombre de slides : **1**
- contenu : une fiche REF structuree et prete a relire

## 16. Resume tres concret

Si vous voulez simplement savoir ou poser les fiches REF deja creees pour que l'agent s'en serve :

`data/reference_library/`

Si vous voulez lancer l'outil :

```bash
python ui/app.py
```
