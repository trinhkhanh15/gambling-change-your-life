from collections.abc import Sequence
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Repository(Protocol):
    def save(self, entity: T) -> T: ...

    def save_many(self, entities: Sequence[T]) -> list[T]: ...

    def get(self, model_type: type[T], entity_id: str) -> T | None: ...

    def list(self, model_type: type[T]) -> list[T]: ...
