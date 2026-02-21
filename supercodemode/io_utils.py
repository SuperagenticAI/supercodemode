from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_artifact(payload: dict[str, Any], *, artifact_dir: str, prefix: str) -> str:
    root = Path(artifact_dir)
    root.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{prefix}_{ts}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)
