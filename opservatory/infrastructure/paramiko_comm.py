from opservatory.infrastructure.communicator import InfrastructureCommunicator
from opservatory.models import Fleet


class ParamikoCommunicator(InfrastructureCommunicator):
    def __init__(self) -> None:
        super().__init__()

    def gather_facts(self, fleet: Fleet) -> Fleet:
        return super().gather_facts(fleet)

    def update_machines_info(self, fleet: Fleet) -> Fleet:
        return super().update_machines_info(fleet)
