from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import Fleet
from opservatory.state.repository import StateRepository


def request_statuses(comm: InfrastructureCommunicator) -> Fleet:
    machines = comm.update_machines_info()
    return Fleet(machines=machines)


def save_fleet(fleet: Fleet, repo: StateRepository):
    repo.save_fleet(fleet)


def get_fleet_state(repo: StateRepository) -> Fleet:
    return repo.read_fleet()
