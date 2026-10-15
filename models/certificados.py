"""
Módulo de Reglas del Negocio y Procesamiento de Certificados.

Aplica las reglas fijas R1 a R6 sin librerías de IA:
- R1: Agrupación por identificación + programa.
- R2: Promedios de notas y asistencia redondeados a 2 decimales.
- R3: Aprobación (promedio >= 70 y asistencia >= 80).
- R4: Participación (promedio < 70 y asistencia >= 80).
- R5: Sin certificado (asistencia < 80).
- R6: Detección de inconsistencias (sin evaluaciones, no en maestro, asistencia < 50%).
"""

from typing import Any, Dict, List, Optional, Tuple
from models.datos import obtener_todas_evaluaciones, obtener_todos_estudiantes

# Constantes fijas del negocio
NOTA_MINIMA: float = 70.0
ASISTENCIA_MINIMA: float = 80.0
ASISTENCIA_CRITICA: float = 50.0


# LADRILLO: función (calcula un promedio redondeado a 2 decimales)
def calcular_promedio(valores: List[float]) -> float:
    # LADRILLO: variables con tipos (lista de números -> número)
    # LADRILLO: condicional (si no hay valores, no se puede dividir)
    if len(valores) == 0:
        return 0.0
    total = float(sum(valores))  # variable tipo float: suma de notas
    cantidad = int(len(valores))  # variable tipo int: módulos cursados
    return round(total / cantidad, 2)


# LADRILLO: función (decide el certificado según AGENTS.md, límites inclusivos)
def decidir_certificado(promedio: float, asistencia: float) -> str:
    # LADRILLO: condicionales (primero asistencia, luego nota)
    if asistencia >= ASISTENCIA_MINIMA:  # el 80 SÍ cuenta
        if promedio >= NOTA_MINIMA:  # el 70 SÍ cuenta
            return "Aprobación"
        return "Participación"
    return "Sin certificado"


def clasificar_estado(promedio: float, asistencia: float) -> str:
    """
    Determina el estado del certificado según las reglas fijas de aprobación:
    - R3: Aprobación si promedio >= 70 y asistencia >= 80.
    - R4: Participación si promedio < 70 y asistencia >= 80.
    - R5: Sin certificado si asistencia < 80.
    """
    return decidir_certificado(promedio, asistencia)


def procesar_certificados(
    estudiantes: Optional[List[Dict[str, Any]]] = None,
    evaluaciones: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Ejecuta el procesamiento integral de estudiantes y evaluaciones aplicando las reglas R1 a R6.
    
    Retorna un diccionario con:
    - totales: dict con conteos ('aprobacion', 'participacion', 'sin_certificado', 'inconsistencias')
    - inconsistencias: lista de alertas detectadas según R6
    - estudiantes: lista detallada para renderizar en la tabla del tablero web
    """
    if estudiantes is None:
        estudiantes = obtener_todos_estudiantes()
    if evaluaciones is None:
        evaluaciones = obtener_todas_evaluaciones()

    # R1: Agrupar evaluaciones por (identificacion, programa)
    evaluaciones_agrupadas: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for ev in evaluaciones:
        ident_ev = str(ev.get("identificacion", "")).strip()
        prog_ev = str(ev.get("programa", "")).strip()
        if not ident_ev:
            continue
        clave = (ident_ev, prog_ev)
        if clave not in evaluaciones_agrupadas:
            evaluaciones_agrupadas[clave] = []
        evaluaciones_agrupadas[clave].append(ev)

    # Identificaciones presentes en el maestro
    ids_maestro = {str(est.get("identificacion", "")).strip() for est in estudiantes}

    totales = {
        "aprobacion": 0,
        "participacion": 0,
        "sin_certificado": 0,
        "inconsistencias": 0,
    }

    inconsistencias: List[Dict[str, Any]] = []
    lista_estudiantes_resultado: List[Dict[str, Any]] = []

    # R6 (caso 2): Identificaciones con evaluaciones que no están en el maestro
    ids_eval_no_en_maestro: List[Dict[str, Any]] = []
    for (ident_ev, prog_ev), evs_lista in evaluaciones_agrupadas.items():
        if ident_ev not in ids_maestro:
            # LADRILLO: función reutilizada (promedio de notas y de asistencia)
            prom_nota = calcular_promedio([float(e.get("nota", 0.0)) for e in evs_lista if e.get("nota") is not None])
            prom_asist = calcular_promedio([float(e.get("asistencia_pct", 0.0)) for e in evs_lista if e.get("asistencia_pct") is not None])

            alerta = {
                "tipo": "No registrado en maestro",
                "alerta": "No registrado en maestro",
                "tipo_alerta": "No registrado en maestro",
                "identificacion": ident_ev,
                "nombre": "Estudiante no registrado",
                "nombre_completo": "Estudiante no registrado",
                "programa": prog_ev,
                "modulos": len(evs_lista),
                "promedio": prom_nota,
                "asistencia": prom_asist,
                "detalle": f"La identificación {ident_ev} registra evaluaciones en '{prog_ev}' pero no existe en el maestro de estudiantes.",
            }
            inconsistencias.append(alerta)
            ids_eval_no_en_maestro.append(alerta)

    # Procesar estudiantes del maestro
    for est in estudiantes:
        ident = str(est.get("identificacion", "")).strip()
        nombre = str(est.get("nombre_completo", "")).strip()
        correo = str(est.get("correo", "")).strip()
        programa = str(est.get("programa", "")).strip()
        cohorte = str(est.get("cohorte", "")).strip()

        # Buscar evaluaciones asociadas a la identificación y programa
        evs = evaluaciones_agrupadas.get((ident, programa))
        if evs is None:
            # Fallback buscando solo por identificación si el nombre del programa tuviera diferencias leves de espaciado
            for (id_k, prog_k), ev_lista in evaluaciones_agrupadas.items():
                if id_k == ident:
                    evs = ev_lista
                    break

        # R6 (caso 1): Estudiante del maestro sin evaluaciones
        if not evs:
            inconsistencias.append({
                "tipo": "Sin evaluaciones",
                "alerta": "Sin evaluaciones",
                "tipo_alerta": "Sin evaluaciones",
                "identificacion": ident,
                "nombre": nombre,
                "nombre_completo": nombre,
                "programa": programa,
                "detalle": f"El estudiante {nombre} ({ident}) está registrado en el maestro pero no cuenta con evaluaciones en el programa '{programa}'.",
            })
            lista_estudiantes_resultado.append({
                "identificacion": ident,
                "nombre_completo": nombre,
                "correo": correo,
                "programa": programa,
                "cohorte": cohorte,
                "modulos": 0,
                "promedio": None,
                "asistencia": None,
                "estado": "Inconsistencia",
                "tiene_inconsistencia": True,
            })
            continue

        # R2: Promedio de notas y asistencia redondeado a 2 decimales
        # LADRILLO: función reutilizada (misma que se validó en el análisis)
        promedio = calcular_promedio([float(e.get("nota", 0.0)) for e in evs if e.get("nota") is not None])
        asistencia = calcular_promedio([float(e.get("asistencia_pct", 0.0)) for e in evs if e.get("asistencia_pct") is not None])

        # R6 (caso 3): Asistencia menor a 50%
        tiene_inconsistencia = False
        if asistencia < ASISTENCIA_CRITICA:
            tiene_inconsistencia = True
            inconsistencias.append({
                "tipo": "Asistencia menor al 50%",
                "alerta": "Asistencia menor al 50%",
                "tipo_alerta": "Asistencia menor al 50%",
                "identificacion": ident,
                "nombre": nombre,
                "nombre_completo": nombre,
                "programa": programa,
                "detalle": f"La asistencia de {nombre} ({asistencia}%) es menor al 50% mínimo requerido.",
            })

        # Aplicación de reglas R3, R4, R5
        estado = clasificar_estado(promedio, asistencia)

        if estado == "Aprobación":
            totales["aprobacion"] += 1
        elif estado == "Participación":
            totales["participacion"] += 1
        elif estado == "Sin certificado":
            totales["sin_certificado"] += 1

        lista_estudiantes_resultado.append({
            "identificacion": ident,
            "nombre_completo": nombre,
            "correo": correo,
            "programa": programa,
            "cohorte": cohorte,
            "modulos": len(evs),
            "promedio": promedio,
            "asistencia": asistencia,
            "estado": estado,
            "tiene_inconsistencia": tiene_inconsistencia,
        })

    # Añadir a la tabla a los estudiantes con evaluaciones que no están en el maestro
    for alerta_ext in ids_eval_no_en_maestro:
        lista_estudiantes_resultado.append({
            "identificacion": alerta_ext["identificacion"],
            "nombre_completo": alerta_ext["nombre_completo"],
            "correo": "-",
            "programa": alerta_ext["programa"],
            "cohorte": "-",
            "modulos": alerta_ext.get("modulos", 0),
            "promedio": alerta_ext.get("promedio"),
            "asistencia": alerta_ext.get("asistencia"),
            "estado": "Inconsistencia",
            "tiene_inconsistencia": True,
        })

    totales["inconsistencias"] = len(inconsistencias)

    return {
        "totales": totales,
        "inconsistencias": inconsistencias,
        "estudiantes": lista_estudiantes_resultado,
    }


def obtener_estudiante_procesado(identificacion: str, programa: str) -> Optional[Dict[str, Any]]:
    """
    Busca y retorna el resultado procesado de un estudiante específico por identificación y programa.
    Útil para la generación individual de certificados en PDF.
    """
    ident_limpia = str(identificacion).strip()
    prog_limpio = str(programa).strip().lower()

    resultado = procesar_certificados()
    for est in resultado.get("estudiantes", []):
        if str(est.get("identificacion", "")).strip() == ident_limpia:
            prog_est = str(est.get("programa", "")).strip().lower()
            if prog_est == prog_limpio or not prog_limpio:
                return est
    return None
