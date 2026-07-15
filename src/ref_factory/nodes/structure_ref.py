import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ref_factory.document_parser import summarize_text
from ref_factory.json_utils import extract_json_object
from ref_factory.llm.client import get_llm, llm_available
from ref_factory.state import RefFactoryState

_SYSTEM_PROMPT = """Tu es REF-Factory.

Tu transformes des sources consultant en contenu de fiche REF PowerPoint mono-slide.

Regles obligatoires :
- Utilise uniquement les informations presentes dans les sources utilisateur.
- Les exemples retrouves servent uniquement d'inspiration de structure et de ton.
- N'invente jamais de faits, noms, chiffres, livrables ou resultats.
- Toute information absente doit etre ecrite exactement [A_COMPLETER].
- Le resultat doit rester concis et directement exploitable sur une seule slide.
- Reponds uniquement avec un objet JSON valide.

Schema JSON attendu :
{
  "title": "str",
  "client": "str",
  "sector": "str",
  "duration": "str",
  "team": "str",
  "keywords": ["str"],
  "confidentiality": "Interne|Externe|Confidentiel",
  "context": "max 320 caracteres",
  "mission": "max 320 caracteres",
  "deliverables": ["max 3 bullets, 95 caracteres max chacun"],
  "results": ["max 3 bullets, 95 caracteres max chacun"],
  "notes": "max 180 caracteres",
  "missing_fields": ["liste des champs a completer"]
}
"""

_MANDATORY_FIELDS = ["title", "client", "sector", "context", "mission", "deliverables", "results"]


def structure_ref(state: RefFactoryState) -> dict:
    structured_ref = _fallback_structured_ref(state)

    if llm_available():
        try:
            llm = get_llm()
            messages = [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        "CHAMPS SAISIS:\n"
                        f"{state.get('manual_fields') or {}}\n\n"
                        "EXEMPLES RECUPERES:\n"
                        f"{state.get('retrieved_examples') or []}\n\n"
                        "SOURCES UTILISATEUR:\n"
                        f"{state.get('combined_source_text') or ''}\n\n"
                        "Genere maintenant le JSON final."
                    )
                ),
            ]
            response = llm.invoke(messages)
            candidate = _normalize_structured_ref(
                extract_json_object(getattr(response, "content", "")),
                state,
            )
            if candidate:
                structured_ref = candidate
        except Exception:
            structured_ref = _fallback_structured_ref(state)

    slide_payload = {
        **structured_ref,
        "reference_examples_used": [
            example.get("filename", "document") for example in (state.get("retrieved_examples") or [])
        ],
    }
    return {
        "structured_ref": structured_ref,
        "slide_payload": slide_payload,
    }


def _normalize_structured_ref(candidate: dict[str, Any], state: RefFactoryState) -> dict[str, Any]:
    manual_fields = state.get("manual_fields") or {}
    normalized = {
        "title": _clean_string(candidate.get("title")) or _clean_string(manual_fields.get("title")) or "Fiche REF",
        "client": _clean_string(candidate.get("client")) or _clean_string(manual_fields.get("client")) or "[A_COMPLETER]",
        "sector": _clean_string(candidate.get("sector")) or _clean_string(manual_fields.get("sector")) or "[A_COMPLETER]",
        "duration": _clean_string(candidate.get("duration")) or _clean_string(manual_fields.get("duration")) or "[A_COMPLETER]",
        "team": _clean_string(candidate.get("team")) or _clean_string(manual_fields.get("team")) or "[A_COMPLETER]",
        "keywords": _normalize_list(candidate.get("keywords"), fallback=_split_keywords(manual_fields.get("keywords", ""))),
        "confidentiality": _normalize_confidentiality(candidate.get("confidentiality") or manual_fields.get("confidentiality")),
        "context": _truncate(_clean_string(candidate.get("context")) or "[A_COMPLETER]", 320),
        "mission": _truncate(_clean_string(candidate.get("mission")) or "[A_COMPLETER]", 320),
        "deliverables": _normalize_list(candidate.get("deliverables"), fallback=["[A_COMPLETER]"], item_limit=3, char_limit=95),
        "results": _normalize_list(candidate.get("results"), fallback=["[A_COMPLETER]"], item_limit=3, char_limit=95),
        "notes": _truncate(_clean_string(candidate.get("notes")) or "", 180),
        "missing_fields": [],
    }
    normalized["missing_fields"] = _compute_missing_fields(normalized)
    return normalized


def _fallback_structured_ref(state: RefFactoryState) -> dict[str, Any]:
    manual_fields = state.get("manual_fields") or {}
    source_text = state.get("combined_source_text") or ""
    sentences = _split_sentences(source_text)
    bullets = _candidate_bullets(source_text)

    candidate = {
        "title": manual_fields.get("title") or _derive_title(manual_fields, sentences),
        "client": manual_fields.get("client") or "[A_COMPLETER]",
        "sector": manual_fields.get("sector") or "[A_COMPLETER]",
        "duration": manual_fields.get("duration") or "[A_COMPLETER]",
        "team": manual_fields.get("team") or "[A_COMPLETER]",
        "keywords": _split_keywords(manual_fields.get("keywords", "")),
        "confidentiality": manual_fields.get("confidentiality", "Interne"),
        "context": summarize_text(" ".join(sentences[:2]) or source_text, max_chars=320) or "[A_COMPLETER]",
        "mission": summarize_text(" ".join(sentences[2:4]) or source_text, max_chars=320) or "[A_COMPLETER]",
        "deliverables": bullets[:3] or ["[A_COMPLETER]"],
        "results": bullets[3:6] or ["[A_COMPLETER]"],
        "notes": summarize_text(source_text, max_chars=180) if source_text else "",
    }
    return _normalize_structured_ref(candidate, state)


def _derive_title(manual_fields: dict[str, str], sentences: list[str]) -> str:
    if manual_fields.get("client"):
        return f"Reference - {manual_fields['client']}"
    if sentences:
        return summarize_text(sentences[0], max_chars=80)
    return "Fiche REF"


def _compute_missing_fields(structured_ref: dict[str, Any]) -> list[str]:
    missing_fields: list[str] = []
    for field_name in _MANDATORY_FIELDS:
        value = structured_ref.get(field_name)
        if _is_missing(value):
            missing_fields.append(field_name)
    return missing_fields


def _candidate_bullets(text: str) -> list[str]:
    lines = []
    for raw_line in re.split(r"[\r\n]+", text or ""):
        cleaned = re.sub(r"^[\-•*\d.\)\s]+", "", raw_line).strip()
        if len(cleaned) >= 10:
            lines.append(_truncate(cleaned, 95))
    if lines:
        return lines
    return [_truncate(sentence, 95) for sentence in _split_sentences(text) if len(sentence) >= 10]


def _split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if not compact:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]


def _split_keywords(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,;]", value) if item.strip()]


def _normalize_list(
    value: Any,
    fallback: list[str] | None = None,
    item_limit: int = 5,
    char_limit: int = 95,
) -> list[str]:
    items: list[str] = []
    if isinstance(value, list):
        for item in value:
            cleaned = _clean_string(item)
            if cleaned:
                items.append(_truncate(cleaned, char_limit))
    elif isinstance(value, str) and value.strip():
        items = [_truncate(value.strip(), char_limit)]

    items = items[:item_limit]
    if items:
        return items
    return fallback or []


def _normalize_confidentiality(value: Any) -> str:
    cleaned = _clean_string(value) or "Interne"
    normalized = cleaned.lower()
    if normalized.startswith("conf"):
        return "Confidentiel"
    if normalized.startswith("ext"):
        return "Externe"
    return "Interne"


def _clean_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _truncate(value: str, max_chars: int) -> str:
    cleaned = _clean_string(value)
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[: max_chars - 3].rstrip()}..."


def _is_missing(value: Any) -> bool:
    if isinstance(value, list):
        return not value or all(_is_missing(item) for item in value)
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    return not cleaned or cleaned == "[A_COMPLETER]"
