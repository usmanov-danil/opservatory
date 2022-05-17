from abc import ABC, abstractmethod

from passlib.context import CryptContext
from pydantic import SecretStr

from opservatory.auth.models import Credentials, Privilege, User


class AuthRepository(ABC):
    def __init__(self, pwd_context: CryptContext) -> None:
        self.pwd_context = pwd_context
        super().__init__()

    def _verify_password(self, plain_password: SecretStr, hashed_password: SecretStr) -> bool:
        return self.pwd_context.verify(plain_password.get_secret_value(), hashed_password.get_secret_value())

    def _get_password_hash(self, password: SecretStr) -> SecretStr:
        return SecretStr(self.pwd_context.hash(password.get_secret_value()))

    @abstractmethod
    def user_info(self, username: str) -> User:
        raise NotImplementedError

    @abstractmethod
    def register(self, user: User):
        raise NotImplementedError

    @abstractmethod
    def login(self, credentials: Credentials) -> bool:
        raise NotImplementedError

    @abstractmethod
    def change_privilege(self, username: str, privilege: Privilege):
        raise NotImplementedError
