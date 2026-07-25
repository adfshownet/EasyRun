from .state import AgentState


class Planner:
    """Defines the structured diagnosis/remediation plan (spec section 4)."""

    def __call__(self, state: AgentState) -> AgentState:
        raise NotImplementedError


class Explainer:
    """Analyzes the root cause via MCP tools (spec section 4)."""

    def __call__(self, state: AgentState) -> AgentState:
        raise NotImplementedError


class Validator:
    """Quiz/Validator: judges remediation efficacy post-execution.

    Runs at temperature 0.1 (see governance.TEMPERATURE_VALIDATOR) to keep
    grading consistent and analytically fair.
    """

    def __call__(self, state: AgentState) -> AgentState:
        raise NotImplementedError


class Coach:
    """Synthesizes learning and decides whether to close or escalate the flow."""

    def __call__(self, state: AgentState) -> AgentState:
        raise NotImplementedError


def request_human_approval(state: AgentState) -> AgentState:
    """HITL gate implemented via LangGraph's interrupt().

    Engineering note (spec section 4): after an interrupt() for human
    intervention, the node MUST return the full AgentState — otherwise
    downstream nodes fail from lost context.
    """
    raise NotImplementedError
