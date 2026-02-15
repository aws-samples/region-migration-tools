"""Compares Bedrock Models available between 
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

def compare_bedrock_models(source_region, target_region, local_cfn_resource_specs):
    """Compare Bedrock Models available in source and target regions"""
    source_models = get_region_spec(source_region, local_cfn_resource_specs)
    target_models = get_region_spec(target_region, local_cfn_resource_specs)

    if not source_models or not target_models:
        return

    source_model_names = set(source_models.get("Models", []))
    target_model_names = set(target_models.get("Models", []))

    difference = source_model_names - target_model_names

    if difference:
        print(f"Bedrock Models in {source_region} but not in {target_region}:")
        for model in sorted(difference):
            print(f"- {model}")
    else:
        print(
            f"No differences in Bedrock Models between {source_region} and {target_region}."
        )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python compare_bedrock_models.py <source_region> <target_region>"
        )
        sys.exit(1)

    with open("cfnResourceSpecs.json", "r", encoding='utf-8') as f:
        cfn_resource_specs = json.load(f)

    SOURCE_REGION = sys.argv[1]
    TARGET_REGION = sys.argv[2]

    compare_bedrock_models(SOURCE_REGION, TARGET_REGION, cfn_resource_specs) 