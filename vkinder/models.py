"""ORM-модели VKinder."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from vkinder.database import Base


class VkUser(Base):

    __tablename__ = "vk_users"

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    sex = Column(Integer, nullable=True)
    city_id = Column(Integer, nullable=True, index=True)
    city_title = Column(String(150), nullable=True)
    bdate = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    search_offset = Column(Integer, nullable=False, default=0)
    current_candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    current_candidate = relationship("Candidate", foreign_keys=[current_candidate_id])


class Candidate(Base):

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    sex = Column(Integer, nullable=True, index=True)
    city_id = Column(Integer, nullable=True, index=True)
    city_title = Column(String(150), nullable=True)
    bdate = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    domain = Column(String(150), nullable=True)
    profile_url = Column(String(255), nullable=False)
    photos_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class ShownCandidate(Base):

    __tablename__ = "shown_candidates"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "candidate_id",
            name="uq_shown_owner_candidate",
        ),
    )

    id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, ForeignKey("vk_users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    shown_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship("VkUser")
    candidate = relationship("Candidate")


class Favorite(Base):

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "candidate_id",
            name="uq_favorite_owner_candidate",
        ),
    )

    id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, ForeignKey("vk_users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship("VkUser")
    candidate = relationship("Candidate")


class BlackList(Base):

    __tablename__ = "blacklist"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "candidate_id",
            name="uq_blacklist_owner_candidate",
        ),
    )

    id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, ForeignKey("vk_users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship("VkUser")
    candidate = relationship("Candidate")
