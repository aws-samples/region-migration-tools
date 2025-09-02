"""
Compare EC2 instance families between two regions.

This script identifies EC2 instance families currently running in the source
region that are not available in the target region, helping identify potential
compatibility issues during migration.
"""
import sys
import boto3
from utils.aws_clients import aws_client_factory

def get_in_use_instance_families_and_ids(region):
    ec2 = aws_client_factory.get_ec2_client(region)
    paginator = ec2.get_paginator('describe_instances')

    instance_families_and_ids = {}

    for page in paginator.paginate(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    ):
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                family = instance['InstanceType'].split('.')[0]
                if family in instance_families_and_ids:
                    instance_families_and_ids[family].append(instance['InstanceId'])
                else:
                    instance_families_and_ids[family] = [instance['InstanceId']]

    return instance_families_and_ids

def compare_instance_families(region1, region2, verbose=False):
    """
    Compare EC2 instance families between two regions
    
    Args:
        region1: Source region with running instances
        region2: Target region to check availability
        verbose: Enable verbose output
    """
    if verbose:
        print(f"Checking EC2 instance families in {region1} vs {region2}")
        print("Fetching running instances from source region...")
    
    families_and_ids_region1 = get_in_use_instance_families_and_ids(region1)
    
    if verbose:
        print(f"Found {len(families_and_ids_region1)} instance families in {region1}")
        print("Fetching available instance types from target region...")
    
    families_region2 = get_ec2_families(region2)
    
    if verbose:
        print(f"Found {len(families_region2)} instance families available in {region2}")

    not_in_region2 = {k: v for k, v in families_and_ids_region1.items() if k not in families_region2}

    if not not_in_region2:
        print(f"✓ All EC2 instance families from {region1} are available in {region2}")
        return
    
    print(f"EC2 Instance Families in use in {region1} not available in {region2}:")
    for family, ids in not_in_region2.items():
        print(f"  Family: {family}, Instance IDs: {ids}")

def get_ec2_families(region):
    ec2 = aws_client_factory.get_ec2_client(region)
    paginator = ec2.get_paginator('describe_instance_types')

    instance_families = set()

    for page in paginator.paginate():
        for instance_type in page['InstanceTypes']:
            instance_families.add(instance_type['InstanceType'].split('.')[0])

    return instance_families

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python check_instance_types.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_instance_families(REGION1, REGION2)
