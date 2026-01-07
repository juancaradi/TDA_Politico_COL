# src/utils/text.py
from __future__ import annotations

import re


def normalize_whitespace(s: str) -> str:
    if not s:
        return s
    return re.sub(r"\s+", " ", s).strip()


def fix_mojibake_best_effort(s: str) -> str:
    """
    Arreglo best-effort para textos tipo:
    'me CagÃ© NicolÃ¡s' -> 'me Cagué Nicolás'
    Esto ocurre cuando UTF-8 se interpreta como Latin-1.

    NOTA: Se conserva en el proyecto, pero NO se aplica en extracción por defecto.
    """
    if not s:
        return s
    if ("Ã" in s) or ("Â" in s) or ("â" in s):
        try:
            return s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            return s
    return s
