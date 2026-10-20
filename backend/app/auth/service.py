"""
Capa de negocio (Service) — el caso de uso "iniciar sesión".

LAS DECISIONES CLAVE (las mismas del auth_service del módulo 04):

    1. ¿El service devuelve un 401? → NO. El service NO sabe de HTTP: no
       importa FastAPI ni lanza HTTPException. Devuelve el Usuario si las
       credenciales valen, o None si no, y el controller decide el status.
       Es el mismo criterio que el 404 del módulo 03.

    2. Normalizar el email es una regla de negocio ("Admin@Fenix.test" y
       "admin@fenix.test" son la misma cuenta), así que vive ACÁ.

    3. Timing attack / user enumeration: si "email inexistente" respondiera
       más rápido que "contraseña incorrecta", un atacante podría medir el
       tiempo y averiguar qué emails están registrados. Por eso, si el email
       no existe, se verifica igual contra un hash señuelo (DUMMY_HASH): los
       dos casos tardan lo mismo y devuelven lo mismo.

    4. Un usuario desactivado no entra, y tampoco se le avisa por qué: el
       control va DESPUÉS de verificar la contraseña, así el tiempo y la
       respuesta son iguales a los de una contraseña incorrecta.
"""

from app.auth.repository import UsuarioRepository
from app.core.security import DUMMY_HASH, verify_password
from app.models import Usuario


class AuthService:
    """Casos de uso de autenticación."""

    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

    def autenticar(self, email: str, password: str) -> Usuario | None:
        """Verifica las credenciales. Devuelve el Usuario, o None si no valen."""
        # 2. Misma normalización con la que el seed guarda los emails.
        email = email.strip().lower()

        usuario = self.repository.get_by_email(email)

        # 3. Email inexistente: se paga igual el costo de bcrypt (señuelo).
        if usuario is None:
            verify_password(password, DUMMY_HASH)
            return None

        if not verify_password(password, usuario.password_hash):
            return None

        # 4. Desactivado: mismo None que una contraseña incorrecta.
        if not usuario.activo:
            return None

        return usuario
