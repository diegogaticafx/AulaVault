from pathlib import Path
from urllib.parse import unquote
from .session import MoodleSession


def download_file(
    session: MoodleSession,
    url: str,
    dest_dir: Path,
    filename: str | None = None,
) -> Path | None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = unquote(url.split("/")[-1].split("?")[0])
    dest = dest_dir / sanitize_filename(filename)

    try:
        r = session.get_raw(url)
        dest.write_bytes(r.content)
        return dest
    except Exception:
        return None


def sanitize_filename(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    name = name.strip().strip(".")
    if not name:
        name = "unnamed"
    return name
