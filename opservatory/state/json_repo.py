from pathlib import Path

from pydantic.error_wrappers import ValidationError

from opservatory.models import Fleet
from opservatory.state.repository import StateRepository


class JsonStateRepository(StateRepository):
    def __init__(self, path: Path):
        self.path = path
        super().__init__()

    def _create_dump_file(self):
        self.path.open(mode="w")

    def save_fleet(self, fleet: Fleet):
        file = self.path.open(mode="w")
        file.write(fleet.json())
        file.close()

    def read_fleet(self) -> Fleet:
        if not self.path.exists():
            self._create_dump_file()

        file = self.path.open(mode="r")
        state = file.read()
        file.close()

        try:
            return Fleet.parse_raw(state)
        except ValidationError:
            return Fleet(machines=[])
