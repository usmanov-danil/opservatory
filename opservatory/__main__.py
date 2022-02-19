from opservatory.app import request_statuses
from opservatory.infrastructure.ansible import AnsibleInfrastructureCommunicator


comm = AnsibleInfrastructureCommunicator()

for machine in request_statuses(comm).machines:
    print(machine)
