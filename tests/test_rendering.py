from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor

from ref_factory.presentation.rendering import render_ref_slide


_PAYLOAD_COMPLET = {
    "title": "Audit de gouvernance SSI - Banque régionale",
    "client": "Banque X (anonymisé)",
    "sector": "Banque / Finance",
    "duration": "8 semaines",
    "team": "1 manager, 2 consultants",
    "keywords": ["audit", "gouvernance", "DORA", "ISO 27001"],
    "confidentiality": "Confidentiel",
    "context": "Évaluation de maturité SSI dans le cadre de la conformité DORA. Entité sans politique SSI formalisée.",
    "mission": "Audit de gouvernance SSI couvrant les 5 domaines DORA. Remise d'un rapport et d'une roadmap sur 18 mois.",
    "deliverables": ["Rapport audit gouvernance SSI", "Cartographie des écarts DORA", "Roadmap conformité 18 mois"],
    "results": ["Maturité 2.1/5 avant intervention", "32 recommandations priorisées", "Validation AMF du plan"],
    "notes": "Mission pilote dans le cadre du programme OCD Banque.",
    "reference_examples_used": ["REF_Banque_DORA.pptx", "REF_Audit_ISO27001.pptx"],
}

_PAYLOAD_MINIMAL = {
    "title": "Fiche REF minimale",
    "confidentiality": "Interne",
    "context": "Contexte test.",
    "mission": "Mission test.",
}


def test_render_creates_single_slide(tmp_path: Path) -> None:
    output_path = Path(render_ref_slide(_PAYLOAD_COMPLET))
    assert output_path.exists(), "Le fichier PPTX n'a pas été créé"
    prs = Presentation(str(output_path))
    assert len(prs.slides) == 1, "La présentation doit contenir exactement 1 slide"
    assert output_path.suffix.lower() == ".pptx"


def test_render_minimal_payload_does_not_crash() -> None:
    output_path = Path(render_ref_slide(_PAYLOAD_MINIMAL))
    assert output_path.exists()
    prs = Presentation(str(output_path))
    assert len(prs.slides) == 1


def test_slide_dimensions_ocd_16_9() -> None:
    """Vérifie les dimensions 33.87 × 19.05 cm imposées par la charte OCD."""
    from pptx.util import Cm
    output_path = Path(render_ref_slide(_PAYLOAD_COMPLET))
    prs = Presentation(str(output_path))
    assert abs(prs.slide_width - Cm(33.87)) < 1000, "Largeur slide incorrecte"
    assert abs(prs.slide_height - Cm(19.05)) < 1000, "Hauteur slide incorrecte"


def test_slide_contains_title_text() -> None:
    """Le texte du titre doit apparaître quelque part dans la slide."""
    output_path = Path(render_ref_slide(_PAYLOAD_COMPLET))
    prs = Presentation(str(output_path))
    slide = prs.slides[0]
    all_text = " ".join(
        shape.text for shape in slide.shapes if hasattr(shape, "text")
    )
    assert "Audit de gouvernance SSI" in all_text


def test_slide_contains_confidentiality_badge() -> None:
    """Le texte de confidentialité doit être présent."""
    output_path = Path(render_ref_slide(_PAYLOAD_COMPLET))
    prs = Presentation(str(output_path))
    slide = prs.slides[0]
    all_text = " ".join(
        shape.text for shape in slide.shapes if hasattr(shape, "text")
    ).upper()
    assert "CONFIDENTIEL" in all_text
