from datetime import datetime, date, time, timezone, timedelta
from lightq import filters, resolvers, Bot, message_handler, resolve, Controller, RecvContext
from lightq.entities import GroupMessage, MessageChain, Plain
from lightq.decorators import regex_fullmatch

from . import leetcode
from .config import Config


def extractor(chain: MessageChain) -> str:
    plain = chain.get(Plain)
    return plain.text.strip() if plain is not None else ''


class LeetCodeController(Controller):
    def __init__(self, bot: Bot, config: Config):
        self.bot = bot
        self.config = config

    def condition(self, context: RecvContext) -> bool:
        return (filters.is_at_bot(context)
                and resolvers.get_group_id(context) in self.config.groups)

    @regex_fullmatch('daily', extractor=extractor)
    @message_handler(GroupMessage, filters=condition)
    async def en_daily(self) -> str:
        return await self.create_en_daily_message()

    @regex_fullmatch('每日一题', extractor=extractor)
    @message_handler(GroupMessage, filters=condition)
    async def cn_daily(self) -> str:
        return await self.create_cn_daily_message()

    @regex_fullmatch('push (?P<option>on|off)', extractor=extractor)
    @resolve(resolvers.group_id)
    @message_handler(GroupMessage, filters=condition)
    def switch_push(self, group_id: int, option: str) -> str:
        on = option == 'on'
        self.config.groups[group_id].push = on
        self.config.save()
        return f'自动推送已{"开启" if on else "关闭"}'

    @regex_fullmatch('(help|帮助)?', extractor=extractor)
    @message_handler(GroupMessage, filters=condition)
    def get_help(self) -> str:
        return '使用帮助\n' \
               '@我并发送相应命令：\n' \
               '- daily：获取 LeetCode 美国站每日一题\n' \
               '- 每日一题：获取 LeetCode 中国站每日一题\n' \
               '- push on/off：打开/关闭自动推送'

    async def push_en_daily_to_groups(self):
        now = datetime.now(timezone(timedelta(hours=0)))  # UTC+0
        if now.time() >= time(23, 59, 55):
            expected_date = now.date() + timedelta(days=1)
        else:
            expected_date = now.date()
        message = await self.create_en_daily_message(expected_date)
        for group in self.config.groups.values():
            if group.push:
                await self.bot.api.send_group_message(group.id, message)

    async def push_cn_daily_to_groups(self):
        now = datetime.now(timezone(timedelta(hours=8)))  # UTC+8
        if now.time() >= time(23, 59, 55):
            expected_date = now.date() + timedelta(days=1)
        else:
            expected_date = now.date()
        message = await self.create_cn_daily_message(expected_date)
        for group in self.config.groups.values():
            if group.push:
                await self.bot.api.send_group_message(group.id, message)

    @staticmethod
    async def create_en_daily_message(expected_date: date | None = None) -> str:
        try:
            problem = await leetcode.en_daily(expected_date)
            return f'Daily LeetCoding Challenge ({problem.date})\n' \
                   f'{problem.frontend_id}. {problem.title}\n' \
                   f'Difficulty: {problem.difficulty}\n' \
                   f'https://leetcode.com/problems/{problem.slug}\n' \
                   f'\n' \
                   f'{problem.description}'
        except leetcode.NetworkException:
            return 'LeetCode 美国站每日一题获取失败'

    @staticmethod
    async def create_cn_daily_message(expected_date: date | None = None) -> str:
        try:
            problem = await leetcode.cn_daily(expected_date)
            return f'力扣每日一题（{problem.date}）\n' \
                   f'{problem.frontend_id}. {problem.title}\n' \
                   f'难度：{problem.difficulty}\n' \
                   f'https://leetcode.cn/problems/{problem.slug}\n' \
                   f'\n' \
                   f'{problem.description}'
        except leetcode.NetworkException:
            return 'LeetCode 中国站每日一题获取失败'
