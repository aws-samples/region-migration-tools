"""
compares the Service Quotas between regions, printing out any differences
"""
import sys
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def get_service_quotas(client, service_code):
    try:
        response = client.list_service_quotas(ServiceCode=service_code)
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting quotas for service {service_code}: {error}")
        return None

    return response["Quotas"]


def compare_service_quotas(region1, region2):
    session1 = boto3.Session(region_name=region1)
    session2 = boto3.Session(region_name=region2)

    service_quotas1 = session1.client("service-quotas")
    service_quotas2 = session2.client("service-quotas")

    paginator1 = service_quotas1.get_paginator("list_services")
    paginator2 = service_quotas2.get_paginator("list_services")

    services1 = set()
    for response in paginator1.paginate():
        for service in response["Services"]:
            services1.add(service["ServiceCode"])

    services2 = set()
    for response in paginator2.paginate():
        for service in response["Services"]:
            services2.add(service["ServiceCode"])

    common_services = services1.intersection(services2)

    for service in common_services:
        quotas1 = get_service_quotas(service_quotas1, service)
        quotas2 = get_service_quotas(service_quotas2, service)

        if quotas1 is None or quotas2 is None:
            continue

        for quota1, quota2 in zip(quotas1, quotas2):
            if quota1["Value"] != quota2["Value"]:
                print(
                    f"Different quota for {service} ({quota1['QuotaName']}) in {region1} ({quota1['Value']}) and {region2} ({quota2['Value']})"
                )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compareQuotas.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_service_quotas(REGION1, REGION2)
