from abc import ABC, abstractmethod

from opservatory.models import Fleet


class StateRepository(ABC):
    @abstractmethod
    def save_fleet(self, fleet: Fleet):
        raise NotImplementedError

    def read_fleet(self) -> Fleet:
        raise NotImplementedError
