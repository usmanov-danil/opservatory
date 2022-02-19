import logging
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from opservatory.app import request_statuses, save_fleet
from opservatory.infrastructure.ansible import AnsibleInfrastructureCommunicator
from opservatory.state.json_repo import JsonStateRepository

logger = logging.getLogger("main")
sched = BackgroundScheduler()


@sched.scheduled_job(id="my_job_id", trigger=CronTrigger.from_crontab("*/3 * * * *"))
def update_fleet():
    print("Updating fleet state...")
    comm = AnsibleInfrastructureCommunicator()
    repo = JsonStateRepository(path=Path("state.json"))
    fleet = request_statuses(comm)
    save_fleet(fleet, repo)
    print("Machines updated: %d", len(fleet.machines))


update_fleet()
