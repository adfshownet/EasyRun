from typing import Optional, TypedDict

from .remediation import RemediationKind
from .severity import AnomalyOrigin, DetectionAlgorithm, IncidentNature, Severity

SCHEMA_VERSION = 2
"""Current version of the AgentState contract.

Bumped from 1 to 2 when the corporate traceability block was added. This is the
scenario the field exists for: during a rolling deployment a state written by
the old code can be read by the new one, and the mismatch must be detectable
instead of surfacing as a KeyError deep inside a downstream node.
"""


class AgentState(TypedDict):
    """Shared state threaded through the LangGraph orchestration (spec section 4).

    Schema is versioned (`schema_version`) so rolling deployments can detect
    when an old and a new version of this contract coexist.
    """

    # --- identity and classification --------------------------------------
    incident_id: str
    anomaly_type: str
    severity: Severity
    detection_algorithm: DetectionAlgorithm
    origin: AnomalyOrigin
    incident_nature: IncidentNature
    schema_version: int

    # --- diagnosis ---------------------------------------------------------
    root_cause: Optional[str]
    confidence: Optional[float]
    remediation_kind: Optional[RemediationKind]
    """Set by the Diagnosta. Routes the whole downstream pipeline."""

    # --- plan and execution ------------------------------------------------
    remediation_plan: list[str]
    remediation_action: Optional[str]

    # --- human in the loop -------------------------------------------------
    hitl_required: bool
    hitl_approved: Optional[bool]

    # --- corporate traceability --------------------------------------------
    # The single thread linking every record the company's process demands.
    # Filled progressively by the traceability node as the pipeline advances.
    servicenow_incident_id: Optional[str]
    servicenow_change_id: Optional[str]
    cmdb_ci: Optional[str]
    iuclick_task_id: Optional[str]
    repository: Optional[str]
    devin_session_id: Optional[str]
    pull_request_url: Optional[str]
    escalated_to: Optional[str]

    # --- observability ------------------------------------------------------
    trace_id: Optional[str]
    """Correlation id shared by Datadog APM, Langfuse and LangSmith."""

    # --- durability and audit -----------------------------------------------
    checkpoint_id: Optional[str]
    history: list[str]
