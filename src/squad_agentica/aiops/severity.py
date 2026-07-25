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
