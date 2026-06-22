from ..models import Module, ResolvedModule
from ..session import MoodleSession


def resolve(session: MoodleSession, module: Module) -> ResolvedModule:
    rm = ResolvedModule(module=module)
    try:
        soup = session.get_html(module.url)
        content = soup.find("div", class_="content")
        if content:
            rm.content_html = str(content)
            rm.content_text = content.get_text(strip=True)
            rm.has_content = True
    except Exception:
        pass
    return rm
