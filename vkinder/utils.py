
from datetime import date


def calculate_age(bdate: str | None) -> int | None:
    if not bdate:
        return None

    parts = bdate.split(".")
    if len(parts) != 3:
        return None

    try:
        day, month, year = map(int, parts)
        today = date.today()
        age = today.year - year
        if (today.month, today.day) < (month, day):
            age -= 1
        return age
    except ValueError:
        return None


def make_profile_url(vk_id: int, domain: str | None) -> str:
    if domain:
        return f"https://vk.com/{domain}"
    return f"https://vk.com/id{vk_id}"
