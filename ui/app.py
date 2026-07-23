import os
import shutil
import sys
import uuid
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ref_factory.config import OUTPUT_DIR, REFERENCE_LIBRARY_DIR, UPLOAD_DIR
from ref_factory.graph import graph
from ref_factory.rag.store import count_reference_files, index_reference_library

# Charte Orange Cyberdefense
ORANGE = "#FF7900"
INK = "#0A0A0A"
GREY = "#595959"

BRIEF_EXAMPLE = """Contexte :
Face à la montée de la menace cyber dans son secteur, le client a souhaité
renforcer sa posture de sécurité. L'entité ne disposait pas encore d'une
politique formalisée ni d'un plan d'action priorisé.

Réalisation :
- Réalisation d'ateliers métiers et techniques avec les équipes concernées
- Élaboration d'un scénario / d'une démarche sur mesure
- Animation de la mission et restitution auprès du COMEX

Livrables :
- Rapport détaillé et cartographie des écarts
- Feuille de route priorisée
- Plan de formation / sensibilisation

Bénéfices :
- Prise de conscience des risques par les équipes
- Priorisation claire des chantiers de remédiation
- Conformité renforcée vis-à-vis des exigences applicables
"""

CSS = f"""
.gradio-container {{ font-family: 'Source Sans Pro', 'Calibri', 'Arial', sans-serif; }}

#ocd-header {{
    background: linear-gradient(90deg, {INK} 0%, #1c1c1c 100%);
    border-left: 8px solid {ORANGE};
    padding: 20px 24px;
    border-radius: 10px;
    margin-bottom: 14px;
}}
#ocd-header h1 {{ color: {ORANGE}; margin: 0; font-size: 1.75rem; letter-spacing: .3px; }}
#ocd-header p {{ color: #dcdcdc; margin: 6px 0 0 0; font-size: .95rem; }}

.ocd-note {{
    border: 1px solid #ececec;
    border-left: 4px solid {ORANGE};
    border-radius: 8px;
    padding: 12px 14px;
    background: #fafafa;
    font-size: .9rem;
}}

.ocd-section > .label-wrap {{ font-weight: 700 !important; color: {INK} !important; }}

button.primary, .ocd-generate button {{
    background: {ORANGE} !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}}
button.primary:hover, .ocd-generate button:hover {{ filter: brightness(1.06); }}

#ocd-status {{ font-weight: 600; }}
"""


def _copy_uploaded_files(uploaded_files) -> list[str]:
    if not uploaded_files:
        return []

    session_dir = UPLOAD_DIR / str(uuid.uuid4())
    session_dir.mkdir(parents=True, exist_ok=True)
    copied_files: list[str] = []

    for source in uploaded_files:
        source_path = Path(source)
        destination = session_dir / source_path.name
        shutil.copy2(source_path, destination)
        copied_files.append(str(destination))

    return copied_files


def _initial_state(
    title: str,
    client: str,
    sector: str,
    location: str,
    date: str,
    duration: str,
    team: str,
    keywords: str,
    confidentiality: str,
    brief_text: str,
    supporting_files: list[str] | None,
) -> dict:
    return {
        "brief_text": brief_text or "",
        "input_files": _copy_uploaded_files(supporting_files),
        "manual_fields": {
            "title": title or "",
            "client": client or "",
            "sector": sector or "",
            "location": location or "",
            "date": date or "",
            "duration": duration or "",
            "team": team or "",
            "keywords": keywords or "",
            "confidentiality": confidentiality or "Interne",
        },
        "source_documents": [],
        "combined_source_text": "",
        "retrieved_examples": [],
        "structured_ref": {},
        "slide_payload": {},
        "output_path": None,
        "quality_score": None,
        "quality_report": None,
        "error": None,
        "messages": [],
    }


def _format_report(report: dict | None) -> str:
    if not report:
        return "*Aucun rapport disponible.*"

    breakdown = report.get("breakdown", {})
    issues = report.get("issues", [])
    recos = report.get("recommendations", [])
    missing = report.get("missing_fields", [])
    score = float(report.get("score", 0))

    lines = [
        f"## Score qualité REF : **{score:.0f} / 100**",
        "",
        f"- Complétude : **{breakdown.get('completeness', 0):.0f}/100**",
        f"- Densité slide : **{breakdown.get('density', 0):.0f}/100**",
        f"- Ancrage références : **{breakdown.get('grounding', 0):.0f}/100**",
        f"- Exemples utilisés : **{report.get('examples_used', 0)}**",
    ]

    if missing:
        lines.extend(["", "### Champs à compléter"])
        lines.extend([f"- {item}" for item in missing])

    if issues:
        lines.extend(["", "### Points d'attention"])
        lines.extend([f"- {item}" for item in issues])

    if recos:
        lines.extend(["", "### Recommandations"])
        lines.extend([f"- {item}" for item in recos])

    return "\n".join(lines)


def _format_examples(examples: list[dict]) -> str:
    if not examples:
        return (
            "Aucun exemple trouvé. Déposez des fiches REF dans "
            f"`{REFERENCE_LIBRARY_DIR}` puis cliquez sur **Indexer la base REF**."
        )

    lines = ["## Exemples similaires récupérés", ""]
    for example in examples:
        filename = example.get("filename", "document")
        excerpt = example.get("excerpt", "")
        lines.append(f"- **{filename}** : {excerpt}")
    return "\n".join(lines)


def cb_index_library() -> str:
    file_count = count_reference_files()
    chunk_count = index_reference_library(verbose=False)
    return (
        f"✅ Base REF indexée — **{file_count}** fichier(s), **{chunk_count}** chunk(s). "
        f"Source : `{REFERENCE_LIBRARY_DIR}`"
    )


def cb_load_example() -> str:
    return BRIEF_EXAMPLE


def cb_generate(
    title,
    client,
    sector,
    location,
    date,
    duration,
    team,
    keywords,
    confidentiality,
    brief_text,
    supporting_files,
    progress=gr.Progress(track_tqdm=False),
):
    progress(0.1, desc="Préparation des entrées…")
    initial_state = _initial_state(
        title=title,
        client=client,
        sector=sector,
        location=location,
        date=date,
        duration=duration,
        team=team,
        keywords=keywords,
        confidentiality=confidentiality,
        brief_text=brief_text,
        supporting_files=supporting_files,
    )
    progress(0.4, desc="Recherche d'exemples et génération…")
    final_state = graph.invoke(initial_state)

    if final_state.get("error"):
        return (
            f"❌ Erreur : {final_state['error']}",
            gr.update(value="*Génération interrompue.*"),
            gr.update(value=""),
            gr.update(value={}),
            gr.update(visible=False, value=None),
        )

    progress(0.9, desc="Finalisation…")
    report = final_state.get("quality_report") or {}
    structured_ref = final_state.get("structured_ref") or {}
    output_path = final_state.get("output_path")
    status = (
        f"✅ Fiche REF générée. Fichier : `{output_path}`"
        if output_path
        else "⚠️ Génération terminée sans fichier de sortie."
    )

    return (
        status,
        gr.update(value=_format_report(report)),
        gr.update(value=_format_examples(final_state.get("retrieved_examples") or [])),
        gr.update(value=structured_ref),
        gr.update(visible=bool(output_path), value=output_path),
    )


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="REF-Factory", theme=gr.themes.Base(), css=CSS) as demo:
        gr.HTML(
            """
            <div id="ocd-header">
              <h1>REF-Factory</h1>
              <p>Génération d'une fiche REF Orange Cyberdefense (PowerPoint une-slide)
              à partir de vos informations et d'une base d'exemples locale.</p>
            </div>
            """
        )

        with gr.Row():
            # ── Colonne saisie ────────────────────────────────────────────
            with gr.Column(scale=5, min_width=380):
                library_status = gr.Markdown(
                    f"📁 Fiches REF détectées : **{count_reference_files()}** "
                    f"dans `{REFERENCE_LIBRARY_DIR}`"
                )

                with gr.Accordion("1. Identité de la fiche", open=True):
                    title = gr.Textbox(
                        label="Titre de la fiche REF",
                        placeholder="Ex : Exercice de crise cyber industriel",
                    )
                    client = gr.Textbox(label="Client", placeholder="Ex : Nexans")
                    confidentiality = gr.Dropdown(
                        label="Confidentialité",
                        choices=["Interne", "Externe", "Confidentiel"],
                        value="Interne",
                    )

                with gr.Accordion("2. Profil de la prestation", open=True):
                    with gr.Row():
                        sector = gr.Textbox(label="Secteur", placeholder="Ex : Transport")
                        location = gr.Textbox(label="Lieu", placeholder="Ex : Paris / Colombie")
                    with gr.Row():
                        date = gr.Textbox(label="Date / Année", placeholder="Ex : 2024")
                        duration = gr.Textbox(label="Durée / charge", placeholder="Ex : 27,25 jours")
                    team = gr.Textbox(label="Équipe / intervenants", placeholder="Ex : 1 manager, 2 consultants")
                    keywords = gr.Textbox(
                        label="Mots-clés",
                        placeholder="Ex : exercice de crise, gestion de crise, OT",
                    )

                with gr.Accordion("3. Contenu de la mission", open=True):
                    gr.Markdown(
                        "<div class='ocd-note'>Renseignez le contenu ci-dessous. "
                        "Astuce : structurez votre texte avec les intitulés "
                        "<b>Contexte / Réalisation / Livrables / Bénéfices</b> "
                        "pour un meilleur découpage. Les sections laissées vides "
                        "resteront vides sur la fiche.</div>"
                    )
                    brief_text = gr.Textbox(
                        label="Brief consultant / résumé de mission",
                        lines=14,
                        placeholder="Collez ici le contexte, la réalisation, les livrables et les bénéfices…",
                    )
                    example_btn = gr.Button("＋ Charger un exemple de brief", size="sm")
                    supporting_files = gr.File(
                        label="Pièces jointes optionnelles",
                        file_types=[".pdf", ".docx", ".pptx", ".txt", ".md", ".json"],
                        file_count="multiple",
                        type="filepath",
                    )

                with gr.Row():
                    index_btn = gr.Button("🔄 Indexer la base REF")
                    generate_btn = gr.Button(
                        "⚡ Générer la fiche REF", variant="primary", elem_classes="ocd-generate"
                    )

                status_box = gr.Markdown("", elem_id="ocd-status")

            # ── Colonne résultats ─────────────────────────────────────────
            with gr.Column(scale=4, min_width=340):
                gr.Markdown("### Résultat")
                download_file = gr.File(
                    label="📥 Fiche PPTX générée", visible=False, interactive=False
                )
                with gr.Accordion("Rapport qualité", open=True):
                    report_md = gr.Markdown("*Le rapport qualité apparaîtra ici après génération.*")
                with gr.Accordion("Fiches REF similaires (RAG)", open=False):
                    examples_md = gr.Markdown("*Les exemples similaires apparaîtront ici.*")
                with gr.Accordion("JSON structuré généré", open=False):
                    structured_json = gr.JSON(value={})

                gr.Markdown(
                    f"""
                    <div class="ocd-note" style="margin-top:10px">
                    Sorties : <code>{OUTPUT_DIR}</code><br>
                    Base d'exemples : <code>{REFERENCE_LIBRARY_DIR}</code><br>
                    Accès à l'interface : <code>http://localhost:7861</code>
                    </div>
                    """
                )

        # ── Câblage ───────────────────────────────────────────────────────
        example_btn.click(fn=cb_load_example, outputs=[brief_text])
        index_btn.click(fn=cb_index_library, outputs=[library_status])
        generate_btn.click(
            fn=cb_generate,
            inputs=[
                title,
                client,
                sector,
                location,
                date,
                duration,
                team,
                keywords,
                confidentiality,
                brief_text,
                supporting_files,
            ],
            outputs=[status_box, report_md, examples_md, structured_json, download_file],
        )

    return demo


if __name__ == "__main__":
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7861, share=False, show_error=True)
