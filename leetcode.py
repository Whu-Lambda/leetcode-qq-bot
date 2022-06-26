import re
from datetime import date, datetime
from dataclasses import dataclass
from typing import Any

import aiohttp
import markdownify


@dataclass
class DailyProblem:
    date: date
    frontend_id: int
    slug: str
    title: str
    difficulty: str
    description: str


class NetworkException(Exception):
    pass


en_base_url = 'https://leetcode.com/graphql'
cn_base_url = 'https://leetcode.cn/graphql'


def html2md(html: str) -> str:
    return markdownify.markdownify(html, bullets='-').replace('\t', '  ')


async def en_daily_problem() -> DailyProblem:
    async with aiohttp.ClientSession() as session:
        async with session.post(en_base_url, json={
            'operationName': 'questionOfToday',
            'variables': {},
            'query': '''
                query questionOfToday {
                    activeDailyCodingChallengeQuestion {
                        date
                        question {
                            questionFrontendId
                            questionTitleSlug
                            title
                            content
                            difficulty
                        }
                    }
                }'''
        }) as response:
            if response.status != 200:
                raise NetworkException(response)
            data: dict[str, Any] = (await response.json())['data']
            question: dict[str, Any] = data['activeDailyCodingChallengeQuestion']['question']
            content = html2md(question['content'])
            if '**Example' in content:
                description = content[:content.find('**Example')]
            else:
                description = content
            description = '\n\n'.join(line.strip() for line in description.split('\n') if len(line.strip()) > 0)
            return DailyProblem(
                date=datetime.strptime(data['activeDailyCodingChallengeQuestion']['date'], '%Y-%m-%d').date(),
                frontend_id=question['questionFrontendId'],
                slug=question['questionTitleSlug'],
                title=question['title'],
                difficulty=question['difficulty'],
                description=description
            )


async def cn_daily_problem() -> DailyProblem:
    async with aiohttp.ClientSession() as session:
        async with session.post(cn_base_url, json={
            'operationName': 'questionOfToday',
            'variables': {},
            'query': '''
                query questionOfToday {
                    todayRecord {
                        date
                        question {
                            questionFrontendId
                            questionTitleSlug
                            translatedTitle
                            translatedContent
                            difficulty
                        }
                    }
                }'''
        }) as response:
            if response.status != 200:
                raise NetworkException(response)
            data: dict[str, Any] = (await response.json())['data']
            question: dict[str, Any] = data['todayRecord'][0]['question']
            content = html2md(question['translatedContent'])
            if '**示例' in content:
                description = content[:content.find('**示例')]
            else:
                description = content
            description = '\n\n'.join(line.strip() for line in description.split('\n') if len(line.strip()) > 0)
            return DailyProblem(
                date=datetime.strptime(data['todayRecord'][0]['date'], '%Y-%m-%d').date(),
                frontend_id=question['questionFrontendId'],
                slug=question['questionTitleSlug'],
                title=question['translatedTitle'],
                difficulty=question['difficulty'],
                description=description
            )
