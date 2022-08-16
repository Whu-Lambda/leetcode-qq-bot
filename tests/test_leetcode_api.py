import unittest
from datetime import datetime, timezone, timedelta

from leetcode_bot import leetcode


class LeetCodeApiTest(unittest.IsolatedAsyncioTestCase):
    async def test_en_daily(self):
        problem = await leetcode.query_en_daily()
        today = datetime.now(timezone(timedelta(hours=0))).date()
        self.assertEqual(today, problem.date)

    async def test_cn_daily(self):
        problem = await leetcode.query_cn_daily()
        today = datetime.now(timezone(timedelta(hours=8))).date()
        self.assertEqual(today, problem.date)
