from abc import ABC, abstractmethod

from opservatory.models import Fleet, Machine


class InfrastructureCommunicator(ABC):
    @abstractmethod
    def gather_facts(self, fleet: Fleet) -> Fleet:
        raise NotImplementedError

    @abstractmethod
    def update_machines_info(self, fleet: Fleet) -> Fleet:
        raise NotImplementedError
