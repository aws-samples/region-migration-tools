"""

"""
import sys
from botocore.exceptions import BotoCoreError, ClientError
import boto3

def get_service_quotas(client, service_code):
    try:
        response = client.list_service_quotas(ServiceCode=service_code)
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting quotas for service {service_code}: {error}")
        return None

    # Filter quotas that start with 'Running'
    quotas = [
        quota
        for quota in response["Quotas"]
        if quota["QuotaName"].startswith("Running")
    ]

    return quotas


def compare_service_quotas(region1, region2):
    session1 = boto3.Session(region_name=region1)
    session2 = boto3.Session(region_name=region2)

    service_quotas1 = session1.client("service-quotas")
    service_quotas2 = session2.client("service-quotas")

    # Use the service code for EC2
    service = "ec2"

    quotas1 = get_service_quotas(service_quotas1, service)
    quotas2 = get_service_quotas(service_quotas2, service)

    if quotas1 is None or quotas2 is None:
        return

    for quota1, quota2 in zip(quotas1, quotas2):
        if quota1["Value"] != quota2["Value"]:
            print(
                f"Different quota for {service} ({quota1['QuotaName']}) in {region1} ({quota1['Value']}) and {region2} ({quota2['Value']})"
            )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_running_ec2_quotas.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_service_quotas(REGION1, REGION2)
