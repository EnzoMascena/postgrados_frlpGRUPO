"""Vista previa de las plantillas de email.

Renderiza las 6 plantillas de `src/shared/email/templates/` con datos de ejemplo y las guarda en
`backend/.storage/previews/` (carpeta que no se sube) para abrirlas en el navegador:

    cd backend && uv run python scripts/previsualizar_emails.py

El logo no se ve en la vista previa: es una imagen embebida (`cid:logo-utn`) que solo existe
cuando `enviar_email` arma el mensaje. Está bien que aparezca el texto alternativo.

Los contextos de `EJEMPLOS` también los usa `tests/shared/test_plantillas_email.py`: si cambia
una variable, cambia en los dos lados.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

BACKEND = Path(__file__).resolve().parents[1]
CARPETA_PLANTILLAS = BACKEND / "src" / "shared" / "email" / "templates"
CARPETA_SALIDA = BACKEND / ".storage" / "previews"

# Un contexto por plantilla, con las variables del plan §11 (ni una más ni una menos).
EJEMPLOS: dict[str, dict[str, object]] = {
    "link_seguimiento.html": {
        "nombre": "Martina",
        "codigo_seguimiento": "PRE-2026-0042",
        "link": "http://localhost:3000/seguimiento/ejemplo-token-123",
    },
    "confirmacion_envio.html": {
        "nombre": "Martina",
        "codigo_seguimiento": "PRE-2026-0042",
        "carreras": [
            "Especialización en Ingeniería en Sistemas de Información",
            "Maestría en Ingeniería en Calidad",
        ],
        "cohorte": "Cohorte 2027",
        "es_correccion": False,
    },
    "observacion.html": {
        "nombre": "Martina",
        "comentario": "El título de grado está cortado en la segunda página.\nSubilo completo, por favor.",
        "link_recuperar": "http://localhost:3000/inscripcion?recuperar=1",
    },
    "aprobacion.html": {
        "nombre": "Martina",
        "numero_legajo": "2027-0015",
        "carreras": ["Especialización en Ingeniería en Sistemas de Información"],
        "fecha_limite": "30/12/2026",
    },
    "rechazo.html": {
        "nombre": "Martina",
        "comentario": "No cumple con el requisito de título de grado afín a la carrera.",
    },
    "vencimiento_coordinador.html": {
        "apellido": "Pérez",
        "nombre": "Martina",
        "numero_legajo": "2027-0015",
        "fecha_aprobacion": "30/11/2026",
    },
}


def crear_entorno() -> Environment:
    # autoescape: todo lo que entra por una variable (por ejemplo, el comentario del
    # coordinador) se escapa, así un <script> sale como texto. StrictUndefined: si falta una
    # variable, el render falla en vez de dejar un hueco en blanco en el email.
    return Environment(
        loader=FileSystemLoader(CARPETA_PLANTILLAS),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )


def main() -> None:
    entorno = crear_entorno()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    for plantilla, contexto in EJEMPLOS.items():
        destino = CARPETA_SALIDA / plantilla
        destino.write_text(entorno.get_template(plantilla).render(**contexto), encoding="utf-8")
        print(f"{plantilla:<30} -> {destino}")


if __name__ == "__main__":
    main()
