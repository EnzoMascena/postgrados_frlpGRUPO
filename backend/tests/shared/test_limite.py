"""El límite de envíos por IP (E7, NFR-S06): la ventana y el 429.

Usan un reloj falso, para mover el tiempo sin esperar una hora.
"""

import threading
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.shared.limite import MAXIMO_ENVIOS, VENTANA_SEGUNDOS, LimitePorIP, mensaje_de_limite

IP = "200.1.2.3"


class RelojFalso:
    def __init__(self) -> None:
        self.ahora = 1000.0

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


def pedido(ip: str | None = IP) -> SimpleNamespace:
    """Lo único que el límite mira del `Request`: `request.client.host`."""
    return SimpleNamespace(client=SimpleNamespace(host=ip) if ip else None)


def enviar(limite: LimitePorIP, veces: int, ip: str | None = IP) -> None:
    for _ in range(veces):
        limite(pedido(ip))


def esta_frenado(limite: LimitePorIP, ip: str | None = IP) -> bool:
    try:
        limite(pedido(ip))
    except HTTPException as error:
        assert error.status_code == 429
        return True
    return False


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


@pytest.fixture
def limite(reloj) -> LimitePorIP:
    return LimitePorIP(reloj=reloj)


# --- La ventana ---


def test_deja_pasar_10_envios_por_hora_y_frena_el_11(limite):
    enviar(limite, MAXIMO_ENVIOS)

    assert esta_frenado(limite)


def test_el_429_dice_cuanto_esperar_en_el_mensaje_y_en_retry_after(limite, reloj):
    enviar(limite, MAXIMO_ENVIOS)
    reloj.avanzar(45 * 60)  # el primero fue hace 45 minutos: faltan 15 para que salga

    with pytest.raises(HTTPException) as error:
        limite(pedido())

    assert error.value.detail == (
        "Llegaste al límite de 10 envíos por hora. Probá de nuevo en 15 minutos"
    )
    assert error.value.headers == {"Retry-After": "900"}


def test_la_ventana_es_deslizante(limite, reloj):
    limite(pedido())  # 1 envío a los 0 minutos
    reloj.avanzar(30 * 60)
    enviar(limite, MAXIMO_ENVIOS - 1)  # 9 más a los 30 minutos: ya son 10
    reloj.avanzar(30 * 60)  # a los 60 minutos, el primero sale de la ventana

    assert not esta_frenado(limite)  # entra uno: vuelven a ser 10 en la última hora
    assert esta_frenado(limite)  # y el siguiente ya no


def test_los_envios_frenados_no_cuentan(limite, reloj):
    enviar(limite, MAXIMO_ENVIOS)
    reloj.avanzar(10 * 60)
    for _ in range(5):
        assert esta_frenado(limite)  # insistir no estira la espera
    reloj.avanzar(50 * 60)

    assert not esta_frenado(limite)


def test_cada_ip_tiene_su_propio_limite(limite):
    enviar(limite, MAXIMO_ENVIOS)

    assert not esta_frenado(limite, ip="200.9.9.9")


def test_los_pedidos_sin_ip_cuentan_juntos(limite):
    enviar(limite, MAXIMO_ENVIOS, ip=None)

    assert esta_frenado(limite, ip=None)


@pytest.mark.parametrize(
    ("segundos", "espera"),
    [(30, "1 minuto"), (61, "2 minutos"), (VENTANA_SEGUNDOS, "60 minutos")],
)
def test_el_mensaje_redondea_los_minutos_para_arriba(segundos, espera):
    assert mensaje_de_limite(10, segundos).endswith(f"Probá de nuevo en {espera}")


def test_con_muchos_envios_simultaneos_pasan_10(limite):
    # Comprueba que bajo hilos sigue contando bien, pero no alcanza para probar el candado: la
    # carrera que evita (dos hilos leen 9 y pasan los dos) es casi imposible de provocar a mano.
    pasaron, frenados = [], []
    largada = threading.Barrier(30)  # que los 30 hilos arranquen a la vez

    def enviar_uno() -> None:
        largada.wait()
        (frenados if esta_frenado(limite) else pasaron).append(1)

    hilos = [threading.Thread(target=enviar_uno) for _ in range(30)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert (len(pasaron), len(frenados)) == (MAXIMO_ENVIOS, 30 - MAXIMO_ENVIOS)


def test_se_olvida_de_las_ips_sin_envios_en_la_ultima_hora(reloj):
    limite = LimitePorIP(maximo_ips=3, reloj=reloj)
    for ip in ("1.1.1.1", "2.2.2.2", "3.3.3.3"):
        limite(pedido(ip))
    reloj.avanzar(VENTANA_SEGUNDOS)

    limite(pedido("4.4.4.4"))  # con la cuarta se pasa del máximo y se borran las viejas

    assert list(limite._envios) == ["4.4.4.4"]


def test_reiniciar_pone_los_contadores_en_cero(limite):
    enviar(limite, MAXIMO_ENVIOS)

    limite.reiniciar()

    assert not esta_frenado(limite)
