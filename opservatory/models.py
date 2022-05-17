from __future__ import annotations
from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Optional
from pydantic import BaseModel, SecretStr

from opservatory.auth.models import User


class Entity(BaseModel):
    def update(self, other: Entity):
        self.__dict__.update(self.__class__(**other.__dict__))
        return self

    def patch(self, data: dict[str, Any]):
        self.__dict__.update(self.__class__(**(self.__dict__ | data)))
        return self


class OS(Entity):
    distribution: str
    version: str


class Memory(Entity):
    free: int
    total: int


class Processor(Entity):
    architecture: str  # ansible_architecture
    name: str  # ansible_processor[2]
    cores: int  # ansible_processor_cores


class DockerContainer(Entity):
    tag: str
    name: str
    uptime: int


class Reservation(Entity):
    user: User
    reason: str

    @staticmethod
    def from_request(request: ReservationRequest, user: User) -> Reservation:
        return Reservation(**request.dict(exclude={"machine_ip"}), user=user)


class ReservationRequest(Entity):
    reason: str
    machine_ip: IPv4Address


class Machine(Entity):
    ip: IPv4Address
    system: str
    hostname: str
    ram: Memory  # ansible_memory_mb.real.total
    os: OS
    processor: Processor
    containers: list[DockerContainer]
    reservation: Optional[Reservation] = None
    updated_at: datetime = datetime.now()

    def update_facts(self, updater: Machine):
        self.ip = updater.ip
        self.system = updater.system
        self.ram = updater.ram
        self.processor = updater.processor
        self.updated_at = datetime.now()


class Fleet(Entity):
    machines: list[Machine]

    @property
    def ip2machine(self) -> dict[IPv4Address, Machine]:
        return {machine.ip: machine for machine in self.machines}


class AuthConfig(Entity):
    secret_key: SecretStr


class Config(Entity):
    company_name: str
    auth: AuthConfig


class FrontendContext(Entity):
    machines: list[Machine]
    company_name: str
