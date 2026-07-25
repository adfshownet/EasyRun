import pytest

from squad_agentica.aiops.governance import (
    GOLD_MODEL,
    MINIMUM_VIABLE_MODEL,
    TEMPERATURE_COACH,
    TEMPERATURE_VALIDATOR,
)
from squad_agentica.aiops.remediation import REMEDIATION_MAP
from squad_agentica.aiops.roles import Coach, Explainer, Planner, Validator, request_human_approval
from squad_agentica.aiops.severity import DetectionAlgorithm, Severity
from squad_agentica.aiops.state import AgentState


def test_agent_state_shape():
    state: AgentState = {
        "incident_id": "ANM-2047",
        "anomaly_type": "latency_spike",
        "severity": Severity.CRITICO,
        "detection_algorithm": DetectionAlgorithm.ROBUST,
        "schema_version": 1,
        "root_cause": None,
        "confidence": None,
        "remediation_plan": [],
        "remediation_action": None,
        "hitl_required": True,
        "hitl_approved": None,
        "checkpoint_id": None,
        "history": [],
    }
    assert state["incident_id"] == "ANM-2047"
    assert state["severity"] is Severity.CRITICO


def test_remediation_map_keys():
    assert set(REMEDIATION_MAP) == {"cpu_spike", "lambda_error_rate", "dns_timeout"}
    assert REMEDIATION_MAP["dns_timeout"].aws_service == "Route 53"
    assert REMEDIATION_MAP["cpu_spike"].aws_service == "ASG (Auto Scaling)"


def test_severity_and_algorithm_members():
    assert {s.value for s in Severity} == {"critico", "alerta", "preditivo"}
    assert {a.value for a in DetectionAlgorithm} == {"basic", "agile", "robust"}


def test_governance_constants():
    assert GOLD_MODEL == "qwen2.5-coder:32b"
    assert MINIMUM_VIABLE_MODEL == "qwen2.5:7b"
    assert TEMPERATURE_VALIDATOR < TEMPERATURE_COACH


@pytest.mark.parametrize("role_cls", [Planner, Explainer, Validator, Coach])
def test_role_stubs_are_not_implemented(role_cls):
    with pytest.raises(NotImplementedError):
        role_cls()(state={})


def test_request_human_approval_stub():
    with pytest.raises(NotImplementedError):
        request_human_approval(state={})
