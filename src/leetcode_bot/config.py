import json
import dataclasses
from typing import Any


@dataclasses.dataclass
class Group:
    id: int
    push: bool = False


@dataclasses.dataclass
class Config:
    bot_id: int
    verify_key: str
    base_url: str
    groups: dict[int, Group]
    file_path: str

    def to_json(self) -> dict[str, Any]:
        j: dict[str, Any] = dataclasses.asdict(self)
        del j['file_path']
        j['groups'] = list(j['groups'].values())
        return j

    def save(self):
        with open(self.file_path, mode='w', encoding='utf-8') as file:
            json.dump(self.to_json(), file, indent=4)

    @staticmethod
    def from_json(obj: dict[str, Any], file_path: str) -> 'Config':
        return Config(
            **{k: v for k, v in obj.items() if k != 'groups'},
            groups={group['id']: Group(**group) for group in obj['groups']},
            file_path=file_path
        )

    @staticmethod
    def from_file(file_path: str) -> 'Config':
        with open(file_path, encoding='utf-8') as file:
            return Config.from_json(json.load(file), file_path)
