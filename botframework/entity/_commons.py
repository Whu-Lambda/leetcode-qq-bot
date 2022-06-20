from dataclasses import dataclass

from . import _mixin
from ._entity import Entity


@dataclass
class Friend(_mixin.FromJsonWithoutType, _mixin.ToJsonWithoutType, Entity):
    id: int
    nickname: str
    remark: str


@dataclass
class Group(_mixin.FromJsonWithoutType, _mixin.ToJsonWithoutType, Entity):
    id: int
    name: str
    permission: str


@dataclass
class Member(_mixin.FromJsonWithoutType, _mixin.ToJsonWithoutType, Entity):
    id: int
    member_name: str
    permission: str
    special_title: str
    join_timestamp: int
    last_speak_timestamp: int
    mute_time_remaining: int
    group: Group


@dataclass
class Client(_mixin.FromJsonWithoutType, _mixin.ToJsonWithoutType, Entity):
    id: int
    platform: str
