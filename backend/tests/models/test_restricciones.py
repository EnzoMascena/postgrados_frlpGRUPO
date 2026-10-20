"""Tests de las restricciones del modelo de datos, contra la base de test.

No prueban lógica de negocio (eso va en cada reglas.py): prueban que la
base frena los datos inválidos aunque una capa de arriba se equivoque.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, text

from app.models import Cohorte, Cursada, Legajo, Seminario
from app.models.enums import EstadoLegajo, TipoCarrera


def _legajo(cohorte: Cohorte, dni: str = "30456789", email: str = "ana@example.com") -> Legajo:
    return Legajo(cohorte_id=cohorte.id, dni=dni, email=email)


def _guardar(session: Session, *filas) -> None:
    session.add_all(filas)
    session.commit()


def test_estan_las_13_tablas_del_plan():
    assert len(SQLModel.metadata.tables) == 13


def test_no_puede_haber_dos_legajos_con_el_mismo_dni_en_la_cohorte(session, cohorte):
    _guardar(session, _legajo(cohorte, email="ana@example.com"))
    session.add(_legajo(cohorte, email="otra@example.com"))
    with pytest.raises(IntegrityError, match="uq_legajos_cohorte_id_dni"):
        session.commit()


def test_no_puede_haber_dos_legajos_con_el_mismo_email_en_la_cohorte(session, cohorte):
    _guardar(session, _legajo(cohorte, dni="30456789"))
    session.add(_legajo(cohorte, dni="31111111"))
    with pytest.raises(IntegrityError, match="uq_legajos_cohorte_id_email"):
        session.commit()


def test_el_mismo_dni_puede_inscribirse_en_otra_cohorte(session, cohorte):
    otra = Cohorte(anio=2027, nombre="Cohorte 2027")
    _guardar(session, otra)
    _guardar(session, _legajo(cohorte), _legajo(otra))
    assert session.exec(text("SELECT count(*) FROM legajos")).one()[0] == 2


def test_un_legajo_nuevo_arranca_en_borrador_y_en_verde(session, cohorte):
    legajo = _legajo(cohorte)
    _guardar(session, legajo)
    session.refresh(legajo)
    assert legajo.estado == EstadoLegajo.BORRADOR
    assert legajo.semaforo == "VERDE"
    assert legajo.created_at.tzinfo is not None  # timestamptz: con zona horaria


def test_el_enum_se_guarda_como_su_valor(session, carrera):
    tipo = session.exec(
        text("SELECT tipo FROM carreras WHERE id = :id"), params={"id": carrera.id}
    ).one()[0]
    assert tipo == TipoCarrera.ESPECIALIZACION.value == "Especializacion"


def test_el_check_rechaza_un_estado_que_no_existe(session, cohorte):
    # "En Riesgo" aparece en el diagrama del SRS, pero es el semáforo ROJO,
    # no un estado del legajo: la base no lo acepta.
    legajo = _legajo(cohorte)
    _guardar(session, legajo)
    with pytest.raises(IntegrityError, match="ck_legajos_estado"):
        session.exec(
            text("UPDATE legajos SET estado = 'EN_RIESGO' WHERE id = :id"),
            params={"id": legajo.id},
        )


def test_usuarios_solo_admite_coordinador_y_cpr(session):
    # El docente entra con el link: no tiene usuario ni contraseña.
    with pytest.raises(IntegrityError, match="ck_usuarios_rol"):
        session.exec(
            text(
                "INSERT INTO usuarios (email, nombre, password_hash, rol, activo) "
                "VALUES ('docente@fenix.test', 'Docente', 'x', 'DOCENTE', true)"
            )
        )


@pytest.mark.parametrize(
    ("nota", "valida"),
    [(Decimal("1"), True), (Decimal("7.5"), True), (Decimal("10"), True), (Decimal("0"), False)],
)
def test_la_nota_va_de_1_a_10(session, cohorte, carrera, nota, valida):
    legajo = _legajo(cohorte)
    seminario = Seminario(
        cohorte_id=cohorte.id,
        carrera_id=carrera.id,
        nombre="Gestión de Proyectos de Software",
        docente_nombre="Ing. Rodríguez, Ana",
        fecha_limite_actas=date(2026, 11, 30),
    )
    _guardar(session, legajo, seminario)
    session.add(Cursada(legajo_id=legajo.id, seminario_id=seminario.id, nota=nota))
    if valida:
        session.commit()
    else:
        with pytest.raises(IntegrityError, match="ck_cursadas_nota_rango"):
            session.commit()
