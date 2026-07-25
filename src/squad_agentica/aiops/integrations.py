"""Contracts for the corporate platforms the squad talks to. Not implemented.

Every class here is a `Protocol` — a structural interface. Nothing imports a
vendor SDK, deliberately: the package stays dependency-free (see `graph.py` for
the same decision about langgraph), and the domain depends on the shape of the
integration rather than on a specific client library. This is the ports side of
the hexagonal architecture; the adapters live outside this package.

Platforms, and what each one is the system of record for:

    ServiceNow   incidents, CMDB (configuration items), change requests (GMUD)
    Datadog      metrics, logs, traces, error tracking, monitors
    IUClick      the company's kanban board — bug cards and their columns
    Devin        the code agent that produces the patch
    GitHub org   source of truth for code; where the pull request lands
"""

from dataclasses import dataclass
from typing import Optional, Protocol


# ---------------------------------------------------------------------------
# Value objects exchanged with the platforms
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfigurationItem:
    """A CMDB entry: the thing that broke, as the company inventories it.

    `repository` is what makes code remediation possible at all — without the
    CMDB knowing which repo backs which service, the code agent has nothing to
    clone. In practice this is the field most likely to be missing or stale in
    a real CMDB, and the pipeline must degrade gracefully when it is.
    """

    ci_id: str
    name: str
    service: str
    owning_team: str
    repository: Optional[str]
    environment: str


@dataclass(frozen=True)
class ChangeRequest:
    """A GMUD. Opened automatically; approved by a human, never by an agent."""

    change_id: str
    ci_id: str
    summary: str
    risk: str
    window: str
    rollback_plan: str


@dataclass(frozen=True)
class PullRequest:
    repository: str
    number: int
    url: str
    branch: str
    files_changed: int
    summary: str


# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------


class ITSMClient(Protocol):
    """ServiceNow: incidents, CMDB and change management."""

    def get_configuration_item(self, ci_id: str) -> ConfigurationItem: ...

    def open_incident(self, summary: str, ci_id: str, severity: str) -> str: ...

    def open_change_request(self, ci_id: str, summary: str, risk: str) -> ChangeRequest: ...

    def close_incident(self, incident_id: str, resolution: str) -> None: ...

    def reassign_incident(self, incident_id: str, team: str, reason: str) -> None:
        """Escalation path: hand the incident back to the owning team."""
        ...


class KanbanClient(Protocol):
    """IUClick: the company's agile board."""

    def create_bug(self, title: str, description: str, incident_id: str) -> str: ...

    def move_card(self, task_id: str, column: str) -> None: ...


class ObservabilityClient(Protocol):
    """Datadog: the telemetry the squad reads to detect and to validate."""

    def query_metric(self, query: str, window_minutes: int) -> list[float]: ...

    def search_logs(self, query: str, window_minutes: int) -> list[dict]: ...

    def get_error_tracking_issue(self, issue_id: str) -> dict: ...


class CodeAgentClient(Protocol):
    """Devin: delegated code analysis and patch authoring.

    `start_session` sends incident context out to a third party. Everything it
    receives must pass through secret and PII redaction first — see
    `observability.REDACTION_REQUIRED_BEFORE_EGRESS`.
    """

    def start_session(self, repository: str, prompt: str, context: dict) -> str: ...

    def fetch_result(self, session_id: str) -> Optional[PullRequest]: ...


class SourceControlClient(Protocol):
    """GitHub organization: clone to analyse, pull request to deliver."""

    def clone(self, repository: str, ref: str) -> str: ...

    def open_pull_request(self, repository: str, branch: str, title: str, body: str) -> PullRequest: ...

    def get_checks(self, repository: str, branch: str) -> dict: ...


# ---------------------------------------------------------------------------
# Registry — what the prototype's "Integrações" screen renders
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Integration:
    platform: str
    role: str
    reads: str
    writes: str
    automatic: bool
    """False when the write requires human approval before taking effect."""


INTEGRATIONS: tuple[Integration, ...] = (
    Integration(
        platform="ServiceNow",
        role="Registro, CMDB e gestão de mudança",
        reads="Incidentes abertos, item de configuração, time dono",
        writes="Anomalia correlacionada, GMUD aberta, incidente encerrado",
        automatic=True,
    ),
    Integration(
        platform="Datadog",
        role="Observabilidade dos sistemas monitorados",
        reads="Métricas, logs, traces, error tracking, monitores",
        writes="Evento de anomalia e janela de validação",
        automatic=True,
    ),
    Integration(
        platform="IUClick",
        role="Kanban do processo ágil",
        reads="Coluna atual do card",
        writes="Bug criado e movido conforme o incidente avança",
        automatic=True,
    ),
    Integration(
        platform="Devin",
        role="Agente de código",
        reads="Sessão, diagnóstico e trecho de código relevante",
        writes="Patch proposto",
        automatic=True,
    ),
    Integration(
        platform="GitHub (org)",
        role="Versionamento e entrega",
        reads="Repositório do CI afetado, checks de CI",
        writes="Pull request — merge sempre sob aprovação humana",
        automatic=False,
    ),
    Integration(
        platform="AWS",
        role="Execução de ações de infraestrutura",
        reads="Estado de ASG, Lambda, Route 53, EBS",
        writes="Ação de remediação aplicada",
        automatic=True,
    ),
)
