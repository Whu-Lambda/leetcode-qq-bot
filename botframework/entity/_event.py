import functools
from abc import ABC
from dataclasses import dataclass
from typing import Any, Type

from . import _mixin
from ._commons import Friend, Group, Member, Client
from ._element import MessageElement
from ._entity import Entity


class Event(Entity, ABC):
    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'Event':
        class_dict = event_class_dict()
        assert obj['type'] in class_dict
        event_class = class_dict[obj['type']]
        return event_class.from_json(obj)


class AbstractEvent(_mixin.FromJsonWithType, _mixin.ToJsonWithType, Event, ABC):
    pass


# region Bot 自身事件

@dataclass
class BotOnlineEvent(AbstractEvent):
    """
    Bot 登录成功
    """
    qq: int


@dataclass
class BotOfflineEventActive(AbstractEvent):
    """
    Bot 主动离线
    """
    qq: int


@dataclass
class BotOfflineEventForce(AbstractEvent):
    """
    Bot 被挤下线
    """
    qq: int


@dataclass
class BotOfflineEventDropped(AbstractEvent):
    """
    Bot 被服务器断开或因网络问题而掉线
    """
    qq: int


@dataclass
class BotReloginEvent(AbstractEvent):
    """
    Bot 主动重新登录
    """
    qq: int


# endregion Bot 自身事件

# region 好友事件

@dataclass
class FriendInputStatusChangedEvent(AbstractEvent):
    """
    好友输入状态改变
    """
    friend: Friend
    inputting: bool


@dataclass
class FriendNickChangedEvent(AbstractEvent):
    """
    好友昵称改变
    """
    friend: Friend
    from_: str
    to: str


# endregion 好友事件

# region 群事件

@dataclass
class BotGroupPermissionChangeEvent(AbstractEvent):
    """
    Bot 在群里的权限被改变，操作人一定是群主
    """
    origin: str
    current: str
    group: Group


@dataclass
class BotMuteEvent(AbstractEvent):
    """
    Bot 被禁言
    """
    duration_seconds: int
    operator: Member


@dataclass
class BotUnmuteEvent(AbstractEvent):
    """
    Bot 被取消禁言
    """
    operator: Member


@dataclass
class BotJoinGroupEvent(AbstractEvent):
    """
    Bot 加入了一个新群
    """
    group: Group
    invitor: Member | None


@dataclass
class BotLeaveEventActive(AbstractEvent):
    """
    Bot 主动退出一个群
    """
    group: Group


@dataclass
class BotLeaveEventKick(AbstractEvent):
    """
    Bot 被踢出一个群
    """
    group: Group
    operator: Member


@dataclass
class GroupRecallEvent(AbstractEvent):
    """
    群消息撤回
    """
    author_id: int
    message_id: int
    time: int
    group: Group
    operator: Member | None


@dataclass
class FriendRecallEvent(AbstractEvent):
    """
    好友消息撤回
    """
    author_id: int
    message_id: int
    time: int
    operator: int


@dataclass
class NudgeEvent(AbstractEvent):
    """
    戳一戳事件
    """

    @dataclass
    class Subject(_mixin.FromJsonWithoutType, _mixin.ToJsonWithoutType, Entity):
        id: int
        kind: str

    from_id: int
    subject: Subject
    action: str
    suffix: str
    target: int


@dataclass
class GroupNameChangeEvent(AbstractEvent):
    """
    某个群名改变
    """
    origin: str
    current: str
    group: Group
    operator: Member | None


@dataclass
class GroupEntranceAnnouncementChangeEvent(AbstractEvent):
    """
    某群入群公告改变
    """
    origin: str
    current: str
    group: Group
    operator: Member | None


@dataclass
class GroupMuteAllEvent(AbstractEvent):
    """
    全员禁言
    """
    origin: bool
    current: bool
    group: Group
    operator: Member | None


@dataclass
class GroupAllowAnonymousChatEvent(AbstractEvent):
    """
    匿名聊天
    """
    origin: bool
    current: bool
    group: Group
    operator: Member | None


@dataclass
class GroupAllowConfessTalkEvent(AbstractEvent):
    """
    坦白说
    """
    origin: bool
    current: bool
    group: Group
    is_by_bot: bool


@dataclass
class GroupAllowMemberInviteEvent(AbstractEvent):
    """
    允许群员邀请好友加群
    """
    origin: bool
    current: bool
    group: Group
    operator: Member | None


@dataclass
class MemberJoinEvent(AbstractEvent):
    """
    新人入群的事件
    """
    member: Member
    invitor: Member | None


@dataclass
class MemberLeaveEventKick(AbstractEvent):
    """
    成员被踢出群（该成员不是 bot）
    """
    member: Member
    operator: Member | None


@dataclass
class MemberLeaveEventQuit(AbstractEvent):
    """
    成员主动离群（该成员不是 bot）
    """
    member: Member


@dataclass
class MemberCardChangeEvent(AbstractEvent):
    """
    群名片改动
    """
    origin: str
    current: str
    member: Member


@dataclass
class MemberSpecialTitleChangeEvent(AbstractEvent):
    """
    群头衔改动（只有群主有操作限权）
    """
    origin: str
    current: str
    member: Member


@dataclass
class MemberPermissionChangeEvent(AbstractEvent):
    """
    成员权限改变的事件（该成员不是 bot）
    """
    origin: str
    current: str
    member: Member


@dataclass
class MemberMuteEvent(AbstractEvent):
    """
    群成员被禁言事件（该成员不是 bot）
    """
    duration_seconds: int
    member: Member
    operator: Member | None


@dataclass
class MemberUnmuteEvent(AbstractEvent):
    """
    群成员被取消禁言事件（该成员不是 bot）
    """
    member: Member
    operator: Member | None


@dataclass
class MemberHonorChangeEvent(AbstractEvent):
    """
    群员称号改变
    """
    member: Member
    action: str
    honor: str


# endregion 群事件

# region 申请事件

@dataclass
class NewFriendRequestEvent(AbstractEvent):
    """
    添加好友申请
    """
    event_id: int
    from_id: int
    group_id: int
    nick: str
    message: str


@dataclass
class MemberJoinRequestEvent(AbstractEvent):
    """
    用户入群申请（bot需要有管理员权限）
    """
    event_id: int
    from_id: int
    group_id: int
    group_name: str
    nick: str
    message: str


@dataclass
class BotInvitedJoinGroupRequestEvent(AbstractEvent):
    """
    Bot 被邀请入群申请
    """
    event_id: int
    from_id: int
    group_id: int
    group_name: str
    nick: str
    message: str


# endregion 申请事件

# region 其他客户端事件

@dataclass
class OtherClientOnlineEvent(AbstractEvent):
    """
    其他客户端上线
    """
    client: Client
    kind: int | None


@dataclass
class OtherClientOfflineEvent(AbstractEvent):
    """
    其他客户端下线
    """
    client: Client


# endregion 其他客户端事件

# region 命令事件

@dataclass
class CommandExecutedEvent(AbstractEvent):
    """
    命令被执行
    """
    name: str
    friend: None
    member: Member | None
    args: list[MessageElement]


# endregion 命令事件

@functools.cache
def event_class_dict() -> dict[str, Type[Event]]:
    return {cls.__name__: cls for cls in EVENT_TYPES}


EVENT_TYPES = (
    BotOnlineEvent,
    BotOfflineEventActive,
    BotOfflineEventForce,
    BotOfflineEventDropped,
    BotReloginEvent,
    FriendInputStatusChangedEvent,
    FriendNickChangedEvent,
    BotGroupPermissionChangeEvent,
    BotMuteEvent,
    BotUnmuteEvent,
    BotJoinGroupEvent,
    BotLeaveEventKick,
    BotLeaveEventKick,
    GroupRecallEvent,
    FriendRecallEvent,
    NudgeEvent,
    GroupNameChangeEvent,
    GroupEntranceAnnouncementChangeEvent,
    GroupMuteAllEvent,
    GroupAllowAnonymousChatEvent,
    GroupAllowConfessTalkEvent,
    GroupAllowMemberInviteEvent,
    MemberJoinEvent,
    MemberLeaveEventKick,
    MemberLeaveEventQuit,
    MemberCardChangeEvent,
    MemberSpecialTitleChangeEvent,
    MemberPermissionChangeEvent,
    MemberMuteEvent,
    MemberUnmuteEvent,
    MemberHonorChangeEvent,
    NewFriendRequestEvent,
    MemberJoinRequestEvent,
    BotInvitedJoinGroupRequestEvent,
    OtherClientOnlineEvent,
    OtherClientOfflineEvent
)
