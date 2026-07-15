from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages


class RefFactoryState(TypedDict):
    brief_text: str
    input_files: list[str]
    manual_fields: dict[str, str]
    source_documents: list[dict[str, Any]]
    combined_source_text: str
    retrieved_examples: list[dict[str, Any]]
    structured_ref: dict[str, Any]
    slide_payload: dict[str, Any]
    output_path: Optional[str]
    quality_score: Optional[float]
    quality_report: Optional[dict[str, Any]]
    error: Optional[str]
    messages: Annotated[list, add_messages]
