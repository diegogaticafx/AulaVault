from bs4 import BeautifulSoup
from ..models import Module, ResolvedModule, ResolvedFile
from ..session import MoodleSession


def resolve(session: MoodleSession, module: Module) -> ResolvedModule:
    rm = ResolvedModule(module=module)
    try:
        soup = session.get_html(module.url)

        desc_div = soup.find("div", class_="no-overflow")
        if desc_div:
            rm.content_html = str(desc_div)
            rm.content_text = desc_div.get_text(strip=True)
            rm.has_content = True

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/pluginfile.php/" in href and "/assignsubmission_file/" in href:
                full_url = session.abs_url(href)
                filename = href.split("/")[-1].split("?")[0]
                rm.files.append(ResolvedFile(filename=filename, url=full_url))
                rm.has_content = True
    except Exception:
        rm.content_text = f"ERROR fetching assignment: {module.url}"
    return rm
