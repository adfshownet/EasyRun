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

    Scope (docs/06, "O contrato de propriedade do estado"): this store is an
    **intra-invocation** mechanism — it protects reasoning progress inside a
    single Step Functions task. The durable resume point between invocations
    (including HITL waits via task token) is always the Step Functions state
    machine, never this store.
    """

    def save(self, checkpoint: Checkpoint) -> None:
        raise NotImplementedError

    def load(self, checkpoint_id: str) -> Checkpoint:
        raise NotImplementedError
