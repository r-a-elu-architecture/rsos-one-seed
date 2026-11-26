"""Compatibility import: the State Runtime moved to rsoslang.core.state (Core v1). This module is that module."""
import sys

from rsoslang.core import state as _impl

sys.modules[__name__] = _impl
