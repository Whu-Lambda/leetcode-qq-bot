import dataclasses
import inspect
import types
import typing
from abc import ABC
from typing import Iterable, Any, Type, TypeVar

from ._entity import Entity
from .._commons import to_camel_case, first

T = TypeVar('T')


# region to_json

class ToJsonWithType(ABC):
    @property
    def type(self) -> str: return type(self).__name__

    def to_json(self) -> dict[str, Any]:
        return {
            'type': self.type,
            **dataclasses.asdict(self, dict_factory=dict_factory)
        }


class ToJsonWithoutType(ABC):
    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self, dict_factory=dict_factory)


def dict_factory(items: Iterable[tuple[str, Entity | list | int | str | bool | None]]) -> dict[str, Any]:
    result = {}
    for name, value in items:
        if isinstance(value, Entity):
            result[to_camel_case(name)] = value.to_json()
        elif isinstance(value, list):
            result[to_camel_case(name)] = [x.to_json() if isinstance(x, Entity) else x for x in value]
        else:
            assert isinstance(value, int | str | bool | types.NoneType)
            result[to_camel_case(name)] = value
    return result


# endregion to_json

# region from_json

class FromJsonWithType(ABC):
    @classmethod
    def from_json(cls: Type[T], obj: dict[str, Any]) -> T:
        assert obj['type'] == cls.__name__
        return from_json(cls, obj)


class FromJsonWithoutType(ABC):
    @classmethod
    def from_json(cls: Type[T], obj: dict[str, Any]) -> T:
        return from_json(cls, obj)


def from_json(cls: Type[T], obj: dict[str, Any]) -> T:
    return cls(**{field.name: deserialize(field.type, obj.get(to_camel_case(field.name)))
                  for field in dataclasses.fields(cls)})


def deserialize(
    annotation: Any,
    json_element: dict[str, Any] | list | int | str | bool | None
) -> Entity | list | int | str | bool | None:
    if inspect.isclass(annotation) and issubclass(annotation, Entity):
        return annotation.from_json(json_element)
    elif typing.get_origin(annotation) == list:  # list[T] or List[T]
        value_type = typing.get_args(annotation)[0]  # T
        return [deserialize(value_type, x) for x in json_element]
    elif (isinstance(annotation, types.UnionType)
          or typing.get_origin(annotation) == typing.Union):  # X | Y or Union[X, Y]
        union_types = typing.get_args(annotation)  # (X, Y)
        return deserialize_union(union_types, json_element)
    else:
        assert issubclass(annotation, int | str | bool | types.NoneType)
        return json_element


def deserialize_union(
    union_types: tuple,
    json_element: dict[str, Any] | list | int | str | bool | None
) -> Entity | list | int | str | bool | None:
    def can_deserialize(expected_type: Type[Entity | list | int | str | bool | types.NoneType]) -> bool:
        if inspect.isclass(expected_type) and issubclass(expected_type, Entity):
            return isinstance(json_element, dict) or isinstance(json_element, list)
        else:  # list, int, str, bool, NoneType
            return expected_type == type(json_element)

    return first(deserialize(annotation, json_element)
                 for annotation in union_types
                 if can_deserialize(annotation))

# endregion from_json
