# AGENTS.md — App_Certificados

Flask + Supabase (PostgreSQL) app for Academia Horizonte (formación técnica a empresas; certifica por estudiante al cerrar cada cohorte; reemplaza proceso manual Excel/Word). Deterministic rules only, no AI inference.

## Structure (MVC strict: Bodega=datos en `Insumos/`, Cocina=backend Flask en `app.py`+`models/`+`services/`+`controllers/`, Salón=`views/` solo muestra)

- `models/datos.py` — ONLY file allowed to touch the DB (`psycopg`, `DATABASE_URL` via `python-dotenv`). Tables: `estudiantes`, `evaluaciones`. All reads have transparent Excel fallback (see below).
- `models/certificados.py` — Business rules R1–R6. Entry: `procesar_certificados()` → `{totales, inconsistencias, estudiantes}`.
- `services/carga_excel.py` — Excel ingest with `pandas`/`openpyxl`. Entry: `cargar_desde_insumos()` / `procesar_y_guardar_archivos(maestro, evaluaciones)`.
- `controllers/tablero.py` — Flask `tablero_bp` Blueprint, route `/` only. Controllers coordinate, never SQL or rule math.
- `views/` — Jinja only (`base.html` layout, `tablero.html`, `cargar.html`). No logic.
- `.agents/agents/` — Subagent contracts (`backend-flask`, `disenador-vistas`, `tester-datos`, `revisor`); consult before crossing layer boundaries.

Gaps an agent must know: `app.py`, `services/generador_pdf.py` (`fpdf2`, A4 horizontal), and routes `/cargar`, `/certificado/<id>/<programa>`, `/descargar-todos` are referenced by `.agents/` and templates but **do not exist yet** — create them following the same MVC split if needed.

## Rules R1–R6 (`models/certificados.py`)

- R1: group evaluations by `(identificacion, programa)` — one certificate per student+program; fallback match by ID alone if program spacing differs.
- R2: mean `nota` / `asistencia_pct`, `round(..., 2)`. Nota scale 0–100.
- R3/R4/R5 (`NOTA_MINIMA=70.0`, `ASISTENCIA_MINIMA=80.0`, limits inclusive): `>=70 and >=80` → `Aprobación`; `<70 and >=80` → `Participación`; `<80 asistencia` → `Sin certificado`.
- R6: `Sin evaluaciones` (in maestro, no evals) / `No registrado en maestro` (evals, no maestro) / `Asistencia menor al 50%` (`ASISTENCIA_CRITICA=50.0`). No-eval and no-maestro rows get `estado="Inconsistencia"`.

## Data quirks

- `identificacion` is always stripped text; `limpiar_identificacion()` also strips trailing `.0`. Never compare as int.
- Excel schemas (exact sheet/column names): `Maestro_Estudiantes.xlsx` sheet `Estudiantes` (`Identificacion, Nombre_Completo, Correo, Programa, Cohorte`); `Registro_Evaluaciones.xlsx` sheet `Evaluaciones` (`Identificacion, Programa, Modulo, Nota, Asistencia_Pct, Fecha_Cierre`). Folder on disk is `Insumos/` (capital I); use `resolver_ruta_archivo()` which probes both `insumos/` and `Insumos/`.
- DB writes are destructive replace: `TRUNCATE ... CASCADE` + `executemany`. No migrations.
- Supabase pooler requires `psycopg.connect(DATABASE_URL, prepare_threshold=None)`. Never print/log `DATABASE_URL`.
- No-DB fallback: if `DATABASE_URL` missing/empty, DB error, or tables empty → read directly from `Insumos/*.xlsx`. Verified control figures via fallback: `aprobacion=19, participacion=3, sin_certificado=1, inconsistencias=3` (IDs `304560321` sin evaluaciones, `999880777` no en maestro, asistencia `36.25%` <50%).

## Commands

- Env is `.venv/` (CPython 3.12, created by `uv`); use `uv` wire, never `pip`. Run via `.venv\Scripts\python.exe` on Windows.
- No `requirements*.txt` / `pyproject.toml`, no tests, no lint/CI, no `.env` committed.
- Decided stack (see PLAN.md): `pandas`+`openpyxl` for Excel (DataFrame grouping/means; `xlrd`/`xlwings` rejected), `Flask`+Jinja for web (3–4 routes; `Django`/`FastAPI` rejected as overkill), `fpdf2` for PDFs (A4 horizontal), `psycopg[binary]`+`python-dotenv` for Supabase (`[binary]` bundles libpq — plain `psycopg` fails on Vercel with "libpq library not found").
- Build order: data-crossing → Flask backend (`app.py`, missing routes, `generador_pdf.py`) → views. Gates in PLAN.md.
- Quick verify (fallback path, no DB needed):
  `.venv\Scripts\python.exe -c "from models.certificados import procesar_certificados; print(procesar_certificados()['totales'])"`
- Expected Flask port is `5000` per subagent contracts.

## Constraints

- Never edit originals in `Insumos/`; never read/expose `.env` or hardcode secrets (`.gitignore` already covers `.env`, `.venv/`, `__pycache__/`, `.vercel`).
- All logic in backend, never in `views/`. Backend agents: don't touch `views/`. Views agent: don't touch `models/`, `services/`, `controllers/`, `app.py`.
- Code: simple, commented in Spanish, labeling the bricks (variables, tipos, condicionales, bucles, funciones).
- Explain in plain Spanish what you are doing as you work.
- UI palette when editing templates: navy `#14213D`, gold `#B8923D`.
