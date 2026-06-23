import json
import random
from typing import Any

import vk_api
from vk_api.exceptions import ApiError

from vkinder.config import Settings
from vkinder.utils import calculate_age, make_profile_url


class VKService:
    def __init__(self, settings: Settings) -> None:
        self.group_session = vk_api.VkApi(
            token=settings.group_token,
            api_version=settings.vk_api_version,
        )
        self.user_session = vk_api.VkApi(
            token=settings.user_token,
            api_version=settings.vk_api_version,
        )
        self.group_vk = self.group_session.get_api()
        self.user_vk = self.user_session.get_api()

    def send_message(
        self,
        peer_id: int,
        message: str,
        attachment: str | None = None,
        keyboard: str | None = None,
    ) -> None:
        params: dict[str, Any] = {
            "peer_id": peer_id,
            "message": message,
            "random_id": random.randint(1, 2_147_483_647),
        }

        if attachment:
            params["attachment"] = attachment
        if keyboard:
            params["keyboard"] = keyboard

        self.group_vk.messages.send(**params)

    def get_profile(self, vk_id: int) -> dict[str, Any]:
        fields = "sex,city,bdate,domain"
        response = self.group_vk.users.get(user_ids=vk_id, fields=fields)
        if not response:
            raise RuntimeError("VK не вернул данные пользователя")

        profile = response[0]
        city = profile.get("city") or {}
        return {
            "vk_id": profile["id"],
            "first_name": profile.get("first_name", ""),
            "last_name": profile.get("last_name", ""),
            "sex": profile.get("sex"),
            "city_id": city.get("id"),
            "city_title": city.get("title"),
            "bdate": profile.get("bdate"),
            "age": calculate_age(profile.get("bdate")),
        }

    def get_city_id(self, city_name: str) -> tuple[int | None, str | None]:
        response = self.user_vk.database.getCities(
            country_id=1,
            q=city_name,
            count=1,
        )
        items = response.get("items", [])
        if not items:
            return None, None

        city = items[0]
        return city["id"], city["title"]

    def search_people(
        self,
        sex: int | None,
        city_id: int | None,
        age: int | None,
        offset: int,
        count: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "count": count,
            "offset": offset,
            "has_photo": 1,
            "fields": "domain,bdate,city,sex",
        }
        target_sex = self.get_opposite_sex(sex)
        if target_sex:
            params["sex"] = target_sex
        if city_id:
            params["city"] = city_id
        if age:
            params["age_from"] = max(age - 5, 18)
            params["age_to"] = age + 5
        else:
            params["age_from"] = 18
        params["status"] = 6
        response = self.user_vk.users.search(**params)
        return response.get("items", [])

    def get_top_photo_attachments(self, owner_id: int) -> list[str]:
        try:
            response = self.user_vk.photos.get(
                owner_id=owner_id,
                album_id="profile",
                extended=1,
                photo_sizes=0,
                count=100,
            )
        except ApiError as error:
            if error.code in (15, 30):
                return []
            raise
        photos = response.get("items", [])
        valid_photos = []
        for photo in photos:
            if not photo.get("id") or not photo.get("owner_id"):
                continue
            sizes = photo.get("sizes")
            if not sizes:
                continue
            likes = photo.get("likes", {}).get("count", 0)
            valid_photos.append({
                "owner_id": photo["owner_id"],
                "id": photo["id"],
                "likes": likes
            })
        valid_photos.sort(key=lambda x: x["likes"], reverse=True)
        return [
            f"photo{p['owner_id']}_{p['id']}"
            for p in valid_photos[:3]
        ]

    @staticmethod
    def get_opposite_sex(sex: int | None) -> int | None:
        if sex == 1:
            return 2
        if sex == 2:
            return 1
        return None

    @staticmethod
    def candidate_from_vk(profile: dict[str, Any]) -> dict[str, Any]:
        city = profile.get("city") or {}
        vk_id = profile["id"]
        domain = profile.get("domain")

        return {
            "vk_id": vk_id,
            "first_name": profile.get("first_name", ""),
            "last_name": profile.get("last_name", ""),
            "sex": profile.get("sex"),
            "city_id": city.get("id"),
            "city_title": city.get("title"),
            "bdate": profile.get("bdate"),
            "age": calculate_age(profile.get("bdate")),
            "domain": domain,
            "profile_url": make_profile_url(vk_id, domain),
            "photos_json": json.dumps([], ensure_ascii=False),
        }
