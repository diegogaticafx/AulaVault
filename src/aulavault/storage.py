import json
from pathlib import Path
from urllib.parse import unquote
from .models import Course, ResolvedModule


def save_course(base_dir: Path, course: Course, results: list[ResolvedModule]):
    course_dir = base_dir / f"{sanitize(course.name)} - {course.id}"
    course_dir.mkdir(parents=True, exist_ok=True)

    has_files = any(rm.files for rm in results)
    if has_files:
        (course_dir / "files").mkdir(exist_ok=True)
        for rm in results:
            if rm.files:
                module_dir = course_dir / "files" / f"{sanitize(rm.module.name)} - {rm.module.id}"
                module_dir.mkdir(parents=True, exist_ok=True)
                for f in rm.files:
                    if f.filepath:
                        src = Path(f.filepath)
                        if src.exists():
                            dst = module_dir / sanitize(unquote(f.filename))
                            if not dst.exists():
                                dst.write_bytes(src.read_bytes())


def sanitize(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name.strip().strip(".") or "unnamed"
