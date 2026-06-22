from .models import Course, Section, Module
from .session import MoodleSession


def fetch_courses(session: MoodleSession) -> list[Course]:
    data = session.ajax("core_course_get_enrolled_courses_by_timeline_classification", {
        "offset": 0, "limit": 0, "classification": "all", "sort": "fullname",
        "customfieldname": "", "customfieldvalue": "",
    })
    if not data:
        return []
    courses = data["courses"]
    return [Course(id=int(c["id"]), name=c["fullname"]) for c in courses]


def build_course_graph(session: MoodleSession, course_id: int, course_name: str = "") -> Course | None:
    data = session.ajax("core_courseformat_get_state", {"courseid": course_id})
    if not data:
        return None

    course_info = data.get("course", {})
    name = course_name or course_info.get("fullname", f"Course {course_id}")
    course = Course(id=int(course_info.get("id", course_id)), name=name)

    section_list = data.get("section", [])
    cm_list = data.get("cm", [])

    cm_by_id: dict[str, dict] = {}
    for cm in cm_list:
        cm_by_id[str(cm.get("id", ""))] = cm

    for sec_data in section_list:
        section = Section(
            id=str(sec_data.get("id", "")),
            title=sec_data.get("title", ""),
            section=sec_data.get("section", 0),
        )

        cm_ids = [str(x) for x in sec_data.get("cmlist", [])]
        for cm_id in cm_ids:
            cm = cm_by_id.get(cm_id)
            if cm:
                mod_type = cm.get("module", cm.get("modname", ""))
                mod = Module(
                    id=str(cm["id"]),
                    type=mod_type,
                    name=cm.get("name", ""),
                    url=cm.get("url", ""),
                )
                section.modules.append(mod)

        course.sections.append(section)

    return course
