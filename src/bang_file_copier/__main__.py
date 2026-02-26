"""Package entry point for ``python -m bang_file_copier``.

This module makes the package executable with ``python -m``.  It simply
imports and calls ``main`` from :mod:`cli` so that the behaviour matches
running the ``bang`` console script.
"""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":  # pragma: no cover - simple forwarder
    raise SystemExit(main())
