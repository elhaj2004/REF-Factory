from ref_factory.rag.store import search_reference_examples
from ref_factory.state import RefFactoryState


def retrieve_examples(state: RefFactoryState) -> dict:
    manual_fields = state.get("manual_fields") or {}
    query_parts = [
        manual_fields.get("title", ""),
        manual_fields.get("client", ""),
        manual_fields.get("sector", ""),
        manual_fields.get("keywords", ""),
        state.get("brief_text", ""),
    ]
    query = " ".join(part.strip() for part in query_parts if part and part.strip())
    examples = search_reference_examples(query=query, k=4)
    return {"retrieved_examples": examples}
