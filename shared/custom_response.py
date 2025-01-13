from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rest_framework.response import Response


@dataclass
class ResponseConfig:
    """Configuration class for CustomResponse."""

    data: dict | None = None
    status: int = 200
    template_name: str | None = None
    headers: dict | None = None
    exception: Exception | None = None
    content_type: str = "application/json"
    code: str = "success"
    message: str | None = None
    errors: dict | None = None


class CustomResponse(Response):
    """Custom response class with standardized format."""

    headers: dict

    def __init__(self, config: ResponseConfig | dict[str, Any] | None = None) -> None:
        """Initialize the CustomResponse with a configuration object.

        Args:
            config: Either a ResponseConfig object or
            a dictionary with configuration values
        """
        if config is None:
            config = ResponseConfig()
        elif isinstance(config, dict):
            config = ResponseConfig(**config)

        # Prepare response body
        body = {
            "data": config.data or {},
            "code": config.code,
        }

        if config.message:
            body["message"] = config.message
        if config.errors:
            body["errors"] = config.errors

        self._content_type = config.content_type

        params_init = {
            "data": body,
            "status": config.status,
            "template_name": config.template_name,
            "headers": config.headers,
            "content_type": config.content_type,
        }
        if config.exception:
            params_init["exception"] = config.exception

        # Call parent class constructor
        super().__init__(**params_init)

        # Set default CORS headers if none provided
        if not config.headers:
            self.headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": (
                    "Origin, Content-Type, Accept, Authorization"
                ),
            }
        else:
            self.headers = config.headers

    @property
    def content_type(self) -> str:
        """Get content type."""
        return self._content_type or self["Content-Type"]

    @content_type.setter
    def content_type(self, value: str) -> None:
        """Set content type."""
        self._content_type = value
        if value is not None:
            self["Content-Type"] = value
