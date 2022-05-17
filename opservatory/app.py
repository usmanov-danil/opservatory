from datetime import datetime, timedelta
from ipaddress import IPv4Address
from opservatory.auth.models import User
from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import Fleet, Machine, Reservation
from opservatory.state.state_repo import StateRepository


def update_fleet_facts(comm: InfrastructureCommunicator, repo: StateRepository) -> Fleet:
    fleet = repo.read_fleet()
    fleet = comm.gather_facts(fleet)
    repo.save_fleet(fleet)
    return fleet


def update_containers_info(comm: InfrastructureCommunicator, repo: StateRepository) -> Fleet:
    fleet = repo.read_fleet()
    fleet = comm.update_machines_info(fleet)
    repo.save_fleet(fleet)
    return fleet


def save_fleet(fleet: Fleet, repo: StateRepository):
    repo.save_fleet(fleet)


def reserve_machine(repo: StateRepository, machine_ip: IPv4Address, reservation: Reservation) -> bool:
    fleet = repo.read_fleet()

    machine = fleet.ip2machine[machine_ip]
    if machine.reservation is not None:
        return False

    machine.reservation = reservation
    save_fleet(fleet, repo)

    return True


def cancel_reservation(repo: StateRepository, machine_ip: IPv4Address, username: str) -> bool:
    fleet = repo.read_fleet()
    machine = fleet.ip2machine[machine_ip]

    if machine.reservation and machine.reservation.user.credentials.username != username:
        raise Exception("You are not the owner of this machine")

    machine.reservation = None
    save_fleet(fleet, repo)

    return True


def get_fleet_state(repo: StateRepository) -> Fleet:
    return repo.read_fleet()


def free_machines(repo: StateRepository) -> list[Machine]:
    machines = repo.read_fleet().machines
    return list(filter(lambda machine: len(machine.containers) <= 0, machines))
