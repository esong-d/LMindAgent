import enum
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseMID




class User(BaseMID):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "email",
            "name",
            name="idx_unique_user_email"
        ),
        {"comment": "用户表,存储用户信息"},
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False, comment="邮箱")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="姓名")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    salt: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码盐")
    is_banned: Mapped[bool] = mapped_column(default=False, nullable=False, comment="是否被封禁")
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, comment="状态")

