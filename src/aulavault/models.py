from pydantic import BaseModel, Field
from typing import Optional


class SessionData(BaseModel):
    moodle_session: str
    sesskey: str
    base_url: str = "https://aulasvirtuales.santotomas.cl"


class Course(BaseModel):
    id: int
    name: str
    sections: list["Section"] = []


class Section(BaseModel):
    id: str
    title: str
    section: int
    modules: list["Module"] = []


class Module(BaseModel):
    id: str
    type: str
    name: str
    url: str


class ResolvedFile(BaseModel):
    filename: str
    url: str
    filepath: str = ""
    size: int = 0
    downloaded: bool = False


class ResolvedModule(BaseModel):
    module: Module
    files: list[ResolvedFile] = []
    links: list[str] = []
    content_text: str = ""
    content_html: str = ""
    has_content: bool = False


class DownloadProgress(BaseModel):
    course_id: int
    course_name: str
    module_name: str
    module_type: str
    current_file: str = ""
    files_total: int = 0
    files_done: int = 0
    status: str = "pending"
