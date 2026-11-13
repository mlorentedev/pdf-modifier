---
id: "lesson-006-docker-multi-stage-venv-shebangs-broken-acros"
type: lesson
status: active
title: "Docker multi-stage: venv shebangs broken across builder/runtime + COPY content semantics"
created: "2026-06-24"
owner: manu
tags: [pdf-modifier-mcp, lesson, docker, multi-stage, venv, windows-wsl, python]
---

# Docker multi-stage: venv shebangs broken across builder/runtime + COPY content semantics

**Context:** INFRA-001 — Docker multi-stage build for FastAPI backend.
**Problem:** Serie de errores encadenados al construir el Dockerfile multi-stage:
1. **Shebang del venv en el builder stage** — copiar el venv creado en `builder` (`/build/.venv/`) al `runtime` produce shebangs apuntando a `/build/.venv/bin/python` (inexistente en runtime). Solución: crear venv limpio en runtime y copiar solo los wheels (`pip wheel --wheel-dir` + `pip install /wheels/*`).
2. **`COPY src/ ./` copia contenido, no directorio** — `src/` contiene `pdf_modifier/`. `COPY src/ ./` copia el *contenido* de `src/` a `/app/`, resultando en `/app/pdf_modifier/` (correcto). Pero `COPY src/ ./pdf_modifier/` copia el contenido al subdirectorio `pdf_modifier/`, generando `/app/pdf_modifier/pdf_modifier/` (anidamiento doble).
3. **Orden COPY/RUN** — `pip install .` necesita `pyproject.toml`. Si el COPY de `pyproject.toml` está después del RUN, el install falla silenciosamente.
4. **Permissions** — el runtime user es `appuser`, pero los directorios (`/app/.pdf-modifier/`, `/app/storage/`) los crea la app en primer inicio. Si no existen y el appuser no tiene permisos en `/app/` (dueño root), falla con `PermissionError`. Solución: `mkdir -p` + `chown` ANTES de `USER appuser`.
**Solution:**
- Fase builder: `pip wheel --wheel-dir /wheels` para descargar wheels.
- Fase runtime: crear venv limpio, instalar wheels, instalar package con `pip install .` (necesita pyproject.toml en el directorio).
- Orden estricto: COPY todo → RUN install → RUN mkdir+chown → USER → CMD.
- Verificar con `docker run --entrypoint ls` antes de correr.
- El error de `pip install .` sin pyproject.toml es **visible en build**, no silencioso: `ERROR: Directory '.' is not installable. Neither 'setup.py' nor 'pyproject.toml' found.`
**Tags:** `#docker` `#multi-stage` `#venv` `#windows-wsl` `#python`
