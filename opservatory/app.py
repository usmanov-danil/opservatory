from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import Fleet, Machine
from opservatory.state.repository import StateRepository


def request_statuses(comm: InfrastructureCommunicator) -> Fleet:
    machines = comm.update_machines_info()
    return Fleet(machines=machines)


def save_fleet(fleet: Fleet, repo: StateRepository):
    repo.save_fleet(fleet)


def get_fleet_state(repo: StateRepository) -> Fleet:
    return repo.read_fleet()


def free_machines(repo: StateRepository) -> list[Machine]:
    machines = repo.read_fleet().machines
    return list(filter(lambda machine: len(machine.containers) <= 0, machines))
