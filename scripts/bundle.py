from pathlib import Path

import stickytape

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT = PROJECT_ROOT / "dungeon_stats_display.py"
ENTRY = PROJECT_ROOT / "main.py"

output = stickytape.script(
    str(ENTRY),
    add_python_paths=[str(SRC_DIR)],
)

OUTPUT.write_text(output, encoding="utf-8")
size = OUTPUT.stat().st_size
print(f"Done! {OUTPUT} ({size:,} bytes)")
