from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import Fleet, Machine
from opservatory.state.repository import StateRepository


def update_fleet_facts(comm: InfrastructureCommunicator) -> Fleet:
    return comm.gather_facts()


def update_containers_info(comm: InfrastructureCommunicator, repo: StateRepository) -> Fleet:
    fleet = repo.read_fleet()
    fleet = comm.update_machines_info(fleet)
    repo.save_fleet(fleet)
    return fleet


def save_fleet(fleet: Fleet, repo: StateRepository):
    repo.save_fleet(fleet)


def get_fleet_state(repo: StateRepository) -> Fleet:
    return repo.read_fleet()


def free_machines(repo: StateRepository) -> list[Machine]:
    machines = repo.read_fleet().machines
    return list(filter(lambda machine: len(machine.containers) <= 0, machines))
