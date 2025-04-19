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
        )
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
                    LOGGER.warning(
                        f"Model {cls} has extra key: {key} with value {value}"
                    ) if value is not None else None

            unused_keys = model.model_fields.keys() - model.model_fields_set
            LOGGER.debug(
                f"Model {cls} has unused keys: {unused_keys}"
            ) if unused_keys else None

            return model
        except ValidationError:
            LOGGER.error(f"Model {cls} failed to validate with data {data}")
            raise
