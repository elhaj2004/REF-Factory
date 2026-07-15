"""
Script de copie en masse des fiches REF depuis O:\ConseiletAudit\Références
vers data/reference_library/ pour la base RAG de REF-Factory.
"""
import sys, os, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
os.chdir(Path(__file__).resolve().parent)

SOURCE = Path(r"O:\ConseiletAudit\Références")
DEST = Path(r"data\reference_library")
DEST.mkdir(parents=True, exist_ok=True)

SUPPORTED = {".pptx", ".ppt", ".potx", ".txt", ".md", ".pdf"}

copied = 0
skipped = 0
errors = []

print("=== COPIE DES FICHES REF ===")
print(f"Source : {SOURCE}")
print(f"Destination : {DEST}")
print()

for file_path in SOURCE.rglob("*"):
    if not file_path.is_file():
        continue
    if file_path.suffix.lower() not in SUPPORTED:
        continue
    # Ignorer les fichiers temporaires
    if file_path.name.startswith("~$"):
        continue
    if file_path.name == "Thumbs.db":
        continue
    
    # Nom relatif pour éviter les collisions (remplacer \ par _)
    rel_name = file_path.relative_to(SOURCE).as_posix().replace("/", "_").replace(" ", "_")
    
    # Tronquer si trop long
    if len(rel_name) > 200:
        stem = rel_name[:80]
        ext = file_path.suffix
        # Prendre les derniers chunks aussi
        rel_name = f"{stem}...{Path(rel_name).stem[-60:]}{ext}"
    
    dest_path = DEST / rel_name
    
    try:
        shutil.copy2(file_path, dest_path)
        copied += 1
        if copied % 50 == 0:
            print(f"   {copied} fichiers copiés...")
    except Exception as e:
        errors.append(f"{rel_name}: {e}")
        skipped += 1

print(f"\nTerminé : {copied} copiés, {skipped} ignorés, {len(errors)} erreurs")

if errors:
    print("\nErreurs :")
    for err in errors[:10]:
        print(f"  - {err}")
    if len(errors) > 10:
        print(f"  ... et {len(errors)-10} autres")

# Vérifier le nombre final
final_count = sum(1 for _ in DEST.rglob("*") if _.is_file() and _.suffix.lower() in SUPPORTED)
print(f"\nFichiers dans reference_library : {final_count}")
