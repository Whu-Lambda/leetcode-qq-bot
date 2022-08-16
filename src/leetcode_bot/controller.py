from lightq import filters, resolvers, Bot, message_handler, resolve, Controller, handler_property
from lightq.entities import GroupMessage, MessageChain, Plain
from lightq.decorators import regex_fullmatch

from . import leetcode
from .config import Config


class LeetCodeController(Controller):
    def __init__(self, bot: Bot, config: Config):
        self.bot = bot
        self.config = config
        self.filters = [filters.is_at_bot, filters.from_group(*config.groups)]

    @staticmethod
    def extractor(chain: MessageChain) -> str:
        plain = chain.get(Plain)
        return plain.text.strip() if plain is not None else ''

    @handler_property
    def en_daily(self):
        @regex_fullmatch('daily', extractor=self.extractor)
        @message_handler(GroupMessage, filters=self.filters)
        async def handler() -> str:
            return await self.create_en_daily_message()

        return handler

    @handler_property
    def cn_daily(self):
        @regex_fullmatch('每日一题', extractor=self.extractor)
        @message_handler(GroupMessage, filters=self.filters)
        async def handler() -> str:
            return await self.create_cn_daily_message()

        return handler

    @handler_property
    def switch_push(self):
        @regex_fullmatch('push (?P<option>on|off)', extractor=self.extractor)
        @resolve(resolvers.group_id)
        @message_handler(GroupMessage, filters=self.filters)
        def handler(group_id: int, option: str) -> str:
            on = option == 'on'
            self.config.groups[group_id].push = on
            self.config.save()
            return f'自动推送已{"开启" if on else "关闭"}'

        return handler

    @handler_property
    def get_help(self):
        @regex_fullmatch('(help|帮助)?', extractor=self.extractor)
        @message_handler(GroupMessage, filters=self.filters)
        def handler() -> str:
            return '使用帮助\n' \
                   '@我并发送相应命令：\n' \
                   '- daily：获取 LeetCode 美国站每日一题\n' \
                   '- 每日一题：获取 LeetCode 中国站每日一题\n' \
                   '- push on/off：打开/关闭自动推送'

        return handler

    async def push_en_daily_to_groups(self):
        message = await self.create_en_daily_message()
        for group in self.config.groups.values():
            if group.push:
                await self.bot.api.send_group_message(group.id, message)

    async def push_cn_daily_to_groups(self):
        message = await self.create_cn_daily_message()
        for group in self.config.groups.values():
            if group.push:
                await self.bot.api.send_group_message(group.id, message)

    @staticmethod
    async def create_en_daily_message() -> str:
        try:
            problem = await leetcode.en_daily()
            return f'Daily LeetCoding Challenge ({problem.date})\n' \
                   f'{problem.frontend_id}. {problem.title}\n' \
                   f'Difficulty: {problem.difficulty}\n' \
                   f'https://leetcode.com/problems/{problem.slug}\n' \
                   f'\n' \
                   f'{problem.description}'
        except leetcode.NetworkException:
            return 'LeetCode 美国站每日一题获取失败'

    @staticmethod
    async def create_cn_daily_message() -> str:
        try:
            problem = await leetcode.cn_daily()
            return f'力扣每日一题（{problem.date}）\n' \
                   f'{problem.frontend_id}. {problem.title}\n' \
                   f'难度：{problem.difficulty}\n' \
                   f'https://leetcode.cn/problems/{problem.slug}\n' \
                   f'\n' \
                   f'{problem.description}'
        except leetcode.NetworkException:
            return 'LeetCode 中国站每日一题获取失败'
