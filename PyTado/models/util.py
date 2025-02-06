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
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: AliasChoices(
                field_name, to_camel(field_name)
            ),
            serialization_alias=to_camel,
        )
    )

    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True)

    def to_dict(self) -> dict:
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

            if isinstance(data, dict):
                _model_keys = []
                for _, val in cls.model_fields.items():
                    if isinstance(val.validation_alias, str):
                        _model_keys.append(val.validation_alias)
                    elif isinstance(val.validation_alias, AliasChoices):
                        _model_keys.extend(
                            [str(c) for c in val.validation_alias.choices]
                        )
                model_keys = set(_model_keys)
                extra_keys = set(data.keys()) - model_keys
                if extra_keys:
                    for k in extra_keys:
                        LOGGER.debug(
                            f"Data for Model {cls} has extra key: {k} with value {data[k]}"
                        )

            unused_keys = [
                key
                for key in cls.__annotations__.keys()
                if (getattr(model, key) is None or getattr(model, key) == "")
            ]
            LOGGER.debug(
                f"Model {cls} has unused keys: {unused_keys}"
            ) if unused_keys else None

            return model
        except ValidationError:
            LOGGER.error(f"Model {cls} failed to validate with data {data}")
            raise
