from pathlib import Path
from .models import Course, ResolvedModule


def sanitize(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name.strip().strip(".") or "unnamed"
