import sys
from .models import SessionData
from .session import MoodleSession
from .course_graph import fetch_courses, build_course_graph
from .resolver import resolve_module
from .resolvers.section_parser import parse_section_html


def main():
    if "--headless" in sys.argv or "--debug" in sys.argv:
        run_headless()
    else:
        from .app import AulaVaultApp
        app = AulaVaultApp()
        app.run()


def run_headless():
    print("=== AulaVault Headless Debug ===")
    base_url = input("URL base de Moodle (ej: https://moodle.miuniversidad.cl): ").strip().rstrip("/") or "https://moodle.miuniversidad.cl"
    moodle_session = input("MoodleSession cookie: ").strip()
    sesskey = input("sesskey: ").strip()

    data = SessionData(moodle_session=moodle_session, sesskey=sesskey, base_url=base_url)
    ms = MoodleSession(data)

    print("\n[1/3] Verificando sesión...")
    if not ms.verify():
        print("[ERROR] Sesión inválida. Revisa los valores.")
        ms.close()
        return
    print("[OK] Sesión válida\n")

    print("[2/3] Obteniendo lista de cursos...")
    try:
        courses = fetch_courses(ms)
        print(f"[OK] {len(courses)} cursos encontrados:\n")
        for c in courses:
            print(f"  [{c.id}] {c.name}")
    except Exception as e:
        print(f"[ERROR] {e}")
        ms.close()
        return

    print("\n[3/3] Probando resolvers en cada curso...")
    for c in courses:
        print(f"\n  --- {c.name} (id={c.id}) ---")
        try:
            graph = build_course_graph(ms, c.id, c.name)
            if not graph:
                print("  [WARN] No se pudo construir el grafo")
                continue

            types = {}
            for s in graph.sections:
                for m in s.modules:
                    types[m.type] = types.get(m.type, 0) + 1
            print(f"  sections={len(graph.sections)}, modules={sum(types.values())}")
            print(f"  types: {types}")

            section_count = sum(1 for s in graph.sections if s.html_content)
            print(f"  sections with HTML content: {section_count}")

            label_with_desc = sum(1 for s in graph.sections for m in s.modules if m.type == "label" and m.description)
            print(f"  labels with description: {label_with_desc}")

            shown = set()
            for s in graph.sections:
                for m in s.modules:
                    if m.type not in ("resource", "assign", "url", "label"):
                        continue
                    key = f"{m.type}:{m.id}"
                    if key in shown:
                        continue
                    shown.add(key)

                    resolved = resolve_module(ms, m)
                    n_files = len(resolved.files)
                    n_links = len(resolved.links)
                    has_text = bool(resolved.content_text[:50]) if resolved.content_text else False
                    mark = ""
                    if n_files:
                        mark = f" [green]{n_files} file(s)[/green]"
                    elif n_links:
                        mark = f" [blue]{n_links} link(s)[/blue]"
                    elif has_text:
                        mark = " [yellow]text[/yellow]"
                    else:
                        mark = " [red]EMPTY[/red]"

                    print(f"    [{m.type}] {m.name[:60]}{mark}")
                    if n_files:
                        for f in resolved.files[:3]:
                            print(f"      → {f.filename}")
                    elif m.type == "label" and m.description:
                        desc_preview = m.description[:100].replace("\n", " ")
                        print(f"      desc: {desc_preview}...")

            for s in graph.sections:
                if s.html_content:
                    section_mods = parse_section_html(s, ms)
                    if section_mods:
                        print(f"\n  Section '{s.title}' - {len(section_mods)} embedded links:")
                        for m in section_mods[:5]:
                            resolved = resolve_module(ms, m)
                            n_files = len(resolved.files)
                            n_links = len(resolved.links)
                            mark = ""
                            if n_files:
                                mark = f" [green]{n_files} file(s)[/green]"
                            elif n_links:
                                mark = f" [blue]{n_links} link(s)[/blue]"
                            else:
                                mark = " [red]EMPTY[/red]"
                            print(f"    [section_resource] {m.name[:60]}{mark}")
                            if n_files:
                                for f in resolved.files[:3]:
                                    print(f"      → {f.filename}")
                        if len(section_mods) > 5:
                            print(f"    ... and {len(section_mods) - 5} more")

        except Exception as e:
            print(f"  [ERROR] {e}")

    ms.close()
    print("\n=== Fin del debug ===")


if __name__ == "__main__":
    main()
