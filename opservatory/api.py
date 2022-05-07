import os
from pathlib import Path
from fastapi import FastAPI
from opservatory.app import get_fleet_state
from opservatory.models import Config, Fleet
from fastapi.staticfiles import StaticFiles
from opservatory.scheduler import sched

from opservatory.state.json_repo import JsonStateRepository
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Opservatory Client")


PROJECT_PATH = Path(os.path.dirname(__file__))
STATE_DUMP_PATH = PROJECT_PATH / 'volumes' / 'state.json'
print('Creating volumes folder...', STATE_DUMP_PATH.parent)
STATE_DUMP_PATH.parent.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = PROJECT_PATH / 'config.json'
CONFIG = Config.parse_raw(CONFIG_PATH.open().read())


sched.start()


from fastapi import APIRouter, FastAPI

app = FastAPI()


api = APIRouter(prefix='/api')


@api.get("/fleet", response_model=Fleet)
async def state() -> Fleet:
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    return get_fleet_state(repo)


app.include_router(api)


app.mount("/", StaticFiles(directory=PROJECT_PATH / 'client' / 'public', html=True), name="app")
app.mount("/build", StaticFiles(directory=PROJECT_PATH / 'client' / 'public' / 'build'), name="build")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
