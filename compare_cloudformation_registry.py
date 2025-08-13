"""Compares Services and Features available between 
source and target region based on CFN APIs"""

import json
import re
import sys
import concurrent.futures
import boto3


def get_resource_types(region):
    """Get all resource type names for a region using CloudFormation API"""
    try:
        cfn_client = boto3.client("cloudformation", region_name=region)
        paginator = cfn_client.get_paginator("list_types")
        resource_types = set()

        # Get all AWS resource types from CloudFormation registry
        for page in paginator.paginate(
            Type="RESOURCE", Visibility="PUBLIC", Filters={"Category": "AWS_TYPES"}
        ):
            for type_summary in page["TypeSummaries"]:
                resource_types.add(type_summary["TypeName"])

        print(f"Found {len(resource_types)} resource types in {region}")
        return resource_types

    except Exception as e:
        print(f"Error accessing region {region}: {e}")
        return set()


def get_property_types(region, resource_types):
    """Get property types for specific resource types by examining their schemas"""
    try:
        cfn_client = boto3.client("cloudformation", region_name=region)
        property_types = []
        total = len(resource_types)

        for i, resource_type in enumerate(resource_types, 1):
            try:
                # Get the JSON schema for this resource type
                response = cfn_client.describe_type(
                    Type="RESOURCE", TypeName=resource_type
                )
                schema = response.get("Schema")
                if schema:
                    schema_data = json.loads(schema)
                    definitions = schema_data.get("definitions", {})

                    # Extract property type names from schema definitions
                    for def_name in definitions.keys():
                        property_types.append(f"{resource_type}.{def_name}")
            except Exception:
                # Skip resources that can't be described
                pass

            # Show progress every 10 resources or at the end
            if i % 10 == 0 or i == total:
                print(f"  {region}: {i}/{total} resource types processed")

        print(f"Found {len(property_types)} property types in {region}")
        return property_types

    except Exception as e:
        print(f"Error processing {region}: {e}")
        return []


def compare_property_types(source_region, target_region, service=None):
    """Compare property types between regions to identify feature differences"""

    # Get resource type lists from both regions in parallel for efficiency
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        source_future = executor.submit(get_resource_types, source_region)
        target_future = executor.submit(get_resource_types, target_region)

        source_resource_types = source_future.result()
        target_resource_types = target_future.result()

    if not source_resource_types or not target_resource_types:
        return

    # Apply service filter if specified
    if service:
        source_resource_types = {
            rt
            for rt in source_resource_types
            if re.search(r"AWS::" + service + "::", rt, re.IGNORECASE)
        }
        target_resource_types = {
            rt
            for rt in target_resource_types
            if re.search(r"AWS::" + service + "::", rt, re.IGNORECASE)
        }

    # Calculate resource types only available in source region
    source_only_types = source_resource_types - target_resource_types

    # Compare property types for resources available in both regions
    common_resource_types = source_resource_types & target_resource_types
    print(f"Analyzing {len(common_resource_types)} common resource types...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        source_future = executor.submit(
            get_property_types, source_region, list(common_resource_types)
        )
        target_future = executor.submit(
            get_property_types, target_region, list(common_resource_types)
        )

        source_property_types = set(source_future.result())
        target_property_types = set(target_future.result())

    # Calculate property types (features) missing in target region
    difference = source_property_types - target_property_types

    # Display results
    service_msg = f" for AWS::{service.upper()}::*" if service else ""

    print(
        f"\nResource types in {source_region} but not in {target_region}{service_msg}:"
    )
    if source_only_types:
        for resource_type in sorted(source_only_types):
            print(f"- {resource_type}")
    else:
        print("(none)")

    print(
        f"\nService Features in {source_region} but not in {target_region}{service_msg}:"
    )
    if difference:
        for item in sorted(difference):
            print(f"- {item}")
    else:
        print("(none)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python compare_service_features.py <source_region> <target_region> [service]"
        )
        sys.exit(1)

    SOURCE_REGION = sys.argv[1]
    TARGET_REGION = sys.argv[2]
    SERVICE = sys.argv[3] if len(sys.argv) == 4 else None

    compare_property_types(SOURCE_REGION, TARGET_REGION, SERVICE)
