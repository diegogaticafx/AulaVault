from urllib.parse import urljoin, unquote
from ..models import Module, ResolvedModule, ResolvedFile
from ..session import MoodleSession


def resolve(session: MoodleSession, module: Module) -> ResolvedModule:
    rm = ResolvedModule(module=module)
    try:
        r = session.get_response(module.url)
        content_type = r.headers.get("content-type", "")

        # Check redirect history for pluginfile URLs
        for resp in r.history:
            if "/pluginfile.php/" in str(resp.url):
                url = str(resp.url)
                filename = unquote(url.split("/")[-1].split("?")[0])
                rm.files.append(ResolvedFile(filename=filename, url=url))
                rm.has_content = True

        # If final response is a file (not HTML), capture it
        if "text/html" not in content_type and not rm.files:
            url = str(r.url)
            filename = unquote(url.split("/")[-1].split("?")[0])
            rm.files.append(ResolvedFile(filename=filename, url=url))
            rm.has_content = True
            return rm

        # Parse HTML for pluginfile links
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/pluginfile.php/" in href:
                full_url = _abs_url(href)
                filename = unquote(href.split("/")[-1].split("?")[0].split("#")[0])
                if filename and "." in filename:
                    rm.files.append(ResolvedFile(filename=filename, url=full_url))
                    rm.has_content = True

        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            if "/pluginfile.php/" in src:
                full_url = _abs_url(src)
                filename = unquote(src.split("/")[-1].split("?")[0])
                if filename and "." in filename:
                    rm.files.append(ResolvedFile(filename=filename, url=full_url))
                    rm.has_content = True

    except Exception as e:
        rm.content_text = f"ERROR: {e}"
    return rm


def _abs_url(path: str) -> str:
    if path.startswith("http"):
        return path
    return urljoin("https://aulasvirtuales.santotomas.cl", path)
