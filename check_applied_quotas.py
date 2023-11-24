import csv
import boto3
import time
from botocore.exceptions import BotoCoreError, ClientError


def read_csv_quotas(csv_file):
    """Read quotas from a CSV file."""
    quotas = {}
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row['Service'], row['Quota Name'])
            quotas[key] = float(row['Applied Quota'])
    return quotas


def get_current_quota(client, service_code, quota_name):
    """Retrieve the current applied quota for a given service and quota name."""
    try:
        response = client.list_service_quotas(ServiceCode=service_code)
        for quota in response['Quotas']:
            if quota['QuotaName'] == quota_name:
                return quota['Value']
    except (BotoCoreError, ClientError) as error:
        print(f"Error getting current quota for {service_code}, {quota_name}: {error}")
        return None


def compare_quotas(region, csv_file):
    """Compare quotas from CSV with current quotas from AWS API."""
    session = boto3.Session(region_name=region)
    service_quotas_client = session.client("service-quotas")

    csv_quotas = read_csv_quotas(csv_file)

    for (service_code, quota_name), csv_quota_value in csv_quotas.items():
        current_quota = get_current_quota(service_quotas_client, service_code, quota_name)
        if current_quota is not None and current_quota != csv_quota_value:
            print(f"Quota mismatch for {service_code}/{quota_name}: CSV - {csv_quota_value}, API - {current_quota}")
        time.sleep(0.2)  # Delay to account for API throttling (5 requests per second)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python check_applied_quotas.py <region> <csv_file>")
        sys.exit(1)

    REGION = sys.argv[1]
    CSV_FILE = sys.argv[2]
    print("Checking Applied verses CSV provided quotas. Note this process takes a while due to API throttle rates")
    compare_quotas(REGION, CSV_FILE)
