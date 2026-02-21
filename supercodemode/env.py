from __future__ import annotations

def bootstrap_reference_paths() -> None:
    """Compatibility no-op.

    SuperCodeMode now relies on installed package dependencies (`gepa`, `mcp`)
    and does not modify import paths at runtime.
    """
    return
