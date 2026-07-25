from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationAction:
    """One row of the anomaly → remediation mapping (spec section 4)."""

    trigger: str
    action: str
    aws_service: str


REMEDIATION_MAP: dict[str, RemediationAction] = {
    "cpu_spike": RemediationAction(
        trigger="CPU Spike > 90%",
        action="Escalonamento Horizontal (Out)",
        aws_service="ASG (Auto Scaling)",
    ),
    "lambda_error_rate": RemediationAction(
        trigger="Lambda Error > 5%",
        action="Rollback ou Update de Config",
        aws_service="AWS Lambda",
    ),
    "dns_timeout": RemediationAction(
        trigger="DNS Timeout",
        action="Failover de Rota",
        aws_service="Route 53",
    ),
}
