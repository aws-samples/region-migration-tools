"""
This script fetches the EC2 instances in use in a specified region, 
checks if they are available in a second region, and looks up the pricing of each instance type
(on-demand linux) to provide a total price impact of moving all available instances to the target region.
Requires Vantage API Token
"""
import sys
from collections import defaultdict
import boto3
import requests

TOKEN = "INSERT_TOKEN_HERE"
HEADERS = {"accept": "application/json", "authorization": f"Bearer {TOKEN}"}


def get_in_use_ec2_types_and_ids(region):
    ec2 = boto3.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instances")

    instance_types_and_ids = defaultdict(list)

    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                if instance["State"]["Name"] == "running":
                    instance_types_and_ids[instance["InstanceType"]].append(
                        instance["InstanceId"]
                    )

    return instance_types_and_ids


def get_vantage_product_ids():
    url = "https://api.vantage.sh/v1/products?service_id=aws-ec2"
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 200:
        return {
            product["name"]: product["id"] for product in response.json()["products"]
        }
    else:
        print(f"Failed to fetch product ids: {response.status_code}, {response.text}")
        sys.exit(1)


def get_vantage_product_price(product_id, region):
    url = f"https://api.vantage.sh/v1/products/{product_id}/prices"
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 200:
        for price in response.json()["prices"]:
            if (
                price["region"] == region
                and price["details"]["lifecycle"] == "on-demand"
            ):
                return price["amount"]
    else:
        print(f"Failed to fetch product price: {response.status_code}, {response.text}")
        sys.exit(1)


def compare_ec2_pricing(region1, region2):
    types_and_ids_region1 = get_in_use_ec2_types_and_ids(region1)
    vantage_product_ids = get_vantage_product_ids()

    total_cost_region1 = 0
    total_cost_region2 = 0

    for instance_type, instance_ids in types_and_ids_region1.items():
        product_id = vantage_product_ids.get(instance_type)
        if product_id:
            price_region1 = get_vantage_product_price(product_id, region1)
            price_region2 = get_vantage_product_price(product_id, region2)

            if price_region1 is not None and price_region2 is not None:
                cost_region1 = len(instance_ids) * price_region1
                cost_region2 = len(instance_ids) * price_region2

                total_cost_region1 += cost_region1
                total_cost_region2 += cost_region2

                print(
                    f"Instance Type: {instance_type}, Instance IDs: {instance_ids}, Cost in {region1}: ${cost_region1}, Cost in {region2}: ${cost_region2}"
                )
            else:
                print(f"Price not available for instance type: {instance_type}")

    print(
        f"\nTotal cost per hour in {region1} (based on on-demand pricing for Linux EC2 instances): ${round(total_cost_region1, 4)}"
    )
    print(
        f"Total cost per hour in {region2} (based on on-demand pricing for Linux EC2 instances): ${round(total_cost_region2, 4)}"
    )
    print(
        f"Cost difference per hour: ${round(total_cost_region2 - total_cost_region1, 4)}"
    )
    print(
        f"{region2} is {'more' if total_cost_region2 > total_cost_region1 else 'less'} expensive than {region1} per hour for on-demand Linux EC2 instances (does not consider differences in licensing costs for Microsoft Windows)"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_ec2_pricing.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_ec2_pricing(REGION1, REGION2)
