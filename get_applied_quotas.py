"""
Export applied service quotas that differ from defaults to CSV.

This script analyzes all AWS service quotas in a region and exports
those that have been modified from their default values to a CSV file.
"""
import sys
import csv
import argparse
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from utils.aws_clients import aws_client_factory


def get_services(client):
    """Retrieve all service codes."""
    services = []
    paginator = client.get_paginator('list_services')
    for page in paginator.paginate():
        for service_info in page['Services']:
            services.append(service_info['ServiceCode'])
    return services


def get_service_quotas(client, service_code):
    """Retrieve quotas for a given service."""
    quotas = []
    try:
        paginator = client.get_paginator('list_service_quotas')
        for page in paginator.paginate(ServiceCode=service_code):
            quotas.extend(page['Quotas'])
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting quotas for service {service_code}: {error}")
    return quotas


def get_default_quota(client, service_code, quota_code):
    """Retrieve the default quota for a given service and quota."""
    try:
        response = client.get_aws_default_service_quota(ServiceCode=service_code, QuotaCode=quota_code)
        return response['Quota']['Value']
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting default quota for {service_code}, {quota_code}: {error}")
        return None


def check_quotas(region, output_file="service_quotas.csv", verbose=False):
    """
    Check quotas for a region, output to CSV where applied quota differs from default.
    
    Args:
        region: AWS region to analyze
        output_file: Output CSV filename
        verbose: Enable verbose output
    """
    service_quotas_client = aws_client_factory.get_quota_client(region)

    services = get_services(service_quotas_client)
    
    if verbose:
        print(f"Found {len(services)} services to analyze in {region}")
    
    print("Analyzing service quotas...")

    differences_found = 0
    
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["Service", "Quota Name", "Applied Quota", "Default Quota"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for service_code in services:
            print(service_code)
            quotas = get_service_quotas(service_quotas_client, service_code)
            for quota in quotas:
                default_quota = get_default_quota(service_quotas_client, service_code, quota['QuotaCode'])
                if default_quota is not None and quota["Value"] != default_quota:
                    writer.writerow({
                        "Service": service_code,
                        "Quota Name": quota["QuotaName"],
                        "Applied Quota": quota["Value"],
                        "Default Quota": default_quota
                    })
                # Removed manual sleep - boto3 handles retries automatically


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_applied_quotas.py <region>")
        sys.exit(1)

    REGION = sys.argv[1]
    print("Checking Applied vs Default quotas. This process may take a while due to the number of API calls required.")
    check_quotas(REGION)
    print("\nDone! Where Applied quota differs from Default it is listed in the created service_quotas.csv file")
