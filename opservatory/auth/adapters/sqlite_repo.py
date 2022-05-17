from pathlib import Path
import sqlite3

from pydantic import SecretStr

from passlib.context import CryptContext
from opservatory.auth.auth_repo import AuthRepository
from opservatory.auth.exceptions import IncorrectPassword, UserAlreadyExists, UserDoesNotExist
from opservatory.auth.models import ContactInfo, Credentials, Privilege, User


class SQLiteAuthRepository(AuthRepository):
    def __init__(self, filepath: Path, pwd_context: CryptContext) -> None:
        self.conn = sqlite3.connect(filepath)
        self.pwd_context = pwd_context
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                name TEXT[100],
                username TEXT[100] PRIMARY KEY,
                password TEXT[100],
                telegram_alias TEXT[100],
                slack_alias TEXT[100],
                email TEXT[100],
                privilege INTEGER
            );
        """
        )

    def user_info(self, username: str) -> User:
        """Reads user info from the database."""
        cursor = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            raise UserDoesNotExist()

        contacts = ContactInfo(telegram_alias=row[3], slack_alias=row[4], email=row[5])
        credentials = Credentials(username=row[1], password=SecretStr(row[2]))
        return User(name=row[0], credentials=credentials, contacts=contacts, privilege=row[6])

    def register(self, user: User) -> None:
        user.credentials.password = self._get_password_hash(user.credentials.password)
        try:
            self.user_info(user.credentials.username)
            raise UserAlreadyExists()
        except UserDoesNotExist:
            cursor = self.conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user.name,
                    user.credentials.username,
                    user.credentials.password.get_secret_value(),
                    user.contacts.telegram_alias,
                    user.contacts.slack_alias,
                    user.contacts.email,
                    user.privilege,
                ),
            )

            self.conn.commit()
            cursor.close()

    def login(self, credentials: Credentials) -> User:
        user = self.user_info(credentials.username)
        if user is None:
            raise UserDoesNotExist()

        if self._verify_password(credentials.password, user.credentials.password):
            return user

        raise IncorrectPassword()

    def change_privilege(self, username: str, privilege: Privilege) -> None:
        cursor = self.conn.execute("UPDATE users SET privilege = ? WHERE username = ?", (privilege, username))
        self.conn.commit()
        cursor.close()
