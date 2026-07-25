"""Observability contract for the agentic pipeline itself (LLMOps).

There are two distinct observability problems in this system and confusing them
is the most common mistake:

1. **Observability of the monitored systems** — Datadog metrics and logs of the
   applications the squad watches. That is the squad's *input*, and it lives in
   `integrations.ObservabilityClient`.

2. **Observability of the squad** — traces of the agents' own reasoning: which
   prompt version ran, how many tokens it burned, what the model answered, how
   long each node took, and whether the diagnosis was right. That is this
   module, and it is what makes an autonomous pipeline auditable.

The two are joined by a single `trace_id` that also reaches the ServiceNow
incident, so an auditor can go from "why did the system revert my deploy at 3am"
straight to the exact model call that decided it.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# --- Project / service identity -------------------------------------------

LANGFUSE_PROJECT = "easyrun-aiops"
LANGSMITH_PROJECT = "easyrun-aiops"
DATADOG_SERVICE = "easyrun-squad"
DATADOG_ENV_TAG = "env"

# --- Egress policy ---------------------------------------------------------

REDACTION_REQUIRED_BEFORE_EGRESS = True
"""Source code and logs must be stripped of secrets and PII before leaving.

Delegating a fix to an external code agent means company source code crosses an
organizational boundary. This flag exists so the decision is explicit in the
contract instead of buried in an adapter — the pipeline must refuse to call
`CodeAgentClient.start_session` when redaction has not run.
"""

REPOSITORY_ALLOWLIST_REQUIRED = True
"""Only repositories explicitly allowlisted may be sent to the code agent."""


class Stage(str, Enum):
    """Where a prompt or agent version sits in its promotion path."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass(frozen=True)
class PromptRef:
    """A prompt as a versioned artifact, never a string literal in the code.

    Prompts change behaviour as much as code does. Treating them as artifacts —
    versioned, promoted per stage, referenced by id — is what makes it possible
    to answer "which prompt produced this decision?" three months later.
    """

    name: str
    version: int
    stage: Stage


@dataclass(frozen=True)
class TraceContext:
    """Correlation across the whole toolchain for one incident run."""

    trace_id: str
    incident_id: str
    servicenow_incident_id: Optional[str] = None
    langfuse_url: Optional[str] = None
    langsmith_run_id: Optional[str] = None
    datadog_trace_url: Optional[str] = None


@dataclass(frozen=True)
class AgentRunMetrics:
    """What is recorded for every agent node execution."""

    agent: str
    prompt: PromptRef
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    tool_calls: int = 0
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
