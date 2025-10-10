"""Utility module providing base model and validation functionality for PyTado.

This module defines the foundational model infrastructure used throughout the PyTado library,
centered around Pydantic for data validation and serialization. It includes:

- A Base model class with customized configuration for:
  - Automatic camelCase/snake_case field name conversion
  - Flexible extra field handling
  - JSON serialization utilities
- Debug-focused validation wrapper that logs:
  - Extra fields present in the data but not in the model
  - Fields defined in the model but not present in the data
  - Validation errors with detailed context

This module serves as the backbone for all data models in PyTado, ensuring consistent
handling of API data and providing helpful debugging information during development.
"""

from typing import Any, Self

from pydantic import (
    AliasChoices,
    AliasGenerator,
    BaseModel,
    ConfigDict,
    ModelWrapValidatorHandler,
    ValidationError,
    model_validator,
)
from pydantic.alias_generators import to_camel

from PyTado.logger import Logger

LOGGER = Logger(__name__)


class Base(BaseModel):
    """Base model for all models in PyTado.

    Provides a custom alias generator that converts snake_case to camelCase for
    serialization, and CamelCase to snake_case for validation.
    Also provides a helper method to dump the model to a JSON string or python dict
    with the correct aliases and some debug logging for model validation.
    """

    model_config = ConfigDict(
        extra="allow",
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: AliasChoices(
                field_name, to_camel(field_name)
            ),
            serialization_alias=to_camel,
        ),
    )

    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)

    @model_validator(mode="wrap")
    @classmethod
    def log_failed_validation(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        """Model validation debug helper.
        Logs in the following cases:
            - (Debug) Keys in data that are not in the model
            - (Debug) Keys in the model that are not in the data
            - (Error) Validation errors
        (This is just for debugging and development, can be removed if not needed anymore)
        """
        try:
            model: Self = handler(data)

            extra = model.model_extra

            if extra:
                for key, value in extra.items():
                    if value is not None:
                        LOGGER.warning(
                            "Model %s has extra key: %s with value %r", cls, key, value
                        )

            unused_keys = model.model_fields.keys() - model.model_fields_set
            if unused_keys:
                LOGGER.debug("Model %s has unused keys: %r", cls, unused_keys)

            return model
        except ValidationError:
            LOGGER.error("Model %s failed to validate with data %r", cls, data)
            raise
