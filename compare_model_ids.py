"""
This script compares the model IDs available in two specified regions using the Bedrock APIs.
It prints the model IDs that are present in the first region but not in the second.
"""
import sys
import boto3

def get_model_ids(region):
    # Initialize the Bedrock client
    bedrock = boto3.client('bedrock', region_name=region)
    
    # Call the list_foundation_models API to get model summaries
    response = bedrock.list_foundation_models()
    
    # Extract model IDs from the response
    model_ids = {model['modelId'] for model in response['modelSummaries']}
    
    return model_ids

def compare_model_ids(region1, region2):
    model_ids_region1 = get_model_ids(region1)
    model_ids_region2 = get_model_ids(region2)

    not_in_region2 = model_ids_region1 - model_ids_region2

    print(f"Model IDs available in {region1} not available in {region2}:")
    for model_id in not_in_region2:
        print(f"Model ID: {model_id}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python compare_model_ids.py <region1> <region2>")
        sys.exit(1)

    REGION1 = sys.argv[1]
    REGION2 = sys.argv[2]

    compare_model_ids(REGION1, REGION2) 