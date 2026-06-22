import json
from pathlib import Path
from urllib.parse import unquote
from .models import Course, ResolvedModule


def save_course(base_dir: Path, course: Course, results: list[ResolvedModule]):
    course_dir = base_dir / f"{sanitize(course.name)} - {course.id}"
    course_dir.mkdir(parents=True, exist_ok=True)

    (course_dir / "files").mkdir(exist_ok=True)

    course_data = course.model_dump()
    (course_dir / "course.json").write_text(
        json.dumps(course_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for rm in results:
        module_dir = course_dir / "files" / f"{sanitize(rm.module.name)} - {rm.module.id}"
        module_dir.mkdir(parents=True, exist_ok=True)

        info = {
            "type": rm.module.type,
            "name": rm.module.name,
            "url": rm.module.url,
            "files": [f.model_dump() for f in rm.files],
            "links": rm.links,
            "content_text": rm.content_text[:500] if rm.content_text else "",
        }
        (module_dir / "info.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    (course_dir / "files").mkdir(exist_ok=True)
    for rm in results:
        if rm.files:
            mod_dir = course_dir / "files" / f"{sanitize(rm.module.name)} - {rm.module.id}"
            for f in rm.files:
                if f.filepath:
                    src = Path(f.filepath)
                    if src.exists():
                        dst = mod_dir / sanitize(unquote(f.filename))
                        if not dst.exists():
                            dst.write_bytes(src.read_bytes())


def sanitize(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name.strip().strip(".") or "unnamed"
