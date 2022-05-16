from datetime import datetime
import os
from pathlib import Path
from platform import machine
import re
from loguru import logger
import yaml
from typing import Optional
from opservatory.infrastructure.communicator import InfrastructureCommunicator
from pytimeparse.timeparse import timeparse

from opservatory.models import OS, DockerContainer, Fleet, Machine, MachineState, Memory, Processor
from kornet import strategize, execute_strategy
from kornet.fleet.raw.hosts_parser import parse_fleet_file
from kornet.strategy.orders.recon.enum import ReconCatalog

CURRENT_PATH = Path(os.path.dirname(__file__))


class KornetCommunicator(InfrastructureCommunicator):
    def __init__(self) -> None:
        self.inventory = parse_fleet_file(CURRENT_PATH / "inventory" / "fleet.yml", group='office')
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
    
    def _parse_container(self, container_info: str) -> Optional[DockerContainer]:
        info = container_info.split()
        if not info:
            return
        tag = info[1]
        name = info[-1]
        uptime_value = self._parse_uptime_seconds(container_info)
        return DockerContainer(tag=tag, name=name, uptime=int(uptime_value))

    def gather_facts(self, fleet: Fleet) -> Fleet:
        strategy = strategize(
            recon=[
                ReconCatalog.OS,
                ReconCatalog.RAM,
                ReconCatalog.CPU,
                ReconCatalog.HOSTNAME,
            ]  # type: ignore
        )
        
        outcome = execute_strategy(strategy, self.inventory)

        for host, outcome in outcome.items():
            if host.ip not in [_machine.ip for _machine in fleet.machines]:
                logger.info('Adding new machine {}'.format(host.ip))
                fleet.machines.append(
                    Machine(
                        ip=host.ip, 
                        hostname='',
                        os=OS(distribution='', version=''),
                        ram=Memory(free=0, total=0),
                        processor=Processor(architecture='', name='', cores=0),
                        containers=[]
                    )
                )
            if outcome.facts.os or outcome.facts.ram or outcome.facts.cpu:
                fleet.ip2machine[host.ip].state = MachineState.FREE

            if outcome.facts.os:
                fleet.ip2machine[host.ip].os = OS(distribution=outcome.facts.os.name, version=outcome.facts.os.version)
            if outcome.facts.ram:
                fleet.ip2machine[host.ip].ram = Memory(total=outcome.facts.ram.total, free=outcome.facts.ram.available)
            if outcome.facts.cpu:
                fleet.ip2machine[host.ip].processor = Processor(cores=outcome.facts.cpu.cores, architecture=outcome.facts.cpu.arch, name=outcome.facts.cpu.model)
            if outcome.facts.hostname:
                fleet.ip2machine[host.ip].hostname = outcome.facts.hostname

            fleet.ip2machine[host.ip].updated_at = datetime.now()

        return fleet
            

    def update_machines_info(self, fleet: Fleet) -> Fleet:
        order = {
            'name': 'List docker containers',
            'command': 'docker ps -a',
            'silent': False
        }
        strategy = strategize(orders=[order])
        outcome = execute_strategy(strategy, self.inventory)

        for host, outcome in outcome.items():
            if host.ip not in fleet.ip2machine:
                continue
            if len(outcome.orders) <= 0:
                continue
            if outcome.orders[0].failed or not outcome.orders[0].outcome:
                continue

            containers = []
            for container in outcome.orders[0].outcome.outputs[1:]:
                containers.append(self._parse_container(container))
            
            fleet.ip2machine[host.ip].containers = containers

            fleet.ip2machine[host.ip].state = MachineState.FREE
            if len(containers) > 0 and fleet.ip2machine[host.ip].state != MachineState.RESERVED:
                fleet.ip2machine[host.ip].state = MachineState.BUSY
        
            fleet.ip2machine[host.ip].updated_at = datetime.now()

        return fleet
