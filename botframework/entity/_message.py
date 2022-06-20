import functools
from abc import ABC
from dataclasses import dataclass
from typing import Any, Type

from . import _mixin
from ._commons import Friend, Member, Client
from ._element import MessageChain
from ._entity import Entity


class Message(Entity, ABC):
    sender: Friend | Member | Client
    message_chain: MessageChain

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'Message':
        class_dict = message_class_dict()
        assert obj['type'] in class_dict
        message_class = class_dict[obj['type']]
        return message_class.from_json(obj)


class AbstractMessage(_mixin.FromJsonWithType, _mixin.ToJsonWithType, Message, ABC):
    pass


@dataclass
class FriendMessage(AbstractMessage):
    """
    好友消息
    """
    sender: Friend
    message_chain: MessageChain


@dataclass
class GroupMessage(AbstractMessage):
    """
    群消息
    """
    sender: Member
    message_chain: MessageChain


@dataclass
class TempMessage(AbstractMessage):
    """
    群临时消息
    """
    sender: Member
    message_chain: MessageChain


@dataclass
class StrangerMessage(AbstractMessage):
    """
    陌生人消息
    """
    sender: Friend
    message_chain: MessageChain


@dataclass
class OtherClientMessage(AbstractMessage):
    """
    其他客户端消息
    """
    sender: Client
    message_chain: MessageChain


@functools.cache
def message_class_dict() -> dict[str, Type[Message]]:
    return {cls.__name__: cls for cls in MESSAGE_TYPES}


MESSAGE_TYPES = (
    FriendMessage,
    GroupMessage,
    TempMessage,
    StrangerMessage,
    OtherClientMessage
)

# TODO sync message type
