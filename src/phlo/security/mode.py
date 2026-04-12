"""Regulated mode detection.

Checks the PHLO_REGULATED_MODE environment variable and optional config file
setting to determine whether regulated mode is active.
"""

from __future__ import annotations

import os

PHLO_REGULATED_MODE_ENV = "PHLO_REGULATED_MODE"


def is_regulated_mode_enabled(config_regulated_mode: bool | None = None) -> bool:
    """Check if regulated mode is enabled.

    Precedence:
        1. PHLO_REGULATED_MODE environment variable
        2. phlo.yaml root regulated_mode setting
        3. Default (False)
    """
    env_value = os.environ.get(PHLO_REGULATED_MODE_ENV, "").strip().lower()
    if env_value in ("1", "true", "yes", "on"):
        return True
    if env_value in ("0", "false", "no", "off"):
        return False

    if config_regulated_mode is not None:
        return config_regulated_mode

    from phlo.infrastructure.config import get_regulated_mode_config

    configured_value = get_regulated_mode_config()
    if configured_value is not None:
        return configured_value

    return False
