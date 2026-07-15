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

ACCENT = "#FF6600"
INK = "#1A1A1A"

CSS = f"""
:root {{
    --accent: {ACCENT};
    --ink: {INK};
}}
.gradio-container {{ font-family: 'Calibri', 'Arial', sans-serif; }}
#header {{
    background: linear-gradient(90deg, #111111 0%, #1a1a1a 100%);
    border-left: 6px solid var(--accent);
    padding: 18px 20px;
    border-radius: 8px;
    margin-bottom: 10px;
}}
#header h1 {{ color: var(--accent); margin: 0; font-size: 1.7rem; }}
#header p {{ color: #d4d4d4; margin: 6px 0 0 0; }}
.panel-note {{
    border: 1px solid #ececec;
    border-radius: 8px;
    padding: 12px;
    background: #fafafa;
}}
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
        f"## Score qualite REF : **{score:.0f} / 100**",
        "",
        f"- Completude : **{breakdown.get('completeness', 0):.0f}/100**",
        f"- Densite slide : **{breakdown.get('density', 0):.0f}/100**",
        f"- Ancrage references : **{breakdown.get('grounding', 0):.0f}/100**",
        f"- Exemples utilises : **{report.get('examples_used', 0)}**",
    ]

    if missing:
        lines.extend(["", "### Champs a completer"])
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
            "Aucun exemple trouve. Deposez des fiches REF dans "
            f"`{REFERENCE_LIBRARY_DIR}` puis cliquez sur `Indexer la base REF`."
        )

    lines = ["## Exemples similaires recuperes", ""]
    for example in examples:
        filename = example.get("filename", "document")
        excerpt = example.get("excerpt", "")
        lines.append(f"- **{filename}** : {excerpt}")
    return "\n".join(lines)


def cb_index_library() -> str:
    file_count = count_reference_files()
    chunk_count = index_reference_library(verbose=False)
    return (
        f"Base REF indexee. Fichiers detectes : {file_count}. "
        f"Chunks indexes : {chunk_count}. Dossier source : `{REFERENCE_LIBRARY_DIR}`"
    )


def cb_generate(
    title,
    client,
    sector,
    duration,
    team,
    keywords,
    confidentiality,
    brief_text,
    supporting_files,
):
    initial_state = _initial_state(
        title=title,
        client=client,
        sector=sector,
        duration=duration,
        team=team,
        keywords=keywords,
        confidentiality=confidentiality,
        brief_text=brief_text,
        supporting_files=supporting_files,
    )
    final_state = graph.invoke(initial_state)

    if final_state.get("error"):
        return (
            f"Erreur : {final_state['error']}",
            gr.update(value="*Generation interrompue.*"),
            gr.update(value=""),
            gr.update(value={}),
            gr.update(visible=False, value=None),
        )

    report = final_state.get("quality_report") or {}
    structured_ref = final_state.get("structured_ref") or {}
    output_path = final_state.get("output_path")
    status = (
        f"Fiche REF generee. Sortie : `{output_path}`"
        if output_path
        else "Generation terminee sans fichier de sortie."
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
            <div id="header">
              <h1>REF-Factory</h1>
              <p>Generation d'une fiche REF PowerPoint une-slide avec base d'exemples locale.</p>
            </div>
            """
        )

        gr.Markdown(
            f"""
            <div class="panel-note">
            Base d'exemples attendue : <code>{REFERENCE_LIBRARY_DIR}</code><br>
            Sorties generees : <code>{OUTPUT_DIR}</code><br>
            Fichiers temporaires UI : <code>{UPLOAD_DIR}</code>
            </div>
            """
        )

        library_status = gr.Markdown(
            f"Fichiers REF detectes actuellement : **{count_reference_files()}** dans `{REFERENCE_LIBRARY_DIR}`"
        )

        with gr.Row():
            with gr.Column(scale=1, min_width=340):
                title = gr.Textbox(label="Titre de la fiche REF", placeholder="Ex : Accompagnement RSSI groupe industriel")
                client = gr.Textbox(label="Client")
                sector = gr.Textbox(label="Secteur")
                duration = gr.Textbox(label="Duree / charge")
                team = gr.Textbox(label="Equipe / intervenants")
                keywords = gr.Textbox(label="Mots-cles", placeholder="Ex : audit, ISO 27001, gouvernance, SOC")
                confidentiality = gr.Dropdown(
                    label="Confidentialite",
                    choices=["Interne", "Externe", "Confidentiel"],
                    value="Interne",
                )
                brief_text = gr.Textbox(
                    label="Brief consultant / resume de mission",
                    lines=14,
                    placeholder=(
                        "Collez ici les informations utiles : contexte client, besoin, perimetre, "
                        "livrables, equipe, resultats, enjeux, points forts, etc."
                    ),
                )
                supporting_files = gr.File(
                    label="Pieces jointes optionnelles",
                    file_types=[".pdf", ".docx", ".pptx", ".txt", ".md", ".json"],
                    file_count="multiple",
                    type="filepath",
                )

                with gr.Row():
                    index_btn = gr.Button("Indexer la base REF")
                    generate_btn = gr.Button("Generer la fiche REF", variant="primary")

                status_box = gr.Markdown("")

            with gr.Column(scale=1, min_width=340):
                report_md = gr.Markdown("*Le rapport qualite apparaitra ici.*")
                examples_md = gr.Markdown("*Les fiches REF similaires apparaitront ici.*")
                structured_json = gr.JSON(label="JSON structure genere", value={})
                download_file = gr.File(label="PPT final une-slide", visible=False, interactive=False)

        index_btn.click(fn=cb_index_library, outputs=[library_status])
        generate_btn.click(
            fn=cb_generate,
            inputs=[
                title,
                client,
                sector,
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
