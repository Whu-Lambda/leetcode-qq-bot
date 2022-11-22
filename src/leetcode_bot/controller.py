import asyncio
from datetime import datetime, time, timezone, timedelta
from typing import Literal

from lightq import filters, resolvers
from lightq import Bot, message_handler, event_handler, resolve, Controller, RecvContext
from lightq.entities import GroupMessage, MessageChain, Plain, NudgeEvent
from lightq.decorators import regex_fullmatch

from . import leetcode
from .config import Config, Group
from .logging import logger


def extractor(chain: MessageChain) -> str:
    plain = chain.get(Plain)
    return plain.text.strip() if plain is not None else ''


def problem_to_en_message(problem: leetcode.DailyProblem) -> str:
    return f'Daily LeetCoding Challenge ({problem.date})\n' \
           f'{problem.frontend_id}. {problem.title}\n' \
           f'Difficulty: {problem.difficulty}\n' \
           f'https://leetcode.com/problems/{problem.slug}\n' \
           f'\n' \
           f'{problem.description}'


def problem_to_cn_message(problem: leetcode.DailyProblem) -> str:
    return f'力扣每日一题（{problem.date}）\n' \
           f'{problem.frontend_id}. {problem.title}\n' \
           f'难度：{problem.difficulty}\n' \
           f'https://leetcode.cn/problems/{problem.slug}\n' \
           f'\n' \
           f'{problem.description}'


class LeetCodeController(Controller):
    def __init__(self, bot: Bot, config: Config):
        self.bot = bot
        self.config = config

    def condition(self, context: RecvContext) -> bool:
        return filters.is_at_bot(context)
        # return (filters.is_at_bot(context)
        #         and resolvers.get_group_id(context) in self.config.groups)

    @regex_fullmatch('daily', extractor=extractor)
    @message_handler(GroupMessage, filters=condition)
    async def en_daily(self) -> str:
        try:
            problem = await leetcode.en_daily(timeout=10.0)
        except Exception:
            message = 'LeetCode 美国站每日一题获取失败'
            logger.exception(f'An exception happened during fetching the EN daily problem.')
        else:
            message = problem_to_en_message(problem)
        return message

    @regex_fullmatch('每日一题', extractor=extractor)
    @message_handler(GroupMessage, filters=condition)
    async def cn_daily(self) -> str:
        try:
            problem = await leetcode.cn_daily(timeout=10.0)
        except Exception:
            message = 'LeetCode 中国站每日一题获取失败'
            logger.exception(f'An exception happened during fetching the CN daily problem.')
        else:
            message = problem_to_cn_message(problem)
        return message

    @regex_fullmatch('push (?P<option>on|off)', extractor=extractor)
    @resolve(resolvers.group_id)
    @message_handler(GroupMessage, filters=condition)
    def switch_push(self, group_id: int, option: str) -> str:
        on = option == 'on'
        if group_id not in self.config.groups:
            self.config.groups[group_id] = Group(group_id)
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

    @event_handler(NudgeEvent)
    async def nudge_response(self, event: NudgeEvent, bot: Bot):
        """谁拍一拍我，我就拍一拍谁"""
        if (event.subject.kind == 'Group'
            and event.target == bot.bot_id
            and event.from_id != bot.bot_id):
            await bot.api.send_nudge(event.from_id, event.subject.id, 'Group')

    async def push_en_daily_to_groups(self):
        await self.__push_daily_to_groups('en')

    async def push_cn_daily_to_groups(self):
        await self.__push_daily_to_groups('cn')

    async def __push_daily_to_groups(self, site: Literal['en', 'cn']):
        utc_offset = 0 if site == 'en' else 8
        now = datetime.now(timezone(timedelta(hours=utc_offset)))
        expected_date = now.date() + timedelta(days=1) \
            if now.time() >= time(23, 59, 55) \
            else now.date()
        try:
            problem = await leetcode.en_daily(expected_date, timeout=60.0) if site == 'en' \
                else await leetcode.cn_daily(expected_date, timeout=60.0)
        except Exception:
            logger.exception(f'An exception happened during fetching the {site.upper()} daily problem.')
        else:
            message = problem_to_en_message(problem) if site == 'en' \
                else problem_to_cn_message(problem)
            _ = await asyncio.gather(*[
                self.bot.api.send_group_message(group.id, message)
                for group in self.config.groups.values() if group.push
            ], return_exceptions=True)
