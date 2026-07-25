from enum import Enum


class Severity(str, Enum):
    """Anomaly severity classification (spec section 3)."""

    CRITICO = "critico"
    ALERTA = "alerta"
    PREDITIVO = "preditivo"


class DetectionAlgorithm(str, Enum):
    """Anomaly detection engine used to classify a metric (spec section 3, Datadog methodology)."""

    BASIC = "basic"
    AGILE = "agile"
    ROBUST = "robust"


class AnomalyOrigin(str, Enum):
    """Where the stimulus that opened the anomaly came from.

    The squad is not only metric-driven: an incident typed into ServiceNow by a
    human is as valid an entry point as a Datadog monitor firing.
    """

    DATADOG = "datadog"
    SERVICENOW = "servicenow"
    AGENDADO = "agendado"
    HUMANO = "humano"


class IncidentNature(str, Enum):
    """Whether the incident is a technical failure or a business outcome failure.

    A business incident (invoices not reconciled, orders not shipped) can happen
    with every infrastructure metric perfectly green — which is exactly why
    detection cannot rely on telemetry alone.
    """

    SISTEMICO = "sistemico"
    NEGOCIO = "negocio"
