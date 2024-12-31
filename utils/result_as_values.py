"""Ejemplo de uso.

@dataclass
class User:
    id: str
    name: str
    email: str


@handle_result
def get_user(user_id: str) -> Result[User]:
    '''Busca un usuario por ID.'''
    if not user_id.strip():
        return Result.fail(
            ErrorKind.INVALID_INPUT,
            "El ID de usuario no puede estar vacío",
        )

    # Simulación de búsqueda en base de datos
    if user_id == "123":
        return Result.ok(
            User(
                id=user_id,
                name="John Doe",
                email="john@example.com",
            ),
        )

    return Result.fail(
        ErrorKind.NOT_FOUND,
        f"Usuario con ID {user_id} no encontrado",
    )


@handle_result
def update_user_name(user: User, new_name: str) -> Result[User]:
    '''Actualiza el nombre de un usuario.'''
    if not new_name.strip():
        return Result.fail(
            ErrorKind.VALIDATION_ERROR,
            "El nombre no puede estar vacío",
        )

    if len(new_name) < 2:
        return Result.fail(
            ErrorKind.VALIDATION_ERROR,
            "El nombre debe tener al menos 2 caracteres",
            {"min_length": 2},
        )

    user.name = new_name
    return Result.ok(user)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


@dataclass
class Error:
    """Estructura para representar errores."""

    code: str
    message: str
    details: dict[str, Any] | None = None


@dataclass
class Result(Generic[T]):
    """Contenedor genérico para manejar resultados que pueden ser exitosos o errores.

    Attributes:
        _value: El valor en caso de éxito
        _error: El error en caso de fallo
    """

    _value: T | None = None
    _error: Error | None = None

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Crea un Result exitoso."""
        return cls(
            _value=value,
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> Result[T]:
        """Crea un Result con error."""
        return cls(
            _error=Error(
                code,
                message,
                details,
            )
        )

    @property
    def is_ok(self) -> bool:
        """Verifica si el resultado es exitoso."""
        return self._error is None

    @property
    def is_error(self) -> bool:
        """Verifica si el resultado contiene un error."""
        return not self.is_ok

    @property
    def value(self) -> T:
        """Obtiene el valor si es exitoso.

        Raises:
            ValueError: Si el resultado es un error
        """
        if self._value is None:
            raise ValueError("Cannot get value from error result")
        return self._value

    @property
    def error(self) -> Error:
        """Obtiene el error si existe.

        Raises:
            ValueError: Si el resultado es exitoso
        """
        if self._error is None:
            raise ValueError("Cannot get error from successful result")
        return self._error

    def unwrap_or(self, default: T) -> T:
        """Retorna el valor si es exitoso, o el valor por defecto si es error."""
        return self._value if self.is_ok else default

    def map(self, fn: Callable[[T], Any]) -> Result[Any]:
        """Aplica una función al valor si es exitoso.

        Args:
            fn: Función a aplicar al valor
        """
        if self.is_error:
            return Result(_error=self._error)
        return Result.ok(fn(self._value))


def handle_result(func: Callable[..., Result[T]]) -> Callable[..., Result[T]]:
    """Decorador para funciones que retornan Result."""
    return func
