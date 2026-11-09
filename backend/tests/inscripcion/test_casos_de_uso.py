"""Casos de uso `inscribir` y `recuperar_acceso` con piezas falsas: sin base y sin SMTP."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

import pytest

from src.cohortes.domain.cohorte import Cohorte
from src.inscripcion.application.inscribir import (
    MENSAJE_CARRERA_NO_DISPONIBLE,
    MENSAJE_COHORTE_INEXISTENTE,
    inscribir,
)
from src.inscripcion.application.recuperar_acceso import recuperar_acceso
from src.inscripcion.domain.errores import PeriodoCerrado
from src.inscripcion.domain.inscripcion import (
    MENSAJE_DNI_REPETIDO,
    MENSAJE_EMAIL_REPETIDO,
    DatosInscripcion,
    LegajoDelAspirante,
    LegajoEnEdicion,
    mensaje_periodo_cerrado,
)
from src.inscripcion.domain.tipos import ComoConocio
from src.legajos.domain.estados import EstadoLegajo
from src.shared.errors import Conflicto, ErrorDeValidacion

CARRERA = uuid4()


class RepoEnMemoria:
    def __init__(self, *cohortes: Cohorte, carreras_activas: Sequence[UUID] = (CARRERA,)) -> None:
        self.cohortes = {cohorte.id: cohorte for cohorte in cohortes}
        self.activas = set(carreras_activas)
        self.legajos: list[tuple[UUID, DatosInscripcion, str]] = []
        self.estados: dict[UUID, EstadoLegajo] = {}

    def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        return self.cohortes.get(cohorte_id)

    def carreras_activas(self, carrera_ids: Sequence[UUID]) -> set[UUID]:
        return self.activas & set(carrera_ids)

    def existe_dni(self, cohorte_id: UUID, dni: str, excepto: UUID | None = None) -> bool:
        return any(
            i != excepto and d.cohorte_id == cohorte_id and d.dni == dni for i, d, _ in self.legajos
        )

    def existe_email(self, cohorte_id: UUID, email: str, excepto: UUID | None = None) -> bool:
        return any(
            i != excepto and d.cohorte_id == cohorte_id and d.email == email
            for i, d, _ in self.legajos
        )

    def crear_legajo(self, datos: DatosInscripcion, codigo_seguimiento: str) -> UUID:
        legajo_id = uuid4()
        self.legajos.append((legajo_id, datos, codigo_seguimiento))
        self.estados[legajo_id] = EstadoLegajo.BORRADOR
        return legajo_id

    def legajo_en_edicion(self, legajo_id: UUID) -> LegajoEnEdicion | None:
        for i, datos, _ in self.legajos:
            if i == legajo_id:
                return LegajoEnEdicion(i, datos.cohorte_id, self.estados[i])
        return None

    def actualizar_legajo(self, legajo_id: UUID, datos: DatosInscripcion) -> None:
        self.legajos = [(i, datos if i == legajo_id else d, c) for i, d, c in self.legajos]

    def buscar_ultimo_por_email(self, email: str) -> LegajoDelAspirante | None:
        for legajo_id, datos, codigo in reversed(self.legajos):
            if datos.email == email:
                return LegajoDelAspirante(legajo_id, datos.nombre, datos.email, codigo)
        return None


class Links:
    """Hace de `crear_link` y de `enviar_link`, y anota todo para revisarlo después."""

    def __init__(self, email_sale: bool = True) -> None:
        self.creados: list[UUID] = []
        self.enviados: list[tuple[str, str, str, str]] = []
        self.email_sale = email_sale

    def crear(self, legajo_id: UUID) -> str:
        self.creados.append(legajo_id)
        return f"token-{len(self.creados)}"

    def enviar(self, email: str, nombre: str, codigo: str, token: str) -> bool:
        self.enviados.append((email, nombre, codigo, token))
        return self.email_sale


def una_cohorte(abierta: bool = True, proxima_apertura: date | None = None) -> Cohorte:
    return Cohorte(uuid4(), 2026, 1, "Cohorte 2026", abierta, None, proxima_apertura)


def un_formulario(cohorte: Cohorte, **cambios) -> DatosInscripcion:
    datos = DatosInscripcion(
        cohorte_id=cohorte.id,
        carrera_ids=(CARRERA,),
        apellido="Rodríguez",
        nombre="Ana Laura",
        nacionalidad="Argentina",
        dni="28456789",
        telefono_movil="+54 221 4567890",
        telefono_fijo=None,
        email="ana@example.com",
        email_alternativo=None,
        domicilio="Av. 7 Nro. 1234",
        ciudad="La Plata",
        provincia="Buenos Aires",
        pais="Argentina",
        titulo_grado="Ingeniería en Sistemas de Información",
        titulo_posgrado=None,
        como_conocio=ComoConocio.EGRESADOS,
        motivacion="Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo.",
        solicita_beca=False,
        tipo_beca=None,
    )
    return replace(datos, **cambios)


def inscribir_con(repo: RepoEnMemoria, datos: DatosInscripcion, links: Links | None = None):
    links = links or Links()
    return inscribir(datos, repo, links.crear, links.enviar)


# --- inscribir ---


def test_inscribir_crea_el_borrador_con_codigo_y_manda_el_link():
    cohorte = una_cohorte()
    repo, links = RepoEnMemoria(cohorte), Links()

    creado = inscribir_con(repo, un_formulario(cohorte), links)

    legajo_id, _, codigo = repo.legajos[0]
    assert creado.legajo_id == legajo_id
    assert creado.estado == EstadoLegajo.BORRADOR
    assert creado.codigo_seguimiento == codigo
    assert len(codigo) == 8 and codigo == codigo.upper()
    int(codigo, 16)  # es hexadecimal
    assert creado.token == "token-1"
    assert links.creados == [legajo_id]
    assert links.enviados == [("ana@example.com", "Ana Laura", codigo, "token-1")]


def test_si_el_email_no_sale_la_inscripcion_igual_queda():
    cohorte = una_cohorte()
    repo = RepoEnMemoria(cohorte)

    creado = inscribir_con(repo, un_formulario(cohorte), Links(email_sale=False))

    assert creado.token == "token-1"
    assert len(repo.legajos) == 1


def test_una_cohorte_que_no_existe_da_422_en_cohorte_id():
    repo, links = RepoEnMemoria(), Links()

    with pytest.raises(ErrorDeValidacion) as error:
        inscribir_con(repo, un_formulario(una_cohorte()), links)

    assert (error.value.campo, error.value.mensaje) == ("cohorteId", MENSAJE_COHORTE_INEXISTENTE)
    assert repo.legajos == [] and links.enviados == []


@pytest.mark.parametrize(
    ("proxima_apertura", "mensaje"),
    [
        (date(2027, 3, 1), "La inscripción está cerrada. Próxima apertura: 01/03/2027"),
        (None, "La inscripción está cerrada"),
    ],
)
def test_con_el_periodo_cerrado_da_409_con_la_proxima_apertura(proxima_apertura, mensaje):
    cohorte = una_cohorte(abierta=False, proxima_apertura=proxima_apertura)
    repo = RepoEnMemoria(cohorte)

    with pytest.raises(PeriodoCerrado) as error:
        inscribir_con(repo, un_formulario(cohorte))

    assert error.value.status_code == 409
    assert error.value.codigo == "PERIODO_CERRADO"
    assert error.value.mensaje == mensaje == mensaje_periodo_cerrado(proxima_apertura)
    assert repo.legajos == []


@pytest.mark.parametrize("carreras", [(uuid4(),), (CARRERA, uuid4())])
def test_una_carrera_inactiva_o_que_no_existe_da_422_en_carrera_ids(carreras):
    cohorte = una_cohorte()
    repo = RepoEnMemoria(cohorte)

    with pytest.raises(ErrorDeValidacion) as error:
        inscribir_con(repo, un_formulario(cohorte, carrera_ids=carreras))

    assert (error.value.campo, error.value.mensaje) == ("carreraIds", MENSAJE_CARRERA_NO_DISPONIBLE)


def test_dos_carreras_activas_se_aceptan():
    otra = uuid4()
    cohorte = una_cohorte()
    repo = RepoEnMemoria(cohorte, carreras_activas=(CARRERA, otra))

    inscribir_con(repo, un_formulario(cohorte, carrera_ids=(CARRERA, otra)))

    assert repo.legajos[0][1].carrera_ids == (CARRERA, otra)


@pytest.mark.parametrize(
    ("cambio", "campo", "mensaje"),
    [
        ({"email": "otra@example.com"}, "dni", MENSAJE_DNI_REPETIDO),
        ({"dni": "30111222"}, "email", MENSAJE_EMAIL_REPETIDO),
    ],
)
def test_un_dni_o_email_repetido_en_la_cohorte_da_409_con_el_campo(cambio, campo, mensaje):
    cohorte = una_cohorte()
    repo = RepoEnMemoria(cohorte)
    inscribir_con(repo, un_formulario(cohorte))

    with pytest.raises(Conflicto) as error:
        inscribir_con(repo, un_formulario(cohorte, **cambio))

    assert (error.value.status_code, error.value.campo) == (409, campo)
    assert error.value.mensaje == mensaje
    assert len(repo.legajos) == 1


def test_el_mismo_dni_y_email_en_otra_cohorte_se_aceptan():
    cohorte_2025, cohorte_2026 = una_cohorte(), una_cohorte()
    repo = RepoEnMemoria(cohorte_2025, cohorte_2026)
    inscribir_con(repo, un_formulario(cohorte_2025))

    inscribir_con(repo, un_formulario(cohorte_2026))

    assert len(repo.legajos) == 2


# --- recuperar_acceso ---


def test_recuperar_acceso_manda_un_link_nuevo_del_legajo_mas_reciente():
    cohorte_2025, cohorte_2026 = una_cohorte(), una_cohorte()
    repo, links = RepoEnMemoria(cohorte_2025, cohorte_2026), Links()
    inscribir_con(repo, un_formulario(cohorte_2025))
    inscribir_con(repo, un_formulario(cohorte_2026))
    mas_reciente, _, codigo = repo.legajos[-1]

    recuperar_acceso("ana@example.com", repo, links.crear, links.enviar)

    assert links.creados == [mas_reciente]
    assert links.enviados == [("ana@example.com", "Ana Laura", codigo, "token-1")]


def test_recuperar_acceso_con_un_email_sin_legajo_no_manda_nada():
    repo, links = RepoEnMemoria(), Links()

    recuperar_acceso("nadie@example.com", repo, links.crear, links.enviar)

    assert links.creados == [] and links.enviados == []
