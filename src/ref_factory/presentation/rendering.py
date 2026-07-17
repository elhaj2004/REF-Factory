"""
Rendu PPTX one-slide conforme à la charte Orange Cyberdefense.
Couleurs et dimensions extraites de :
  - Tools and templates PPT - FR/French/6. XML/Orange WHT Core.xml
  - Tools and templates PPT - FR/French/6. XML/Orange BLK Core.xml
  - Tools and templates PPT - FR/French/2. Templates/French/*.potx
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
_CONF_COLORS = _CHARTER.get("confidentiality_colors", {})

PRIMARY_FONT = _FONTS.get("primary", "Source Sans Pro")


def _font(name_override: str | None = None) -> str:
    return name_override or PRIMARY_FONT


def _rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Palette OCD officielle — source : Orange WHT Core.xml / Orange BLK Core.xml
ORANGE = _rgb(_COLORS.get("primary_orange", "#FF7900"))
BLACK = _rgb(_COLORS.get("black", "#000000"))
DARK_GREY = _rgb(_COLORS.get("dark_grey", "#595959"))
MEDIUM_GREY = _rgb(_COLORS.get("medium_grey", "#8F8F8F"))
LIGHT_GREY = _rgb(_COLORS.get("light_grey", "#D6D6D6"))
VERY_LIGHT_GREY = _rgb(_COLORS.get("very_light_grey", "#F5F5F5"))
WHITE = _rgb(_COLORS.get("white", "#FFFFFF"))

# Dimensions OCD officielles 16:9 (33.87 × 19.05 cm)
SLIDE_W = Cm(33.87)
SLIDE_H = Cm(19.05)

# Constantes de grille
MARGIN = Cm(1.2)
BANDEAU_H = Cm(0.6)           # bandeau orange OCD en haut
HEADER_H = Cm(3.5)            # zone titre+sous-titre
LEFT_PANEL_W = Cm(9.0)        # largeur colonne gauche (métadonnées)
GUTTER = Cm(0.5)              # gouttière entre les deux colonnes
RIGHT_X = MARGIN + LEFT_PANEL_W + GUTTER
RIGHT_W = SLIDE_W - RIGHT_X - MARGIN
CONTENT_TOP = BANDEAU_H + HEADER_H + Cm(0.3)
CONTENT_H = SLIDE_H - CONTENT_TOP - Cm(1.5)   # espace avant footer


# ── Rendu principal ──────────────────────────────────────────────────────────

def render_ref_slide(payload: dict[str, Any]) -> str:
    """Génère une slide REF unique conforme à la charte OCD."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    _add_bandeau(slide)
    _add_header_zone(slide, payload)
    _add_left_panel(slide, payload)
    _add_right_content(slide, payload)
    _add_footer(slide, payload)

    output_path = _build_output_path(payload.get("title"))
    prs.save(output_path)
    return str(output_path)


# ── Bandeau OCD ──────────────────────────────────────────────────────────────

def _add_bandeau(slide) -> None:
    """Bandeau orange plein en haut (signature OCD)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Cm(0), Cm(0), SLIDE_W, BANDEAU_H
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = ORANGE
    shape.line.fill.background()

    # Nom de la marque dans le bandeau
    txBox = slide.shapes.add_textbox(MARGIN, Cm(0.1), Cm(14), Cm(0.4))
    p = txBox.text_frame.paragraphs[0]
    p.text = "Orange Cyberdefense"
    p.font.name = _font()
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = WHITE


# ── Zone titre / sous-titre / badge ──────────────────────────────────────────

def _add_header_zone(slide, payload: dict[str, Any]) -> None:
    """Zone de titre avec badge confidentialité (fond blanc, trait orange bas)."""
    y0 = BANDEAU_H
    title_text = _coerce(payload.get("title"), "Fiche Référence")
    confidentiality = payload.get("confidentiality", "Interne")

    # Titre principal
    txTitle = slide.shapes.add_textbox(MARGIN, y0 + Cm(0.35), SLIDE_W - MARGIN * 2 - Cm(3.8), Cm(1.5))
    tf = txTitle.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    s = _STYLES.get("title", {})
    p.font.name = _font(s.get("font_name"))
    p.font.size = Pt(s.get("font_size", 26))
    p.font.bold = s.get("bold", True)
    p.font.color.rgb = _rgb(s.get("color", "#000000"))

    # Sous-titre : client | secteur | durée
    parts = [
        _coerce(payload.get("client"), ""),
        _coerce(payload.get("sector"), ""),
        _coerce(payload.get("duration"), ""),
    ]
    subtitle_text = "  |  ".join(p for p in parts if p)
    if not subtitle_text:
        subtitle_text = "[Client / Secteur / Durée à compléter]"

    txSub = slide.shapes.add_textbox(MARGIN, y0 + Cm(2.0), SLIDE_W - MARGIN * 2 - Cm(3.8), Cm(0.9))
    tf2 = txSub.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = subtitle_text
    s2 = _STYLES.get("subtitle", {})
    p2.font.name = _font(s2.get("font_name"))
    p2.font.size = Pt(s2.get("font_size", 14))
    p2.font.bold = s2.get("bold", False)
    p2.font.color.rgb = _rgb(s2.get("color", "#595959"))

    # Trait orange sous le titre
    sep = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, MARGIN, y0 + Cm(3.15), SLIDE_W - MARGIN * 2, Cm(0.06)
    )
    sep.fill.solid()
    sep.fill.fore_color.rgb = ORANGE
    sep.line.fill.background()

    # Badge confidentialité
    _add_badge(slide, confidentiality)


def _add_badge(slide, confidentiality: str) -> None:
    badge_w = Cm(3.2)
    badge_h = Cm(0.65)
    x = SLIDE_W - badge_w - MARGIN
    y = BANDEAU_H + Cm(0.5)

    conf_hex = _CONF_COLORS.get(confidentiality, _COLORS.get("dark_grey", "#595959"))
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, badge_w, badge_h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(conf_hex)
    shape.line.fill.background()

    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = confidentiality.upper()
    s = _STYLES.get("badge_text", {})
    p.font.name = _font(s.get("font_name"))
    p.font.size = Pt(s.get("font_size", 9))
    p.font.bold = s.get("bold", True)
    p.font.color.rgb = WHITE


# ── Panneau gauche : métadonnées ─────────────────────────────────────────────

def _add_left_panel(slide, payload: dict[str, Any]) -> None:
    """Colonne gauche sur fond très légèrement grisé — infos structurées."""
    panel_x = MARGIN
    panel_y = CONTENT_TOP
    panel_h = CONTENT_H

    # Fond
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, panel_x, panel_y, LEFT_PANEL_W, panel_h)
    bg.fill.solid()
    bg.fill.fore_color.rgb = VERY_LIGHT_GREY
    bg.line.color.rgb = LIGHT_GREY
    bg.line.width = Pt(0.5)

    rows = [
        ("CLIENT", _coerce(payload.get("client"), "[À COMPLÉTER]")),
        ("SECTEUR", _coerce(payload.get("sector"), "[À COMPLÉTER]")),
        ("DURÉE", _coerce(payload.get("duration"), "[À COMPLÉTER]")),
        ("ÉQUIPE", _coerce(payload.get("team"), "[À COMPLÉTER]")),
        ("MOTS-CLÉS", ", ".join(payload.get("keywords") or ["[À COMPLÉTER]"])),
    ]
    if payload.get("notes"):
        rows.append(("NOTE", _coerce(payload["notes"], "")))

    txBox = slide.shapes.add_textbox(
        panel_x + Cm(0.35), panel_y + Cm(0.4), LEFT_PANEL_W - Cm(0.7), panel_h - Cm(0.5)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.clear()

    label_s = _STYLES.get("metadata_label", {})
    value_s = _STYLES.get("metadata_value", {})

    for idx, (label, value) in enumerate(rows):
        if idx > 0:
            sp = tf.add_paragraph()
            sp.text = ""
            sp.space_after = Pt(2)

        p_lbl = tf.add_paragraph() if idx > 0 or True else tf.paragraphs[0]
        if idx == 0:
            p_lbl = tf.paragraphs[0]
        else:
            p_lbl = tf.add_paragraph()
        p_lbl.text = label
        p_lbl.font.name = _font(label_s.get("font_name"))
        p_lbl.font.size = Pt(label_s.get("font_size", 9))
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = _rgb(label_s.get("color", "#FF7900"))
        p_lbl.space_after = Pt(1)

        p_val = tf.add_paragraph()
        p_val.text = value
        p_val.font.name = _font(value_s.get("font_name"))
        p_val.font.size = Pt(value_s.get("font_size", 10))
        p_val.font.bold = False
        p_val.font.color.rgb = _rgb(value_s.get("color", "#000000"))
        p_val.space_after = Pt(4)


# ── Zone droite : sections de contenu ────────────────────────────────────────

def _add_right_content(slide, payload: dict[str, Any]) -> None:
    """Zone principale à droite — Contexte, Mission, Livrables, Résultats."""
    x = RIGHT_X
    w = RIGHT_W
    y = CONTENT_TOP
    h = CONTENT_H

    half_h = (h - Cm(0.4)) / 2
    col_w = (w - Cm(0.5)) / 2

    # Contexte (haut gauche)
    _add_text_section(slide, "CONTEXTE", _coerce(payload.get("context"), "[À COMPLÉTER]"),
                      x, y, col_w, half_h)

    # Mission (haut droite)
    _add_text_section(slide, "MISSION", _coerce(payload.get("mission"), "[À COMPLÉTER]"),
                      x + col_w + Cm(0.5), y, col_w, half_h)

    # Séparateur horizontal
    sep_y = y + half_h + Cm(0.15)
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, sep_y, w, Cm(0.04))
    sep.fill.solid()
    sep.fill.fore_color.rgb = LIGHT_GREY
    sep.line.fill.background()

    y2 = sep_y + Cm(0.2)
    h2 = SLIDE_H - y2 - Cm(1.5)

    # Livrables (bas gauche)
    _add_bullet_section(slide, "LIVRABLES",
                        payload.get("deliverables") or ["[À COMPLÉTER]"],
                        x, y2, col_w, h2)

    # Résultats (bas droite)
    _add_bullet_section(slide, "RÉSULTATS / VALEUR",
                        payload.get("results") or ["[À COMPLÉTER]"],
                        x + col_w + Cm(0.5), y2, col_w, h2)


def _add_text_section(slide, heading: str, body: str, x, y, w, h) -> None:
    heading_s = _STYLES.get("heading", {})
    body_s = _STYLES.get("body", {})

    txH = slide.shapes.add_textbox(x, y, w, Cm(0.6))
    p = txH.text_frame.paragraphs[0]
    p.text = heading
    p.font.name = _font(heading_s.get("font_name"))
    p.font.size = Pt(heading_s.get("font_size", 11))
    p.font.bold = True
    p.font.color.rgb = _rgb(heading_s.get("color", "#FF7900"))

    txB = slide.shapes.add_textbox(x, y + Cm(0.65), w, h - Cm(0.65))
    tf = txB.text_frame
    tf.word_wrap = True
    p2 = tf.paragraphs[0]
    p2.text = body
    p2.font.name = _font(body_s.get("font_name"))
    p2.font.size = Pt(body_s.get("font_size", 11))
    p2.font.bold = False
    p2.font.color.rgb = _rgb(body_s.get("color", "#000000"))


def _add_bullet_section(slide, heading: str, items: list[str], x, y, w, h) -> None:
    heading_s = _STYLES.get("heading", {})
    bullet_s = _STYLES.get("bullet", {})

    txH = slide.shapes.add_textbox(x, y, w, Cm(0.6))
    p = txH.text_frame.paragraphs[0]
    p.text = heading
    p.font.name = _font(heading_s.get("font_name"))
    p.font.size = Pt(heading_s.get("font_size", 11))
    p.font.bold = True
    p.font.color.rgb = _rgb(heading_s.get("color", "#FF7900"))

    txB = slide.shapes.add_textbox(x, y + Cm(0.65), w, h - Cm(0.65))
    tf = txB.text_frame
    tf.word_wrap = True
    tf.clear()

    visible_items = (items or ["[À COMPLÉTER]"])[:3]
    for i, item in enumerate(visible_items):
        p2 = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p2.text = f"▸  {_coerce(item, '[À COMPLÉTER]')}"
        p2.font.name = _font(bullet_s.get("font_name"))
        p2.font.size = Pt(bullet_s.get("font_size", 10))
        p2.font.bold = False
        p2.font.color.rgb = _rgb(bullet_s.get("color", "#000000"))
        p2.space_after = Pt(5)


# ── Footer ────────────────────────────────────────────────────────────────────

def _add_footer(slide, payload: dict[str, Any]) -> None:
    footer_y = SLIDE_H - Cm(1.3)

    sep = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, MARGIN, footer_y - Cm(0.1), SLIDE_W - MARGIN * 2, Cm(0.03)
    )
    sep.fill.solid()
    sep.fill.fore_color.rgb = LIGHT_GREY
    sep.line.fill.background()

    refs = payload.get("reference_examples_used") or []
    refs_text = f"Basé sur : {', '.join(refs[:3])}" if refs else ""
    date_str = datetime.now().strftime("%d/%m/%Y")

    left_text = "Orange Cyberdefense — Conseil & Audit"
    right_text = f"{refs_text}  |  REF-Factory  |  {date_str}" if refs_text else f"REF-Factory  |  {date_str}"

    footer_s = _STYLES.get("footer", {})

    txL = slide.shapes.add_textbox(MARGIN, footer_y, Cm(16), Cm(0.7))
    pL = txL.text_frame.paragraphs[0]
    pL.text = left_text
    pL.font.name = _font(footer_s.get("font_name"))
    pL.font.size = Pt(footer_s.get("font_size", 8))
    pL.font.color.rgb = _rgb(footer_s.get("color", "#8F8F8F"))

    txR = slide.shapes.add_textbox(SLIDE_W - Cm(17) - MARGIN, footer_y, Cm(17), Cm(0.7))
    pR = txR.text_frame.paragraphs[0]
    pR.text = right_text
    pR.alignment = PP_ALIGN.RIGHT
    pR.font.name = _font(footer_s.get("font_name"))
    pR.font.size = Pt(footer_s.get("font_size", 8))
    pR.font.color.rgb = _rgb(footer_s.get("color", "#8F8F8F"))


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
