from __future__ import annotations

# Optional pretty output dependencies.  Any failure means we fall back to plain text.
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    import pyfiglet
    _HAS_RICH = True
except Exception:  # pragma: no cover - noncritical
    _HAS_RICH = False
    Console = Panel = Table = box = pyfiglet = None
