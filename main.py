from vkinder.bot import VKinderBot
from vkinder.config import get_settings
from vkinder.database import init_db
from vkinder.vk_service import VKService


def main() -> None:
    settings = get_settings()
    init_db()

    vk = VKService(settings)
    bot = VKinderBot(vk=vk, group_id=settings.group_id)
    bot.run()


if __name__ == "__main__":
    main()
