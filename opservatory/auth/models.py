from enum import Enum
from typing import Optional
from pydantic import BaseModel, SecretStr


class Privilege(int, Enum):
    ADMIN = 77
    VIEWER = 0


class Credentials(BaseModel):
    username: str
    password: SecretStr


class ContactInfo(BaseModel):
    slack_alias: Optional[str] = None
    telegram_alias: Optional[str] = None
    email: Optional[str] = None


class User(BaseModel):
    name: str
    credentials: Credentials
    contacts: ContactInfo = ContactInfo()
    privilege: Privilege = Privilege.VIEWER

    @property
    def is_admin(self):
        return self.privilege == Privilege.ADMIN
