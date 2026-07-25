"""Evaluation and safe rollout contract for agent versions (MLOps). Not implemented.

An agentic pipeline that acts on production cannot be shipped the way a
stateless service is. There is no single expected output to assert against: two
different root-cause explanations can both be correct. So promotion is gated by
*measured* behaviour on historical incidents rather than by unit tests alone.

The loop this module describes:

    incidentes históricos do ServiceNow  →  golden set
                                         →  roda a versão candidata
                                         →  LLM-as-judge pontua
                                         →  portão de regressão
                                         →  shadow  →  canário  →  produção
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .remediation import RemediationKind
from .severity import Severity


class RolloutMode(str, Enum):
    """How much authority a given agent version has in production."""

    SHADOW = "shadow"
    """Runs on real incidents and records what it *would* do. Never acts.

    This is what makes autonomy sellable in a risk-averse organization: the new
    version accumulates a track record against real traffic before it is
    allowed to touch anything.
    """

    CANARY = "canary"
    """Acts on a small, bounded slice of incidents."""

    FULL = "full"
    """Acts on all eligible incidents."""


@dataclass(frozen=True)
class EvalCase:
    """One historical incident replayed as a test case.

    Sourced from closed ServiceNow incidents, which is why the golden set grows
    on its own: every incident the squad resolves today is a test case tomorrow.
    """

    case_id: str
    incident_id: str
    anomaly_type: str
    severity: Severity
    expected_remediation_kind: RemediationKind
    expected_root_cause: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class EvalResult:
    """Score of one candidate version against one case."""

    case_id: str
    agent_version: str
    remediation_kind_correct: bool
    root_cause_score: float
    """0.0–1.0, assigned by the judge model at temperature 0.1."""

    latency_ms: int
    cost_usd: float


# --- Regression gate -------------------------------------------------------

GOLDEN_SET_MIN_SIZE = 40
"""Below this, a score difference is noise rather than signal."""

MIN_ROOT_CAUSE_SCORE = 0.80
MIN_REMEDIATION_KIND_ACCURACY = 0.90
"""Misrouting the remediation kind is the costlier error: it sends an infra
problem down the code path, or worse, the reverse."""

MAX_REGRESSION_TOLERANCE = 0.02
"""A candidate may score at most this much below the incumbent and still pass."""


def passes_regression_gate(
    candidate: list[EvalResult],
    incumbent: list[EvalResult],
) -> bool:
    """Whether a candidate version may be promoted to the next rollout stage."""
    raise NotImplementedError
