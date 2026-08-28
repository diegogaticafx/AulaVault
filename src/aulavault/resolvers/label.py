from urllib.parse import unquote
from bs4 import BeautifulSoup
from ..models import Module, ResolvedModule, ResolvedFile
from ..session import MoodleSession


def resolve(session: MoodleSession, module: Module) -> ResolvedModule:
    rm = ResolvedModule(module=module)
    try:
        html_content = module.description

        if html_content:
            soup = BeautifulSoup(html_content, "lxml")

            rm.content_text = soup.get_text(strip=True)
            rm.has_content = True

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/pluginfile.php/" in href:
                    full_url = session.abs_url(href) if session else href
                    filename = unquote(href.split("/")[-1].split("?")[0].split("#")[0])
                    if filename:
                        rm.files.append(ResolvedFile(filename=filename, url=full_url))
                elif href.startswith("http") and any(ext in href.lower() for ext in [".pdf", ".pptx", ".docx", ".xlsx", ".zip", ".rar", ".exe", ".txt"]):
                    rm.files.append(ResolvedFile(
                        filename=unquote(href.split("/")[-1].split("?")[0].split("#")[0]),
                        url=href,
                    ))
                elif "/mod/resource/view.php" in href or "/mod/url/view.php" in href:
                    rm.links.append(session.abs_url(href) if session else href)
                elif href.startswith("http"):
                    link_text = a.get_text(strip=True)
                    if link_text and any(kw in link_text.lower() for kw in ["instalador", "descargar", "download", "acceso"]):
                        rm.links.append(href)

    except Exception:
        pass
    return rm
