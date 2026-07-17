"""
Tests de conformité à la charte OCD.
Vérifie que les couleurs et paramètres du fichier charter correspondent
aux valeurs officielles extraites des XML de la Brand Box Orange.
"""
import json
from pathlib import Path

CHARTER_PATH = Path(__file__).resolve().parents[1] / "src" / "ref_factory" / "charter" / "ocd_charter.json"

OCD_ORANGE = "FF7900"    # source : Orange WHT Core.xml / Orange BLK Core.xml (accent1 / lt2)
OCD_DARK_GREY = "595959" # source : accent3 / accent6
OCD_MED_GREY = "8F8F8F"  # source : dk2 / accent4
OCD_LIGHT_GREY = "D6D6D6" # source : accent5


def _charter() -> dict:
    return json.loads(CHARTER_PATH.read_text(encoding="utf-8"))


def test_charter_file_exists() -> None:
    assert CHARTER_PATH.exists(), f"Fichier charte manquant : {CHARTER_PATH}"


def test_primary_orange_matches_brand_xml() -> None:
    """La couleur orange principale doit être #FF7900 (brand XML OCD)."""
    charter = _charter()
    orange = charter["colors"]["primary_orange"].lstrip("#").upper()
    assert orange == OCD_ORANGE, (
        f"Orange OCD attendu : #{OCD_ORANGE}, trouvé : #{orange}\n"
        f"Source officielle : Tools and templates PPT - FR/French/6. XML/Orange WHT Core.xml"
    )


def test_dark_grey_matches_brand_xml() -> None:
    charter = _charter()
    dg = charter["colors"]["dark_grey"].lstrip("#").upper()
    assert dg == OCD_DARK_GREY, f"Dark grey OCD attendu : #{OCD_DARK_GREY}, trouvé : #{dg}"


def test_medium_grey_matches_brand_xml() -> None:
    charter = _charter()
    mg = charter["colors"]["medium_grey"].lstrip("#").upper()
    assert mg == OCD_MED_GREY, f"Medium grey OCD attendu : #{OCD_MED_GREY}, trouvé : #{mg}"


def test_light_grey_matches_brand_xml() -> None:
    charter = _charter()
    lg = charter["colors"]["light_grey"].lstrip("#").upper()
    assert lg == OCD_LIGHT_GREY, f"Light grey OCD attendu : #{OCD_LIGHT_GREY}, trouvé : #{lg}"


def test_slide_dimensions_16_9() -> None:
    """Les dimensions de slide doivent être 33.87 × 19.05 cm (16:9 standard OCD)."""
    charter = _charter()
    pptx = charter["pptx"]
    assert pptx["slide_width_cm"] == 33.87
    assert pptx["slide_height_cm"] == 19.05


def test_font_primary_is_source_sans_pro() -> None:
    """La police principale OCD est Source Sans Pro."""
    charter = _charter()
    assert charter["fonts"]["primary"] == "Source Sans Pro"


def test_heading_color_is_orange() -> None:
    """Les titres de section doivent utiliser la couleur orange OCD."""
    charter = _charter()
    heading_color = charter["pptx"]["styles"]["heading"]["color"].lstrip("#").upper()
    assert heading_color == OCD_ORANGE, (
        f"Les titres de section doivent être orange OCD #{OCD_ORANGE}, trouvé #{heading_color}"
    )


def test_rendering_uses_charter_orange() -> None:
    """Le module de rendu doit utiliser la couleur orange de la charte."""
    from ref_factory.presentation.rendering import ORANGE
    from pptx.dml.color import RGBColor
    expected = RGBColor(0xFF, 0x79, 0x00)
    assert ORANGE == expected, f"Couleur orange du rendu : {ORANGE}, attendu : {expected}"
