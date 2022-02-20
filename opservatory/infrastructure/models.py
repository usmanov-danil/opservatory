from ipaddress import IPv4Address
from pydantic import BaseModel, SecretStr


class InventoryMachine(BaseModel):
    name: str
    ip: IPv4Address
    username: SecretStr
    password: SecretStr
