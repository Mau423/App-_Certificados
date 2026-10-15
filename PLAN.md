# PLAN.md — App_Certificados (Academia Horizonte)

Construcción por etapas: primero validar el cruce de datos, luego el backend Flask, al final la interfaz. Sin saltar validaciones.

## Etapa 1 — Validar el cruce de datos (sin servidor)

**Objetivo:** demostrar con los Excel reales que el cruce Identificación + Programa y las reglas R1–R6 dan las cifras de control.

1. Normalizar identificaciones como texto (`strip`, quitar `.0`) en ambos archivos.
2. Verificar esquemas exactos: hoja `Estudiantes` (5 columnas) y hoja `Evaluaciones` (6 columnas).
3. Cruce: agrupar evaluaciones por (identificación, programa); detectar los 3 casos R6 (`304560321` sin evaluaciones, `999880777` sin maestro, asistencia 36.25% < 50%).
4. Calcular promedios redondeados a 2 decimales y clasificar (≥70/≥80 Aprobación, <70/≥80 Participación, <80 Sin certificado).

**Validación (puerta antes de Etapa 2):**
`.venv\Scripts\python.exe -c "from models.certificados import procesar_certificados; print(procesar_certificados()['totales'])"`
Debe dar `aprobacion=19, participacion=3, sin_certificado=1, inconsistencias=3`. Si difiere, se detiene aquí.

## Etapa 2 — Backend con Flask

**Objetivo:** servidor con la lógica completa, sin depender aún de la interfaz final.

1. `app.py`: crear instancia Flask, registrar Blueprints, puerto 5000.
2. `controllers/tablero.py`: ruta `/` (ya existe) muestra el consolidado.
3. Nuevos controladores: `/cargar` (subir los 2 Excel → `procesar_y_guardar_archivos`), `/certificado/<id>/<programa>` (PDF individual vía `obtener_estudiante_procesado`), `/descargar-todos` (ZIP).
4. `services/generador_pdf.py`: crear con `fpdf2`, A4 horizontal, solo para Aprobación/Participación.
5. Persistencia solo en `models/datos.py` (`psycopg`, `prepare_threshold=None`, reemplazo por `TRUNCATE` + `executemany`).

**Validación (puerta antes de Etapa 3):**
Levantar Flask y probar con `curl`/navegador: `/` responde 200 con 19/3/1; `/cargar` acepta los 2 Excel de `Insumos/`; `/certificado/101230456/<programa>` descarga PDF; `/descargar-todos` descarga ZIP de 22 certificados. Casos que deben bloquearse: los 3 inconsistentes no generan PDF.

## Etapa 3 — Interfaz (Salón)

**Objetivo:** páginas que solo muestran lo que el backend ya calculó.

1. Reutilizar `views/base.html` (paleta azul marino `#14213D` / dorado `#B8923D`).
2. `views/tablero.html`: 3 contadores, alertas R6 y tabla con buscador (ya existe; solo ajustar a los datos del backend).
3. `views/cargar.html`: formulario de 2 archivos (ya existe; conectar a `/cargar`).
4. Verificar estados vacíos y mensajes flash.

**Validación final:**
Recorrido manual completo: abrir `/`, buscar un estudiante, subir Excel, descargar un PDF y el ZIP. Criterio de aceptación: cifras 19/3/1 + 3 alertas visibles y 0 errores en consola.

## Reglas del plan

- Orden estricto: 1 → 2 → 3. Ninguna etapa empieza sin pasar su puerta.
- No se modifican los originales en `Insumos/`; no se exponen secretos (`.env` fuera del repo).
- Código simple y comentado en español; explicación en español sencillo en cada avance.
