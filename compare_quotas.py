"""
Compare AWS service quotas between two regions.

This script compares service quotas between a source and target region,
identifying differences that might impact migration planning.
"""

import sys
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from utils.aws_clients import aws_client_factory


def get_service_quotas(client, service_code):
    try:
        quotas = []
        paginator = client.get_paginator("list_service_quotas")
        for page in paginator.paginate(ServiceCode=service_code):
            quotas.extend(page["Quotas"])
        return quotas
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting quotas for service {service_code}: {error}")
        return None


def compare_service_quotas(region1, region2):
    # Use optimized quota clients with proper retry configuration
    service_quotas1 = aws_client_factory.get_quota_client(region1)
    service_quotas2 = aws_client_factory.get_quota_client(region2)

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

        quotas1_quota_value = {quota["QuotaName"]: quota["Value"] for quota in quotas1}
        quotas2_quota_value = {quota["QuotaName"]: quota["Value"] for quota in quotas2}

        # Compare quotas in both regions
        for key in set(quotas1_quota_value.keys()) | set(quotas2_quota_value.keys()):
            if key in quotas1_quota_value and key in quotas2_quota_value:
                if quotas1_quota_value[key] != quotas2_quota_value[key]:
                    print(
                        f"Different quota for {service} ({key}) in {region1} ({quotas1_quota_value[key]}) and {region2} ({quotas2_quota_value[key]})"
                    )
            elif key in quotas1_quota_value:
                print(
                    f"Quota {key} for {service} only exists in {region1} ({quotas1_quota_value[key]})"
                )
            else:
                print(
                    f"Quota {key} for {service} only exists in {region2} ({quotas2_quota_value[key]})"
                )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compareQuotas.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_service_quotas(REGION1, REGION2)
