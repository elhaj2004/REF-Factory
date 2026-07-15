from ref_factory.nodes.check_quality import evaluate_slide_payload


def test_quality_report_flags_missing_fields() -> None:
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
    assert report["examples_used"] == 0
