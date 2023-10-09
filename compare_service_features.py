"""Compares Services and Features available between 
source and target region based on CFN Resource Spec"""
import json
import re
import sys

import requests

def get_region_spec(region, local_cfn_resource_specs):
    """get CFN Resource Spec for a given region"""
    url = local_cfn_resource_specs.get(region)
    if not url:
        print(f"Region {region} not found in cfnResourceSpecs.json.")
        return None
    response = requests.get(url, timeout=10)
    return response.json() if response.status_code == 200 else None


def compare_property_types(
    source_region, target_region, local_cfn_resource_specs, service=None
):
    """compare property types which equate to service/feature"""
    source_spec = get_region_spec(source_region, local_cfn_resource_specs)
    target_spec = get_region_spec(target_region, local_cfn_resource_specs)

    if not source_spec or not target_spec:
        return

    source_property_types = set(source_spec.get("PropertyTypes", {}).keys())
    target_property_types = set(target_spec.get("PropertyTypes", {}).keys())

    difference = source_property_types - target_property_types

    if service:
        service = service.lower()
        difference = {
            item
            for item in difference
            if re.search(r"AWS::" + service + "::", item, re.IGNORECASE)
        }

    if difference:
        print(f"Service Features in {source_region} but not in {target_region}:")
        for item in sorted(difference):
            print(f"- {item}")
    else:
        print(
            f"No differences in Service Features between {source_region} and {target_region}."
        )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python compare_service_features.py <source_region> <target_region> [service]"
        )
        sys.exit(1)

    with open("cfnResourceSpecs.json", "r", encoding='utf-8') as f:
        cfn_resource_specs = json.load(f)

    SOURCE_REGION = sys.argv[1]
    TARGET_REGION = sys.argv[2]
    SERVICE = sys.argv[3] if len(sys.argv) == 4 else None

    compare_property_types(SOURCE_REGION, TARGET_REGION, cfn_resource_specs, SERVICE)
