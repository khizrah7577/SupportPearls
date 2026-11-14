"""Real authentication with bcrypt-hashed passwords."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import bcrypt

from src.auth.db import get_connection, init_db


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class User:
    id: int
    email: str
    full_name: str
    theme: str = "pearl"
    preferred_model: str = "gpt-4o-mini"
    created_at: str = ""
    last_login_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> User:
        data = dict(row)
        return cls(
            id=int(data["id"]),
            email=str(data["email"]),
            full_name=str(data["full_name"]),
            theme=str(data.get("theme") or "pearl"),
            preferred_model=str(data.get("preferred_model") or "gpt-4o-mini"),
            created_at=str(data.get("created_at") or ""),
            last_login_at=data.get("last_login_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "theme": self.theme,
            "preferred_model": self.preferred_model,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at,
        }


class AuthService:
    def __init__(self) -> None:
        init_db()

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except ValueError:
            return False

    @staticmethod
    def validate_email(email: str) -> str | None:
        email = email.strip().lower()
        if not EMAIL_RE.match(email):
            return "Enter a valid email address."
        return None

    @staticmethod
    def validate_password(password: str) -> str | None:
        if len(password) < 8:
            return "Password must be at least 8 characters."
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            return "Password must include letters and numbers."
        return None

    def register(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        recovery_hint: str,
        recovery_answer: str,
    ) -> tuple[User | None, str | None]:
        email_err = self.validate_email(email)
        if email_err:
            return None, email_err
        name = full_name.strip()
        if len(name) < 2:
            return None, "Please enter your full name."
        pwd_err = self.validate_password(password)
        if pwd_err:
            return None, pwd_err
        if len(recovery_answer.strip()) < 3:
            return None, "Recovery answer must be at least 3 characters."

        email_norm = email.strip().lower()
        conn = get_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?", (email_norm,)
            ).fetchone()
            if existing:
                return None, "An account with this email already exists."
            conn.execute(
                """
                INSERT INTO users (
                    email, full_name, password_hash, recovery_hint, recovery_hash
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    email_norm,
                    name,
                    self._hash_password(password),
                    recovery_hint.strip()[:120],
                    self._hash_password(recovery_answer.strip().lower()),
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email_norm,)
            ).fetchone()
            return User.from_row(row), None
        finally:
            conn.close()

    def login(self, email: str, password: str) -> tuple[User | None, str | None]:
        email_norm = email.strip().lower()
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email_norm,)
            ).fetchone()
            if not row or not self._verify_password(password, row["password_hash"]):
                return None, "Incorrect email or password."
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "UPDATE users SET last_login_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            conn.commit()
            user = User.from_row(row)
            user.last_login_at = now
            return user, None
        finally:
            conn.close()

    def get_user(self, user_id: int) -> User | None:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return User.from_row(row) if row else None
        finally:
            conn.close()

    def reset_password(
        self,
        *,
        email: str,
        recovery_answer: str,
        new_password: str,
    ) -> str | None:
        pwd_err = self.validate_password(new_password)
        if pwd_err:
            return pwd_err
        email_norm = email.strip().lower()
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email_norm,)
            ).fetchone()
            if not row:
                return "No account found for that email."
            if not self._verify_password(
                recovery_answer.strip().lower(), row["recovery_hash"]
            ):
                return "Recovery answer is incorrect."
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (self._hash_password(new_password), row["id"]),
            )
            conn.commit()
            return None
        finally:
            conn.close()

    def get_recovery_hint(self, email: str) -> str | None:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT recovery_hint FROM users WHERE email = ?",
                (email.strip().lower(),),
            ).fetchone()
            return str(row["recovery_hint"]) if row else None
        finally:
            conn.close()

    def update_profile(
        self,
        user_id: int,
        *,
        full_name: str | None = None,
        theme: str | None = None,
        preferred_model: str | None = None,
    ) -> User | None:
        conn = get_connection()
        try:
            user = self.get_user(user_id)
            if not user:
                return None
            name = full_name.strip() if full_name is not None else user.full_name
            theme_val = theme or user.theme
            model = preferred_model or user.preferred_model
            conn.execute(
                """
                UPDATE users
                SET full_name = ?, theme = ?, preferred_model = ?
                WHERE id = ?
                """,
                (name, theme_val, model, user_id),
            )
            conn.commit()
            return self.get_user(user_id)
        finally:
            conn.close()

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> str | None:
        pwd_err = self.validate_password(new_password)
        if pwd_err:
            return pwd_err
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not row or not self._verify_password(current_password, row["password_hash"]):
                return "Current password is incorrect."
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (self._hash_password(new_password), user_id),
            )
            conn.commit()
            return None
        finally:
            conn.close()
