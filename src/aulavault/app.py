from pathlib import Path
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Input, ListView, ListItem, RichLog, ProgressBar, Static, Label, Tree
from textual.containers import Horizontal, Vertical
from textual import work

from .models import SessionData, Course, Module
from .session import MoodleSession
from .course_graph import fetch_courses, build_course_graph
from .resolver import resolve_module
from .downloader import download_file
from .storage import save_course


ICONS = {
    "resource": "\U0001F4C4",
    "url": "\U0001F517",
    "assign": "\U0001F4DD",
    "label": "\U0001F3F7",
    "forum": "\U0001F4AC",
    "feedback": "\U0001F4CB",
    "quiz": "\U00002753",
    "adaptivequiz": "\U0001F9D0",
    "default": "\U0001F4CB",
}


def module_icon(mtype: str) -> str:
    return ICONS.get(mtype, ICONS["default"])


def sanitize(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name.strip().strip(".") or "unnamed"


# ────────────────────────────── Auth Screen ──────────────────────────────


class AuthScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("AulaVault - Moodle Course Extractor", id="title"),
            Label("Paso 1: Inicia sesión en tu Moodle en el navegador", classes="instruction"),
            Input(placeholder="URL de tu Moodle (ej: https://moodle.miuniversidad.cl)", id="base-url", value=""),
            Label("Paso 2: Abre DevTools (F12) \u2192 Application \u2192 Cookies \u2192 copia los valores:", classes="instruction"),
            Label("", classes="instruction"),
            Label("\u2022 MoodleSession: el valor de la cookie MoodleSession", classes="hint"),
            Label("\u2022 sesskey: búscalo en la URL como ?sesskey=XXXXX", classes="hint"),
            Label("", classes="instruction"),
            Input(placeholder="MoodleSession (cópialo de DevTools \u2192 Cookies)", id="moodle-session"),
            Input(placeholder="sesskey (cópialo de la URL ?sesskey=XXXXX)", id="sesskey"),
            Button("Conectar", variant="primary", id="connect-btn"),
            Static(id="auth-status"),
            id="auth-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "connect-btn":
            session_val = self.query_one("#moodle-session", Input).value.strip()
            sesskey_val = self.query_one("#sesskey", Input).value.strip()
            base_url_val = self.query_one("#base-url", Input).value.strip().rstrip("/")
            status = self.query_one("#auth-status", Static)

            if not session_val or not sesskey_val or not base_url_val:
                status.update("[red]Todos los campos son obligatorios[/red]")
                return

            status.update("[yellow]Verificando sesión...[/yellow]")
            self._do_connect(session_val, sesskey_val, base_url_val)

    @work(thread=True)
    def _do_connect(self, session_val: str, sesskey_val: str, base_url_val: str):
        data = SessionData(moodle_session=session_val, sesskey=sesskey_val, base_url=base_url_val)
        ms = MoodleSession(data)
        if ms.verify():
            ms.close()
            self.app.call_from_thread(self.app.push_screen, MainScreen(data))
        else:
            ms.close()
            status = self.app.call_from_thread(self.query_one, "#auth-status", Static)
            self.app.call_from_thread(status.update, "[red]Sesión inválida. Revisa los valores.[/red]")


# ────────────────────────────── Main Screen ──────────────────────────────


class MainScreen(Screen):
    def __init__(self, session_data: SessionData):
        super().__init__()
        self.session_data = session_data
        self.session: MoodleSession | None = None
        self.courses: list[Course] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Label("Cursos", classes="panel-title"),
                ListView(id="course-list"),
                Horizontal(
                    Button("Actualizar", id="refresh-btn"),
                    Button("Seleccionar Módulos", variant="primary", id="select-btn"),
                    Button("Descargar Todo", id="download-all-btn"),
                    id="action-bar",
                ),
                classes="panel-left",
            ),
            Vertical(
                RichLog(id="log-panel", highlight=True, markup=True),
                ProgressBar(total=100, id="progress-bar"),
                Static(id="status-text"),
                classes="panel-right",
            ),
        )
        yield Footer()

    def on_mount(self):
        self.session = MoodleSession(self.session_data)
        self._load_courses()

    @work(thread=True)
    def _load_courses(self):
        log = self.app.call_from_thread(self.query_one, "#log-panel", RichLog)
        self.app.call_from_thread(log.write, "[blue]Obteniendo lista de cursos...[/blue]")
        try:
            courses = fetch_courses(self.session)
            self.app.call_from_thread(self._display_courses, courses)
            self.app.call_from_thread(log.write, f"[green]\u2713 {len(courses)} cursos encontrados[/green]")
        except Exception as e:
            self.app.call_from_thread(log.write, f"[red]Error al obtener cursos: {e}[/red]")

    def _display_courses(self, courses: list[Course]):
        self.courses = courses
        lv = self.query_one("#course-list", ListView)
        lv.clear()
        for c in courses:
            lv.append(ListItem(Label(c.name)))
        self.query_one("#status-text", Static).update(f"[green]{len(courses)} cursos cargados[/green]")

    def _get_selected_course(self) -> Course | None:
        lv = self.query_one("#course-list", ListView)
        idx = lv.index
        if idx is not None and 0 <= idx < len(self.courses):
            return self.courses[idx]
        return None

    def on_button_pressed(self, event: Button.Pressed):
        btn = event.button
        if btn.id == "refresh-btn":
            self._load_courses()
        elif btn.id == "select-btn":
            course = self._get_selected_course()
            if not course:
                self.query_one("#status-text", Static).update("[yellow]Selecciona un curso primero[/yellow]")
                return
            self._open_selector(course)
        elif btn.id == "download-all-btn":
            self._start_download_all()

    def _open_selector(self, course: Course):
        log = self.query_one("#log-panel", RichLog)
        log.write(f"[bold]Cargando m\u00f3dulos de:[/bold] {course.name}")
        self.query_one("#status-text", Static).update(f"Construyendo grafo del curso...")
        self._build_and_show_selector(course)

    @work(thread=True)
    def _build_and_show_selector(self, course: Course):
        session = MoodleSession(self.session_data)
        try:
            graph = build_course_graph(session, course.id, course.name)
            session.close()
            if not graph:
                self.app.call_from_thread(
                    self.query_one("#status-text", Static).update,
                    "[red]Error al construir el curso[/red]",
                )
                return
            self.app.call_from_thread(
                self.app.push_screen,
                ModuleSelectScreen(self.session_data, graph),
            )
        except Exception as e:
            session.close()
            self.app.call_from_thread(
                self.query_one("#status-text", Static).update,
                f"[red]Error: {e}[/red]",
            )

    def _start_download_all(self):
        if not self.courses:
            return
        self.run_pipeline(self.session_data, [(c.id, c.name) for c in self.courses])

    @work(thread=True)
    def run_pipeline(self, session_data: SessionData, course_list: list[tuple[int, str]]):
        session = MoodleSession(session_data)
        log = self.app.call_from_thread(self.query_one, "#log-panel", RichLog)
        progress = self.app.call_from_thread(self.query_one, "#progress-bar", ProgressBar)
        status = self.query_one("#status-text", Static)

        total_courses = len(course_list)
        base_dir = Path("courses")

        for ci, (course_id, course_name) in enumerate(course_list):
            self.app.call_from_thread(log.write, f"\n[bold cyan]\u25b6 [{ci+1}/{total_courses}] {course_name}[/bold cyan]")
            self.app.call_from_thread(progress.update, progress=0)
            self.app.call_from_thread(status.update, f"Procesando: {course_name}")

            try:
                course = build_course_graph(session, course_id, course_name)
                if not course:
                    self.app.call_from_thread(log.write, "[red]  \u2717 No se pudo obtener estructura del curso[/red]")
                    continue
            except Exception as e:
                self.app.call_from_thread(log.write, f"[red]  \u2717 Error: {e}[/red]")
                continue

            all_modules = [
                m for s in course.sections for m in s.modules
                if m.type in ("resource", "url", "assign", "label")
            ]
            total_modules = len(all_modules)

            resolved_modules = []
            for mi, module in enumerate(all_modules):
                self.app.call_from_thread(
                    status.update,
                    f"{course_name}: [{mi+1}/{total_modules}] {module.type} - {module.name[:60]}",
                )
                self.app.call_from_thread(progress.update, progress=int((mi + 1) / total_modules * 100))

                resolved = resolve_module(session, module)
                for f in resolved.files:
                    dest_dir = Path("downloads") / sanitize(f"{course.name} {course.id}")
                    path = download_file(session, f.url, dest_dir / sanitize(f"{module.name}-{module.id}"))
                    if path:
                        f.downloaded = True
                        f.filepath = str(path)
                        self.app.call_from_thread(log.write, f"  [green]\u2713[/green] {f.filename}")
                    else:
                        self.app.call_from_thread(log.write, f"  [red]\u2717[/red] {f.filename}")

                if resolved.links:
                    for link in resolved.links:
                        self.app.call_from_thread(log.write, f"  [blue]\u2192[/blue] {link[:80]}")

                resolved_modules.append(resolved)

            try:
                save_course(base_dir, course, resolved_modules)
                self.app.call_from_thread(
                    log.write,
                    f"[green]  \u2713 Curso guardado en courses/{sanitize(course.name)} {course.id}/[/green]",
                )
            except Exception as e:
                self.app.call_from_thread(log.write, f"[red]  \u2717 Error guardando curso: {e}[/red]")

        session.close()
        self.app.call_from_thread(progress.update, progress=100)
        self.app.call_from_thread(status.update, "[bold green]\u00a1Completado![/bold green]")
        self.app.call_from_thread(log.write, "\n[bold green]\u2713 Proceso finalizado[/bold green]")


# ────────────────────────────── Module Select Screen ──────────────────────────────


class ModuleSelectScreen(Screen):
    def __init__(self, session_data: SessionData, course: Course):
        super().__init__()
        self.session_data = session_data
        self.course = course
        self.selected: dict[str, bool] = {}
        self.downloading = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Label(f"Curso: {self.course.name}", id="module-course-name"),
                Tree("M\u00f3dulos", id="module-tree"),
                id="selector-left",
            ),
            Vertical(
                RichLog(id="dl-log", highlight=True, markup=True),
                ProgressBar(total=100, id="dl-progress"),
                Static(id="dl-status"),
                id="selector-right",
            ),
            id="selector-split",
        )
        yield Horizontal(
            Button("Select All", id="select-all-btn"),
            Button("Descargar Seleccionados (0)", variant="primary", id="dl-selected-btn"),
            Button("Volver", id="back-btn"),
            id="selector-actions",
        )
        yield Footer()

    def on_mount(self):
        self._build_tree()

    def _build_tree(self):
        tree = self.query_one("#module-tree", Tree)
        tree.root.expand()

        for section in self.course.sections:
            sec_label = section.title if section.title else f"Section {section.section}"
            sec_node = tree.root.add(sec_label, expand=True)
            for mod in section.modules:
                if mod.type not in ("resource", "url", "assign", "label"):
                    continue
                icon = module_icon(mod.type)
                label = f"\u2610 {icon} {mod.name} ({mod.type})"
                leaf = sec_node.add_leaf(label, data=mod)
                self.selected[mod.id] = False

        self._update_count()

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        node = event.node
        if len(node.children) == 0 and node.data is not None:
            mod: Module = node.data
            self.selected[mod.id] = not self.selected[mod.id]
            icon = module_icon(mod.type)
            checked = "\u2611" if self.selected[mod.id] else "\u2610"
            node.label = f"{checked} {icon} {mod.name} ({mod.type})"
            self._update_count()

    def _update_count(self):
        n = sum(1 for v in self.selected.values() if v)
        btn = self.query_one("#dl-selected-btn", Button)
        btn.label = f"Descargar Seleccionados ({n})"

    def on_button_pressed(self, event: Button.Pressed):
        btn = event.button
        if btn.id == "select-all-btn":
            self._toggle_all()
        elif btn.id == "dl-selected-btn":
            self._start_selected_download()
        elif btn.id == "back-btn":
            self.app.pop_screen()

    def _toggle_all(self):
        all_selected = all(self.selected.values())
        new_val = not all_selected
        tree = self.query_one("#module-tree", Tree)
        for node in tree.root.children:
            for leaf in node.children:
                if leaf.data is not None:
                    mod: Module = leaf.data
                    self.selected[mod.id] = new_val
                    icon = module_icon(mod.type)
                    checked = "\u2611" if new_val else "\u2610"
                    leaf.label = f"{checked} {icon} {mod.name} ({mod.type})"
        self._update_count()

    def _start_selected_download(self):
        selected_ids = [mid for mid, sel in self.selected.items() if sel]
        if not selected_ids:
            return

        self.downloading = True
        self.query_one("#module-tree", Tree).disabled = True
        self.query_one("#select-all-btn", Button).disabled = True
        self.query_one("#dl-selected-btn", Button).disabled = True
        self._run_selected_download(selected_ids)

    @work(thread=True)
    def _run_selected_download(self, selected_ids: list[str]):
        session = MoodleSession(self.session_data)
        log = self.app.call_from_thread(self.query_one, "#dl-log", RichLog)
        progress = self.app.call_from_thread(self.query_one, "#dl-progress", ProgressBar)
        status = self.app.call_from_thread(self.query_one, "#dl-status", Static)
        base_dir = Path("courses")

        self.app.call_from_thread(log.write, f"[bold cyan]\u25b6 Descargando m\u00f3dulos seleccionados[/bold cyan]")

        all_modules = [
            m for s in self.course.sections for m in s.modules
            if m.id in selected_ids and m.type in ("resource", "url", "assign", "label")
        ]
        total = len(all_modules)
        resolved_modules = []

        for mi, module in enumerate(all_modules):
            self.app.call_from_thread(
                status.update,
                f"[{mi+1}/{total}] {module.type} - {module.name[:50]}",
            )
            self.app.call_from_thread(progress.update, progress=int((mi + 1) / total * 100))

            resolved = resolve_module(session, module)
            for f in resolved.files:
                dest_dir = Path("downloads") / sanitize(f"{self.course.name} {self.course.id}")
                path = download_file(session, f.url, dest_dir / sanitize(f"{module.name}-{module.id}"))
                if path:
                    f.downloaded = True
                    f.filepath = str(path)
                    self.app.call_from_thread(log.write, f"  [green]\u2713[/green] {f.filename}")
                else:
                    self.app.call_from_thread(log.write, f"  [red]\u2717[/red] {f.filename}")

            resolved_modules.append(resolved)

        try:
            save_course(base_dir, self.course, resolved_modules)
            self.app.call_from_thread(
                log.write,
                f"[green]\u2713 Curso guardado en courses/{sanitize(self.course.name)} {self.course.id}/[/green]",
            )
        except Exception as e:
            self.app.call_from_thread(log.write, f"[red]\u2717 Error guardando: {e}[/red]")

        session.close()
        self.app.call_from_thread(progress.update, progress=100)
        self.app.call_from_thread(status.update, "[bold green]\u00a1Descarga completada![/bold green]")
        self.app.call_from_thread(log.write, "\n[bold green]\u2713 Proceso finalizado[/bold green]")


# ────────────────────────────── App ──────────────────────────────


class AulaVaultApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    #auth-container {
        align: center middle;
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
    }
    #base-url {
        width: 100%;
    }
    #title {
        text-style: bold;
        content-align: center middle;
        width: 100%;
        margin-bottom: 1;
    }
    #subtitle {
        content-align: center middle;
        width: 100%;
        margin-bottom: 1;
    }
    .instruction {
        text-style: bold;
        margin: 0 1;
    }
    .hint {
        margin: 0 2;
        color: $text-muted;
    }
    Input {
        margin: 1 0;
    }
    Button {
        margin: 1 0;
    }
    #auth-status {
        margin-top: 1;
        text-align: center;
    }
    .panel-left {
        width: 40%;
        border-right: solid $primary;
        padding: 1;
        height: 1fr;
    }
    .panel-right {
        width: 60%;
        padding: 1;
        height: 1fr;
    }
    .panel-title {
        text-style: bold;
        padding: 0 1;
        margin-bottom: 1;
    }
    #course-list {
        height: 1fr;
        margin-bottom: 1;
    }
    #action-bar {
        height: 5;
        align: center middle;
    }
    #log-panel {
        height: 1fr;
        border: solid $primary;
    }
    #progress-bar {
        margin: 1 0;
    }
    #status-text {
        text-style: italic;
        padding: 0 1;
    }
    /* Module Select Screen */
    #selector-split {
        height: 1fr;
    }
    #module-course-name {
        text-style: bold;
        padding: 1;
        border-bottom: solid $primary;
    }
    #module-tree {
        height: 1fr;
        border: solid $primary;
    }
    #selector-left {
        width: 50%;
        padding: 1;
        height: 1fr;
    }
    #selector-right {
        width: 50%;
        padding: 1;
        height: 1fr;
    }
    #dl-log {
        height: 1fr;
        border: solid $primary;
    }
    #dl-progress {
        margin: 1 0;
    }
    #dl-status {
        text-style: italic;
        padding: 0 1;
    }
    #selector-actions {
        dock: bottom;
        height: 5;
        align: center middle;
        border-top: solid $primary;
        background: $surface;
    }
    #selector-actions Button {
        margin: 0 1;
    }
    """

    def on_mount(self):
        self.push_screen(AuthScreen())
