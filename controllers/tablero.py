"""
Controlador del Tablero Principal (Dashboard).

Maneja la ruta principal ('/') coordinando la obtención de métricas,
alertas de inconsistencias y la lista de estudiantes procesados,
delegando el renderizado a la vista tablero.html.
"""

from flask import Blueprint, render_template
from models.certificados import procesar_certificados

tablero_bp = Blueprint("tablero", __name__)


@tablero_bp.route("/")
def index():
    """
    Ruta raíz del tablero.

    Obtiene los cálculos deterministas de modelos/certificados.py
    y los pasa a la plantilla views/tablero.html.
    """
    # LADRILLO: variable (diccionario con totales, inconsistencias y estudiantes)
    resultado = procesar_certificados()

    # LADRILLO: variables (listas ya calculadas por el modelo, aquí no se calcula nada)
    estudiantes = resultado.get("estudiantes", [])
    inconsistencias = resultado.get("inconsistencias", [])
    totales = resultado.get("totales", {})

    # LADRILLO: bucle + condicional (ordena por programa y nombre para la tabla)
    estudiantes_ordenados = sorted(
        estudiantes,
        key=lambda e: (str(e.get("programa", "")), str(e.get("nombre_completo", ""))),
    )

    # LADRILLO: bucle (junta los programas únicos para el filtro, sin repetir)
    programas = []
    for est in estudiantes_ordenados:
        prog = str(est.get("programa", "")).strip()
        if prog and prog not in programas:
            programas.append(prog)

    return render_template(
        "tablero.html",
        totales=totales,
        inconsistencias=inconsistencias,
        estudiantes=estudiantes_ordenados,
        programas=programas,
        resultado=resultado,
    )
