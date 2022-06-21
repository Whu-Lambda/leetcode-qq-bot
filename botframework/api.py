import asyncio
import json
import urllib.parse
from collections import deque
from typing import Any, Callable, overload, Literal

import websockets

from . import entity
from . import exception
from ._commons import AutoIncrement, remove_if
from ._logging import logger
from .entity import Message, Event, MessageChain, Plain

__ALL__ = [
    'CODE_TO_EXCEPTION',
    'MiraiApi'
]

CODE_TO_EXCEPTION = {
    1: exception.WrongVerifyKey,
    2: exception.BotNotExist,
    3: exception.InvalidSession,
    4: exception.InactiveSession,
    5: exception.TargetNotExist,
    6: exception.FileNotExist,
    10: exception.NoPermission,
    20: exception.BotInSilence,
    30: exception.MessageTooLong,
    400: exception.IncorrectAccess
}


class MiraiApi:
    class Iter:
        def __init__(self, api: 'MiraiApi'):
            self.__api = api

        def __aiter__(self): return self

        async def __anext__(self) -> Message | Event | dict[str, Any]:
            try:
                return await self.__api.recv()
            except websockets.ConnectionClosedOK:
                raise StopIteration()

    def __init__(
        self,
        bot_id: int,
        verify_key: str,
        host='localhost',
        port=8080
    ):
        self.__bot_id = bot_id
        self.__verify_key = verify_key
        self.__host = host
        self.__port = port
        self.__ws = None
        self.__unhandled: deque[dict[str, Any]] = deque(maxlen=10)
        self.__session_key: str | None = None
        self.__increment = AutoIncrement(start=233, max_value=int(1e8))
        self.__waiting_for_recv = False

    @property
    def bot_id(self) -> int: return self.__bot_id

    @property
    def verify_key(self) -> str: return self.__verify_key

    @property
    def host(self) -> str: return self.__host

    @property
    def port(self) -> int: return self.__port

    @property
    def session_key(self) -> str | None: return self.__session_key

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Mirai-api-http 传入格式：
        ::
            {
                "syncId": 123,                  // 消息同步的字段
                "command": "sendFriendMessage", // 命令字
                "subCommand": null,             // 子命令字, 可空
                "content": {}                   // 命令的数据对象, 与通用接口定义相同
            }

        ``syncId`` 由 ``send`` 方法自动生成，无需放在 JSON 中。

        :returns: 若状态码为 0 则将响应的 JSON 返回
        :raises MiraiApiException: 若状态码非 0 则抛出对应的异常
        """
        await self.connect()
        sync_id = self.__increment.get()
        data['syncId'] = sync_id
        logger.info(f'websocket send: {data}')
        await self.__ws.send(json.dumps(data))
        # 响应结果的 syncId 为字符串而非数字
        response = await self.__expect_data(lambda x: x['syncId'] == str(sync_id))
        response = response['data']
        if 'code' not in response:  # 有的响应不含 code 字段
            return response
        if response['code'] == 0:
            return response
        else:
            assert response['code'] in CODE_TO_EXCEPTION
            exception_class = CODE_TO_EXCEPTION[response['code']]
            raise exception_class(response)

    async def recv(self) -> Message | Event | dict[str, Any]:
        """
        Mirai-api-http 推送格式：
        ::
            {
                "syncId": "123", // 消息同步的字段
                "data": {}     // 推送消息内容, 与通用接口定义相同
            }

        ``recv`` 方法返回其中的 ``data`` 部分。
        """
        # 非响应结果（他人发送的消息），syncId 为 "-1"
        data = await self.__expect_data(lambda x: int(x['syncId']) < 0)
        data = data['data']
        if data['type'] in entity.message_class_dict():
            return Message.from_json(data)
        elif data['type'] in entity.event_class_dict():
            return Event.from_json(data)
        else:
            return data

    @overload
    async def send_friend_message(self, friend_id: int, message: str) -> int: pass

    @overload
    async def send_friend_message(self, friend_id: int, message: MessageChain) -> int: pass

    async def send_friend_message(self, friend_id: int, message: str | MessageChain) -> int:
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send({
            'command': 'sendFriendMessage',
            'content': {
                'target': friend_id,
                'messageChain': chain.to_json()
            }
        }))['messageId']

    @overload
    async def send_group_message(self, group_id: int, message: str) -> int: pass

    @overload
    async def send_group_message(self, group_id: int, message: MessageChain) -> int: pass

    async def send_group_message(self, group_id: int, message: str | MessageChain) -> int:
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send({
            'command': 'sendGroupMessage',
            'content': {
                'target': group_id,
                'messageChain': chain.to_json()
            }
        }))['messageId']

    @overload
    async def send_temp_message(self, qq: int, group: int, message: str) -> int: pass

    @overload
    async def send_temp_message(self, qq: int, group: int, message: MessageChain) -> int: pass

    async def send_temp_message(self, qq: int, group: int, message: str | MessageChain) -> int:
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send({
            'command': 'sendTempMessage',
            'content': {
                'qq': qq,
                'group': group,
                'messageChain': chain.to_json()
            }
        }))['messageId']

    async def send_nudge(
        self,
        target: int,
        subject: int,
        kind: Literal['Friend', 'Group', 'Stranger']
    ) -> int:
        return (await self.send({
            'command': 'sendNudge',
            'content': {
                'target': target,
                'subject': subject,
                'kind': kind
            }
        }))['messageId']

    async def recall(self, message_id: str):
        await self.send({
            'command': 'recall',
            'content': {'target': message_id}
        })

    async def message_from_id(self, message_id: int) -> Message | None:
        try:
            return Message.from_json((await self.send({
                'command': 'messageFromId',
                'content': {'id': message_id}
            }))['data'])
        except exception.TargetNotExist:
            return None

    async def __expect_data(self, predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
        await self.connect()
        while True:
            data = remove_if(self.__unhandled, lambda x: predicate(x))  # from queue
            if data is not None:
                return data
            if self.__waiting_for_recv:
                await asyncio.sleep(0)  # let other coroutine receive data
                continue
            self.__waiting_for_recv = True
            data: dict[str, Any] = json.loads(await self.__ws.recv())  # from websocket
            self.__waiting_for_recv = False
            logger.info(f'websocket recv: {data}')
            if data['syncId'] == '':  # first message after connected
                self.__session_key = data['data']['session']
                continue
            elif predicate(data):
                return data
            else:
                self.__unhandled.append(data)
            await asyncio.sleep(0)

    async def connect(self):
        if self.__ws is not None:
            return
        encoded_key = urllib.parse.quote_plus(self.verify_key)
        self.__ws = await websockets.connect(
            f'ws://{self.host}:{self.port}/all?verifyKey={encoded_key}&qq={self.bot_id}'
        )

    async def close(self):
        if self.__ws is None:
            return
        await self.__ws.close()
        self.__ws = None
        self.__session_key = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __aiter__(self):
        return self.Iter(self)
