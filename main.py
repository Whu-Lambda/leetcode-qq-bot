import asyncio
import os.path
import sys
from datetime import time, timezone, timedelta
from lightq import Bot

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from leetcode_bot import LeetCodeController, Config


async def main():
    config = Config.from_file(os.path.join(os.path.dirname(__file__), 'config.json'))
    bot = Bot(config.bot_id, config.verify_key, config.base_url)
    controller = LeetCodeController(bot, config)
    bot.add_all(controller.handlers)
    bot.create_everyday_task(
        time(0, 0, 5, tzinfo=timezone(timedelta(hours=0))),
        controller.push_en_daily_to_groups
    )  # push en daily at 00:00:05 (UTC+00:00)
    bot.create_everyday_task(
        time(0, 0, 5, tzinfo=timezone(timedelta(hours=8))),
        controller.push_cn_daily_to_groups
    )  # push cn daily at 00:00:05 (UTC+08:00)
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
