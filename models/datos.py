"""
Módulo de acceso y persistencia de datos (PostgreSQL / Supabase).

Este es el ÚNICO archivo autorizado para conectarse y comunicarse con Supabase.
Maneja la creación de tablas, inserción por lotes y consultas de conteo.
"""

import os
from typing import Any, Dict, List
from dotenv import load_dotenv
import psycopg

# Cargar variables de entorno desde .env
load_dotenv()


def obtener_conexion():
    """
    Establece y retorna una conexión a la base de datos PostgreSQL en Supabase.
    
    Utiliza prepare_threshold=None debido al uso de pooler en Supabase.
    NUNCA imprime ni expone DATABASE_URL en consola ni en logs.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Error de configuración: Variable DATABASE_URL no encontrada en el entorno.")
    
    return psycopg.connect(database_url, prepare_threshold=None)


def crear_tablas() -> None:
    """
    Crea las tablas estudiantes y evaluaciones si no existen en la base de datos.
    """
    sql_estudiantes = """
    CREATE TABLE IF NOT EXISTS estudiantes (
        identificacion TEXT PRIMARY KEY,
        nombre_completo TEXT,
        correo TEXT,
        programa TEXT,
        cohorte TEXT
    );
    """
    sql_evaluaciones = """
    CREATE TABLE IF NOT EXISTS evaluaciones (
        id SERIAL PRIMARY KEY,
        identificacion TEXT,
        programa TEXT,
        modulo TEXT,
        nota NUMERIC,
        asistencia_pct NUMERIC,
        fecha_cierre TEXT
    );
    """
    with obtener_conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_estudiantes)
            cur.execute(sql_evaluaciones)
        conn.commit()


def reemplazar_estudiantes(registros: List[Dict[str, Any]]) -> int:
    """
    Limpia la tabla estudiantes e inserta una nueva lista de estudiantes en lote.
    """
    sql_truncate = "TRUNCATE TABLE estudiantes CASCADE;"
    sql_insert = """
    INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte)
    VALUES (%s, %s, %s, %s, %s);
    """
    datos = [
        (
            r.get("identificacion"),
            r.get("nombre_completo"),
            r.get("correo"),
            r.get("programa"),
            r.get("cohorte"),
        )
        for r in registros
    ]
    with obtener_conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_truncate)
            cur.executemany(sql_insert, datos)
        conn.commit()
    return len(datos)


def reemplazar_evaluaciones(registros: List[Dict[str, Any]]) -> int:
    """
    Limpia la tabla evaluaciones e inserta una nueva lista de evaluaciones en lote.
    """
    sql_truncate = "TRUNCATE TABLE evaluaciones;"
    sql_insert = """
    INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    datos = [
        (
            r.get("identificacion"),
            r.get("programa"),
            r.get("modulo"),
            r.get("nota"),
            r.get("asistencia_pct"),
            r.get("fecha_cierre"),
        )
        for r in registros
    ]
    with obtener_conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_truncate)
            cur.executemany(sql_insert, datos)
        conn.commit()
    return len(datos)


def obtener_conteo_filas() -> Dict[str, int]:
    """
    Devuelve la cantidad actual de registros en las tablas estudiantes y evaluaciones.
    """
    with obtener_conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM estudiantes;")
            total_estudiantes = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM evaluaciones;")
            total_evaluaciones = cur.fetchone()[0]
    return {
        "estudiantes": total_estudiantes,
        "evaluaciones": total_evaluaciones,
    }


def _obtener_estudiantes_fallback_excel() -> List[Dict[str, Any]]:
    """Lee estudiantes directamente desde insumos/Maestro_Estudiantes.xlsx como fallback."""
    try:
        from services.carga_excel import resolver_ruta_archivo, leer_maestro_estudiantes
        ruta = resolver_ruta_archivo("Maestro_Estudiantes.xlsx")
        return leer_maestro_estudiantes(ruta)
    except Exception:
        return []


def _obtener_evaluaciones_fallback_excel() -> List[Dict[str, Any]]:
    """Lee evaluaciones directamente desde insumos/Registro_Evaluaciones.xlsx como fallback."""
    try:
        from services.carga_excel import resolver_ruta_archivo, leer_registro_evaluaciones
        ruta = resolver_ruta_archivo("Registro_Evaluaciones.xlsx")
        evaluaciones = leer_registro_evaluaciones(ruta)
        for idx, item in enumerate(evaluaciones, start=1):
            if "id" not in item:
                item["id"] = idx
        return evaluaciones
    except Exception:
        return []


def obtener_todos_estudiantes() -> List[Dict[str, Any]]:
    """
    Recupera todos los registros de la tabla estudiantes en formato de lista de diccionarios.
    
    Si DATABASE_URL no está configurada en .env o la base de datos no está disponible,
    utiliza un fallback transparente leyendo directamente desde los Excel de insumos/.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url or not database_url.strip():
        return _obtener_estudiantes_fallback_excel()

    try:
        with obtener_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT identificacion, nombre_completo, correo, programa, cohorte FROM estudiantes;")
                columnas = [col.name for col in cur.description]
                filas = cur.fetchall()
                registros = [dict(zip(columnas, fila)) for fila in filas]
                if not registros:
                    return _obtener_estudiantes_fallback_excel()
                return registros
    except Exception:
        return _obtener_estudiantes_fallback_excel()


def obtener_todas_evaluaciones() -> List[Dict[str, Any]]:
    """
    Recupera todos los registros de la tabla evaluaciones en formato de lista de diccionarios.
    
    Si DATABASE_URL no está configurada en .env o la base de datos no está disponible,
    utiliza un fallback transparente leyendo directamente desde los Excel de insumos/.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url or not database_url.strip():
        return _obtener_evaluaciones_fallback_excel()

    try:
        with obtener_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre FROM evaluaciones;")
                columnas = [col.name for col in cur.description]
                filas = cur.fetchall()
                registros = []
                for fila in filas:
                    d = dict(zip(columnas, fila))
                    if d.get("nota") is not None:
                        d["nota"] = float(d["nota"])
                    if d.get("asistencia_pct") is not None:
                        d["asistencia_pct"] = float(d["asistencia_pct"])
                    registros.append(d)
                if not registros:
                    return _obtener_evaluaciones_fallback_excel()
                return registros
    except Exception:
        return _obtener_evaluaciones_fallback_excel()
