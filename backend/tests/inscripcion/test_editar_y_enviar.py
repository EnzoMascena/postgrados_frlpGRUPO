"""Casos de uso `editar_legajo` y `enviar_legajo` con piezas falsas: sin base ni emails."""

from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

import pytest

from src.gestion_documental.domain.documento import LegajoParaDocumentos
from src.gestion_documental.domain.requisitos import DOCUMENTOS_OBLIGATORIOS, DocumentosFaltantes
from src.gestion_documental.domain.tipos import TipoDocumento as T
from src.inscripcion.application.editar_legajo import MENSAJE_LEGAJO_NO_EDITABLE, editar_legajo
from src.inscripcion.application.enviar_legajo import enviar_legajo
from src.inscripcion.domain.errores import LegajoNoEditable, PeriodoCerrado
from src.inscripcion.domain.inscripcion import MENSAJE_DNI_REPETIDO
from src.legajos.domain.estados import Accion, EstadoLegajo, TransicionInvalida
from src.shared.errors import Conflicto, ErrorDeValidacion, NoEncontrado
from src.shared.roles import Actor, Rol
from tests.inscripcion.test_casos_de_uso import (
    CARRERA,
    RepoEnMemoria,
    inscribir_con,
    un_formulario,
    una_cohorte,
)

NO_EDITABLES = [e for e in EstadoLegajo if e not in (EstadoLegajo.BORRADOR, EstadoLegajo.OBSERVADO)]


# --- editar_legajo ---


def con_un_legajo(**cambios_cohorte):
    cohorte = una_cohorte(**cambios_cohorte)
    repo = RepoEnMemoria(cohorte)
    legajo_id = inscribir_con(repo, un_formulario(cohorte)).legajo_id
    return repo, cohorte, legajo_id


def editar(repo, legajo_id, **cambios):
    """Edita con el formulario de siempre más `cambios`; la cohorte la pone el caso de uso."""

    def armar_datos(cohorte_id: UUID):
        return replace(un_formulario(repo.cohortes[cohorte_id]), **cambios)

    editar_legajo(legajo_id, armar_datos, repo)


def datos_guardados(repo, legajo_id):
    return next(datos for i, datos, _ in repo.legajos if i == legajo_id)


def test_editar_reemplaza_los_datos_y_conserva_la_cohorte():
    repo, cohorte, legajo_id = con_un_legajo()

    editar(repo, legajo_id, apellido="Gómez", motivacion="m" * 60)

    datos = datos_guardados(repo, legajo_id)
    assert (datos.apellido, datos.motivacion, datos.cohorte_id) == ("Gómez", "m" * 60, cohorte.id)


def test_el_propio_dni_y_email_no_cuentan_como_repetidos():
    repo, _, legajo_id = con_un_legajo()

    editar(repo, legajo_id, apellido="Gómez")  # mismo DNI y email que ya tenía

    assert datos_guardados(repo, legajo_id).apellido == "Gómez"


def test_el_dni_de_otro_legajo_de_la_cohorte_da_409():
    repo, cohorte, legajo_id = con_un_legajo()
    inscribir_con(repo, un_formulario(cohorte, dni="30111222", email="otra@example.com"))

    with pytest.raises(Conflicto) as error:
        editar(repo, legajo_id, dni="30111222")

    assert (error.value.campo, error.value.mensaje) == ("dni", MENSAJE_DNI_REPETIDO)


@pytest.mark.parametrize("estado", NO_EDITABLES)
def test_fuera_de_borrador_u_observado_da_409_y_no_cambia_nada(estado):
    repo, _, legajo_id = con_un_legajo()
    repo.estados[legajo_id] = estado

    with pytest.raises(LegajoNoEditable) as error:
        editar(repo, legajo_id, apellido="Gómez")

    assert (error.value.status_code, error.value.mensaje) == (409, MENSAJE_LEGAJO_NO_EDITABLE)
    assert datos_guardados(repo, legajo_id).apellido == "Rodríguez"


def test_en_observado_se_puede_editar():
    repo, _, legajo_id = con_un_legajo()
    repo.estados[legajo_id] = EstadoLegajo.OBSERVADO

    editar(repo, legajo_id, apellido="Gómez")

    assert datos_guardados(repo, legajo_id).apellido == "Gómez"


def test_con_el_periodo_cerrado_no_se_puede_editar():
    repo, cohorte, legajo_id = con_un_legajo()
    repo.cohortes[cohorte.id] = replace(
        cohorte, inscripcion_abierta=False, proxima_apertura=date(2027, 3, 1)
    )

    with pytest.raises(PeriodoCerrado):
        editar(repo, legajo_id, apellido="Gómez")


def test_una_carrera_inactiva_da_422():
    repo, _, legajo_id = con_un_legajo()

    with pytest.raises(ErrorDeValidacion) as error:
        editar(repo, legajo_id, carrera_ids=(CARRERA, uuid4()))

    assert error.value.campo == "carreraIds"


def test_editar_un_legajo_que_no_existe_da_404():
    repo, _, _ = con_un_legajo()

    with pytest.raises(NoEncontrado):
        editar(repo, uuid4(), apellido="Gómez")


# --- enviar_legajo ---


class RepoDocumentos:
    def __init__(self, legajo: LegajoParaDocumentos | None, cargados=DOCUMENTOS_OBLIGATORIOS):
        self._legajo = legajo
        self.cargados = list(cargados)

    def legajo(self, legajo_id: UUID) -> LegajoParaDocumentos | None:
        return self._legajo

    def tipos_cargados(self, legajo_id: UUID) -> list[T]:
        return self.cargados


class Servicio:
    """Hace de `ServicioEstados.cambiar` y anota cada llamada."""

    def __init__(self) -> None:
        self.llamadas: list[tuple[UUID, Accion, Actor]] = []

    def cambiar(self, legajo_id: UUID, accion: Accion, actor: Actor) -> None:
        self.llamadas.append((legajo_id, accion, actor))


def un_legajo(estado=EstadoLegajo.BORRADOR, beca=False) -> LegajoParaDocumentos:
    return LegajoParaDocumentos(uuid4(), uuid4(), estado, beca, False)


@pytest.mark.parametrize(
    ("estado", "accion"),
    [(EstadoLegajo.BORRADOR, Accion.ENVIAR), (EstadoLegajo.OBSERVADO, Accion.CORREGIR)],
)
def test_con_todo_cargado_envia_o_corrige_segun_el_estado(estado, accion):
    legajo, servicio = un_legajo(estado), Servicio()

    resultado = enviar_legajo(legajo.id, RepoDocumentos(legajo), servicio.cambiar)

    assert resultado == accion
    assert servicio.llamadas == [(legajo.id, accion, Actor(Rol.ASPIRANTE))]


def test_si_falta_un_documento_da_422_y_no_cambia_el_estado():
    legajo, servicio = un_legajo(), Servicio()
    cargados = [T.FORM_INSCRIPCION, T.DNI, T.PARTIDA, T.CUIT_CUIL]

    with pytest.raises(DocumentosFaltantes) as error:
        enviar_legajo(legajo.id, RepoDocumentos(legajo, cargados), servicio.cambiar)

    assert error.value.mensaje == "Faltan documentos obligatorios: Copia del título de grado"
    assert servicio.llamadas == []


def test_con_beca_tambien_pide_el_formulario_de_beca():
    legajo, servicio = un_legajo(beca=True), Servicio()

    with pytest.raises(DocumentosFaltantes):
        enviar_legajo(legajo.id, RepoDocumentos(legajo), servicio.cambiar)

    assert servicio.llamadas == []


def test_un_legajo_ya_enviado_da_409_antes_de_mirar_los_documentos():
    legajo, servicio = un_legajo(EstadoLegajo.PENDIENTE), Servicio()

    with pytest.raises(TransicionInvalida) as error:
        enviar_legajo(legajo.id, RepoDocumentos(legajo, cargados=[]), servicio.cambiar)

    assert error.value.status_code == 409
    assert servicio.llamadas == []


def test_enviar_un_legajo_que_no_existe_da_404():
    with pytest.raises(NoEncontrado):
        enviar_legajo(uuid4(), RepoDocumentos(None), Servicio().cambiar)
