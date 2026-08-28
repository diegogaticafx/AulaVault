# 🏛️ AulaVault
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Git](https://img.shields.io/badge/Git-2.0%2B-green.svg)](https://git-scm.com/downloads/)

Herramienta para sincronizar y descargar automaticamente todos los recursos educativos disponibles en plataformas Moodle.

AulaVault permite crear una copia local estructurada de sus cursos, incluyendo materiales como:

-   📄 Documentos
-   📊 Presentaciones
-   📝 Archivos compartidos
-   📚 Recursos del curso
-   📋 Actividades y entregas

El proyecto nació como una solución personal para optimizar y mejorar la gestión de materiales académicos y explorar la arquitectura interna de una plataforma LMS ampliamente utilizada.

---

## 🔍 Descripción técnica

AulaVault funciona mediante el análisis de la comunicación entre el navegador y Moodle para construir una representación local de la estructura del curso.

El sistema interpreta la información proporcionada por Moodle para reconstruir:

```
Curso
 └── Secciones
      └── Módulos
           ├── Recursos
           ├── Actividades
           ├── Enlaces externos
           └── Contenido HTML
```

La aplicación utiliza la sesión autenticada del usuario para acceder únicamente a los recursos disponibles dentro de su propia cuenta.

---

## 🏗️ Arquitectura

El proyecto está dividido en módulos independientes:

```
┌───────────────────────┐
│ Authentication Layer  │
│ Gestión de sesión     │
└──────────┬────────────┘
           │
┌──────────▼────────────┐
│ Course Graph Builder  │
│ Construcción cursos   │
└──────────┬────────────┘
           │
┌──────────▼────────────┐
│ Module Resolver       │
│ Resolución recursos   │
└──────────┬────────────┘
           │
┌──────────▼────────────┐
│ Download Manager      │
│ Sincronización local  │
└───────────────────────┘
```

---

## ✨ Características

-   ✅ Descubrimiento automático de cursos disponibles
-   ✅ Construcción del árbol de contenidos
-   ✅ Selección granular de módulos
-   ✅ Descarga organizada de recursos
-   ✅ Soporte para distintos tipos de módulos Moodle: `resource`, `assign`, `url`, `label`
-   ✅ Interfaz interactiva tipo dashboard (TUI)

---

## 📦 Instalación

### Requisitos

-   Python 3.12 o superior
-   Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/aulavault.git
cd src/

# 2. Instalar dependencias
pip install -e .
```

---

## 🚀 Uso

### 1. Autenticación

AulaVault utiliza la sesión activa del usuario. Debes iniciar sesión normalmente en tu plataforma Moodle y proporcionar una sesión válida para acceder a los recursos autorizados.

### 2. Ejecutar

```bash
python -m aulavault
```

La aplicación permite:

-   Visualizar cursos disponibles.
-   Explorar la estructura de cada curso.
-   Seleccionar módulos específicos.
-   Descargar contenido localmente.

---

## 📁 Ejemplo de estructura generada

```
AulaVault/
│
├── Programación/
│   ├── Unidad 1/
│   │   ├── Introducción.pdf
│   │   └── ejercicios.pdf
│   │
│   └── Unidad 2/
│       └── presentación.pptx
│
└── Base de Datos/
    └── material.pdf
```

---

## 🔐 Uso responsable

AulaVault fue desarrollado para fines educativos y de productividad personal.

La herramienta está diseñada para trabajar con cuentas autorizadas y acceder únicamente a contenido que el usuario ya puede visualizar dentro de la plataforma.
