from abc import ABC
from typing import Any


class MiraiApiException(Exception, ABC):
    pass


class WrongVerifyKey(MiraiApiException):
    """
    错误的 verify key（状态码 1）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class BotNotExist(MiraiApiException):
    """
    指定的 bot 不存在（状态码 2）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class InvalidSession(MiraiApiException):
    """
    Session 失效或不存在（状态码 3）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class InactiveSession(MiraiApiException):
    """
    Session 未认证（未激活）（状态码 4）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class TargetNotExist(MiraiApiException):
    """
    发送消息目标不存在（指定对象不存在）（状态码 5）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class FileNotExist(MiraiApiException):
    """
    指定文件不存在，出现于发送本地图片（状态码 6）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class NoPermission(MiraiApiException):
    """
    无操作权限，指 bot 没有对应操作的限权（状态码 10）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class BotInSilence(MiraiApiException):
    """
    Bot 被禁言，指 bot 当前无法向指定群发送消息（状态码 20）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class MessageTooLong(MiraiApiException):
    """
    消息过长（状态码 30）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response


class IncorrectAccess(MiraiApiException):
    """
    错误的访问，如参数错误等（状态码 400）
    """

    def __init__(self, response: dict[str, Any]):
        self.response = response
