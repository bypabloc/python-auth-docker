from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import UUID

from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request

from utils.logger import logger


def json_serializable(obj: dict) -> str:
    """Convierte objetos no serializables en JSON a formatos serializables.

    Args:
    ----
        obj: El objeto a serializar.

    Returns:
    -------
        Una representación serializable del objeto.

    Raises:
    ------
        TypeError: Si el objeto no es de un tipo conocido para la serialización.

    :Authors:
        - Pablo Contreras

    :Created:
        - 2024-08-29
    """
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def log_api(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorador para registrar detalles de las solicitudes API.

    Este decorador registra información sobre la solicitud API, incluyendo el usuario,
    método HTTP, ruta, parámetros de consulta,
    cuerpo de la solicitud y parámetros de ruta.

    Args:
    ----
        view_func (Callable[..., Any]): La función de vista a decorar.

    Returns:
    -------
        Callable[..., Any]: La función de vista envuelta.

    :Authors:
        - Pablo Contreras

    :Created:
        - 2024-08-29
    """

    @wraps(view_func)
    def wrapper(
        request: Request,
        *args: dict[str, Any],
        **kwargs: dict[str, Any],
    ) -> Callable[..., Any]:
        """Envoltura para la función de vista decorada."""
        user = (
            request.user
            if not isinstance(request.user, AnonymousUser)
            else "AnonymousUser"
        )

        validated_data = getattr(request, "validated_data", {})

        log_data = {
            "user": str(user),
            "method": request.method,
            "path": request.path,
            "query_params": dict(request.GET),
            "body": validated_data.get("body", {}),
            "path_params": validated_data.get("path_params", {}),
        }

        resp = view_func(request, *args, **kwargs)

        log_data["response"] = resp.data

        try:
            logger.info(
                "API Request",
                extra=log_data,
            )
        except Exception as e:
            logger.error(f"Error al serializar log_data: {e!s}")
            logger.info(f"API Request (no serializado): {log_data!s}")

        return resp

    return wrapper
