from ..models import Module, ResolvedModule
from ..session import MoodleSession


def resolve(session: MoodleSession, module: Module) -> ResolvedModule:
    rm = ResolvedModule(module=module)
    try:
        soup = session.get_html(module.url)
        iframe = soup.find("iframe", src=True)
        if iframe:
            rm.links.append(session.abs_url(iframe["src"]))
            rm.has_content = True
        else:
            meta = soup.find("meta", attrs={"http-equiv": "refresh"})
            if meta and meta.get("content"):
                content = meta["content"]
                if "url=" in content.lower():
                    url_part = content.split("url=", 1)[1].split(";")[0].strip()
                    rm.links.append(session.abs_url(url_part))
                    rm.has_content = True
            else:
                a = soup.find("a", class_="btn-primary", href=True)
                if a:
                    rm.links.append(session.abs_url(a["href"]))
                    rm.has_content = True
    except Exception:
        rm.content_text = f"ERROR fetching URL module: {module.url}"
    return rm
