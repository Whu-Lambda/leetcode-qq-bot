import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Type, Iterable, Iterator

from . import _mixin
from ._entity import Entity


class MessageElement(Entity, ABC):
    @property
    @abstractmethod
    def type(self) -> str: pass

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'MessageElement':
        class_dict = message_element_class_dict()
        assert obj['type'] in class_dict
        element_class = class_dict[obj['type']]
        return element_class.from_json(obj)


class MessageChain(list, Entity):
    def __init__(self, elements: Iterable[MessageElement] = ()):
        list.__init__(self, elements)

    def to_json(self) -> list[dict[str, Any]]:
        return [element.to_json() for element in self]

    @classmethod
    def from_json(cls, chain: list[dict[str, Any]]) -> 'MessageChain':
        return MessageChain([MessageElement.from_json(obj) for obj in chain])


class AbstractMessageElement(_mixin.FromJsonWithType, _mixin.ToJsonWithType, MessageElement, ABC):
    pass


@dataclass
class Source(AbstractMessageElement):
    id: int
    time: int


@dataclass
class Quote(AbstractMessageElement):
    id: int
    group_id: int
    sender_id: int
    target_id: int
    origin: MessageChain


@dataclass
class At(AbstractMessageElement):
    target: int
    display: str | None = None


@dataclass
class AtAll(AbstractMessageElement):
    pass


@dataclass
class Face(AbstractMessageElement):
    face_id: int | None = None
    name: str | None = None


@dataclass
class Plain(AbstractMessageElement):
    text: str


@dataclass
class Image(AbstractMessageElement):
    image_id: str | None = None
    url: str | None = None
    path: str | None = None
    base64: str | None = None


@dataclass
class FlashImage(AbstractMessageElement):
    image_id: str | None = None
    url: str | None = None
    path: str | None = None
    base64: str | None = None


@dataclass
class Voice(AbstractMessageElement):
    voice_id: str | None = None
    url: str | None = None
    path: str | None = None
    base64: str | None = None
    length: int | None = None


@dataclass
class Xml(AbstractMessageElement):
    xml: str


@dataclass
class Json(AbstractMessageElement):
    json: str


@dataclass
class App(AbstractMessageElement):
    content: str


@dataclass
class Poke(AbstractMessageElement):
    name: str


@dataclass
class Dice(AbstractMessageElement):
    value: int


@dataclass
class MarketFace(AbstractMessageElement):
    id: int
    name: str


@dataclass
class MusicShare(AbstractMessageElement):
    kind: str
    title: str
    summary: str
    jump_url: str
    picture_url: str
    music_url: str
    brief: str


@dataclass
class Forward(AbstractMessageElement):
    @dataclass
    class Node(_mixin.FromJsonWithoutType, _mixin.ToJsonWithoutType, Entity):
        sender_id: int
        time: int
        sender_name: str
        message_chain: MessageChain
        message_id: str

    node_list: list[Node]


@dataclass
class File(AbstractMessageElement):
    id: str
    name: str
    size: int


@dataclass
class MiraiCode(AbstractMessageElement):
    code: str


@functools.cache
def message_element_class_dict() -> dict[str, Type[MessageElement]]:
    return {cls.__name__: cls for cls in MESSAGE_ELEMENT_TYPES}


MESSAGE_ELEMENT_TYPES = (
    Source,
    Quote,
    At,
    AtAll,
    Face,
    Plain,
    Image,
    FlashImage,
    Voice,
    Xml,
    Json,
    App,
    Poke,
    Dice,
    MarketFace,
    MusicShare,
    Forward,
    File,
    MiraiCode
)
