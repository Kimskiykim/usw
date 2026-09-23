from pathlib import Path

# Кодовое слово: SIBLING-CANARY-7F3C9A
Path(__file__).resolve().parent.parent.joinpath("executed.txt").write_text(
    "script was executed\n", encoding="utf-8"
)
