from ref_factory.nodes.check_quality import evaluate_slide_payload

_PAYLOAD_COMPLET = {
    "title": "Audit SOC - Groupe industriel",
    "client": "Groupe industriel",
    "sector": "Industrie",
    "context": "Déploiement d'un SOC managé sur périmètre IT/OT.",
    "mission": "Configuration SIEM, 120 règles, runbooks 24/7.",
    "deliverables": ["Architecture SOC IT/OT", "Runbooks incident"],
    "results": ["MTTD < 2h", "Certification NIS2"],
    "duration": "6 mois",
    "team": "3 analystes SOC",
}

_EXAMPLES_3 = [
    {"filename": "A.pptx", "excerpt": "SOC"},
    {"filename": "B.pptx", "excerpt": "SIEM"},
    {"filename": "C.pptx", "excerpt": "OT"},
]


def test_complete_payload_scores_high() -> None:
    report = evaluate_slide_payload(_PAYLOAD_COMPLET, _EXAMPLES_3)
    assert report["score"] >= 80, f"Score attendu >= 80, obtenu {report['score']}"
    assert report["compliant"] is True
    assert report["missing_fields"] == []


def test_missing_fields_flagged() -> None:
    payload = {
        "title": "Fiche REF",
        "client": "[A_COMPLETER]",
        "sector": "Banque",
        "context": "[A_COMPLETER]",
        "mission": "Mission de cadrage.",
        "deliverables": ["Cadrage"],
        "results": ["[A_COMPLETER]"],
    }
    report = evaluate_slide_payload(payload, examples=[])
    assert report["score"] < 80
    assert "client" in report["missing_fields"]
    assert "context" in report["missing_fields"]
    assert "results" in report["missing_fields"]
    assert report["examples_used"] == 0


def test_no_examples_degrades_score() -> None:
    """Sans exemples RAG, le score doit être plus faible qu'avec 3 exemples."""
    report_0 = evaluate_slide_payload(_PAYLOAD_COMPLET, [])
    report_3 = evaluate_slide_payload(_PAYLOAD_COMPLET, _EXAMPLES_3)
    assert report_3["score"] > report_0["score"]


def test_density_check_too_long_text() -> None:
    """Des textes trop longs doivent dégrader la densité."""
    payload = dict(_PAYLOAD_COMPLET)
    payload["context"] = "x" * 400   # dépasse 320 chars
    payload["mission"] = "y" * 400
    report = evaluate_slide_payload(payload, _EXAMPLES_3)
    assert report["breakdown"]["density"] < 100


def test_report_structure() -> None:
    """Le rapport doit toujours contenir les clés attendues."""
    report = evaluate_slide_payload(_PAYLOAD_COMPLET, _EXAMPLES_3)
    for key in ("score", "compliant", "breakdown", "missing_fields", "examples_used", "issues", "recommendations"):
        assert key in report, f"Clé manquante dans le rapport : {key}"
    for key in ("completeness", "density", "grounding"):
        assert key in report["breakdown"]
