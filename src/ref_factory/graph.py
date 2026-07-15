from langgraph.graph import END, START, StateGraph

from ref_factory.nodes.check_quality import check_quality
from ref_factory.nodes.collect_inputs import collect_inputs
from ref_factory.nodes.render_pptx import render_pptx
from ref_factory.nodes.retrieve_examples import retrieve_examples
from ref_factory.nodes.structure_ref import structure_ref
from ref_factory.state import RefFactoryState


def _route_after(node_name: str):
    def _router(state: RefFactoryState) -> str:
        return END if state.get("error") else node_name

    return _router


def create_graph():
    builder = StateGraph(RefFactoryState)
    builder.add_node("collect_inputs", collect_inputs)
    builder.add_node("retrieve_examples", retrieve_examples)
    builder.add_node("structure_ref", structure_ref)
    builder.add_node("render_pptx", render_pptx)
    builder.add_node("check_quality", check_quality)

    builder.add_edge(START, "collect_inputs")
    builder.add_conditional_edges("collect_inputs", _route_after("retrieve_examples"))
    builder.add_edge("retrieve_examples", "structure_ref")
    builder.add_conditional_edges("structure_ref", _route_after("render_pptx"))
    builder.add_conditional_edges("render_pptx", _route_after("check_quality"))
    builder.add_edge("check_quality", END)
    return builder.compile()


graph = create_graph()
