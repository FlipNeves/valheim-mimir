"""Garante saída UTF-8 no console (Windows usa cp1252 por padrão e quebra
com acentos/símbolos como →, •, 📇). Chamar enable_utf8() no início dos
entrypoints (pipeline, chat, scripts)."""
import sys


def enable_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
