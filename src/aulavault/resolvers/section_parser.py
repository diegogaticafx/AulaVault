from urllib.parse import unquote
from bs4 import BeautifulSoup
from ..models import Module, Section


def parse_section_html(section: Section, session) -> list[Module]:
    if not section.html_content:
        return []

    soup = BeautifulSoup(section.html_content, "lxml")
    modules = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        full_url = session.abs_url(href) if session else href
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        link_text = a.get_text(strip=True)
        if not link_text:
            link_text = _filename_from_url(full_url)

        mod = Module(
            id=f"section_{section.id}_{len(modules)}",
            type="section_resource",
            name=link_text,
            url=full_url,
        )
        modules.append(mod)

    return modules


def _filename_from_url(url: str) -> str:
    path = url.split("?")[0].split("#")[0]
    filename = unquote(path.split("/")[-1])
    return filename or "recurso"
