"""Untrusted fixture provider module.

Must NEVER be imported by static validation. If any validation path
imports provider code, this module leaves a marker file behind and the
no-import proof test fails.
"""

from pathlib import Path

_MARKER = Path(__file__).with_name("imported.marker")
_MARKER.write_text("imported at import time; static validation must never do this")
