import json

from sqlalchemy import and_, exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from vkinder.models import BlackList, Candidate, Favorite, ShownCandidate, VkUser
from vkinder.vk_service import VKService


class UserRepository:
    """Репозиторий пользователей бота."""

    @staticmethod
    def get_by_vk_id(db: Session, vk_id: int) -> VkUser | None:
        return db.scalar(select(VkUser).where(VkUser.vk_id == vk_id))

    @staticmethod
    def get_or_create_from_vk(db: Session, vk: VKService, vk_id: int) -> VkUser:
        profile = vk.get_profile(vk_id)
        user = UserRepository.get_by_vk_id(db, vk_id)

        if user is None:
            user = VkUser(**profile)
            db.add(user)
        else:
            user.first_name = profile.get("first_name", user.first_name)
            user.last_name = profile.get("last_name", user.last_name)
            user.sex = profile.get("sex")
            user.bdate = profile.get("bdate")
            user.age = profile.get("age")

            if not user.city_id:
                user.city_id = profile.get("city_id")
                user.city_title = profile.get("city_title")

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_city(
        db: Session,
        user: VkUser,
        city_id: int,
        city_title: str,
    ) -> None:
        user.city_id = city_id
        user.city_title = city_title
        user.search_offset = 0
        user.current_candidate_id = None

        db.commit()
        db.refresh(user)


class CandidateRepository:

    @staticmethod
    def get_or_create(db: Session, data: dict) -> Candidate:
        candidate = db.scalar(
            select(Candidate).where(Candidate.vk_id == data["vk_id"]),
        )

        if candidate is None:
            candidate = Candidate(**data)
            db.add(candidate)
        else:
            for key, value in data.items():
                setattr(candidate, key, value)

        db.commit()
        db.refresh(candidate)
        return candidate


    @staticmethod
    def find_not_shown(db: Session, owner: VkUser) -> Candidate | None:
        target_sex = VKService.get_opposite_sex(owner.sex)

        conditions = []
        if target_sex:
            conditions.append(Candidate.sex == target_sex)
        if owner.city_id:
            conditions.append(Candidate.city_id == owner.city_id)
        if owner.age:
            conditions.append(Candidate.age >= max(owner.age - 5, 18))
            conditions.append(Candidate.age <= owner.age + 5)

        shown_exists = exists().where(
            and_(
                ShownCandidate.owner_user_id == owner.id,
                ShownCandidate.candidate_id == Candidate.id,
            ),
        )
        favorite_exists = exists().where(
            and_(
                Favorite.owner_user_id == owner.id,
                Favorite.candidate_id == Candidate.id,
            ),
        )
        black_exists = exists().where(
            and_(
                BlackList.owner_user_id == owner.id,
                BlackList.candidate_id == Candidate.id,
            ),
        )

        stmt = (
            select(Candidate)
            .where(*conditions)
            .where(~shown_exists)
            .where(~favorite_exists)
            .where(~black_exists)
            .order_by(Candidate.id)
            .limit(1)
        )
        return db.scalar(stmt)

    @staticmethod
    def set_photos(db: Session, candidate: Candidate, attachments: list[str]) -> None:
        candidate.photos_json = json.dumps(attachments, ensure_ascii=False)
        db.commit()

    @staticmethod
    def get_photos(candidate: Candidate) -> list[str]:
        if not candidate.photos_json:
            return []
        try:
            data = json.loads(candidate.photos_json)
            if isinstance(data, list):
                return [str(item) for item in data]
        except json.JSONDecodeError:
            return []
        return []


class ActionRepository:

    @staticmethod
    def mark_shown(db: Session, owner: VkUser, candidate: Candidate) -> None:
        shown = ShownCandidate(owner_user_id=owner.id, candidate_id=candidate.id)
        owner.current_candidate_id = candidate.id
        db.add(shown)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            owner.current_candidate_id = candidate.id
            db.commit()

    @staticmethod
    def add_favorite(db: Session, owner: VkUser, candidate: Candidate) -> bool:
        favorite = Favorite(owner_user_id=owner.id, candidate_id=candidate.id)
        db.add(favorite)
        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False

    @staticmethod
    def add_blacklist(db: Session, owner: VkUser, candidate: Candidate) -> bool:
        black = BlackList(owner_user_id=owner.id, candidate_id=candidate.id)
        db.add(black)
        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False

    @staticmethod
    def get_favorites(db: Session, owner: VkUser) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .join(Favorite, Favorite.candidate_id == Candidate.id)
            .where(Favorite.owner_user_id == owner.id)
            .order_by(Favorite.created_at.desc())
        )
        return list(db.scalars(stmt).all())
