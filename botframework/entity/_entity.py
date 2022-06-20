from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

T = TypeVar('T')


class Entity(ABC):
    @abstractmethod
    def to_json(self) -> dict[str, Any] | list[dict[str, Any]]: pass

    @classmethod
    @abstractmethod
    def from_json(cls: Type[T], object_or_list: dict[str, Any] | list[dict[str, Any]]) -> T: pass
