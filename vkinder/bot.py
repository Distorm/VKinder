from sqlalchemy.orm import Session
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

from vkinder.database import SessionLocal
from vkinder.keyboards import main_keyboard
from vkinder.models import Candidate, VkUser
from vkinder.repositories import (
    ActionRepository,
    CandidateRepository,
    UserRepository,
)
from vkinder.vk_service import VKService


class VKinderBot:
    def __init__(self, vk: VKService, group_id: int) -> None:
        self.vk = vk
        self.group_id = group_id
        self.keyboard = main_keyboard()

    def run(self) -> None:
        longpoll = VkBotLongPoll(self.vk.group_session, self.group_id)
        print("VKinder запущен. Ожидаю сообщения...")

        for event in longpoll.listen():
            if event.type != VkBotEventType.MESSAGE_NEW:
                continue

            message = event.object.message
            if message.get("from_id", 0) < 0:
                continue

            peer_id = message["peer_id"]
            user_vk_id = message["from_id"]
            text = message.get("text", "").strip()

            try:
                self.handle_message(peer_id, user_vk_id, text)
            except Exception as error:  # noqa: BLE001
                print(f"Ошибка обработки сообщения: {error}")
                self.vk.send_message(
                    peer_id,
                    "Произошла ошибка. Попробуй ещё раз или напиши 'Помощь'.",
                    keyboard=self.keyboard,
                )

    def handle_message(self, peer_id: int, user_vk_id: int, text: str) -> None:
        command = text.lower()

        with SessionLocal() as db:
            user = UserRepository.get_or_create_from_vk(db, self.vk, user_vk_id)

            if command in {"начать", "старт", "start", "help", "помощь"}:
                self.send_help(peer_id, user)
                return

            if command.startswith("город "):
                city_name = text.split(" ", maxsplit=1)[1].strip()
                self.set_city(db, peer_id, user, city_name)
                return

            if command in {"следующий", "next", "далее"}:
                self.show_next_candidate(db, peer_id, user)
                return

            if command in {"в избранное", "избранное+", "лайк"}:
                self.add_current_to_favorites(db, peer_id, user)
                return

            if command in {"избранное", "мои избранные", "список избранных"}:
                self.show_favorites(db, peer_id, user)
                return

            if command in {"в чёрный список", "в черный список", "чс", "blacklist"}:
                self.add_current_to_blacklist(db, peer_id, user)
                return

            self.vk.send_message(
                peer_id,
                "Команда не распознана. Напиши 'Помощь'.",
                keyboard=self.keyboard,
            )

    def send_help(self, peer_id: int, user: VkUser) -> None:
        city = user.city_title or "не указан"
        age = user.age if user.age is not None else "не указан"

        message = (
            "Привет! Я VKinder.\n\n"
            f"Твои данные для поиска:\n"
            f"Город: {city}\n"
            f"Возраст: {age}\n\n"
            "Команды:\n"
            "Следующий — показать новую анкету.\n"
            "В избранное — сохранить текущую анкету.\n"
            "Избранное — показать сохранённые анкеты.\n"
            "В чёрный список — больше не показывать текущую анкету.\n"
            "Город Красноярск — вручную указать город для поиска."
        )
        self.vk.send_message(peer_id, message, keyboard=self.keyboard)

    def set_city(
        self,
        db: Session,
        peer_id: int,
        user: VkUser,
        city_name: str,
    ) -> None:
        city_id, city_title = self.vk.get_city_id(city_name)
        if city_id is None or city_title is None:
            self.vk.send_message(
                peer_id,
                f"Город '{city_name}' не найден. Попробуй другое название.",
                keyboard=self.keyboard,
            )
            return

        UserRepository.set_city(db, user, city_id, city_title)
        self.vk.send_message(
            peer_id,
            f"Город поиска установлен: {city_title}. Теперь нажми 'Следующий'.",
            keyboard=self.keyboard,
        )

    def show_next_candidate(
        self,
        db: Session,
        peer_id: int,
        user: VkUser,
    ) -> None:
        if not user.city_id:
            self.vk.send_message(
                peer_id,
                "У тебя не указан город. Напиши, например: Город Красноярск",
                keyboard=self.keyboard,
            )
            return

        candidate = self.get_next_candidate(db, user)
        if candidate is None:
            self.vk.send_message(
                peer_id,
                "Новых анкет пока нет. Попробуй изменить город или повторить позже.",
                keyboard=self.keyboard,
            )
            return

        attachments = CandidateRepository.get_photos(candidate)
        if not attachments:
            attachments = self.vk.get_top_photo_attachments(candidate.vk_id)
            CandidateRepository.set_photos(db, candidate, attachments)

        ActionRepository.mark_shown(db, user, candidate)
        text = self.format_candidate(candidate)
        attachment = ",".join(attachments) if attachments else None
        self.vk.send_message(
            peer_id,
            text,
            attachment=attachment,
            keyboard=self.keyboard,
        )

    def get_next_candidate(self, db: Session, user: VkUser) -> Candidate | None:
        candidate = CandidateRepository.find_not_shown(db, user)
        if candidate:
            return candidate
        for _ in range(5):
            if user.search_offset >= 1000:
                user.search_offset = 0
                db.commit()
                break

            profiles = self.vk.search_people(
                sex=user.sex,
                city_id=user.city_id,
                age=user.age,
                offset=user.search_offset,
                count=50,
            )
            user.search_offset += 50
            db.commit()

            for profile in profiles:
                data = self.vk.candidate_from_vk(profile)
                CandidateRepository.get_or_create(db, data)

            candidate = CandidateRepository.find_not_shown(db, user)
            if candidate:
                return candidate

        return None

    @staticmethod
    def format_candidate(candidate: Candidate) -> str:
        bdate = candidate.bdate or "не указана"
        city = candidate.city_title or "не указан"
        return (
            f"👤 {candidate.first_name} {candidate.last_name}\n"
            f"🎂 Дата рождения: {bdate}\n"
            f"📍 Город: {city}\n"
            f"🔗 Профиль: {candidate.profile_url}"
        )

    def add_current_to_favorites(
        self,
        db: Session,
        peer_id: int,
        user: VkUser,
    ) -> None:
        candidate = user.current_candidate
        if candidate is None:
            self.vk.send_message(
                peer_id,
                "Сначала нажми 'Следующий', чтобы выбрать анкету.",
                keyboard=self.keyboard,
            )
            return

        created = ActionRepository.add_favorite(db, user, candidate)
        if created:
            message = "Анкета добавлена в избранное."
        else:
            message = "Эта анкета уже есть в избранном."

        self.vk.send_message(peer_id, message, keyboard=self.keyboard)

    def add_current_to_blacklist(
        self,
        db: Session,
        peer_id: int,
        user: VkUser,
    ) -> None:
        candidate = user.current_candidate
        if candidate is None:
            self.vk.send_message(
                peer_id,
                "Сначала нажми 'Следующий', чтобы выбрать анкету.",
                keyboard=self.keyboard,
            )
            return

        created = ActionRepository.add_blacklist(db, user, candidate)
        if created:
            message = "Анкета добавлена в чёрный список. Больше её не покажу."
        else:
            message = "Эта анкета уже есть в чёрном списке."

        self.vk.send_message(peer_id, message, keyboard=self.keyboard)

    def show_favorites(self, db: Session, peer_id: int, user: VkUser) -> None:
        candidates = ActionRepository.get_favorites(db, user)
        if not candidates:
            self.vk.send_message(
                peer_id,
                "Список избранных пока пуст.",
                keyboard=self.keyboard,
            )
            return

        lines = ["Избранные анкеты:"]
        for index, candidate in enumerate(candidates, start=1):
            lines.append(
                f"{index}. {candidate.first_name} {candidate.last_name} — "
                f"{candidate.profile_url}",
            )

        self.vk.send_message(peer_id, "\n".join(lines), keyboard=self.keyboard)
