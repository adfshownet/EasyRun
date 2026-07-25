from typing import Optional, TypedDict

from .severity import DetectionAlgorithm, Severity


class AgentState(TypedDict):
    """Shared state threaded through the LangGraph orchestration (spec section 4).

    Schema is versioned (`schema_version`) so rolling deployments can detect
    when an old and a new version of this contract coexist.
    """

    incident_id: str
    anomaly_type: str
    severity: Severity
    detection_algorithm: DetectionAlgorithm
    schema_version: int
    root_cause: Optional[str]
    confidence: Optional[float]
    remediation_plan: list[str]
    remediation_action: Optional[str]
    hitl_required: bool
    hitl_approved: Optional[bool]
    checkpoint_id: Optional[str]
    history: list[str]
