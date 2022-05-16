from __future__ import annotations
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address
from pydantic import BaseModel


class OS(BaseModel):
    distribution: str
    version: str


class Memory(BaseModel):
    free: int
    total: int


class Processor(BaseModel):
    architecture: str  # ansible_architecture
    name: str  # ansible_processor[2]
    cores: int  # ansible_processor_cores


class DockerContainer(BaseModel):
    tag: str
    name: str
    uptime: int


class MachineState(str, Enum):
    UNREACHABLE = "unreachable"
    FREE = "free"
    BUSY = "busy"
    RESERVED = "reserved"


class Machine(BaseModel):
    ip: IPv4Address
    hostname: str
    ram: Memory  # ansible_memory_mb.real.total
    os: OS
    processor: Processor
    containers: list[DockerContainer]
    updated_at: datetime = datetime.now()
    state: MachineState = MachineState.UNREACHABLE

    def update_facts(self, updater: Machine):
        self.ip = updater.ip
        self.system = updater.system
        self.ram = updater.ram
        self.processor = updater.processor
        self.updated_at = datetime.now()


class Fleet(BaseModel):
    machines: list[Machine]

    @property
    def ip2machine(self) -> dict[IPv4Address, Machine]:
        return {machine.ip: machine for machine in self.machines}


class Config(BaseModel):
    company_name: str


class FrontendContext(BaseModel):
    machines: list[Machine]
    company_name: str
