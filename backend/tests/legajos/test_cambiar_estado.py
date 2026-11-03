"""`ServicioEstados` con un repositorio y un notificador falsos: sin base y sin emails."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.legajos.application.cambiar_estado import MENSAJE_LEGAJO_NO_ENCONTRADO, ServicioEstados
from src.legajos.domain.entidades import DatosCohorte, Legajo, RegistroAuditoria
from src.legajos.domain.estados import Accion, EstadoLegajo, TransicionInvalida
from src.shared.errors import ErrorDeValidacion, NoEncontrado, SinPermiso
from src.shared.roles import Actor, Rol

AHORA = datetime(2026, 11, 3, 15, 30, tzinfo=UTC)
COORDINADOR = Actor(Rol.COORDINADOR, "coordinador@example.com")
ASPIRANTE = Actor(Rol.ASPIRANTE)
SISTEMA = Actor(Rol.SISTEMA)


class RepoEnMemoria:
    """Guarda copias: si el servicio toca el legajo y después falla, lo guardado no cambia.

    `eventos` anota el orden de las llamadas, compartido con el notificador falso.
    """

    def __init__(self, eventos: list[str], ultimo_secuencial: int = 0) -> None:
        self.legajos: dict[UUID, Legajo] = {}
        self.registros: list[RegistroAuditoria] = []
        self.eventos = eventos
        self.ultimo_secuencial = ultimo_secuencial
        self.cohorte = DatosCohorte(anio=2026, numero=1, nombre="Cohorte 2026")

    def agregar(self, legajo: Legajo) -> Legajo:
        self.legajos[legajo.id] = replace(legajo)
        return legajo

    def obtener(self, legajo_id: UUID) -> Legajo | None:
        legajo = self.legajos.get(legajo_id)
        return replace(legajo) if legajo else None

    def siguiente_secuencial(self, cohorte_id: UUID) -> int:
        self.eventos.append("secuencial")
        return self.ultimo_secuencial + 1

    def datos_cohorte(self, cohorte_id: UUID) -> DatosCohorte:
        return self.cohorte

    def nombres_carreras(self, legajo_id: UUID) -> list[str]:
        return ["Maestría en Tecnología Informática"]

    def guardar_cambio(self, legajo: Legajo, registro: RegistroAuditoria) -> None:
        self.eventos.append("guardar")
        self.legajos[legajo.id] = replace(legajo)
        self.registros.append(registro)


class NotificadorFalso:
    def __init__(self, eventos: list[str], falla: bool = False) -> None:
        self.avisos: list[tuple[Legajo, Accion, str | None]] = []
        self.eventos = eventos
        self.falla = falla

    def notificar(self, legajo: Legajo, accion: Accion, comentario: str | None) -> None:
        self.eventos.append("notificar")
        if self.falla:
            raise RuntimeError("plantilla rota")
        self.avisos.append((replace(legajo), accion, comentario))


def nuevo_legajo(estado: EstadoLegajo, **campos) -> Legajo:
    datos = {
        "id": uuid4(),
        "cohorte_id": uuid4(),
        "estado": estado,
        "numero_legajo": None,
        "codigo_seguimiento": "7F3A9C21",
        "nombre": "Ana Laura",
        "apellido": "Rodríguez",
        "email": "ana.rodriguez@example.com",
    }
    datos.update(campos)
    return Legajo(**datos)


@pytest.fixture
def eventos() -> list[str]:
    return []


@pytest.fixture
def repo(eventos) -> RepoEnMemoria:
    return RepoEnMemoria(eventos)


@pytest.fixture
def notificador(eventos) -> NotificadorFalso:
    return NotificadorFalso(eventos)


@pytest.fixture
def servicio(repo, notificador) -> ServicioEstados:
    return ServicioEstados(repo, notificador, reloj=lambda: AHORA)


# --- Cada acción válida: estado nuevo, auditoría y aviso ---


@pytest.mark.parametrize(
    ("accion", "desde", "hacia", "actor"),
    [
        (Accion.ENVIAR, EstadoLegajo.BORRADOR, EstadoLegajo.PENDIENTE, ASPIRANTE),
        (Accion.REVISAR, EstadoLegajo.PENDIENTE, EstadoLegajo.EN_REVISION, COORDINADOR),
        (Accion.OBSERVAR, EstadoLegajo.EN_REVISION, EstadoLegajo.OBSERVADO, COORDINADOR),
        (Accion.CORREGIR, EstadoLegajo.OBSERVADO, EstadoLegajo.PENDIENTE, ASPIRANTE),
        (Accion.APROBAR, EstadoLegajo.EN_REVISION, EstadoLegajo.COMPLETADO, COORDINADOR),
        (Accion.RECHAZAR, EstadoLegajo.EN_REVISION, EstadoLegajo.RECHAZADO, COORDINADOR),
        (Accion.MATRICULAR, EstadoLegajo.COMPLETADO, EstadoLegajo.ACTIVO, COORDINADOR),
        (Accion.VENCER, EstadoLegajo.COMPLETADO, EstadoLegajo.VENCIDO, SISTEMA),
        (Accion.DAR_DE_BAJA, EstadoLegajo.ACTIVO, EstadoLegajo.BAJA, COORDINADOR),
        (Accion.GRADUAR, EstadoLegajo.ACTIVO, EstadoLegajo.GRADUADO, SISTEMA),
    ],
)
def test_cada_accion_valida_cambia_el_estado_audita_y_avisa(
    servicio, repo, notificador, accion, desde, hacia, actor
):
    legajo = repo.agregar(nuevo_legajo(desde))
    comentario = "Falta la copia del título legalizada"

    resultado = servicio.cambiar(legajo.id, accion, actor, comentario)

    assert resultado.estado == hacia
    assert repo.legajos[legajo.id].estado == hacia
    assert repo.registros == [
        RegistroAuditoria(
            legajo_id=legajo.id,
            accion=accion,
            estado_anterior=desde,
            estado_nuevo=hacia,
            comentario=comentario,
            rol=actor.rol,
            usuario_email=actor.email,
            fecha=AHORA,
        )
    ]
    assert [(aviso.estado, acc, com) for aviso, acc, com in notificador.avisos] == [
        (hacia, accion, comentario)
    ]


# --- Efectos de cada acción (plan §9) ---


def test_enviar_guarda_la_fecha_de_inscripcion(servicio, repo):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.BORRADOR))

    servicio.cambiar(legajo.id, Accion.ENVIAR, ASPIRANTE)

    assert repo.legajos[legajo.id].fecha_inscripcion == AHORA


def test_corregir_no_pisa_la_fecha_de_inscripcion_original(servicio, repo):
    original = datetime(2026, 10, 20, 10, 0, tzinfo=UTC)
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.OBSERVADO, fecha_inscripcion=original))

    servicio.cambiar(legajo.id, Accion.CORREGIR, ASPIRANTE)

    assert repo.legajos[legajo.id].fecha_inscripcion == original


def test_aprobar_genera_el_numero_con_el_secuencial_siguiente_y_guarda_la_fecha(
    servicio, repo, eventos
):
    repo.ultimo_secuencial = 44
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.EN_REVISION))

    servicio.cambiar(legajo.id, Accion.APROBAR, COORDINADOR)

    guardado = repo.legajos[legajo.id]
    assert guardado.numero_legajo == "26-001-045"
    assert guardado.fecha_aprobacion == AHORA
    # El secuencial se pide (y la cohorte se bloquea) antes del único commit.
    assert eventos == ["secuencial", "guardar", "notificar"]


def test_matricular_guarda_la_fecha_de_activacion(servicio, repo):
    legajo = repo.agregar(
        nuevo_legajo(EstadoLegajo.COMPLETADO, numero_legajo="26-001-001", fecha_aprobacion=AHORA)
    )

    servicio.cambiar(legajo.id, Accion.MATRICULAR, COORDINADOR)

    guardado = repo.legajos[legajo.id]
    assert guardado.fecha_activacion == AHORA
    assert guardado.numero_legajo == "26-001-001"


@pytest.mark.parametrize(
    ("accion", "desde"),
    [
        (Accion.REVISAR, EstadoLegajo.PENDIENTE),
        (Accion.RECHAZAR, EstadoLegajo.EN_REVISION),
        (Accion.DAR_DE_BAJA, EstadoLegajo.ACTIVO),
    ],
)
def test_las_acciones_sin_efectos_no_tocan_numero_ni_fechas(servicio, repo, accion, desde):
    legajo = repo.agregar(nuevo_legajo(desde))

    servicio.cambiar(legajo.id, accion, COORDINADOR)

    guardado = repo.legajos[legajo.id]
    assert guardado.numero_legajo is None
    assert (guardado.fecha_inscripcion, guardado.fecha_aprobacion, guardado.fecha_activacion) == (
        None,
        None,
        None,
    )


def test_vencer_lo_audita_el_sistema_sin_email_de_usuario(servicio, repo):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.COMPLETADO, numero_legajo="26-001-003"))

    servicio.cambiar(legajo.id, Accion.VENCER, SISTEMA)

    assert repo.registros[0].rol == Rol.SISTEMA
    assert repo.registros[0].usuario_email is None


# --- Comentarios ---


@pytest.mark.parametrize("comentario", [None, "", "   "])
def test_un_comentario_vacio_se_guarda_como_nulo(servicio, repo, notificador, comentario):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.EN_REVISION))

    servicio.cambiar(legajo.id, Accion.RECHAZAR, COORDINADOR, comentario)

    assert repo.registros[0].comentario is None
    assert notificador.avisos[0][2] is None


def test_el_comentario_se_guarda_sin_espacios_en_los_bordes(servicio, repo):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.EN_REVISION))

    servicio.cambiar(legajo.id, Accion.OBSERVAR, COORDINADOR, "  Falta el DNI  ")

    assert repo.registros[0].comentario == "Falta el DNI"


# --- Errores: no se guarda ni se avisa nada ---


def _sin_cambios(repo: RepoEnMemoria, notificador: NotificadorFalso, legajo: Legajo) -> None:
    assert repo.legajos[legajo.id] == legajo
    assert repo.registros == []
    assert notificador.avisos == []
    assert repo.eventos == []


def test_legajo_inexistente_da_no_encontrado(servicio, repo, notificador):
    with pytest.raises(NoEncontrado, match=MENSAJE_LEGAJO_NO_ENCONTRADO):
        servicio.cambiar(uuid4(), Accion.REVISAR, COORDINADOR)

    assert repo.registros == []
    assert notificador.avisos == []


def test_accion_que_no_corresponde_al_estado_da_transicion_invalida(servicio, repo, notificador):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.PENDIENTE))

    with pytest.raises(TransicionInvalida):
        servicio.cambiar(legajo.id, Accion.APROBAR, COORDINADOR)

    # Tampoco se pidió un secuencial: un APROBAR fallido no gasta números.
    _sin_cambios(repo, notificador, legajo)


def test_accion_que_no_corresponde_al_rol_da_sin_permiso(servicio, repo, notificador):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.BORRADOR))

    with pytest.raises(SinPermiso):
        servicio.cambiar(legajo.id, Accion.ENVIAR, COORDINADOR)

    _sin_cambios(repo, notificador, legajo)


def test_el_rol_se_valida_antes_que_el_estado(servicio, repo):
    # Un docente no puede aprobar, y además el legajo no está EN_REVISION: gana el 403.
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.PENDIENTE))

    with pytest.raises(SinPermiso):
        servicio.cambiar(legajo.id, Accion.APROBAR, Actor(Rol.DOCENTE, "docente@example.com"))


@pytest.mark.parametrize("comentario", [None, "", "abc", "    "])
def test_observar_sin_comentario_suficiente_da_error_de_validacion(
    servicio, repo, notificador, comentario
):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.EN_REVISION))

    with pytest.raises(ErrorDeValidacion) as error:
        servicio.cambiar(legajo.id, Accion.OBSERVAR, COORDINADOR, comentario)

    assert error.value.campo == "comentario"
    _sin_cambios(repo, notificador, legajo)


# --- El aviso ---


def test_avisa_despues_de_guardar(servicio, repo, eventos):
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.PENDIENTE))

    servicio.cambiar(legajo.id, Accion.REVISAR, COORDINADOR)

    assert eventos == ["guardar", "notificar"]


def test_si_el_aviso_falla_el_cambio_queda_guardado(repo, eventos, caplog):
    servicio = ServicioEstados(repo, NotificadorFalso(eventos, falla=True), reloj=lambda: AHORA)
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.EN_REVISION))

    resultado = servicio.cambiar(legajo.id, Accion.APROBAR, COORDINADOR)

    assert resultado.estado == EstadoLegajo.COMPLETADO
    assert repo.legajos[legajo.id].estado == EstadoLegajo.COMPLETADO
    assert "No se pudo avisar APROBAR" in caplog.text


def test_sin_reloj_usa_la_hora_actual_en_utc(repo, notificador):
    servicio = ServicioEstados(repo, notificador)
    legajo = repo.agregar(nuevo_legajo(EstadoLegajo.BORRADOR))

    servicio.cambiar(legajo.id, Accion.ENVIAR, ASPIRANTE)

    fecha = repo.legajos[legajo.id].fecha_inscripcion
    assert fecha.tzinfo is not None
    assert abs((datetime.now(UTC) - fecha).total_seconds()) < 5
