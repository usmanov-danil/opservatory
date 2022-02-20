from contextlib import contextmanager
import os
from pathlib import Path
import re
from typing import Any, cast

from pytimeparse.timeparse import timeparse
import ansible_runner
from ansible_runner import Runner
from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import OS, DockerContainer, Machine, Memory, Processor


MachineInfo = dict[str, Any]
CURRENT_PATH = Path(os.path.dirname(__file__))


class AnsibleInfrastructureCommunicator(InfrastructureCommunicator):
    def __init__(self) -> None:
        self.runner = ansible_runner
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
            os=os
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

    def _run_playbook(self) -> Runner:
        if not (CURRENT_PATH / "inventory/hosts").exists():
            raise RuntimeError('hosts file is not in opservatory/inventory/hosts')
        runner = self.runner.run(
            private_data_dir=str(CURRENT_PATH / "ansible/tmp"),
            playbook=str(CURRENT_PATH / "ansible/docker_list_playbook.yml"),
            inventory=str(CURRENT_PATH / "inventory/hosts")
        )
        return cast(Runner, runner)

    def _parse_containers(self, host_name: str, runner: Runner) -> list[DockerContainer]:
        containers_registred = []
        for host in self._docker_tasks(runner, host_name):
            docker_engine = host["res"]["msg"].split("\n")[1:]
            for containers in docker_engine:
                containers_registred.append(self._parse_container(containers))
        return containers_registred

    def update_machines_info(self) -> list[Machine]:
        runner = self._run_playbook()

        machines = []
        for facts in self._gathered_facts(runner):
            host_name = facts["host"]
            containers = self._parse_containers(host_name, runner)
            machine = self._parse_machine(facts["res"]["ansible_facts"], containers)
            machines.append(machine)

        return machines
