# 🏛️ AulaVault

**Extrae, estructura y descarga el contenido de tus cursos de Aulas Virtuales Santo Tomás (Moodle) a tu computador.**

Preserva localmente los materiales de tus asignaturas: PDFs, presentaciones, documentos, tareas entregadas, y más.

---
## 🔍 Cómo funciona

AulaVault se basa en **reverse engineering** de las APIs internas de Moodle.

Al encontrar `core_courseformat_get_state`, un endpoint interno que el frontend de Moodle usa para construir la página del curso. Devuelve el árbol completo: curso → secciones → módulos con URLs y metadatos. Lo llamamos directamente desde Python, reutilizando la sesión del navegador (cookie `MoodleSession` + token `sesskey`) para saltarnos el SSO de Microsoft.

**Los archivos** se descargan desde `/pluginfile.php`, el servidor privado de Moodle que requiere sesión activa. Cada tipo de módulo se resuelve distinto: `resource` busca links a pluginfile, `assign` parsea la página de la tarea, `url` extrae el destino del redirect, `label` captura el texto HTML.

> Este proyecto no usa ninguna API oficial — todo se descubrió observando el tráfico de red con las DevTools del navegador.

## ✨ Funcionalidades

-   Interfaz interactiva tipo dashboard (TUI)
-   Listado automático de cursos en los que estás matriculado
-   Vista por secciones con selector de módulos a descargar
-   Descarga de archivos (`resource`), URLs (`url`), tareas (`assign`) y textos (`label`)
---

## 📦 Instalación

### Requisitos

-   Python 3.11 o superior
-   Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/aulavault.git
cd aulavault

# 2. Instalar dependencias
pip install -e .
```

---

## 🚀 Cómo usar

### 1. Obtener tus credenciales de Moodle

AulaVault no usa contraseña. Necesitas copiar dos valores desde tu navegador:

1.  Inicia sesión en [aulasvirtuales.santotomas.cl](https://aulasvirtuales.santotomas.cl) con tu cuenta institucional (Microsoft SSO).

2.  Abre las herramientas de desarrollador:
    -   **Chrome/Edge**: `F12` o clic derecho → **Inspeccionar**
    -   **Firefox**: `F12` o clic derecho → **Inspeccionar elemento**

3.  Ve a la pestaña **Application** (Chrome) o **Storage** (Firefox).

4.  En el panel izquierdo, busca **Cookies** → `https://aulasvirtuales.santotomas.cl`.

5.  Copia estos dos valores:

    | ¿Qué buscas?          | ¿Dónde está?                                       |
    | --------------------- | -------------------------------------------------- |
    | **MoodleSession**     | Ve a la pestaña **Application** (Chrome) o **Storage** (Firefox). Donde el **Name** es `MoodleSession` → copia el **Value** |
    | **sesskey**           | En la pestaña **Network** si filtras por Fetch/XHR encontraras  una Request URL:  https://service.php?sesskey=XXXXXXX&info=core... , debes copiar solo XXXXXXX|
   

> ⚠️ `MoodleSession` y `sesskey` **cambian cada vez que cierras sesión**. Si deja de funcionar, repite este paso.

### 2. Ejecutar

```bash
python -m aulavault
```

Se abrirá una interfaz con dos pasos:

**Paso 1 — Ingresar credenciales**
Pega los valores que copiaste en los campos correspondientes y haz clic en **Conectar**.

**Paso 2 — Seleccionar y descargar**
-   Verás la lista de todos tus cursos.
-   Selecciona un curso y haz clic en **Seleccionar Módulos**.
-   Se mostrará un árbol con las secciones y los módulos disponibles.
-   Marca/desmarca los que quieras descargar usando clic o Enter.
-   Haz clic en **Descargar Seleccionados (N)**.

También puedes descargar todo de golpe con **Descargar Todo**.

