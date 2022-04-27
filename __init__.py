from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from datetime import datetime
import logging
import azure.functions as func
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.basicConfig(format='%(asctime)s <> %(message)s', level=logging.INFO)
    logging.info('Python HTTP trigger function processed a request.')

    subscription_id = os.environ['SUBSCRIPTION_ID']
    tenant_id = os.environ['TENANT_ID']
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']

    credential = ClientSecretCredential(
        tenant_id = tenant_id,
        client_id= client_id,
        client_secret= client_secret
    )
    vm_client = ComputeManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)

    resource_group_name_list = ["Hawkeye-east-us", "Hawkeye-east-us2", "hawkeye-west-us2"]

    for resource_group_name in resource_group_name_list:
        virtual_machine_list = vm_client.virtual_machines.list(resource_group_name = resource_group_name)
        for NUMBERS, vm_instance_details in enumerate(virtual_machine_list):
            vm_instance_details = vm_instance_details.as_dict()
            instance_name = vm_instance_details['name']
            instance_tags = vm_instance_details['tags'] if 'tags' in vm_instance_details.keys() else None

            if not instance_tags == None:
                termination_time = instance_tags['TerminationTime'] if 'TerminationTime' in instance_tags.keys() else None
                
                if not termination_time == None:
                    termination_time = termination_time.split(".")[0]
                    instance_datetime = datetime.fromisoformat(termination_time)
                    today_date = datetime.utcnow()
                    if today_date > instance_datetime:
                        logging.info(f"{instance_name} passed TerminationTime date.")
                        logging.info(f"Terminating {instance_name}")
                        vm_termination = vm_client.virtual_machines.begin_delete(resource_group_name, instance_name)
                        vm_termination.wait()
                        logging.info(vm_termination)
                        logging.info(f"{instance_name} VM Terminated.")
                        network_interface_name = vm_instance_details['network_profile']['network_interfaces'][0]['id'].split("/")[-1]
                        network_interface_delete = network_client.network_interfaces.begin_delete(resource_group_name, network_interface_name)
                        network_interface_delete.wait()
                        logging.info(network_interface_delete)
                        logging.info(f"{network_interface_name} Networrk Interface Deleted.")
                    else:
                        logging.info(f"{instance_name} does not passed TerminationTime date.")
                else:
                    logging.info(f"{instance_name} does not have TerminationTime tags...")
            else:
                logging.info(f"{instance_name} does not have TerminationTime tags...")
    
    return func.HttpResponse("Code run successfully", status_code=200)