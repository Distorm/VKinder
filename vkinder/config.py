from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    group_token: str
    user_token: str
    group_id: int
    database_url: str
    vk_api_version: str = "5.199"


def get_settings() -> Settings:
    group_token = getenv("GROUP_TOKEN", "").strip()
    user_token = getenv("USER_TOKEN", "").strip()
    group_id = getenv("GROUP_ID", "").strip()
    database_url = getenv("DATABASE_URL", "").strip()
    vk_api_version = getenv("VK_API_VERSION", "5.199").strip()

    missed = []
    if not group_token:
        missed.append("GROUP_TOKEN")
    if not user_token:
        missed.append("USER_TOKEN")
    if not group_id:
        missed.append("GROUP_ID")
    if not database_url:
        missed.append("DATABASE_URL")

    if missed:
        names = ", ".join(missed)
        raise RuntimeError(f"Не заполнены переменные окружения: {names}")

    return Settings(
        group_token=group_token,
        user_token=user_token,
        group_id=int(group_id),
        database_url=database_url,
        vk_api_version=vk_api_version,
    )
