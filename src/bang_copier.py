#!/usr/bin/env python3
"""Legacy compatibility shim.

All real logic now lives in the :mod:`bang_file_copier` package.  This
module simply exposes the same ``main()`` entry point so that any
scripts or imports referring to ``bang_copier`` continue to work until
those callers are updated.
"""

from __future__ import annotations

from bang_file_copier.cli import main


def _deprecated_main(argv=None):
    """Backward‑compatible wrapper with the old API."""
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
