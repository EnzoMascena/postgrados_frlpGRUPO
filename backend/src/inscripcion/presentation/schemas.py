"""Schemas de la inscripción (plan §10): JSON en camelCase, atributos en snake_case.

Acá se validan los datos que llegan del formulario: es la puerta de entrada del sistema. Un dato
mal formado da 422 con el campo en `field` (lo arma `error_handlers.py`). El texto de un
`ValueError` de los validadores de abajo es el `message` que lee el aspirante: se escribe para él.
"""

import re
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, ValidationInfo, field_validator

from src.inscripcion.domain.inscripcion import DatosInscripcion
from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.domain.estados import EstadoLegajo
from src.shared.schemas import CamelModel

LARGO_MINIMO_MOTIVACION = 50
# El endpoint es público y la columna es `text`: sin tope, cualquiera podría llenar la base con
# pocos envíos. 2000, como el comentario del coordinador (`LARGO_MAXIMO_COMENTARIO`).
LARGO_MAXIMO_MOTIVACION = 2000


_EJEMPLO_DATOS = {
    "carreraIds": ["5d2f8a1b-3c4d-4e5f-9a0b-1c2d3e4f5a6b"],
    "apellido": "Rodríguez",
    "nombre": "Ana Laura",
    "nacionalidad": "Argentina",
    "dni": "28.456.789",
    "telefonoMovil": "+54 221 4567890",
    "telefonoFijo": None,
    "email": "ana.rodriguez@example.com",
    "emailAlternativo": "ana.trabajo@example.com",
    "domicilio": "Av. 7 Nro. 1234",
    "ciudad": "La Plata",
    "provincia": "Buenos Aires",
    "pais": "Argentina",
    "tituloGrado": "Ingeniería en Sistemas de Información",
    "tituloPosgrado": None,
    "comoConocio": "EGRESADOS",
    "motivacion": (
        "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo como analista."
    ),
    "solicitaBeca": True,
    "tipoBeca": "30",
}


class DatosLegajoRequest(CamelModel):
    """Los datos del formulario sin la cohorte: el cuerpo de `PUT /seguimiento/{token}` (F6).

    `InscripcionRequest` suma `cohorteId`. Así el alta y la edición validan exactamente igual.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True, json_schema_extra={"examples": [_EJEMPLO_DATOS]}
    )

    # 1 o 2 carreras distintas (BR-001). Que estén activas lo controla el caso de uso.
    carrera_ids: list[UUID] = Field(min_length=1, max_length=2)
    apellido: str = Field(min_length=1, max_length=100)
    nombre: str = Field(min_length=1, max_length=100)
    nacionalidad: str = Field(min_length=1, max_length=100)
    dni: str
    telefono_movil: str = Field(min_length=1, max_length=30)
    telefono_fijo: str | None = Field(default=None, max_length=30)
    email: EmailStr = Field(max_length=255)
    # Obligatorio: lo pide el SRS (campos obligatorios) y el contrato del plan §10.
    email_alternativo: EmailStr = Field(max_length=255)
    domicilio: str = Field(min_length=1, max_length=255)
    ciudad: str = Field(min_length=1, max_length=100)
    provincia: str = Field(min_length=1, max_length=100)
    pais: str = Field(min_length=1, max_length=100)
    titulo_grado: str = Field(min_length=1, max_length=255)
    titulo_posgrado: str | None = Field(default=None, max_length=255)
    como_conocio: ComoConocio
    motivacion: str = Field(min_length=LARGO_MINIMO_MOTIVACION)
    solicita_beca: bool
    # validate_default: el control de abajo corre también cuando no viene en el JSON.
    tipo_beca: TipoBeca | None = Field(default=None, validate_default=True)

    @field_validator("telefono_fijo", "titulo_posgrado", mode="before")
    @classmethod
    def opcional_vacio_es_none(cls, valor: object) -> object:
        # El formulario manda "" cuando el campo queda en blanco. Se guarda None: así
        # `titulo_posgrado is not None` dice bien si hay que pedir el título de posgrado.
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @field_validator("dni", mode="before")
    @classmethod
    def normalizar_dni(cls, valor: object) -> object:
        # "28.456.789" y "28 456 789" se guardan como "28456789".
        if not isinstance(valor, str):
            return valor
        dni = re.sub(r"[.\s]", "", valor)
        if not re.fullmatch(r"\d{7,8}", dni):
            raise ValueError("El DNI tiene que tener 7 u 8 dígitos")
        return dni

    @field_validator("telefono_movil", "telefono_fijo")
    @classmethod
    def telefono_con_8_numeros(cls, valor: str | None) -> str | None:
        # La misma regla que el formulario (validaciones.ts): 8 números o más, sin contar
        # espacios, "+", guiones ni paréntesis. [0-9] y no \d: \d acepta dígitos de otros idiomas.
        if valor is not None and not re.fullmatch(r"[0-9]{8,}", re.sub(r"[\s+()-]", "", valor)):
            raise ValueError("Ingresá un teléfono de al menos 8 números, con código de área")
        return valor

    @field_validator("email", "email_alternativo")
    @classmethod
    def email_en_minusculas(cls, valor: str | None) -> str | None:
        # Así "Ana@Mail.com" y "ana@mail.com" son el mismo email en la cohorte.
        return valor.lower() if valor else valor

    @field_validator("motivacion")
    @classmethod
    def motivacion_con_tope(cls, valor: str) -> str:
        # Llega sin los espacios de los bordes (`str_strip_whitespace`): se cuenta el mismo texto
        # que se guarda.
        if len(valor) > LARGO_MAXIMO_MOTIVACION:
            raise ValueError(
                f"La motivación puede tener hasta {LARGO_MAXIMO_MOTIVACION} caracteres"
            )
        return valor

    @field_validator("carrera_ids")
    @classmethod
    def carreras_distintas(cls, valor: list[UUID]) -> list[UUID]:
        if len(set(valor)) != len(valor):
            raise ValueError("Las dos carreras tienen que ser distintas")
        return valor

    @field_validator("tipo_beca")
    @classmethod
    def beca_coherente(cls, valor: TipoBeca | None, info: ValidationInfo) -> TipoBeca | None:
        # `solicita_beca` está declarado antes: si llegó bien, ya está en `info.data`.
        solicita_beca = info.data.get("solicita_beca")
        if solicita_beca and valor is None:
            raise ValueError("Elegí el tipo de beca")
        if solicita_beca is False and valor is not None:
            raise ValueError("Sin beca no corresponde un tipo de beca")
        return valor

    def a_datos_de_cohorte(self, cohorte_id: UUID) -> DatosInscripcion:
        return DatosInscripcion(
            **self.model_dump(exclude={"carrera_ids", "cohorte_id"}),
            cohorte_id=cohorte_id,
            carrera_ids=tuple(self.carrera_ids),
        )


class InscripcionRequest(DatosLegajoRequest):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"cohorteId": "c1a2b3c4-d5e6-4f70-8a9b-0c1d2e3f4a5b", **_EJEMPLO_DATOS}]
        }
    )

    cohorte_id: UUID

    def a_datos(self) -> DatosInscripcion:
        return self.a_datos_de_cohorte(self.cohorte_id)


class InscripcionResponse(CamelModel):
    """Se arma directo desde `LegajoCreado`: `InscripcionResponse.model_validate(creado)`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "legajoId": "4b0e6c2a-1d3f-4a5b-8c7d-9e0f1a2b3c4d",
                    "codigoSeguimiento": "7F3A9C21",
                    "token": "Q3JxVq0yZ2l4b2w...",
                    "estado": "BORRADOR",
                }
            ]
        }
    )

    legajo_id: UUID
    codigo_seguimiento: str
    token: str
    estado: EstadoLegajo


class RecuperarAccesoRequest(CamelModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"email": "ana.rodriguez@example.com"}]},
    )

    email: EmailStr = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def email_en_minusculas(cls, valor: str) -> str:
        return valor.lower()


class RecuperarAccesoResponse(CamelModel):
    mensaje: str
