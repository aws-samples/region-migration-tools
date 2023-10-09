"""
This script gets the EC2 instance families from two regions and compares them. 
It then prints the instance families that are in the first region, 
along with the Instance ID to help identify, but not in the second.
"""
import sys
import boto3

def get_in_use_instance_families_and_ids(region):
    ec2 = boto3.client('ec2', region_name=region)
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

def compare_instance_families(region1, region2):
    families_and_ids_region1 = get_in_use_instance_families_and_ids(region1)
    families_region2 = get_ec2_families(region2)

    not_in_region2 = {k: v for k, v in families_and_ids_region1.items() if k not in families_region2}

    print(f"EC2 Instance Families in use in {region1} not available in {region2}:")
    for family, ids in not_in_region2.items():
        print(f"Family: {family}, Instance IDs: {ids}")

def get_ec2_families(region):
    ec2 = boto3.client('ec2', region_name=region)
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
