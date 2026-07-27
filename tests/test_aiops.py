import pytest

from squad_agentica.aiops.evaluation import (
    GOLDEN_SET_MIN_SIZE,
    MIN_REMEDIATION_KIND_ACCURACY,
    MIN_ROOT_CAUSE_SCORE,
    RolloutMode,
    passes_regression_gate,
)
from squad_agentica.aiops.governance import (
    GATES_POR_TIER,
    GMUD_SEMPRE_HUMANA,
    GOLD_MODEL,
    MINIMUM_VIABLE_MODEL,
    TEMPERATURE_COACH,
    TEMPERATURE_VALIDATOR,
    AutonomyLevel,
    RiskTier,
)
from squad_agentica.aiops.integrations import INTEGRATIONS
from squad_agentica.aiops.observability import (
    REDACTION_REQUIRED_BEFORE_EGRESS,
    REPOSITORY_ALLOWLIST_REQUIRED,
    AgentRunMetrics,
    PromptRef,
    Stage,
)
from squad_agentica.aiops.remediation import REMEDIATION_MAP, RemediationKind
from squad_agentica.aiops.roles import (
    Coach,
    CodeRemediationNode,
    Explainer,
    Planner,
    TraceabilityNode,
    Validator,
    classify_remediation,
    escalate,
    request_human_approval,
)
from squad_agentica.aiops.severity import (
    AnomalyOrigin,
    DetectionAlgorithm,
    IncidentNature,
    Severity,
)
from squad_agentica.aiops.state import SCHEMA_VERSION, AgentState


def _sample_state() -> AgentState:
    return {
        "incident_id": "ANM-2047",
        "anomaly_type": "latency_spike",
        "severity": Severity.CRITICO,
        "detection_algorithm": DetectionAlgorithm.ROBUST,
        "origin": AnomalyOrigin.DATADOG,
        "incident_nature": IncidentNature.SISTEMICO,
        "schema_version": SCHEMA_VERSION,
        "root_cause": None,
        "confidence": None,
        "remediation_kind": None,
        "remediation_plan": [],
        "remediation_action": None,
        "hitl_required": True,
        "hitl_approved": None,
        "servicenow_incident_id": "INC-0098431",
        "servicenow_change_id": None,
        "cmdb_ci": "svc-checkout-api",
        "iuclick_task_id": "BUG-4471",
        "repository": None,
        "devin_session_id": None,
        "pull_request_url": None,
        "escalated_to": None,
        "trace_id": "9f2c4a1e",
        "checkpoint_id": None,
        "history": [],
    }


def test_agent_state_shape():
    state = _sample_state()
    assert state["incident_id"] == "ANM-2047"
    assert state["severity"] is Severity.CRITICO
    assert state["origin"] is AnomalyOrigin.DATADOG
    assert state["incident_nature"] is IncidentNature.SISTEMICO


def test_schema_version_is_two():
    """Traceability block was added in v2 — the bump is the point of the field."""
    assert SCHEMA_VERSION == 2
    assert _sample_state()["schema_version"] == 2


def test_traceability_fields_present():
    state = _sample_state()
    for field in (
        "servicenow_incident_id",
        "servicenow_change_id",
        "cmdb_ci",
        "iuclick_task_id",
        "repository",
        "devin_session_id",
        "pull_request_url",
        "escalated_to",
        "trace_id",
    ):
        assert field in state


def test_remediation_map_keys():
    assert set(REMEDIATION_MAP) == {
        "cpu_spike",
        "lambda_error_rate",
        "dns_timeout",
        "disk_exhaustion_forecast",
        "code_defect",
        "config_drift",
        "third_party_outage",
    }
    assert REMEDIATION_MAP["dns_timeout"].platform == "Route 53"
    assert REMEDIATION_MAP["cpu_spike"].platform == "ASG (Auto Scaling)"


def test_remediation_kinds_are_coherent():
    """Code defects go to the code agent; third-party outages are escalated."""
    assert REMEDIATION_MAP["code_defect"].kind is RemediationKind.CODIGO
    assert REMEDIATION_MAP["config_drift"].kind is RemediationKind.CONFIG
    assert REMEDIATION_MAP["third_party_outage"].kind is RemediationKind.EXTERNO
    assert REMEDIATION_MAP["cpu_spike"].kind is RemediationKind.INFRA
    assert {a.kind for a in REMEDIATION_MAP.values()} == set(RemediationKind)


def test_severity_and_algorithm_members():
    assert {s.value for s in Severity} == {"critico", "alerta", "preditivo"}
    assert {a.value for a in DetectionAlgorithm} == {"basic", "agile", "robust"}


def test_origin_and_nature_members():
    assert {o.value for o in AnomalyOrigin} == {
        "datadog",
        "servicenow",
        "agendado",
        "humano",
    }
    assert {n.value for n in IncidentNature} == {"sistemico", "negocio"}


def test_remediation_kind_members():
    assert {k.value for k in RemediationKind} == {"infra", "codigo", "config", "externo"}


def test_governance_constants():
    assert GOLD_MODEL == "qwen2.5-coder:32b"
    assert MINIMUM_VIABLE_MODEL == "qwen2.5:7b"
    assert TEMPERATURE_VALIDATOR < TEMPERATURE_COACH


def test_risk_tier_members():
    assert {t.value for t in RiskTier} == {"alto", "baixo"}


def test_gates_por_tier():
    """High risk always costs more human attention than low risk."""
    assert GATES_POR_TIER[RiskTier.ALTO] == 2
    assert GATES_POR_TIER[RiskTier.BAIXO] == 1
    assert GATES_POR_TIER[RiskTier.ALTO] > GATES_POR_TIER[RiskTier.BAIXO]


def test_gmud_never_auto_approved():
    """Promotion may waive gates, never the change request itself."""
    assert GMUD_SEMPRE_HUMANA is True


def test_autonomy_level_stub():
    level = AutonomyLevel(tier=RiskTier.BAIXO, rollout=RolloutMode.FULL)
    with pytest.raises(NotImplementedError):
        level.gates_required()


def test_egress_policy_is_locked_on():
    """Company source code must never reach an external agent unredacted."""
    assert REDACTION_REQUIRED_BEFORE_EGRESS is True
    assert REPOSITORY_ALLOWLIST_REQUIRED is True


def test_integrations_registry():
    platforms = {i.platform for i in INTEGRATIONS}
    assert platforms == {
        "ServiceNow",
        "Datadog",
        "IUClick",
        "Devin",
        "GitHub (org)",
        "AWS",
    }
    github = next(i for i in INTEGRATIONS if i.platform == "GitHub (org)")
    assert github.automatic is False, "merge sempre exige aprovação humana"


def test_agent_run_metrics_total_tokens():
    metrics = AgentRunMetrics(
        agent="diagnosta",
        prompt=PromptRef(name="root-cause", version=7, stage=Stage.PROD),
        model="claude-sonnet",
        input_tokens=1200,
        output_tokens=340,
        latency_ms=2100,
    )
    assert metrics.total_tokens == 1540


def test_rollout_modes_are_ordered_by_authority():
    assert {m.value for m in RolloutMode} == {"shadow", "canary", "full"}


def test_regression_gate_thresholds():
    assert GOLDEN_SET_MIN_SIZE >= 30
    assert MIN_REMEDIATION_KIND_ACCURACY > MIN_ROOT_CAUSE_SCORE, (
        "errar o roteamento custa mais do que uma explicação imprecisa"
    )


@pytest.mark.parametrize(
    "role_cls",
    [Planner, Explainer, Validator, Coach, TraceabilityNode, CodeRemediationNode],
)
def test_role_stubs_are_not_implemented(role_cls):
    with pytest.raises(NotImplementedError):
        role_cls()(state={})


@pytest.mark.parametrize(
    "func", [request_human_approval, classify_remediation, escalate]
)
def test_function_stubs_are_not_implemented(func):
    with pytest.raises(NotImplementedError):
        func(state={})


def test_regression_gate_stub():
    with pytest.raises(NotImplementedError):
        passes_regression_gate(candidate=[], incumbent=[])
