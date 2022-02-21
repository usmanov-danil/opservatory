from opservatory.app import update_fleet_facts
from opservatory.infrastructure.ansible import AnsibleInfrastructureCommunicator


comm = AnsibleInfrastructureCommunicator()

for machine in update_fleet_facts(comm).machines:
    print(machine)
