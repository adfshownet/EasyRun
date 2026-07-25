"""The nodes of the orchestration graph (spec section 4). Not implemented.

Two families of node live here, and the distinction matters:

* **Reasoning roles** — Planner, Explainer, Validator, Coach. These are the four
  roles of the specification; each one calls a model.
* **Adapter nodes** — `TraceabilityNode` and `CodeRemediationNode`. These call
  the corporate platforms through the ports in `integrations.py`. In the product
  UI they are presented as the agents *Elo* and *Artífice*, because that is how
  the squad is introduced to people; architecturally they are tool-using nodes,
  not reasoners.

Both views are correct at their own level, and the prototype shows the first one
while this module encodes the second.
"""

from .remediation import RemediationKind
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


class TraceabilityNode:
    """Elo: keeps the corporate record in sync with what the squad is doing.

    Reads the CMDB to learn what broke and which repository backs it, opens the
    bug on the kanban, opens the change request, moves the card as the pipeline
    advances, closes the incident — or hands it back to the owning team.

    Every write it performs is a record someone would otherwise fill in by hand,
    which is where most of the wall-clock time of an incident is actually spent.
    """

    def __call__(self, state: AgentState) -> AgentState:
        raise NotImplementedError


class CodeRemediationNode:
    """Artífice: turns a diagnosis into a pull request.

    Clones the repository named by the CMDB, narrows the diagnosis down to the
    relevant code, delegates the patch to the external code agent and opens the
    pull request on the organization.

    Precondition (see `observability.REDACTION_REQUIRED_BEFORE_EGRESS`): nothing
    leaves for the external agent before secret and PII redaction has run, and
    only repositories on the allowlist are eligible.
    """

    def __call__(self, state: AgentState) -> AgentState:
        raise NotImplementedError


def classify_remediation(state: AgentState) -> RemediationKind:
    """Decide which branch of the graph the incident takes.

    Called right after the Explainer. This is the highest-leverage decision of
    the whole pipeline: routing an infrastructure problem down the code path
    wastes a Devin session and a review cycle, and routing a code defect down
    the infrastructure path "fixes" the symptom while the bug ships again on the
    next deploy.
    """
    raise NotImplementedError


def escalate(state: AgentState) -> AgentState:
    """Give up safely: hand the incident to the owning team with the context.

    Reached when the plan was rejected and replanning did not produce an option
    within the guardrails, or when the remediation kind is EXTERNO. Knowing when
    to stop is a feature — an agent that keeps trying is more dangerous than one
    that escalates.
    """
    raise NotImplementedError
