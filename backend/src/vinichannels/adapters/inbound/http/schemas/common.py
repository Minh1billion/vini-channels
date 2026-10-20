from pydantic import BaseModel

from vinichannels.application.dto import UNSET, Maybe


def given[T](value: T | None) -> Maybe[T]:
    return UNSET if value is None else value


def given_nullable[T](model: BaseModel, name: str, value: T | None) -> Maybe[T | None]:
    return value if name in model.model_fields_set else UNSET
