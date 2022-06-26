import asyncio
import logging
import json
import datetime
import sys
import os.path
from typing import Any, Awaitable, Callable

sys.path.append(os.path.dirname(__file__))
import leetcode
import botframework.exception
from botframework import MiraiApi, logger
from botframework.entity import GroupMessage, MessageChain, At, Plain
from botframework._commons import first


async def query_en_daily() -> str:
    try:
        problem = await leetcode.en_daily_problem()
        return f'Daily LeetCoding Challenge ({problem.date})\n' \
               f'{problem.frontend_id}. {problem.title}\n' \
               f'Difficulty: {problem.difficulty}\n' \
               f'https://leetcode.com/problems/{problem.slug}\n' \
               f'\n' \
               f'{problem.description}'
    except leetcode.NetworkException:
        return 'LeetCode 美国站每日一题获取失败'


async def query_cn_daily() -> str:
    try:
        problem = await leetcode.cn_daily_problem()
        return f'力扣每日一题（{problem.date}）\n' \
               f'{problem.frontend_id}. {problem.title}\n' \
               f'难度：{problem.difficulty}\n' \
               f'https://leetcode.cn/problems/{problem.slug}\n' \
               f'\n' \
               f'{problem.description}'
    except leetcode.NetworkException:
        return 'LeetCode 中国站每日一题获取失败'


def is_at_me(chain: MessageChain, bot_id: int) -> bool:
    return any(isinstance(e, At) and e.target == bot_id for e in chain)


def extract_text(chain: MessageChain) -> str:
    text = first(e.text for e in chain if isinstance(e, Plain))
    return text.strip() if text is not None else ''


def load_json(path: str):
    with open(path, encoding='utf-8') as file:
        return json.load(file)


async def sleep_until(until: datetime.datetime):
    now = datetime.datetime.now(until.tzinfo)
    await asyncio.sleep((until - now).total_seconds())


async def do_everyday(time: datetime.time, async_func: Callable[..., Awaitable]):
    now = datetime.datetime.now(time.tzinfo)
    until = datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=time.hour,
        minute=time.minute,
        second=time.second,
        microsecond=time.microsecond,
        tzinfo=time.tzinfo
    )
    if until <= now:
        until = until + datetime.timedelta(days=1)
    while True:
        await sleep_until(until)
        await async_func()
        until = until + datetime.timedelta(days=1)


async def main_async():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config: dict[str, Any] = load_json(config_path)

    def set_push(group_id: int, value: bool):
        config['group_setting'][str(group_id)]['push'] = value
        with open(config_path, mode='w', encoding='utf-8') as file:
            json.dump(config, file, indent=4)

    bot_id = config['bot_id']
    target_groups: list[int] = [int(group_id) for group_id in config['group_setting']]
    async with MiraiApi(
        config['bot_id'],
        config['verify_key'],
        config['host'],
        config['port']
    ) as mirai:
        async def push_en_daily():
            daily_message = await query_en_daily()
            for group_id, group_setting in config['group_setting'].items():
                if group_setting['push']:
                    await mirai.send_group_message(int(group_id), daily_message)

        async def push_cn_daily():
            daily_message = await query_cn_daily()
            for group_id, group_setting in config['group_setting'].items():
                if group_setting['push']:
                    await mirai.send_group_message(int(group_id), daily_message)

        tasks = set()
        loop = asyncio.get_running_loop()

        def create_everyday_task(time: datetime.time, async_func: Callable[..., Awaitable]):
            task = loop.create_task(do_everyday(time, async_func))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            return task

        create_everyday_task(
            datetime.time(
                hour=0, minute=0, second=50,
                tzinfo=datetime.timezone(datetime.timedelta(hours=0))
            ),
            push_en_daily
        )  # 00:00 (UTC+00:00)
        create_everyday_task(
            datetime.time(
                hour=0, minute=0, second=50,
                tzinfo=datetime.timezone(datetime.timedelta(hours=8))
            ),
            push_cn_daily
        )  # 00:00 (UTC+08:00)

        async for data in mirai:
            if not isinstance(data, GroupMessage):
                continue
            group_id = data.sender.group.id
            if group_id not in target_groups:
                continue
            if not is_at_me(data.message_chain, bot_id):
                continue
            text = extract_text(data.message_chain)

            async def handler():
                try:
                    if text == 'daily':
                        await mirai.send_group_message(group_id, await query_en_daily())
                    elif text == '每日一题':
                        await mirai.send_group_message(group_id, await query_cn_daily())
                    elif text == 'push on':
                        set_push(group_id, True)
                        await mirai.send_group_message(group_id, '自动推送已开启')
                    elif text == 'push off':
                        set_push(group_id, False)
                        await mirai.send_group_message(group_id, '自动推送已关闭')
                    elif text == '' or text == 'help' or text == '帮助':
                        await mirai.send_group_message(
                            group_id,
                            '使用帮助\n'
                            '@我并发送相应命令：\n'
                            '- daily：获取 LeetCode 美国站每日一题\n'
                            '- 每日一题：获取 LeetCode 中国站每日一题\n'
                            '- push on/off：打开/关闭自动推送'
                        )
                    # elif text == 'delay':
                    #     await mirai.send_group_message(group_id, 'delay begin')
                    #     await asyncio.sleep(10)
                    #     await mirai.send_group_message(group_id, 'delay end')
                except botframework.exception.MiraiApiException:
                    logger.exception()

            task = loop.create_task(handler())
            tasks.add(task)
            task.add_done_callback(tasks.discard)


def main():
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
