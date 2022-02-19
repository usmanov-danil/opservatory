import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from opservatory.app import get_fleet_state
from opservatory.models import Fleet
from opservatory.scheduler import sched

from opservatory.state.json_repo import JsonStateRepository

app = FastAPI()
templates_path = Path(os.path.dirname(__file__)) / "templates"
templates = Jinja2Templates(directory=str(templates_path))

sched.start()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    repo = JsonStateRepository(path=Path("state.json"))
    fleet = get_fleet_state(repo)
    machines = fleet.machines
    return templates.TemplateResponse("index.html", {"request": request, "machines": list(machines)})


@app.get("/state", response_model=Fleet)
async def state() -> Fleet:
    repo = JsonStateRepository(path=Path("state.json"))
    return get_fleet_state(repo)
