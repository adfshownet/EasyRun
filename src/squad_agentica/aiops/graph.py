"""Stub describing the intended LangGraph wiring (spec section 4). Not implemented.

Intended flow: Planner -> Explainer -> Validator -> (interrupt() if
state["hitl_required"]) -> Coach. Deliberately does not import langgraph —
this module only documents the shape for a future real implementation.
"""


def build_graph():
    raise NotImplementedError
