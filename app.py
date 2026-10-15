"""
LA COCINA (app.py) — Academia Horizonte.

Punto de entrada de la aplicación web con Flask.
Aquí NO se calcula nada: solo se enciende el servidor
y se conectan las piezas (controladores -> modelos -> vistas).

Lógica reutilizada de models/certificados.py:
- FUNCIÓN calcular_promedio (promedio redondeado a 2 decimales).
- FUNCIÓN decidir_certificado (CONDICIONALES con límites inclusivos).
- BUCLE que recorre cada estudiante y cruza por Identificación + Programa.
"""

# LADRILLO: variables (librería Flask, rutas y controlador del tablero)
import os
from pathlib import Path

from flask import Flask
from controllers.tablero import tablero_bp


# LADRILLO: variables (carpeta raíz del proyecto, salga de donde salga el arranque)
# Path(__file__) = ubicación de ESTE archivo; así "Insumos/" se encuentra
# aunque la app se ejecute desde otra carpeta (por ejemplo, en Vercel).
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)


# LADRILLO: función (arma la aplicación y conecta sus piezas)
def crear_app():
    # LADRILLO: variable tipo Flask (template_folder apunta al SALÓN: views/)
    app = Flask(__name__, template_folder="views")
    # Conecta el controlador de la ruta "/" con la aplicación
    app.register_blueprint(tablero_bp)
    return app


# LADRILLO: variable (la aplicación lista para servir)
app = crear_app()


# LADRILLO: condicional (solo arranca el servidor si se ejecuta este archivo)
if __name__ == "__main__":
    # Puerto 5000 = http://localhost:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
