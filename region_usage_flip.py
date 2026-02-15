import boto3
import json
from botocore.config import Config

def get_aws_hourly_cost(service_code, usage_type):
    # Create a pricing client with retry configuration
    retry_config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'adaptive'
        }
    )
    client = boto3.client('pricing', region_name='us-east-1', config=retry_config)

    # Construct the query
    response = client.get_products(
        ServiceCode=service_code,
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'usageType', 'Value': usage_type}
        ],
        FormatVersion='aws_v1'
    )

    # Initialize a dictionary to hold price information
    hourly_prices = {}

    # Parse the response
    for product in response['PriceList']:
        product_data = json.loads(product)
        terms = product_data.get('terms', {})

        # Check for OnDemand key in terms
        if 'OnDemand' in terms:
            for offerTermCode, offerTerm in terms['OnDemand'].items():
                priceDimensions = offerTerm['priceDimensions']
                for priceDimension in priceDimensions.values():
                    # Extract hourly pricing
                    if priceDimension['unit'] == 'Hrs':
                        price_per_hour = priceDimension['pricePerUnit']['USD']
                        description = priceDimension['description']
                        hourly_prices[description] = price_per_hour

    return hourly_prices

# Example usage
service_code = 'AmazonEC2'
usage_type = 'APS2-BoxUsage:t3.xlarge'
hourly_cost = get_aws_hourly_cost(service_code, usage_type)
print(hourly_cost)
