"""Governance contracts: FinOps constants and risk-tiered autonomy.

Two concerns live here:

* FinOps / model governance constants (spec section 5) — reference values only.
* The risk-tiered autonomy contract that calibrates how many HITL gates a
  change class requires (docs/10, "Gates por nível de risco"). Approval
  fatigue is a real failure mode: asking a human to approve everything twice
  trains the human to stop reading. The answer is not fewer controls but
  controls proportional to risk, recalibrated continuously by the HITL
  decisions themselves (docs/11, feedback loop).
"""

from dataclasses import dataclass
from enum import Enum

from .evaluation import RolloutMode

GOLD_MODEL = "qwen2.5-coder:32b"
MINIMUM_VIABLE_MODEL = "qwen2.5:7b"

TEMPERATURE_VALIDATOR = 0.1
TEMPERATURE_COACH = 0.4
TEMPERATURE_EXPLAINER = 0.4

LOCAL_VRAM_GB_32B = 24
LOCAL_VRAM_GB_7B = 8


# --- Risk-tiered autonomy --------------------------------------------------


class RiskTier(str, Enum):
    """Risk tier of a change class — decides how many HITL gates it takes."""

    ALTO = "alto"
    """High risk: code in production, rollbacks, anything hard to reverse.

    Always two separate gates on the code path (PR content and change window),
    because they are two different authorities — see docs/10.
    """

    BAIXO = "baixo"
    """Low risk: standard window, tested automatic rollback, bounded blast
    radius. One consolidated gate: content and window reviewed in a single
    human decision."""


GATES_POR_TIER: dict[RiskTier, int] = {
    RiskTier.ALTO: 2,
    RiskTier.BAIXO: 1,
}
"""How many HITL gates each tier requires before execution."""

GMUD_SEMPRE_HUMANA = True
"""Promotion never waives the change request: a GMUD is approved by a human,
never by an agent — mirrors `integrations.ChangeRequest`. Auto-approval only
ever applies to gates *below* this line."""


@dataclass(frozen=True)
class AutonomyLevel:
    """Effective autonomy of a change class: risk tier × rollout mode.

    The two axes compose: the tier says how many gates the class needs today;
    the rollout mode (`evaluation.RolloutMode`) says how much of that can be
    delegated. A BAIXO class whose agent version reached FULL with a proven
    golden-set track record is a candidate for auto-approval (zero pauses);
    an ALTO class never drops below two gates regardless of rollout mode.

    Calibration is continuous: every HITL decision becomes labelled data
    (docs/11, feedback loop) and feeds tier reviews — a class that humans
    approve unchanged for months is evidence for demotion to BAIXO; a
    rejection is evidence for the opposite.
    """

    tier: RiskTier
    rollout: RolloutMode

    def gates_required(self) -> int:
        """Gates this class must pass today, given tier and rollout mode."""
        raise NotImplementedError
