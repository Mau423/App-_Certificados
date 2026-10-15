"""
Servicio para la lectura, validación y carga de archivos Excel.

Lee los archivos de estudiantes y evaluaciones, normaliza los datos
(garantizando identificación como texto sin espacios) y delega la persistencia
al modelo de datos de Supabase.
"""

from datetime import date, datetime
import os
from typing import Any, Dict, List, Union
import pandas as pd
from models.datos import reemplazar_estudiantes, reemplazar_evaluaciones


def resolver_ruta_archivo(nombre_archivo: str, directorio_base: str = ".") -> str:
    """
    Busca un archivo dentro de la carpeta insumos o Insumos.
    """
    posibles_carpetas = ["insumos", "Insumos"]
    for carpeta in posibles_carpetas:
        ruta = os.path.join(directorio_base, carpeta, nombre_archivo)
        if os.path.exists(ruta):
            return ruta
    
    # Si no se encuentra en las subcarpetas, probar directamente
    if os.path.exists(nombre_archivo):
        return nombre_archivo
        
    raise FileNotFoundError(f"No se encontró el archivo '{nombre_archivo}' en la carpeta insumos.")


def limpiar_texto(valor: Any) -> str:
    """
    Limpia un valor de texto eliminando espacios sobrantes y manejando valores nulos.
    """
    if pd.isna(valor) or valor is None:
        return ""
    return str(valor).strip()


def limpiar_identificacion(valor: Any) -> str:
    """
    Limpia la identificación tratándola siempre como texto estricto sin espacios.
    Elimina sufijos decimales no deseados si existieran.
    """
    if pd.isna(valor) or valor is None:
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return texto


def formatear_fecha(valor: Any) -> str:
    """
    Formatea fechas a texto estándar AAAA-MM-DD o cadena limpia.
    """
    if pd.isna(valor) or valor is None:
        return ""
    if isinstance(valor, (pd.Timestamp, datetime, date)):
        return valor.strftime("%Y-%m-%d")
    return str(valor).strip()


def leer_maestro_estudiantes(origen: Union[str, Any]) -> List[Dict[str, Any]]:
    """
    Lee la hoja 'Estudiantes' del archivo Excel maestro y valida sus columnas.
    """
    df = pd.read_excel(origen, sheet_name="Estudiantes", dtype=str)
    
    columnas_esperadas = {"Identificacion", "Nombre_Completo", "Correo", "Programa", "Cohorte"}
    columnas_presentes = set(df.columns)
    columnas_faltantes = columnas_esperadas - columnas_presentes
    if columnas_faltantes:
        raise ValueError(f"El archivo de Estudiantes no contiene las columnas requeridas: {columnas_faltantes}")
    
    registros: List[Dict[str, Any]] = []
    for _, fila in df.iterrows():
        identificacion = limpiar_identificacion(fila["Identificacion"])
        if not identificacion:
            continue  # Ignorar filas vacías
        registros.append({
            "identificacion": identificacion,
            "nombre_completo": limpiar_texto(fila["Nombre_Completo"]),
            "correo": limpiar_texto(fila["Correo"]),
            "programa": limpiar_texto(fila["Programa"]),
            "cohorte": limpiar_texto(fila["Cohorte"]),
        })
    return registros


def leer_registro_evaluaciones(origen: Union[str, Any]) -> List[Dict[str, Any]]:
    """
    Lee la hoja 'Evaluaciones' del archivo Excel de evaluaciones y valida sus columnas.
    """
    df = pd.read_excel(origen, sheet_name="Evaluaciones")
    
    columnas_esperadas = {"Identificacion", "Programa", "Modulo", "Nota", "Asistencia_Pct", "Fecha_Cierre"}
    columnas_presentes = set(df.columns)
    columnas_faltantes = columnas_esperadas - columnas_presentes
    if columnas_faltantes:
        raise ValueError(f"El archivo de Evaluaciones no contiene las columnas requeridas: {columnas_faltantes}")
    
    registros: List[Dict[str, Any]] = []
    for _, fila in df.iterrows():
        identificacion = limpiar_identificacion(fila["Identificacion"])
        if not identificacion:
            continue  # Ignorar filas vacías
        
        try:
            nota = float(fila["Nota"]) if pd.notna(fila["Nota"]) else 0.0
        except (ValueError, TypeError):
            nota = 0.0
            
        try:
            asistencia_pct = float(fila["Asistencia_Pct"]) if pd.notna(fila["Asistencia_Pct"]) else 0.0
        except (ValueError, TypeError):
            asistencia_pct = 0.0
            
        fecha_cierre = formatear_fecha(fila["Fecha_Cierre"])
        
        registros.append({
            "identificacion": identificacion,
            "programa": limpiar_texto(fila["Programa"]),
            "modulo": limpiar_texto(fila["Modulo"]),
            "nota": nota,
            "asistencia_pct": asistencia_pct,
            "fecha_cierre": fecha_cierre,
        })
    return registros


def procesar_y_guardar_archivos(origen_estudiantes: Union[str, Any], origen_evaluaciones: Union[str, Any]) -> Dict[str, int]:
    """
    Lee ambos archivos, valida y reemplaza la información en Supabase.
    Retorna un diccionario con la cantidad de filas procesadas.
    """
    estudiantes = leer_maestro_estudiantes(origen_estudiantes)
    evaluaciones = leer_registro_evaluaciones(origen_evaluaciones)
    
    total_estudiantes = reemplazar_estudiantes(estudiantes)
    total_evaluaciones = reemplazar_evaluaciones(evaluaciones)
    
    return {
        "estudiantes": total_estudiantes,
        "evaluaciones": total_evaluaciones,
    }


def cargar_desde_insumos() -> Dict[str, int]:
    """
    Carga los datos leyendo directamente de la carpeta insumos/.
    No modifica los archivos originales.
    """
    ruta_estudiantes = resolver_ruta_archivo("Maestro_Estudiantes.xlsx")
    ruta_evaluaciones = resolver_ruta_archivo("Registro_Evaluaciones.xlsx")
    
    return procesar_y_guardar_archivos(ruta_estudiantes, ruta_evaluaciones)
