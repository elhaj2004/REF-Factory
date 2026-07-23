"""
Diagnostic : quelle clé API / URL / modèle l'agent utilise-t-il reellement ?

Affiche la configuration LLM effectivement chargee (clé masquee), et d'ou
elle provient (variable systeme, REF-Factory/.env, ou ../Pres-Factory/.env).
Aide a verifier qu'on utilise bien la clé du pool partage (llmproxy)
et non une clé personnelle plafonnee.

Usage :
    python scripts/diagnose_llm.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def mask(value: str) -> str:
    if not value:
        return "(vide)"
    if len(value) <= 12:
        return value[:2] + "…" + value[-2:]
    return f"{value[:6]}…{value[-4:]} (len={len(value)})"


def source_of(var: str, ref_env: dict, sibling_env: dict) -> str:
    """Determine d'ou vient la valeur finale d'une variable."""
    if var in os.environ and os.environ[var] and var not in ref_env and var not in sibling_env:
        return "variable systeme / shell"
    if var in ref_env:
        return "REF-Factory/.env"
    if var in sibling_env:
        return "../Pres-Factory/.env"
    if var in os.environ:
        return "variable systeme / shell"
    return "non defini"


def read_env_file(path: Path) -> dict:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()
    return values


def main() -> int:
    ref_env_path = ROOT / ".env"
    sibling_env_path = ROOT.parent / "Pres-Factory" / ".env"
    ref_env = read_env_file(ref_env_path)
    sibling_env = read_env_file(sibling_env_path)

    # Snapshot des variables système AVANT chargement des .env.
    pre_env = {
        k: os.environ.get(k)
        for k in (
            "OPENAI_COMPAT_API_KEY", "DINOOTOO_API_KEY",
            "OPENAI_COMPAT_BASE_URL", "DINOOTOO_BASE_URL",
            "OPENAI_COMPAT_MODEL", "DINOOTOO_MODEL",
        )
    }

    print("=== Fichiers .env detectes ===")
    print(f"  REF-Factory/.env       : {'OUI' if ref_env_path.exists() else 'ABSENT'}  ({ref_env_path})")
    print(f"  ../Pres-Factory/.env   : {'OUI' if sibling_env_path.exists() else 'ABSENT'}  ({sibling_env_path})")

    print("\n=== Variables déjà présentes dans le shell AVANT chargement .env ===")
    any_pre = False
    for k, v in pre_env.items():
        if v:
            any_pre = True
            print(f"  {k} = {mask(v)}   <-- ecrase les .env (override=False)")
    if not any_pre:
        print("  (aucune — bon signe : la clé viendra d'un fichier .env)")

    # Chargement réel via la logique de l'application.
    from ref_factory.config import load_environment
    from ref_factory.llm.client import (
        _openai_compatible_api_key,
        _openai_compatible_base_url,
        _chat_model_name,
        _embedding_model_name,
        llm_available,
    )

    load_environment()

    api_key = _openai_compatible_api_key()
    base_url = _openai_compatible_base_url()

    print("\n=== Configuration LLM effective (ce que l'agent utilise) ===")
    print(f"  Clé API      : {mask(api_key)}")
    print(f"     provenance : {source_of('OPENAI_COMPAT_API_KEY', ref_env, sibling_env) if os.getenv('OPENAI_COMPAT_API_KEY') else source_of('DINOOTOO_API_KEY', ref_env, sibling_env)}")
    print(f"     variable   : {'OPENAI_COMPAT_API_KEY' if os.getenv('OPENAI_COMPAT_API_KEY') else 'DINOOTOO_API_KEY'}")
    print(f"  Base URL     : {base_url}")
    print(f"  Modele chat  : {_chat_model_name()}")
    print(f"  Modele embed : {_embedding_model_name()}")
    print(f"  USE_LOCAL_EMBEDDINGS : {os.getenv('USE_LOCAL_EMBEDDINGS', 'false')}")
    print(f"  LLM disponible ? {llm_available()}")

    print("\n=== A verifier ===")
    print("  - La 'Clé API' ci-dessus est-elle bien celle du pool partage (llmproxy),")
    print("    et non 'kilo2' (plafonnee a 40 $) ?")
    print("  - Si la provenance est '../Pres-Factory/.env' ou 'variable systeme',")
    print("    definis la bonne clé directement dans REF-Factory/.env pour la forcer.")
    print("  - USE_LOCAL_EMBEDDINGS doit etre 'true' pour ne pas consommer le budget")
    print("    a l'indexation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
