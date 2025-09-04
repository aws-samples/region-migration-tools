"""
Update AWS Calculator estimates for multiple regions.

This script takes an AWS Calculator estimate and creates new estimates
for each specified region by updating all region references in the estimate.
"""
import sys
import json
import argparse
import logging
import requests

SOURCE_URL = "https://d3knqfixx3sbls.cloudfront.net/"
SAVE_AS_URL = "https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs"
CALC_URL = "https://calculator.aws/#/estimate?id="

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.ERROR)
requests_log.propagate = True


def modify_region_in_json(data, new_region):
    def update_region(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "region":
                    obj[k] = new_region
                elif isinstance(v, (dict, list)):
                    update_region(v)
        elif isinstance(obj, list):
            for item in obj:
                update_region(item)

    update_region(data)

    return data


def post_data_to_url(data):
    headers = {"Content-Type": "application/json"}
    try:
        request = requests.post(SAVE_AS_URL, headers=headers, json=data, timeout=10)
        request.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        return None

    try:
        response = request.json()
        response_body = json.loads(response["body"])
        return response_body["savedKey"]
    except KeyError:
        print("Key 'savedKey' not found in the response")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("estimate_id", help="The Estimate ID of the source calculator")
    parser.add_argument("aws_regions", nargs="+", help="List of AWS Region codes")
    args = parser.parse_args()
    # Form the URL using the Estimate ID and fetch the JSON data
    url = f"{SOURCE_URL}{args.estimate_id}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        logging.error(
            f"Failed to fetch data for Estimate ID {args.estimate_id}. Status code: {response.status_code}"
        )
        sys.exit(1)

    source_json = response.json()

    for region in args.aws_regions:
        print(f"Processing region {region}")
        data = modify_region_in_json(source_json, region)
        if data is not None:
            #print(data)
            saved_key = post_data_to_url(data)
            if saved_key is not None:
                print(f"Updated Calculator URL for {region}: {CALC_URL}{saved_key}")


if __name__ == "__main__":
    main()
