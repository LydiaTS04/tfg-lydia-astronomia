import os
import runpy

# Ejecuta el gestor completo (sus pestañas: datos, mediciones, resultados,
# animación, errores y fotos) como esta página de la app.
_GESTOR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "gestor_web.py",
)
runpy.run_path(_GESTOR, run_name="__main__")
