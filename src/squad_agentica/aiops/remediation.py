from dataclasses import dataclass
from enum import Enum


class RemediationKind(str, Enum):
    """What the anomaly actually requires — the routing decision of the pipeline.

    Classified by the Diagnosta right after root cause analysis. Everything
    downstream branches on this value: who executes, which approval gates are
    raised, and what the final artifact is.
    """

    INFRA = "infra"
    """Runtime action on infrastructure. Executor acts directly."""

    CODIGO = "codigo"
    """Requires a software change. Routed to the code agent, ends in a pull request."""

    CONFIG = "config"
    """Parameter, feature flag or reference data. Ends in a change request (GMUD)."""

    EXTERNO = "externo"
    """Outside the squad's scope. Escalated to the owning team or vendor."""


@dataclass(frozen=True)
class RemediationAction:
    """One row of the anomaly → remediation mapping (spec section 4)."""

    trigger: str
    action: str
    platform: str
    """Where the action lands. Not always AWS — can be Devin, GitHub or ServiceNow."""

    kind: RemediationKind


REMEDIATION_MAP: dict[str, RemediationAction] = {
    "cpu_spike": RemediationAction(
        trigger="CPU Spike > 90%",
        action="Escalonamento Horizontal (Out)",
        platform="ASG (Auto Scaling)",
        kind=RemediationKind.INFRA,
    ),
    "lambda_error_rate": RemediationAction(
        trigger="Lambda Error > 5%",
        action="Rollback ou Update de Config",
        platform="AWS Lambda",
        kind=RemediationKind.INFRA,
    ),
    "dns_timeout": RemediationAction(
        trigger="DNS Timeout",
        action="Failover de Rota",
        platform="Route 53",
        kind=RemediationKind.INFRA,
    ),
    "disk_exhaustion_forecast": RemediationAction(
        trigger="Projeção de disco em 100% < 4h",
        action="Expansão preventiva de volume",
        platform="EC2 (EBS)",
        kind=RemediationKind.INFRA,
    ),
    "code_defect": RemediationAction(
        trigger="Erro recorrente rastreado a um commit",
        action="Correção de código via agente + Pull Request",
        platform="Devin · GitHub org",
        kind=RemediationKind.CODIGO,
    ),
    "config_drift": RemediationAction(
        trigger="Parâmetro divergente do baseline aprovado",
        action="Correção de configuração sob GMUD",
        platform="ServiceNow (GMUD) · SSM",
        kind=RemediationKind.CONFIG,
    ),
    "third_party_outage": RemediationAction(
        trigger="Degradação em serviço de terceiro",
        action="Escalonamento para o time/fornecedor dono",
        platform="ServiceNow (reatribuição)",
        kind=RemediationKind.EXTERNO,
    ),
}
