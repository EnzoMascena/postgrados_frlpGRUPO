"""Tests de las plantillas de email (plan §11).

No usan base de datos: renderizan cada plantilla con Jinja2 y miran el HTML que sale.
Los contextos de ejemplo son los mismos que usa `scripts/previsualizar_emails.py`.
"""

import pytest
from jinja2 import UndefinedError

from scripts.previsualizar_emails import CARPETA_PLANTILLAS, EJEMPLOS, crear_entorno

SCRIPT = "<script>alert('hola')</script>"


@pytest.fixture(scope="module")
def entorno():
    return crear_entorno()


def renderizar(entorno, plantilla: str, **cambios) -> str:
    return entorno.get_template(plantilla).render(**{**EJEMPLOS[plantilla], **cambios})


def test_estan_las_seis_plantillas_y_la_base():
    archivos = {p.name for p in CARPETA_PLANTILLAS.glob("*.html")}
    assert archivos == {"base.html", *EJEMPLOS}


@pytest.mark.parametrize("plantilla", EJEMPLOS)
def test_renderiza_con_el_logo_y_el_pie(entorno, plantilla):
    html = renderizar(entorno, plantilla)
    assert 'src="cid:logo-utn"' in html
    assert "Sistema de Posgrado" in html
    assert "Este es un mensaje automático, no lo respondas" in html


@pytest.mark.parametrize("plantilla", EJEMPLOS)
def test_aparece_cada_variable(entorno, plantilla):
    html = renderizar(entorno, plantilla)
    for variable, valor in EJEMPLOS[plantilla].items():
        if isinstance(valor, bool):
            continue  # es_correccion no se imprime: cambia el título (test aparte)
        valores = valor if isinstance(valor, list) else [valor]
        for v in valores:
            # El comentario tiene saltos de línea y comillas: se compara ya escapado.
            assert str(entorno.from_string("{{ v }}").render(v=v)) in html, (
                f"{plantilla}: no aparece {variable}"
            )


@pytest.mark.parametrize(
    ("plantilla", "variable"),
    [(p, v) for p, contexto in EJEMPLOS.items() for v in contexto],
)
def test_si_falta_una_variable_falla(entorno, plantilla, variable):
    contexto = {k: v for k, v in EJEMPLOS[plantilla].items() if k != variable}
    with pytest.raises(UndefinedError):
        entorno.get_template(plantilla).render(**contexto)


@pytest.mark.parametrize("plantilla", ["observacion.html", "rechazo.html"])
def test_el_comentario_con_script_sale_escapado(entorno, plantilla):
    html = renderizar(entorno, plantilla, comentario=SCRIPT)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_confirmacion_cambia_el_titulo_si_es_correccion(entorno):
    envio = renderizar(entorno, "confirmacion_envio.html", es_correccion=False)
    correccion = renderizar(entorno, "confirmacion_envio.html", es_correccion=True)
    assert "Recibimos tu preinscripción" in envio
    assert "Recibimos tu corrección" not in envio
    assert "Recibimos tu corrección" in correccion


def test_rechazo_sin_comentario_no_muestra_el_motivo(entorno):
    html = renderizar(entorno, "rechazo.html", comentario="")
    assert "El motivo que dejó la Secretaría" not in html
    assert "no fue aceptada" in html


@pytest.mark.parametrize("plantilla", EJEMPLOS)
def test_sin_javascript_ni_recursos_externos(entorno, plantilla):
    html = renderizar(entorno, plantilla).lower()
    assert "<script" not in html
    assert "<link" not in html
    assert 'src="http' not in html
