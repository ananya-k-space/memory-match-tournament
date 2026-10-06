"""Generate scoring.js (used by index.html) from scoring.json (used by memory_game.py).

scoring.json is the single source of truth for scoring rules and difficulty levels.
Run this after editing it:  python sync_scoring.py
"""
import json
from pathlib import Path

root = Path(__file__).parent
data = json.loads((root / "scoring.json").read_text(encoding="utf-8"))
js = (
    "// AUTO-GENERATED from scoring.json by sync_scoring.py - do not edit by hand\n"
    "const SCORING = " + json.dumps(data, indent=2) + ";\n"
)
(root / "scoring.js").write_text(js, encoding="utf-8")
print("scoring.js updated")
