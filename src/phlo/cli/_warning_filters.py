"""Startup warning filters for Phlo CLI."""

from __future__ import annotations

import warnings

warnings.filterwarnings(
    "ignore",
    message=r"urllib3 .* or chardet.*/charset_normalizer .* doesn't match a supported version!",
    module=r"requests(\..*)?$",
)
