from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from ipaddress import IPv4Address
import json
import os
from pathlib import Path
import re
from typing import Any, Optional, cast
from pydantic import SecretStr

from pytimeparse.timeparse import timeparse
import ansible_runner
from ansible_runner import Runner
from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.infrastructure.models import InventoryMachine
from opservatory.models import OS, DockerContainer, Fleet, Machine, Memory, Processor


MachineInfo = dict[str, Any]
CURRENT_PATH = Path(os.path.dirname(__file__))


class AnsibleInfrastructureCommunicator(InfrastructureCommunicator):
    def __init__(self) -> None:
        self.runner = ansible_runner
        self._inventory_path = CURRENT_PATH / "inventory/hosts"
        super().__init__()

    def _find_uptime_mention(self, container_info: str) -> str:
        uptime_mentions = re.findall(r"Up\s\d\s\w+", container_info)
        if not uptime_mentions:
            return "0 seconds"
        return uptime_mentions[-1].replace("Up ", "")

    def _parse_uptime_seconds(self, container_info: str) -> int:
        uptime = self._find_uptime_mention(container_info)
        seconds = timeparse(uptime, granularity="seconds")
        if not seconds:
            return 0
        return int(seconds)

    def _parse_container(self, container_info: str) -> DockerContainer:
        info = container_info.split()
        tag = info[1]
        name = info[-1]
        uptime_value = self._parse_uptime_seconds(container_info)
        return DockerContainer(tag=tag, name=name, uptime=int(uptime_value))

    def _parse_processor(self, machine_info: dict[str, Any]) -> Processor:
        return Processor(
            architecture=machine_info["ansible_architecture"],
            name=machine_info["ansible_processor"][2],
            cores=machine_info["ansible_processor_cores"],
        )

    def _parse_os(self, machine_info: MachineInfo) -> OS:
        return OS(
            distribution=machine_info["ansible_distribution"],
            version=machine_info["ansible_distribution_version"]
        )

    def _parse_ram(self, machine_info: MachineInfo) -> Memory:
        return Memory(
            free=machine_info["ansible_memory_mb"]["real"]["free"],
            total=machine_info["ansible_memory_mb"]["real"]["total"],
        )

    def _parse_machine(self, machine_info: MachineInfo, containers: list[DockerContainer]) -> Machine:
        processor = self._parse_processor(machine_info)
        os = self._parse_os(machine_info)
        ram = self._parse_ram(machine_info)
        return Machine(
            system=machine_info["ansible_system"],
            ip=machine_info["ansible_default_ipv4"]["address"],
            ram=ram,
            processor=processor,
            containers=containers,
            os=os,
            updated_at=datetime.now()
        )

    def _gathered_facts(self, runner: Runner) -> list[dict[str, Any]]:
        return [
            result["event_data"]
            for result in runner.events
            if result.get("event_data", {}).get("task_action") == "gather_facts"
            and result.get("event") == "runner_on_ok"
        ]

    def _docker_tasks(self, runner: Runner, host: str) -> list[dict[str, Any]]:
        return [
            result["event_data"]
            for result in runner.events
            if "msg" in result.get("stdout", {}) and result.get("event_data", {}).get("host") == host
        ]

    def _find_docker_containers(self) -> Runner:
        if not (CURRENT_PATH / "inventory/hosts").exists():
            raise RuntimeError('hosts file is not in opservatory/inventory/hosts')
        runner = self.runner.run(
            private_data_dir=str(CURRENT_PATH / "ansible/tmp"),
            playbook=str(CURRENT_PATH / "ansible/docker_list_playbook.yml"),
            inventory=str(self._inventory_path)
        )
        return cast(Runner, runner)

    def _parse_containers(self, host_name: str, runner: Runner) -> list[DockerContainer]:
        containers_registred = []
        for host in self._docker_tasks(runner, host_name):
            docker_engine = host["res"]["msg"].split("\n")[1:]
            for containers in docker_engine:
                containers_registred.append(self._parse_container(containers))
        return containers_registred

    def _parse_inventory_machine(self, name: str, inventory_machine: dict[str, Any]) -> InventoryMachine:
        return InventoryMachine(
            name=name,
            ip=inventory_machine['ansible_host'],
            username=SecretStr(inventory_machine['ansible_user']),
            password=SecretStr(inventory_machine['ansible_password'])
        )

    @property
    def _inventory_machines(self) -> list[InventoryMachine]:
        inventory_json = self.runner.get_inventory('list', [str(self._inventory_path)])[0]
        inventory = json.loads(inventory_json)['_meta']['hostvars']
        return [self._parse_inventory_machine(name, machine) for name, machine in inventory.items()]

    def list_docker_containers(self, host: str) -> list[DockerContainer]:
        runner = self.runner.run(
            private_data_dir=str(CURRENT_PATH / "ansible/tmp"),
            playbook=str(CURRENT_PATH / "ansible/docker_list_playbook.yml"),
            inventory=str(self._inventory_path),
            limit=host
        )
        runner = cast(Runner, runner)
        return self._parse_containers(host, runner)

    def gather_facts(self, fleet: Fleet) -> Fleet:
        runner = self.runner.run(
            private_data_dir=str(CURRENT_PATH / "ansible/tmp"),
            playbook=str(CURRENT_PATH / "ansible/gather_facts.yml"),
            inventory=str(self._inventory_path)
        )
        runner = cast(Runner, runner)
        machines = []
        for facts in self._gathered_facts(runner):
            machine = self._parse_machine(facts["res"]["ansible_facts"], [])
            machines.append(machine)
            fleet.ip2machine[machine.ip].update_facts(machine)

        return fleet

    def _find_machine_by_ip(self, ip: IPv4Address, fleet: Fleet) -> Optional[Machine]:
        return fleet.ip2machine.get(ip, None)

    def update_machines_info(self, fleet: Fleet) -> Fleet:
        for host in self._inventory_machines:
            machine = self._find_machine_by_ip(host.ip, fleet)
            if not machine:
                continue

            containers = self.list_docker_containers(host.name)
            machine.containers = containers
            machine.updated_at = datetime.now()

        return fleet
