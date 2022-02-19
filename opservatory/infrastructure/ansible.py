import os
from pathlib import Path
import re
from typing import Any, cast

from pytimeparse.timeparse import timeparse
import ansible_runner
from ansible_runner import Runner
from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import OS, DockerContainer, Machine, Memory, Processor


class AnsibleInfrastructureCommunicator(InfrastructureCommunicator):
    def _parse_container(self, container_info: str) -> DockerContainer:
        info = container_info.split()
        tag = info[1]
        name = info[-1]
        uptime = re.findall(r"Up\s\d\s\w+", container_info)
        if uptime:
            uptime = uptime[0].replace("Up ", "")
        else:
            uptime = "0 seconds"
        uptime_value = timeparse(uptime, granularity="seconds")
        if uptime_value is None:
            uptime_value = -1
        return DockerContainer(tag=tag, name=name, uptime=int(uptime_value))

    def _parse_machine(self, machine_info: dict[str, Any], containers: list[DockerContainer]) -> Machine:
        processor = Processor(
            architecture=machine_info["ansible_architecture"],
            name=machine_info["ansible_processor"][2],
            cores=machine_info["ansible_processor_cores"],
        )
        os = OS(distribution=machine_info["ansible_distribution"], version=machine_info["ansible_distribution_version"])
        ram = Memory(
            free=machine_info["ansible_memory_mb"]["real"]["free"],
            total=machine_info["ansible_memory_mb"]["real"]["total"],
        )
        return Machine(
            system=machine_info["ansible_system"],
            ip=machine_info["ansible_default_ipv4"]["address"],
            ram=ram,
            processor=processor,
            containers=containers,
            os=os,
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

    def update_machines_info(self) -> list[Machine]:
        path = Path(os.path.dirname(__file__))
        runner = ansible_runner.run(
            private_data_dir=str(path / "ansible/tmp"),
            playbook=str(path / "ansible/test.yml"),
            inventory=str(path / "inventory/hosts"),
        )
        print((path / "inventory/hosts").open().read)
        runner = cast(Runner, runner)

        machines = []
        for facts in self._gathered_facts(runner):
            host_name = facts["host"]
            print(host_name)
            containers_registred = []

            for host in self._docker_tasks(runner, host_name):
                host = host["res"]["msg"].split("\n")[1:]
                for containers in host:
                    containers_registred.append(self._parse_container(containers))

            machine = self._parse_machine(facts["res"]["ansible_facts"], containers_registred)
            machines.append(machine)

        return machines
