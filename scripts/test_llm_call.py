"""
Test : le LLM generatif repond-il, ou est-il toujours bloque (budget) ?

Fait UN vrai appel minimal au LLM configure et affiche le resultat sans
ambiguite. Contrairement a la generation de fiche (qui masque l'echec du LLM
en basculant en silence sur le fallback heuristique), ce script montre
directement si l'appel reussit ou echoue, et pourquoi.

Usage :
    python scripts/test_llm_call.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ref_factory.llm.client import get_llm, llm_available


def main() -> int:
    if not llm_available():
        print("❌ Aucune clé LLM configurée (OPENAI_COMPAT_API_KEY / DINOOTOO_API_KEY).")
        print("   -> Le projet fonctionne quand meme, mais uniquement en fallback heuristique.")
        return 1

    print("Envoi d'un appel de test au LLM…\n")
    try:
        from langchain_core.messages import HumanMessage

        response = get_llm().invoke(
            [HumanMessage(content="Reponds exactement le mot: OK")]
        )
        content = getattr(response, "content", "")
        print("✅ LE LLM REPOND — l'IA generative est operationnelle.")
        print(f"   Reponse recue : {content!r}")
        print("   -> Tes fiches beneficieront de la reformulation intelligente.")
        return 0
    except Exception as exc:
        message = str(exc)
        print("❌ LE LLM NE REPOND PAS — l'IA generative est indisponible.")
        if "budget" in message.lower() or "429" in message:
            print("   Cause : BUDGET DEPASSE sur la clé (probablement kilo2, plafond 40 $).")
            print("   -> Change de clé (pool partage) ou fais relever le plafond.")
        else:
            print(f"   Detail : {message[:300]}")
        print("   -> En attendant, le projet tourne en fallback heuristique (sans reformulation LLM).")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
