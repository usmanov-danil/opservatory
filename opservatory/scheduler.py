import logging
import os
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import shutil

from opservatory.app import update_containers_info, update_fleet_facts
from opservatory.infrastructure.ansible import AnsibleInfrastructureCommunicator
from opservatory.state.json_repo import JsonStateRepository

logger = logging.getLogger("main")
sched = BackgroundScheduler()

TEMP_FILES_PATH = Path(os.path.dirname(__file__)) / 'infrastructure' / 'ansible' / 'tmp'
PROJECT_PATH = Path(os.path.dirname(__file__))
STATE_DUMP_PATH = PROJECT_PATH / Path('state.json')


@sched.scheduled_job(id="facts_update", trigger=CronTrigger.from_crontab("*/10 * * * *"))
def update_fleet():
    print("Updating fleet facts...")
    comm = AnsibleInfrastructureCommunicator()
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    fleet = update_fleet_facts(comm, repo)

    shutil.rmtree(TEMP_FILES_PATH)

    print("Machines updated:", len(fleet.machines))


@sched.scheduled_job(id="containers_update", trigger=CronTrigger.from_crontab("* * * * *"))
def update_docker_images():
    print("Updating fleet business state...")
    comm = AnsibleInfrastructureCommunicator()
    repo = JsonStateRepository(path=STATE_DUMP_PATH)
    fleet = update_containers_info(comm, repo)
    print("Machines updated:", len(fleet.machines))


update_fleet()
update_docker_images()
