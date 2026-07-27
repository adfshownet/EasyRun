"""Stub describing the intended LangGraph wiring (spec section 4). Not implemented.

Intended flow, with the conditional routing that `remediation_kind` introduces::

    TraceabilityNode           # abre INC/Bug, resolve o CI e o repositório
      -> Planner
      -> Explainer             # causa raiz
      -> classify_remediation  # decide o ramo
           |
           +-- INFRA    -> [interrupt() se hitl_required] -> Executor
           +-- CONFIG   -> TraceabilityNode(GMUD) -> interrupt() -> Executor
           +-- CODIGO   -> CodeRemediationNode     # clona, delega, abre PR
           |               -> TraceabilityNode(GMUD)
           |               -> interrupt()          # aprovação do PR
           |               -> interrupt()          # aprovação da GMUD
           |               -> Executor             # merge e deploy
           +-- EXTERNO  -> escalate
      -> Validator             # eficácia pós-execução
      -> TraceabilityNode      # move o kanban, encerra o incidente
      -> Coach

Two engineering notes worth keeping in front of whoever implements this:

* The CODIGO branch interrupts **twice**, for two different decisions taken by
  possibly two different people — approving a code change is not the same
  authority as approving a production change window. Each interrupt must return
  the full AgentState (see `roles.request_human_approval`).
* `TraceabilityNode` appears three times on purpose. Corporate records are not a
  final step: the bug is opened at the start, the change request in the middle,
  the closure at the end. Batching them all to the end would leave the incident
  invisible to everyone outside this tool while it is being worked on.

State ownership (docs/06, "O contrato de propriedade do estado"):

* The graph built here is **ephemeral, scoped to one Step Functions task
  invocation**. It receives the incident state as input, reasons, and returns
  the serialized AgentState as the task output. There is no graph checkpoint
  that survives across invocations.
* Every `interrupt()` above ends the current task invocation. The long wait for
  the human decision belongs to Step Functions (task token /
  ``waitForTaskToken``), never to the graph. Step Functions is the single owner
  of the durable incident state; the graph owns it only while its task runs.

Deliberately does not import langgraph — this module only documents the shape
for a future real implementation, and keeps the package dependency-free.
"""


def build_graph():
    raise NotImplementedError
