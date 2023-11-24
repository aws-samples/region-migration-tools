import sys
import csv
import boto3
import time
from botocore.exceptions import BotoCoreError, ClientError


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


def check_quotas(region):
    """Check quotas for a region, output to CSV where applied quota differs from default."""
    session = boto3.Session(region_name=region)
    service_quotas_client = session.client("service-quotas")

    services = get_services(service_quotas_client)
    print("Comparing: ")

    with open("service_quotas.csv", "w", newline="") as csvfile:
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
                time.sleep(0.2)  # Delay to account for API throttling (5 requests per second)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_applied_quotas.py <region>")
        sys.exit(1)

    REGION = sys.argv[1]
    print("Checking Applied verses Default quotas. Note this process takes a while due to API throttle rates")
    check_quotas(REGION)
    print("\nDone! Where Applied quota differs from Default it is listed in the created service_quotas.csv file")
