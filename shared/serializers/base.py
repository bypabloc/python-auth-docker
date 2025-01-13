from __future__ import annotations

from typing import Any

from rest_framework import serializers


class BaseSerializer(serializers.Serializer):
    """Base serializer that ensures validated_data returns a dict[str, Any]."""

    @property
    def validated_data(self) -> dict[str, Any]:
        """Override validated_data to ensure string keys and proper typing.

        Returns:
            dict[str, Any]: Dictionary with string keys and validated data
        """
        if not hasattr(self, "_validated_data"):
            return {}

        # Convert all keys to strings and handle nested serializers
        def process_value(
            value: dict | list | BaseSerializer | str | int | float | bool | None,
        ) -> dict | list | str | int | float | bool | None:
            if isinstance(value, BaseSerializer):
                return value.validated_data
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            elif isinstance(value, dict):
                return {str(k): process_value(v) for k, v in value.items()}
            return value

        return {
            str(key): process_value(value)
            for key, value in super().validated_data.items()
        }
