"""RustFS service plugin package."""

from phlo_rustfs.plugin import RustfsServicePlugin
from phlo_rustfs.settings import RustfsSettings, get_settings

__all__ = ["RustfsServicePlugin", "RustfsSettings", "get_settings"]
__version__ = "0.2.4"
