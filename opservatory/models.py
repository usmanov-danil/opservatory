from datetime import datetime
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


class Machine(BaseModel):
    ip: IPv4Address
    system: str
    ram: Memory  # ansible_memory_mb.real.total
    os: OS
    processor: Processor
    containers: list[DockerContainer]
    updated_at: datetime = datetime.now()


class Fleet(BaseModel):
    machines: list[Machine]


class Config(BaseModel):
    company_name: str


class FrontendContext(BaseModel):
    machines: list[Machine]
    company_name: str
