import unittest
import json

from leetcode_bot.config import Config, Group


class ConfigTest(unittest.TestCase):
    def test_config_from_json(self):
        j = json.loads('''{
            "bot_id": 12345,
            "verify_key": "verify_key",
            "base_url": "ws://localhost:8080",
            "groups": [
                {
                    "id": 123456789,
                    "push": true
                },
                {
                    "id": 987654321,
                    "push": false
                },
                {
                    "id": 12345
                }
            ]
        }''')
        expected = Config(
            bot_id=12345,
            verify_key='verify_key',
            base_url='ws://localhost:8080',
            groups={
                123456789: Group(123456789, True),
                987654321: Group(987654321, False),
                12345: Group(12345)
            },
            file_path=''
        )
        self.assertEqual(expected, Config.from_json(j, ''))

    def test_config_to_json(self):
        config = Config(
            bot_id=12345,
            verify_key='verify_key',
            base_url='ws://localhost:8080',
            groups={
                123456789: Group(123456789, True),
                987654321: Group(987654321, False),
                12345: Group(12345)
            },
            file_path=''
        )
        expected_groups = [
            {
                "id": 123456789,
                "push": True
            },
            {
                "id": 987654321,
                "push": False
            },
            {
                "id": 12345,
                "push": False
            }
        ]
        self.assertCountEqual(expected_groups, config.to_json()['groups'])
