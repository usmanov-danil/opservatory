from abc import ABC, abstractmethod

from opservatory.models import Machine


class InfrastructureCommunicator(ABC):
    @abstractmethod
    def update_machines_info(self) -> list[Machine]:
        raise NotImplementedError
