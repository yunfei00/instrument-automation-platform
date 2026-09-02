"""Temporary stable DSO-X panel compatibility layer.

The writable Channel/Trigger panel introduced in PR #13 is temporarily disabled
because a real Windows/PySide6 run reported a native process exit when refreshing
an otherwise hardware-verified screenshot.  Keep the backend Driver/Operation
controls available, but restore the exact previously verified DSOX3000Panel Qt
surface until the new controls are reintroduced by composition and verified on
real hardware.
"""

from __future__ import annotations

from .dsox_control_operations import ensure_dsox_control_operations_registered
from .gui_panels import DSOX3000Panel


# Backend operations remain registered for generic Instrument Operations / tests.
ensure_dsox_control_operations_registered()

# Important: use the exact previously hardware-verified Qt panel object instead
# of subclassing it.  This removes the PR #13 UI extension from the screenshot
# render path without reverting the new reusable Driver/Operation APIs.
DSOX3000ControlPanel = DSOX3000Panel
