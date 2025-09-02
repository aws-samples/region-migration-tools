"""
Compare running EC2 instance quotas between regions.

This script compares EC2 service quotas related to running instances
between two regions, focusing on quotas that match currently running
instance types in both regions.
"""
import sys
from botocore.exceptions import BotoCoreError, ClientError
import boto3
from utils.aws_clients import aws_client_factory

def get_running_instance_types(client):
    try:
        response = client.describe_instances()
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting EC2 instances: {error}")
        return []

    instance_types = set()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                instance_types.add(instance['InstanceType'])
    
    return instance_types

def get_service_quotas(client, service_code, instance_types):
    try:
        response = client.list_service_quotas(ServiceCode=service_code)
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting quotas for service {service_code}: {error}")
        return None

    quotas = [
        quota
        for quota in response["Quotas"]
        if any(instance_type in quota["QuotaName"] for instance_type in instance_types)
    ]

    return quotas

def compare_service_quotas(region1, region2, verbose=False):
    """
    Compare EC2 service quotas related to running instances between regions
    
    Args:
        region1: Source region
        region2: Target region
        verbose: Enable verbose output
    """
    if verbose:
        print(f"Comparing running EC2 instance quotas between {region1} and {region2}")
        print("Fetching running instances from both regions...")
    
    ec2_client1 = aws_client_factory.get_ec2_client(region1)
    ec2_client2 = aws_client_factory.get_ec2_client(region2)
    
    service_quotas1 = aws_client_factory.get_quota_client(region1)
    service_quotas2 = aws_client_factory.get_quota_client(region2)

    instance_types1 = get_running_instance_types(ec2_client1)
    instance_types2 = get_running_instance_types(ec2_client2)
    
    if verbose:
        print(f"Found {len(instance_types1)} instance types running in {region1}")
        print(f"Found {len(instance_types2)} instance types running in {region2}")

    # Use the service code for EC2
    service = "ec2"

    quotas1 = get_service_quotas(service_quotas1, service, instance_types1)
    quotas2 = get_service_quotas(service_quotas2, service, instance_types2)

    if quotas1 is None or quotas2 is None:
        print("Failed to retrieve quotas from one or both regions")
        return

    if verbose:
        print(f"Comparing {len(quotas1)} quotas from {region1} with {len(quotas2)} quotas from {region2}")

    differences_found = 0
    
    # Create a mapping of quota names to values for easier comparison
    quotas1_dict = {quota["QuotaName"]: quota["Value"] for quota in quotas1}
    quotas2_dict = {quota["QuotaName"]: quota["Value"] for quota in quotas2}
    
    # Compare quotas that exist in both regions
    common_quotas = set(quotas1_dict.keys()) & set(quotas2_dict.keys())
    
    for quota_name in common_quotas:
        if quotas1_dict[quota_name] != quotas2_dict[quota_name]:
            print(
                f"Different quota for {service} ({quota_name}) in {region1} ({quotas1_dict[quota_name]}) and {region2} ({quotas2_dict[quota_name]})"
            )
            differences_found += 1
    
    # Report quotas that exist in only one region
    only_in_region1 = set(quotas1_dict.keys()) - set(quotas2_dict.keys())
    only_in_region2 = set(quotas2_dict.keys()) - set(quotas1_dict.keys())
    
    for quota_name in only_in_region1:
        print(f"Quota {quota_name} exists only in {region1} ({quotas1_dict[quota_name]})")
        differences_found += 1
        
    for quota_name in only_in_region2:
        print(f"Quota {quota_name} exists only in {region2} ({quotas2_dict[quota_name]})")
        differences_found += 1
    
    if differences_found == 0:
        print(f"✓ All EC2 running instance quotas match between {region1} and {region2}")
    elif verbose:
        print(f"Found {differences_found} quota differences")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_running_ec2_quotas.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_service_quotas(REGION1, REGION2)

