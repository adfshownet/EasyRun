from dataclasses import dataclass

from .state import AgentState


@dataclass(frozen=True)
class Checkpoint:
    """A saved point-in-time snapshot of an incident's AgentState."""

    checkpoint_id: str
    incident_id: str
    state: AgentState


class CheckpointStore:
    """Stub for the PostgreSQL-backed checkpoint store (spec section 4).

    On failure, remediation resumes exactly from the last saved checkpoint
    instead of re-running already-applied corrective actions.
    """

    def save(self, checkpoint: Checkpoint) -> None:
        raise NotImplementedError

    def load(self, checkpoint_id: str) -> Checkpoint:
        raise NotImplementedError
