from pathlib import Path
from pydantic.error_wrappers import ValidationError
from opservatory.models import Fleet
from opservatory.state.repository import StateRepository


class JsonStateRepository(StateRepository):
    def __init__(self, path: Path):
        self.path = path
        super().__init__()

    def save_fleet(self, fleet: Fleet):
        file = self.path.open(mode="w")
        file.write(fleet.json())

    def read_fleet(self) -> Fleet:
        if not self.path.exists():
            self.path.open(mode="w")
        file = self.path.open(mode="r")
        try:
            return Fleet.parse_raw(file.read())
        except ValidationError:
            raise ValueError("State is empty")
