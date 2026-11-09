"""`obtener_detalle` con un repositorio falso: sin base."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.cohortes.domain.tipos import TipoCarrera
from src.gestion_documental.domain.tipos import TipoDocumento
from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.application.obtener_detalle import (
    MENSAJE_LEGAJO_NO_ENCONTRADO,
    CarreraResumen,
    CohorteResumen,
    DocumentoCargado,
    FichaLegajo,
    ItemDocumento,
    obtener_detalle,
)
from src.legajos.domain.entidades import RegistroAuditoria
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.shared.errors import NoEncontrado
from src.shared.roles import Rol

AHORA = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)


class RepoEnMemoria:
    def __init__(
        self,
        ficha: FichaLegajo,
        cargados: list[DocumentoCargado] | None = None,
        historial: list[RegistroAuditoria] | None = None,
    ) -> None:
        self._ficha = ficha
        self._cargados = cargados or []
        self._historial = historial or []

    def ficha(self, legajo_id: UUID) -> FichaLegajo | None:
        return self._ficha if legajo_id == self._ficha.id else None

    def documentos_cargados(self, legajo_id: UUID) -> list[DocumentoCargado]:
        return self._cargados

    def historial(self, legajo_id: UUID) -> list[RegistroAuditoria]:
        return self._historial


def nueva_ficha(**campos) -> FichaLegajo:
    datos = {
        "id": uuid4(),
        "codigo_seguimiento": "7F3A9C21",
        "numero_legajo": None,
        "estado": EstadoLegajo.EN_REVISION,
        "cohorte": CohorteResumen(id=uuid4(), nombre="Cohorte 2026", anio=2026),
        "carreras": [
            CarreraResumen(
                id=uuid4(), nombre="Maestría en Tecnología Informática", tipo=TipoCarrera.MAESTRIA
            )
        ],
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "nacionalidad": "Argentina",
        "dni": "28456789",
        "telefono_movil": "+54 221 4567890",
        "telefono_fijo": None,
        "email": "ana@example.com",
        "email_alternativo": None,
        "domicilio": "Av. 7 Nro. 1234",
        "ciudad": "La Plata",
        "provincia": "Buenos Aires",
        "pais": "Argentina",
        "titulo_grado": "Ingeniería en Sistemas de Información",
        "titulo_posgrado": None,
        "como_conocio": ComoConocio.EGRESADOS,
        "motivacion": "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo.",
        "solicita_beca": False,
        "tipo_beca": None,
        "fecha_inscripcion": AHORA,
        "fecha_aprobacion": None,
        "fecha_activacion": None,
        "created_at": AHORA - timedelta(hours=1),
    }
    datos.update(campos)
    return FichaLegajo(**datos)


def documento(tipo: TipoDocumento, nombre: str = "archivo.pdf") -> DocumentoCargado:
    return DocumentoCargado(
        id=uuid4(), tipo=tipo, nombre_original=nombre, tamanio_bytes=183_412, fecha_subida=AHORA
    )


def registro(legajo_id: UUID, accion: Accion, comentario: str | None = None, **campos):
    datos = {
        "legajo_id": legajo_id,
        "accion": accion,
        "estado_anterior": EstadoLegajo.PENDIENTE,
        "estado_nuevo": EstadoLegajo.EN_REVISION,
        "comentario": comentario,
        "rol": Rol.COORDINADOR,
        "usuario_email": "coordinador@example.com",
        "fecha": AHORA,
    }
    datos.update(campos)
    return RegistroAuditoria(**datos)


# --- Datos y no encontrado ---


def test_trae_todos_los_datos_de_la_ficha():
    ficha = nueva_ficha()

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha), "coordinador")

    for nombre in FichaLegajo.__dataclass_fields__:
        assert getattr(detalle, nombre) == getattr(ficha, nombre), nombre


def test_legajo_inexistente_da_no_encontrado():
    with pytest.raises(NoEncontrado, match=MENSAJE_LEGAJO_NO_ENCONTRADO):
        obtener_detalle(uuid4(), RepoEnMemoria(nueva_ficha()), "coordinador")


# --- Documentos ---


def test_los_documentos_son_los_requeridos_con_los_datos_del_archivo_cargado():
    ficha = nueva_ficha()
    dni = documento(TipoDocumento.DNI, "dni.pdf")

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, cargados=[dni]), "coordinador")

    assert [item.tipo for item in detalle.documentos] == [
        TipoDocumento.FORM_INSCRIPCION,
        TipoDocumento.DNI,
        TipoDocumento.TITULO_GRADO,
        TipoDocumento.PARTIDA,
        TipoDocumento.CUIT_CUIL,
    ]
    assert detalle.documentos[1] == ItemDocumento(
        tipo=TipoDocumento.DNI,
        nombre="Copia del DNI o pasaporte",
        obligatorio=True,
        cargado=True,
        documento_id=dni.id,
        nombre_original="dni.pdf",
        tamanio_bytes=183_412,
        fecha_subida=AHORA,
    )
    assert detalle.documentos[2] == ItemDocumento(
        tipo=TipoDocumento.TITULO_GRADO,
        nombre="Copia del título de grado",
        obligatorio=True,
        cargado=False,
    )
    assert all(item.obligatorio for item in detalle.documentos)


def test_los_faltantes_son_los_requeridos_sin_cargar_en_el_orden_del_checklist():
    ficha = nueva_ficha(titulo_posgrado="Especialista en Redes")
    cargados = [documento(TipoDocumento.FORM_INSCRIPCION), documento(TipoDocumento.PARTIDA)]

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, cargados=cargados), "coordinador")

    assert detalle.documentos_faltantes == [
        TipoDocumento.DNI,
        TipoDocumento.TITULO_GRADO,
        TipoDocumento.CUIT_CUIL,
        TipoDocumento.TITULO_POSGRADO,
    ]


def test_con_beca_y_titulo_de_posgrado_pide_los_7_documentos():
    ficha = nueva_ficha(
        solicita_beca=True, tipo_beca=TipoBeca.TREINTA, titulo_posgrado="Especialista en Redes"
    )

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha), "coordinador")

    assert len(detalle.documentos) == 7
    assert detalle.documentos[-2].tipo == TipoDocumento.TITULO_POSGRADO
    assert detalle.documentos[-1].tipo == TipoDocumento.FORM_BECA


@pytest.mark.parametrize(
    ("titulo_posgrado", "lo_pide"), [(None, False), ("Especialista en Redes", True)]
)
def test_pide_la_copia_del_titulo_de_posgrado_solo_si_declaro_uno(titulo_posgrado, lo_pide):
    # Los opcionales vacíos llegan como None desde el formulario de Fran (#44).
    ficha = nueva_ficha(titulo_posgrado=titulo_posgrado)

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha), "coordinador")

    assert (TipoDocumento.TITULO_POSGRADO in [item.tipo for item in detalle.documentos]) is lo_pide


def test_un_documento_cargado_que_ya_no_corresponde_no_aparece():
    # Subió el formulario de beca y después sacó la beca.
    ficha = nueva_ficha(solicita_beca=False)
    cargados = [documento(TipoDocumento.FORM_BECA)]

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, cargados=cargados), "coordinador")

    assert TipoDocumento.FORM_BECA not in [item.tipo for item in detalle.documentos]


# --- Última observación ---


def test_sin_observaciones_la_ultima_observacion_es_nula():
    ficha = nueva_ficha()
    historial = [registro(ficha.id, Accion.REVISAR)]

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, historial=historial), "coordinador")

    assert detalle.ultima_observacion is None


def test_la_ultima_observacion_es_el_comentario_del_ultimo_observar():
    ficha = nueva_ficha()
    historial = [
        registro(ficha.id, Accion.OBSERVAR, "Falta el DNI"),
        registro(ficha.id, Accion.CORREGIR, rol=Rol.ASPIRANTE, usuario_email=None),
        registro(ficha.id, Accion.REVISAR),
        registro(ficha.id, Accion.OBSERVAR, "El título no está legalizado"),
        registro(ficha.id, Accion.CORREGIR, rol=Rol.ASPIRANTE, usuario_email=None),
    ]

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, historial=historial), "aspirante")

    assert detalle.ultima_observacion == "El título no está legalizado"


# --- Vistas ---


@pytest.mark.parametrize(
    ("estado", "acciones"),
    [
        (EstadoLegajo.PENDIENTE, [Accion.REVISAR]),
        (EstadoLegajo.EN_REVISION, [Accion.OBSERVAR, Accion.APROBAR, Accion.RECHAZAR]),
        (EstadoLegajo.COMPLETADO, [Accion.MATRICULAR]),
        (EstadoLegajo.OBSERVADO, []),
    ],
)
def test_la_vista_coordinador_trae_historial_y_acciones_permitidas(estado, acciones):
    ficha = nueva_ficha(estado=estado)
    historial = [registro(ficha.id, Accion.REVISAR)]

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, historial=historial), "coordinador")

    assert detalle.historial == historial
    assert detalle.acciones_permitidas == acciones
    assert detalle.puede_editar is None


@pytest.mark.parametrize(
    ("estado", "puede_editar"),
    [
        (EstadoLegajo.BORRADOR, True),
        (EstadoLegajo.OBSERVADO, True),
        (EstadoLegajo.PENDIENTE, False),
        (EstadoLegajo.EN_REVISION, False),
        (EstadoLegajo.COMPLETADO, False),
    ],
)
def test_la_vista_aspirante_trae_puede_editar_y_no_el_historial(estado, puede_editar):
    ficha = nueva_ficha(estado=estado)
    historial = [registro(ficha.id, Accion.REVISAR)]

    detalle = obtener_detalle(ficha.id, RepoEnMemoria(ficha, historial=historial), "aspirante")

    assert detalle.puede_editar is puede_editar
    assert detalle.historial is None
    assert detalle.acciones_permitidas is None
