import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from opservatory.app import get_fleet_state, free_machines
from opservatory.models import Config, Fleet
from opservatory.scheduler import sched

from opservatory.state.json_repo import JsonStateRepository

app = FastAPI()

PROJECT_PATH = Path(os.path.dirname(__file__))
STATE_DUMP_PATH = PROJECT_PATH / Path('state.json')
TEMPLATES_PATH = PROJECT_PATH / "templates"
CONFIG_PATH = PROJECT_PATH / Path('config.json')

CONFIG = Config.parse_raw(CONFIG_PATH.open().read())
TEMPLATES = Jinja2Templates(directory=str(TEMPLATES_PATH))

sched.start()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    machines = get_fleet_state(repo).machines
    total_free = len(free_machines(repo))

    context = {
        "request": request,
        "machines": list(machines),
        "company_name": CONFIG.company_name,
        "total_free": total_free
    }

    return TEMPLATES.TemplateResponse("index.html", context)


@app.get("/state", response_model=Fleet)
async def state() -> Fleet:
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    return get_fleet_state(repo)
