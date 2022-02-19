from infrastructure.ansible import AnsibleInfrastructureCommunicator


comm = AnsibleInfrastructureCommunicator()
print(comm.update_machines_info())
