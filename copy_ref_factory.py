"""
Script de copie en masse des fiches REF depuis O:\\ConseiletAudit
vers data/reference_library/ pour la base RAG de REF-Factory.

Parcourt tout l'arbre O:\\ConseiletAudit (pas seulement un sous-dossier
"Références") et ne copie QUE les fichiers dont le nom contient
explicitement "REF" ou "Reference" (filtre strict sur le nom, insensible
aux accents/majuscules). Les fichiers déjà copiés lors d'une exécution
précédente qui ne passent plus le filtre (ou qui ont disparu de la source)
sont supprimés de data/reference_library/.

Usage :
    python copy_ref_factory.py
    python copy_ref_factory.py --apply-legacy-cleanup   # 1re exécution avec
        des fichiers déjà présents dans data/reference_library/ copiés par
        une ancienne version non filtrée du script
"""
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

SOURCE = Path(r"O:\ConseiletAudit")
DEST = Path("data/reference_library")
MANIFEST_PATH = DEST / ".copy_manifest.json"

SUPPORTED = {".pptx", ".ppt", ".potx", ".txt", ".md", ".pdf"}

# Nom de fichier obligatoire : doit contenir "ref" ou "reference" comme
# token (pas comme simple sous-chaine noyee dans un autre mot, ex.
# "Preferences_utilisateur" est rejete). Insensible aux accents/majuscules
# (voir strip_accents). Couvre REF_xxx, Fiche_REF_xxx, REF2024_xxx,
# Reference_xxx, Références_xxx...
NAME_ACCEPT_PATTERN = re.compile(r"(?i)(^|[^a-z])ref(erence)?s?($|[^a-z])")

# Exclusions de securite meme si "ref"/"reference" apparait dans le nom.
NAME_REJECT_PATTERN = re.compile(
    r"(?i)compte[_\-\s]?rendu|\bcr[_\-\s]|planning|proposition|devis|facture"
    r"|contrat|\bpv[_\-\s]|note[_\-\s]interne|formation|gabarit|mod(e|è)le|template"
)


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def is_ref_fiche(file_path: Path) -> tuple[bool, str]:
    """Retourne (accepte, motif) pour un fichier source candidat, sur la base du nom uniquement."""
    name = strip_accents(file_path.stem)

    if NAME_REJECT_PATTERN.search(name):
        return False, "nom exclu (mot-clé non-REF)"

    if NAME_ACCEPT_PATTERN.search(name):
        return True, "nom conforme (REF/Reference)"

    return False, "nom ne contient ni REF ni Reference"


def rel_dest_name(file_path: Path) -> str:
    rel_name = file_path.relative_to(SOURCE).as_posix().replace("/", "_").replace(" ", "_")
    if len(rel_name) > 200:
        stem = rel_name[:80]
        ext = file_path.suffix
        rel_name = f"{stem}...{Path(rel_name).stem[-60:]}{ext}"
    return rel_name


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    apply_legacy_cleanup = "--apply-legacy-cleanup" in sys.argv

    DEST.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    print("=== COPIE DES FICHES REF (filtre strict sur le nom) ===")
    print(f"Source : {SOURCE}")
    print(f"Destination : {DEST}")
    print()

    if not SOURCE.exists():
        print(f"ERREUR : source introuvable ({SOURCE}). "
              "Ce script doit être lancé depuis un poste avec accès au lecteur réseau Orange.")
        return 1

    copied = 0
    rejected = 0
    errors: list[str] = []
    new_manifest: dict = {}

    for file_path in sorted(SOURCE.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED:
            continue
        if file_path.name.startswith("~$") or file_path.name == "Thumbs.db":
            continue

        accepted, reason = is_ref_fiche(file_path)
        if not accepted:
            rejected += 1
            continue

        dest_name = rel_dest_name(file_path)
        dest_path = DEST / dest_name
        try:
            shutil.copy2(file_path, dest_path)
            copied += 1
            new_manifest[dest_name] = {"source": str(file_path), "reason": reason}
            if copied % 50 == 0:
                print(f"   {copied} fichiers copiés...")
        except Exception as e:
            errors.append(f"{dest_name}: {e}")
            rejected += 1

    # Nettoyage : supprime les fichiers copiés lors d'une exécution précédente
    # de CE script qui ne sont plus valides (source disparue ou filtre plus strict).
    removed = []
    for dest_name in list(manifest.keys()):
        if dest_name not in new_manifest:
            stale_path = DEST / dest_name
            if stale_path.exists():
                stale_path.unlink()
                removed.append(dest_name)

    # Réconciliation ponctuelle : fichiers présents dans data/reference_library/
    # copiés par une ancienne version non filtrée du script, jamais tracés dans
    # le manifest. On les liste toujours ; on ne les supprime que si
    # --apply-legacy-cleanup est passé, pour éviter de supprimer par erreur des
    # fiches ajoutées manuellement.
    tracked_names = set(new_manifest.keys()) | set(manifest.keys())
    legacy_candidates = []
    for existing in DEST.iterdir():
        if not existing.is_file():
            continue
        if existing.name == MANIFEST_PATH.name or existing.name == ".gitkeep":
            continue
        if existing.suffix.lower() == ".json":
            continue  # fiches JSON (ex. seed anonymisé) : jamais issues de ce script
        if existing.name in tracked_names:
            continue
        legacy_candidates.append(existing)

    if legacy_candidates:
        print(f"\n{len(legacy_candidates)} fichier(s) non tracés trouvés dans {DEST} "
              "(probablement copiés par une ancienne version non filtrée du script) :")
        for candidate in legacy_candidates:
            print(f"  - {candidate.name}")
        if apply_legacy_cleanup:
            for candidate in legacy_candidates:
                candidate.unlink()
            print(f"-> {len(legacy_candidates)} fichier(s) supprimé(s) (--apply-legacy-cleanup).")
        else:
            print("-> Relancez avec --apply-legacy-cleanup pour les supprimer automatiquement, "
                  "ou vérifiez-les manuellement s'il s'agit de vraies fiches REF mal nommées.")

    save_manifest(new_manifest)

    print(f"\nTerminé : {copied} copiés, {rejected} ignorés (non conformes), "
          f"{len(removed)} supprimés (obsolètes), {len(errors)} erreurs")

    if removed:
        print("\nFichiers supprimés (ne passent plus le filtre REF ou disparus de la source) :")
        for name in removed[:20]:
            print(f"  - {name}")
        if len(removed) > 20:
            print(f"  ... et {len(removed) - 20} autres")

    if errors:
        print("\nErreurs :")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... et {len(errors) - 10} autres")

    final_count = sum(
        1 for p in DEST.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED and p.name != MANIFEST_PATH.name
    )
    print(f"\nFichiers REF dans reference_library : {final_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
