"""
Rendu PPTX one-slide conforme à la charte Orange Cyberdefense.
Couleurs, polices et dimensions issues de ocd_charter.json.
"""
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Cm, Pt

from ref_factory.config import OUTPUT_DIR

# ── Chargement de la charte ──────────────────────────────────────────────────
_CHARTER_PATH = Path(__file__).resolve().parents[1] / "charter" / "ocd_charter.json"

def _load_charter() -> dict:
    if _CHARTER_PATH.exists():
        return json.loads(_CHARTER_PATH.read_text(encoding="utf-8"))
    return {}

_CHARTER = _load_charter()
_COLORS = _CHARTER.get("colors", {})
_FONTS = _CHARTER.get("fonts", {})
_STYLES = _CHARTER.get("pptx", {}).get("styles", {})

PRIMARY_FONT = _FONTS.get("primary", "Source Sans Pro")
FALLBACK = _FONTS.get("fallback", ["Calibri", "Arial"])[0]

def _font(name_override: str | None = None) -> str:
    return name_override or PRIMARY_FONT

def _rgb(hex_color: str) -> RGBColor:
    hex_color = hex_color.lstrip("#")
    return RGBColor(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))

# Couleurs OCD
ORANGE = _rgb(_COLORS.get("primary_orange", "#FF6600"))
BLACK = _rgb(_COLORS.get("black", "#000000"))
DARK_GREY = _rgb(_COLORS.get("dark_grey", "#333333"))
MEDIUM_GREY = _rgb(_COLORS.get("medium_grey", "#666666"))
LIGHT_GREY = _rgb(_COLORS.get("light_grey", "#F2F2F2"))
WHITE = _rgb(_COLORS.get("white", "#FFFFFF"))
ACCENT_BG = _rgb(_COLORS.get("table_accent", "#FFF3E0"))

# Dimensions OCD exactes (33.87 x 19.05 cm)
SLIDE_W = Cm(33.87)
SLIDE_H = Cm(19.05)

# ── Rendu principal ──────────────────────────────────────────────────────────

def render_ref_slide(payload: dict[str, Any]) -> str:
    """Génère une slide REF conforme à la charte OCD."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # 1. Bandeau orange supérieur
    _add_bandeau(slide)

    # 2. Logo OCD (texte simulé faute de logo embeddé)
    _add_logo_text(slide)

    # 3. Badge confidentialité
    _add_badge(slide, payload.get("confidentiality", "Interne"))

    # 4. Titre et sous-titre
    _add_title_block(slide, payload)

    # 5. Panneau métadonnées (gauche)
    _add_metadata_panel(slide, payload)

    # 6. Sections principales (droite)
    _add_content_sections(slide, payload)

    # 7. Footer
    _add_footer(slide, payload)

    output_path = _build_output_path(payload.get("title"))
    prs.save(output_path)
    return str(output_path)


# ── Composants visuels ───────────────────────────────────────────────────────

def _add_bandeau(slide) -> None:
    """Bandeau orange fin en haut de slide (signature OCD)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Cm(0), Cm(0), SLIDE_W, Cm(0.15)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = ORANGE
    shape.line.fill.background()


def _add_logo_text(slide) -> None:
    """Texte 'Orange Cyberdefense' en haut à gauche."""
    txBox = slide.shapes.add_textbox(Cm(1.0), Cm(0.35), Cm(8), Cm(0.9))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Orange Cyberdefense"
    p.font.name = _font()
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLACK

    # Ligne orange sous le logo
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Cm(1.0), Cm(1.1), Cm(3.5), Cm(0.04)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = ORANGE
    line.line.fill.background()


def _add_badge(slide, confidentiality: str) -> None:
    """Badge de confidentialité en haut à droite."""
    badge_w = Cm(3.2)
    badge_h = Cm(0.7)
    x = SLIDE_W - badge_w - Cm(1.0)
    y = Cm(0.4)

    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, badge_w, badge_h
    )
    is_conf = confidentiality.lower().startswith("conf")
    shape.fill.solid()
    shape.fill.fore_color.rgb = BLACK if is_conf else ORANGE
    shape.line.fill.background()

    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = confidentiality
    p.font.name = _font()
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = WHITE


def _add_title_block(slide, payload: dict[str, Any]) -> None:
    """Titre principal + sous-titre client/secteur/durée."""
    title = _coerce(payload.get("title"), "Fiche Référence")

    # Titre
    txBox = slide.shapes.add_textbox(Cm(1.0), Cm(1.5), Cm(26), Cm(1.4))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    style = _STYLES.get("title", {})
    p.font.name = _font(style.get("font_name"))
    p.font.size = Pt(style.get("font_size", 28))
    p.font.bold = style.get("bold", True)
    p.font.color.rgb = _rgb(style.get("color", "#FF6600"))

    # Sous-titre
    subtitle_parts = [
        _coerce(payload.get("client"), "[Client à compléter]"),
        _coerce(payload.get("sector"), "[Secteur à compléter]"),
        _coerce(payload.get("duration"), "[Durée à compléter]"),
    ]
    subtitle = "  |  ".join(subtitle_parts)

    txBox2 = slide.shapes.add_textbox(Cm(1.0), Cm(2.85), Cm(26), Cm(0.7))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = subtitle
    style_sub = _STYLES.get("subtitle", {})
    p2.font.name = _font(style_sub.get("font_name"))
    p2.font.size = Pt(style_sub.get("font_size", 16))
    p2.font.bold = style_sub.get("bold", False)
    p2.font.color.rgb = _rgb(style_sub.get("color", "#333333"))


def _add_metadata_panel(slide, payload: dict[str, Any]) -> None:
    """Panneau latéral gauche avec infos clés (fond gris clair)."""
    panel_x = Cm(1.0)
    panel_y = Cm(3.8)
    panel_w = Cm(8.5)
    panel_h = Cm(13.8)

    # Fond du panneau
    bg = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, panel_x, panel_y, panel_w, panel_h
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = LIGHT_GREY
    bg.line.fill.background()

    # Contenu texte
    txBox = slide.shapes.add_textbox(
        Cm(1.5), Cm(4.2), Cm(7.5), Cm(13.0)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.clear()

    rows = [
        ("CLIENT", _coerce(payload.get("client"), "[À COMPLÉTER]")),
        ("SECTEUR", _coerce(payload.get("sector"), "[À COMPLÉTER]")),
        ("DURÉE", _coerce(payload.get("duration"), "[À COMPLÉTER]")),
        ("ÉQUIPE", _coerce(payload.get("team"), "[À COMPLÉTER]")),
        ("MOTS-CLÉS", ", ".join(payload.get("keywords") or ["[À COMPLÉTER]"])),
    ]

    label_style = _STYLES.get("metadata_label", {})
    value_style = _STYLES.get("metadata_value", {})

    for idx, (label, value) in enumerate(rows):
        if idx > 0:
            spacer = tf.add_paragraph()
            spacer.text = ""
            spacer.space_after = Pt(3)

        # Label
        p_label = tf.add_paragraph()
        p_label.text = label
        p_label.font.name = _font(label_style.get("font_name"))
        p_label.font.size = Pt(label_style.get("font_size", 9))
        p_label.font.bold = True
        p_label.font.color.rgb = _rgb(label_style.get("color", "#FF6600"))
        p_label.space_after = Pt(2)

        # Value
        p_value = tf.add_paragraph()
        p_value.text = value
        p_value.font.name = _font(value_style.get("font_name"))
        p_value.font.size = Pt(value_style.get("font_size", 13))
        p_value.font.bold = False
        p_value.font.color.rgb = _rgb(value_style.get("color", "#000000"))
        p_value.space_after = Pt(14)


def _add_content_sections(slide, payload: dict[str, Any]) -> None:
    """Sections principales à droite du panneau."""
    x_start = Cm(10.5)
    w = Cm(22)

    sections = [
        ("CONTEXTE", payload.get("context", "[À COMPLÉTER]"), Cm(3.8), Cm(3.9)),
        ("MISSION", payload.get("mission", "[À COMPLÉTER]"), Cm(7.8), Cm(3.9)),
    ]

    heading_style = _STYLES.get("heading", {})
    body_style = _STYLES.get("body", {})

    for title, body, y, h in sections:
        # Titre de section
        txTitle = slide.shapes.add_textbox(x_start, y, w, Cm(0.8))
        p = txTitle.text_frame.paragraphs[0]
        p.text = title
        p.font.name = _font(heading_style.get("font_name"))
        p.font.size = Pt(heading_style.get("font_size", 18))
        p.font.bold = True
        p.font.color.rgb = _rgb(heading_style.get("color", "#FF6600"))

        # Contenu
        txBody = slide.shapes.add_textbox(x_start, y + Cm(0.9), w, h - Cm(0.9))
        tf = txBody.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = _coerce(body, "[À COMPLÉTER]")
        p.font.name = _font(body_style.get("font_name"))
        p.font.size = Pt(body_style.get("font_size", 14))
        p.font.bold = False
        p.font.color.rgb = _rgb(body_style.get("color", "#000000"))

    # Livrables & Résultats (deux colonnes)
    col_y = Cm(12.5)
    col_w = Cm(10.2)
    _add_bullet_section(slide, "LIVRABLES", payload.get("deliverables") or ["[À COMPLÉTER]"],
                        x_start, col_y, col_w, Cm(4.5))
    _add_bullet_section(slide, "RÉSULTATS / VALEUR", payload.get("results") or ["[À COMPLÉTER]"],
                        x_start + col_w + Cm(0.8), col_y, col_w, Cm(4.5))


def _add_bullet_section(slide, title: str, items: list[str],
                        x, y, w, h) -> None:
    """Bloc avec bullet points."""
    heading_style = _STYLES.get("heading", {})
    bullet_style = _STYLES.get("bullet", {})

    # Titre
    txTitle = slide.shapes.add_textbox(x, y, w, Cm(0.7))
    p = txTitle.text_frame.paragraphs[0]
    p.text = title
    p.font.name = _font(heading_style.get("font_name"))
    p.font.size = Pt(heading_style.get("font_size", 18))
    p.font.bold = True
    p.font.color.rgb = _rgb(heading_style.get("color", "#FF6600"))

    # Bullets
    txBody = slide.shapes.add_textbox(x, y + Cm(0.8), w, h - Cm(0.8))
    tf = txBody.text_frame
    tf.word_wrap = True
    tf.clear()

    items = items[:3] if items else ["[À COMPLÉTER]"]
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = _coerce(item, "[À COMPLÉTER]")
        p.level = 0
        p.font.name = _font(bullet_style.get("font_name"))
        p.font.size = Pt(bullet_style.get("font_size", 14))
        p.font.bold = False
        p.font.color.rgb = _rgb(bullet_style.get("color", "#000000"))
        p.space_after = Pt(6)

        # Ajouter un vrai bullet character
        p.text = f"• {p.text}"


def _add_footer(slide, payload: dict[str, Any]) -> None:
    """Footer discret avec copyright et références utilisées."""
    footer_y = SLIDE_H - Cm(1.2)

    # Ligne de séparation fine
    sep = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Cm(1.0), footer_y - Cm(0.15), Cm(32), Cm(0.02)
    )
    sep.fill.solid()
    sep.fill.fore_color.rgb = LIGHT_GREY
    sep.line.fill.background()

    refs = payload.get("reference_examples_used") or []
    refs_text = f"Fiches similaires : {', '.join(refs[:3])}" if refs else "Aucune fiche similaire trouvée"

    footer_text = f"Orange Cyberdefense — REF-Factory | {refs_text} | Généré le {datetime.now().strftime('%d/%m/%Y')}"

    txBox = slide.shapes.add_textbox(Cm(1.0), footer_y, Cm(32), Cm(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = footer_text
    p.alignment = PP_ALIGN.LEFT
    footer_style = _STYLES.get("footer", {})
    p.font.name = _font(footer_style.get("font_name"))
    p.font.size = Pt(footer_style.get("font_size", 8))
    p.font.color.rgb = _rgb(footer_style.get("color", "#666666"))


# ── Utilitaires ──────────────────────────────────────────────────────────────

def _build_output_path(title: str | None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base = _slugify(title or "fiche-ref")
    return OUTPUT_DIR / f"{base}_{timestamp}.pptx"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_val = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_val = re.sub(r"[^A-Za-z0-9]+", "-", ascii_val).strip("-")
    return ascii_val[:80] or "fiche-ref"


def _coerce(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default
