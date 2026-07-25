"""FinOps / model governance constants (spec section 5). Reference values only."""

GOLD_MODEL = "qwen2.5-coder:32b"
MINIMUM_VIABLE_MODEL = "qwen2.5:7b"

TEMPERATURE_VALIDATOR = 0.1
TEMPERATURE_COACH = 0.4
TEMPERATURE_EXPLAINER = 0.4

LOCAL_VRAM_GB_32B = 24
LOCAL_VRAM_GB_7B = 8
