from typing import Any

from ref_factory.state import RefFactoryState

MANDATORY_FIELDS = ["title", "client", "sector", "context", "mission", "deliverables", "results"]


def evaluate_slide_payload(payload: dict[str, Any], examples: list[dict[str, Any]]) -> dict[str, Any]:
    missing_fields = [field_name for field_name in MANDATORY_FIELDS if _is_missing(payload.get(field_name))]

    completeness = round(100 * (len(MANDATORY_FIELDS) - len(missing_fields)) / len(MANDATORY_FIELDS), 2)

    density_checks = [
        len(payload.get("context", "")) <= 320,
        len(payload.get("mission", "")) <= 320,
        len(payload.get("deliverables") or []) <= 3,
        len(payload.get("results") or []) <= 3,
        all(len(item) <= 95 for item in (payload.get("deliverables") or [])),
        all(len(item) <= 95 for item in (payload.get("results") or [])),
    ]
    density = round(100 * sum(1 for item in density_checks if item) / len(density_checks), 2)

    examples_used = len(examples or [])
    grounding = 100.0 if examples_used >= 3 else 75.0 if examples_used == 2 else 55.0 if examples_used == 1 else 30.0

    score = round(completeness * 0.6 + density * 0.25 + grounding * 0.15, 2)

    issues: list[str] = []
    recommendations: list[str] = []

    if missing_fields:
        issues.append("Certains champs obligatoires restent a completer avant diffusion.")
        recommendations.append("Completer les champs marques [A_COMPLETER] dans le brief ou corriger le JSON genere.")
    if examples_used == 0:
        issues.append("Aucune fiche REF d'exemple n'a ete retrouvee dans la base locale.")
        recommendations.append("Deposer des fiches REF terminees dans data/reference_library/ puis reindexer la base.")
    if density < 100:
        issues.append("La densite de texte de la slide peut encore etre optimisee.")
        recommendations.append("Raccourcir certains textes si le rendu visuel parait trop dense.")

    if not issues:
        issues.append("La fiche REF est exploitable et suffisamment complete pour une relecture metier.")
    if not recommendations:
        recommendations.append("Faire une validation humaine rapide avant usage externe.")

    return {
        "score": score,
        "compliant": score >= 75 and not missing_fields,
        "breakdown": {
            "completeness": completeness,
            "density": density,
            "grounding": grounding,
        },
        "missing_fields": missing_fields,
        "examples_used": examples_used,
        "issues": issues,
        "recommendations": recommendations,
    }


def check_quality(state: RefFactoryState) -> dict:
    report = evaluate_slide_payload(
        payload=state.get("slide_payload") or {},
        examples=state.get("retrieved_examples") or [],
    )
    return {
        "quality_score": float(report.get("score", 0)),
        "quality_report": report,
    }


def _is_missing(value: Any) -> bool:
    if isinstance(value, list):
        return not value or all(_is_missing(item) for item in value)
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    return not cleaned or cleaned == "[A_COMPLETER]"
