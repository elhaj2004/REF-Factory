from ref_factory.document_parser import build_combined_source_text, parse_supporting_documents
from ref_factory.state import RefFactoryState


def collect_inputs(state: RefFactoryState) -> dict:
    source_documents = parse_supporting_documents(state.get("input_files") or [])
    combined_source_text = build_combined_source_text(
        manual_fields=state.get("manual_fields") or {},
        brief_text=state.get("brief_text") or "",
        source_documents=source_documents,
    )
    if not combined_source_text.strip():
        return {"error": "Aucune information exploitable fournie. Ajoutez un brief ou une piece jointe."}

    return {
        "source_documents": source_documents,
        "combined_source_text": combined_source_text,
    }
