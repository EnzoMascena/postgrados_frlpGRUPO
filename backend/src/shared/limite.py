"""Límite de envíos por IP en los formularios públicos (NFR-S06, E7).

Hasta 10 envíos por hora desde una misma IP en `POST /legajos` y otros 10 en
`POST /legajos/recuperar-acceso`, contados por separado. El envío número 11 recibe un 429
`RATE_LIMITED`, con el header `Retry-After` (en segundos) y un mensaje que dice cuánto esperar.
Cuenta cualquier envío que llega al endpoint, salga bien o no: lo que se limita es el intento.
Se usan como dependencias de FastAPI:

    @router.post("", dependencies=[Depends(limite_inscripciones)])

Los contadores viven en la memoria del proceso: alcanza porque la API corre en un solo proceso
(`start.sh`), y al reiniciarla empiezan de cero. La IP es la que ve el servidor
(`request.client.host`). En desarrollo, el front llega a través del proxy de Vite, así que todos
sus envíos tienen la IP del contenedor del front: el límite es por máquina, no por persona. No se
lee `X-Forwarded-For` a mano porque cualquiera puede inventarlo; detrás de un proxy de verdad,
uvicorn lo toma solo si se le dice en cuál confiar (`--forwarded-allow-ips`).
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status

MAXIMO_ENVIOS = 10
VENTANA_SEGUNDOS = 60 * 60
# Con más IPs que esto, se olvidan las que no enviaron nada en la última hora: así la memoria no
# crece sin fin si alguien prueba desde muchas IPs distintas.
MAXIMO_IPS = 10_000


def mensaje_de_limite(maximo: int, segundos: float) -> str:
    minutos = max(1, math.ceil(segundos / 60))
    unidad = "minuto" if minutos == 1 else "minutos"
    return f"Llegaste al límite de {maximo} envíos por hora. Probá de nuevo en {minutos} {unidad}"


class LimitePorIP:
    """Una ventana deslizante por IP: guarda la hora de los envíos de la última hora de cada una.

    Con una ventana fija (de 3:00 a 4:00) se podrían hacer 20 envíos seguidos a las 3:59 y a las
    4:00; con la deslizante, en cualquier hora corrida hay como mucho 10.
    """

    def __init__(
        self,
        maximo: int = MAXIMO_ENVIOS,
        ventana: float = VENTANA_SEGUNDOS,
        maximo_ips: int = MAXIMO_IPS,
        reloj: Callable[[], float] = time.monotonic,  # no salta si cambian la hora de la máquina
    ) -> None:
        self.maximo = maximo
        self.ventana = ventana
        self.maximo_ips = maximo_ips
        self.reloj = reloj
        self._envios: dict[str, deque[float]] = {}
        # Los endpoints `def` corren en varios hilos a la vez: sin el candado, dos envíos
        # simultáneos podrían leer la misma cuenta y pasar los dos el límite.
        self._candado = threading.Lock()

    def __call__(self, request: Request) -> None:
        ip = request.client.host if request.client else "desconocida"
        ahora = self.reloj()
        with self._candado:
            envios = self._envios.setdefault(ip, deque())
            while envios and ahora - envios[0] >= self.ventana:
                envios.popleft()
            if len(envios) >= self.maximo:
                espera = self.ventana - (ahora - envios[0])
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=mensaje_de_limite(self.maximo, espera),
                    headers={"Retry-After": str(math.ceil(espera))},
                )
            envios.append(ahora)
            if len(self._envios) > self.maximo_ips:
                self._olvidar_ips_sin_envios(ahora)

    def _olvidar_ips_sin_envios(self, ahora: float) -> None:
        self._envios = {
            ip: envios for ip, envios in self._envios.items() if ahora - envios[-1] < self.ventana
        }

    def reiniciar(self) -> None:
        """Pone todos los contadores en cero (lo usan los tests)."""
        with self._candado:
            self._envios.clear()


limite_inscripciones = LimitePorIP()
limite_recuperar_acceso = LimitePorIP()
