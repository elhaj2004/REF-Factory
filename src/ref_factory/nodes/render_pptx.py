from ref_factory.presentation.rendering import render_ref_slide
from ref_factory.state import RefFactoryState


def render_pptx(state: RefFactoryState) -> dict:
    try:
        output_path = render_ref_slide(state.get("slide_payload") or {})
        return {"output_path": output_path}
    except Exception as exc:
        return {"error": f"Erreur generation PPTX: {exc}"}
