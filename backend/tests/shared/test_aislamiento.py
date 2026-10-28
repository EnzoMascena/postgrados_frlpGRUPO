"""Prueba que el rollback por test funciona: lo que un test commitea no lo ve el siguiente.

Son dos tests que dependen del orden (pytest respeta el del archivo): el primero crea una tabla
y hace `commit()`; el segundo, que corre con otra sesión, comprueba que esa tabla ya no existe.
"""

from sqlalchemy import text


def test_un_commit_del_test_queda_dentro_de_la_transaccion_de_afuera(session):
    session.exec(text("CREATE TABLE prueba_aislamiento (id integer)"))
    session.exec(text("INSERT INTO prueba_aislamiento VALUES (1)"))
    session.commit()

    assert session.exec(text("SELECT count(*) FROM prueba_aislamiento")).scalar() == 1


def test_lo_que_commiteo_el_test_anterior_ya_no_existe(session):
    tabla = session.exec(text("SELECT to_regclass('prueba_aislamiento')")).scalar()

    assert tabla is None
