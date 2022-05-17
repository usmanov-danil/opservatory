from datetime import timedelta
from ipaddress import IPv4Address
import os
from pathlib import Path
from starlette.datastructures import Headers
from fastapi import FastAPI, Request, Response
from pydantic import SecretStr
import yaml
from opservatory.app import cancel_reservation, get_fleet_state, reserve_machine
from opservatory.auth.adapters.sqlite_repo import SQLiteAuthRepository
from opservatory.auth.exceptions import IncorrectPassword, UserAlreadyExists, UserDoesNotExist
from opservatory.auth.jwt import create_access_token, decode_payload, user_from_token, verify_token
from opservatory.auth.models import Credentials, User
from opservatory.models import Config, Fleet, Reservation, ReservationRequest
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from opservatory.scheduler import sched

from opservatory.state.adapters.json_repo import JsonStateRepository
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Opservatory Client")


PROJECT_PATH = Path(os.path.dirname(__file__))
STATE_DUMP_PATH = PROJECT_PATH / "mounts" / "state.json"
USER_DB_PATH = PROJECT_PATH / "mounts" / "users.db"
print("Creating volumes folder...", STATE_DUMP_PATH.parent)
STATE_DUMP_PATH.parent.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = PROJECT_PATH / "mounts" / "config.yml"
config_file = yaml.load(open(CONFIG_PATH, "r"), Loader=yaml.FullLoader)
CONFIG = Config.parse_obj(config_file)


sched.start()


from fastapi import APIRouter, FastAPI

app = FastAPI()


api = APIRouter(prefix="/api")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = CONFIG.auth.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(seconds=3600 * 24 * 30)


def check_token(headers: Headers) -> bool:
    return verify_token(
        headers.get("Authorization", " ").split(" ")[1], SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
    )


@api.get("/fleet", response_model=Fleet)
async def state() -> Fleet:
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    return get_fleet_state(repo)


@api.get("/me")
async def read_me(request: Request) -> User:
    repo = SQLiteAuthRepository(filepath=USER_DB_PATH, pwd_context=pwd_context)
    username = user_from_token(request.headers.get("Authorization", " ").split(" ")[1], SECRET_KEY, ALGORITHM)
    return repo.user_info(username)


@api.get("/user/{username}")
async def get_user(username: str) -> User:
    repo = SQLiteAuthRepository(filepath=USER_DB_PATH, pwd_context=pwd_context)
    return repo.user_info(username)


@api.post("/login", response_model=dict[str, str])
async def login(credentials: Credentials, request: Request):
    repo = SQLiteAuthRepository(filepath=USER_DB_PATH, pwd_context=pwd_context)
    has_valid_token = check_token(request.headers)
    if has_valid_token:
        return Response(status_code=200, content="You are already logged in")

    try:
        user = repo.login(credentials)
        to_encode = {"user": user.dict(exclude={"credentials": {"password"}, "contacts": True})}
        print(f"{to_encode=}")
        token = create_access_token(
            data=to_encode, secret_key=SECRET_KEY, algorithm=ALGORITHM, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return {"token": token}
    except IncorrectPassword:
        return Response(status_code=401)
    except UserDoesNotExist:
        return Response(status_code=404)


@api.post("/register")
async def register(user: User):
    repo = SQLiteAuthRepository(filepath=USER_DB_PATH, pwd_context=pwd_context)
    try:
        repo.register(user)
        return Response(status_code=200)
    except UserAlreadyExists:
        return Response(status_code=409)


@api.post("/reservation")
async def reserve(reservation_req: ReservationRequest, request: Request):
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    users = SQLiteAuthRepository(filepath=USER_DB_PATH, pwd_context=pwd_context)
    username = user_from_token(request.headers.get("Authorization", " ").split(" ")[1], SECRET_KEY, ALGORITHM)
    user = users.user_info(username)

    reservation = Reservation.from_request(reservation_req, user)
    success = reserve_machine(repo, reservation_req.machine_ip, reservation)
    if not success:
        return Response(status_code=409)

    return Response(status_code=200)


@api.delete("/reservation")
async def delete_reservation(machine_ip: IPv4Address, request: Request):
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    username = user_from_token(request.headers.get("Authorization", " ").split(" ")[1], SECRET_KEY, ALGORITHM)

    success = cancel_reservation(repo, machine_ip, username)

    if not success:
        return Response(status_code=409)

    return Response(status_code=200)


app.include_router(api)

app.mount("/", StaticFiles(directory=PROJECT_PATH / "client" / "public", html=True), name="app")
app.mount("/build", StaticFiles(directory=PROJECT_PATH / "client" / "public" / "build"), name="build")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
