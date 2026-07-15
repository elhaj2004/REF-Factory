from pathlib import Path

from pptx import Presentation

from ref_factory.presentation.rendering import render_ref_slide


def test_render_ref_slide_creates_single_slide(tmp_path: Path) -> None:
    payload = {
        "title": "Reference - Audit gouvernance cyber",
        "client": "Client Test",
        "sector": "Industrie",
        "duration": "6 semaines",
        "team": "1 manager, 1 consultant",
        "keywords": ["audit", "gouvernance", "ISO 27001"],
        "confidentiality": "Interne",
        "context": "Mission de cadrage cyber sur un environnement industriel multi-sites.",
        "mission": "Structurer la gouvernance et prioriser les chantiers de mise en conformite.",
        "deliverables": ["Diagnostic de maturite", "Feuille de route 12 mois"],
        "results": ["Vision cible partagee", "Plan d'action priorise"],
        "notes": "Test automatique",
        "reference_examples_used": ["Exemple_A.pptx", "Exemple_B.pptx"],
    }

    output_path = Path(render_ref_slide(payload))

    assert output_path.exists()
    presentation = Presentation(str(output_path))
    assert len(presentation.slides) == 1
    assert output_path.suffix.lower() == ".pptx"
