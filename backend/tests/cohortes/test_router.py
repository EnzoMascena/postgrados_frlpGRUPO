"""`GET /cohortes`, `GET /carreras` y `PATCH /cohortes/{id}/inscripcion` contra la app real y la
base de test."""

from datetime import date
from uuid import uuid4

from src.cohortes.domain.tipos import TipoCarrera
from tests.fabricas import crear_carrera, crear_cohorte

COHORTES = "/api/v1/cohortes"
CARRERAS = "/api/v1/carreras"


def inscripcion(cohorte_id) -> str:
    return f"{COHORTES}/{cohorte_id}/inscripcion"


def periodos(client) -> dict[str, tuple[bool, str | None]]:
    """Nombre de cada cohorte → (inscripcionAbierta, proximaApertura), según `GET /cohortes`."""
    return {
        c["nombre"]: (c["inscripcionAbierta"], c["proximaApertura"])
        for c in client.get(COHORTES).json()
    }


# --- GET /cohortes y GET /carreras ---


def test_get_cohortes_es_publico_y_devuelve_el_json_del_plan(client, session):
    cohorte = crear_cohorte(session, anio=2026, fecha_inicio=date(2026, 4, 1))

    respuesta = client.get(COHORTES)

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {
            "id": str(cohorte.id),
            "anio": 2026,
            "numero": 1,
            "nombre": "Cohorte 2026",
            "inscripcionAbierta": True,
            "fechaInicio": "2026-04-01",
            "proximaApertura": None,
        }
    ]


def test_get_cohortes_ordena_de_la_mas_nueva_a_la_mas_vieja(client, session):
    crear_cohorte(session, anio=2025)
    crear_cohorte(session, anio=2026, numero=2)
    crear_cohorte(session, anio=2026)

    nombres = [c["nombre"] for c in client.get(COHORTES).json()]

    assert nombres == ["Cohorte 2026-2", "Cohorte 2026", "Cohorte 2025"]


def test_get_carreras_es_publico_y_devuelve_solo_las_activas_por_nombre(client, session):
    maestria = crear_carrera(session, nombre="Maestría en Ingeniería")
    especializacion = crear_carrera(
        session, nombre="Especialización en Ingeniería", tipo=TipoCarrera.ESPECIALIZACION
    )
    crear_carrera(
        session, nombre="Doctorado en Ingeniería", tipo=TipoCarrera.DOCTORADO, activa=False
    )

    respuesta = client.get(CARRERAS)

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {
            "id": str(especializacion.id),
            "nombre": "Especialización en Ingeniería",
            "tipo": "Especializacion",
        },
        {"id": str(maestria.id), "nombre": "Maestría en Ingeniería", "tipo": "Maestria"},
    ]


# --- PATCH /cohortes/{id}/inscripcion ---


def test_patch_sin_token_da_401(client, session):
    cohorte = crear_cohorte(session)

    respuesta = client.patch(inscripcion(cohorte.id), json={"abierta": False})

    assert respuesta.status_code == 401
    assert periodos(client)["Cohorte 2026"] == (True, None)


def test_patch_con_un_rol_que_no_es_coordinador_da_403(client, session, headers_docente):
    cohorte = crear_cohorte(session)

    respuesta = client.patch(
        inscripcion(cohorte.id), json={"abierta": False}, headers=headers_docente
    )

    assert respuesta.status_code == 403
    assert periodos(client)["Cohorte 2026"] == (True, None)


def test_el_coordinador_cierra_con_proxima_apertura_y_queda_guardado(
    client, session, headers_coordinador
):
    cohorte = crear_cohorte(session)

    respuesta = client.patch(
        inscripcion(cohorte.id),
        json={"abierta": False, "proximaApertura": "2099-03-01"},
        headers=headers_coordinador,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["inscripcionAbierta"] is False
    assert respuesta.json()["proximaApertura"] == "2099-03-01"
    assert periodos(client)["Cohorte 2026"] == (False, "2099-03-01")


def test_el_coordinador_abre_y_se_borra_la_proxima_apertura(client, session, headers_coordinador):
    cohorte = crear_cohorte(session, abierta=False, proxima_apertura=date(2099, 3, 1))

    respuesta = client.patch(
        inscripcion(cohorte.id), json={"abierta": True}, headers=headers_coordinador
    )

    assert respuesta.status_code == 200
    assert periodos(client)["Cohorte 2026"] == (True, None)


def test_cada_cohorte_tiene_su_propio_periodo(client, session, headers_coordinador):
    cohorte_2025 = crear_cohorte(session, anio=2025)
    crear_cohorte(session, anio=2026)

    client.patch(inscripcion(cohorte_2025.id), json={"abierta": False}, headers=headers_coordinador)

    assert periodos(client) == {"Cohorte 2026": (True, None), "Cohorte 2025": (False, None)}


def test_patch_con_una_proxima_apertura_pasada_da_422_con_el_campo(
    client, session, headers_coordinador
):
    cohorte = crear_cohorte(session)

    respuesta = client.patch(
        inscripcion(cohorte.id),
        json={"abierta": False, "proximaApertura": "2020-01-01"},
        headers=headers_coordinador,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "VALIDATION_ERROR"
    assert respuesta.json()["field"] == "proximaApertura"
    assert periodos(client)["Cohorte 2026"] == (True, None)


def test_patch_sin_abierta_da_422(client, session, headers_coordinador):
    cohorte = crear_cohorte(session)

    respuesta = client.patch(inscripcion(cohorte.id), json={}, headers=headers_coordinador)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "VALIDATION_ERROR"


def test_patch_de_una_cohorte_que_no_existe_da_404(client, headers_coordinador):
    respuesta = client.patch(
        inscripcion(uuid4()), json={"abierta": False}, headers=headers_coordinador
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "NOT_FOUND"
