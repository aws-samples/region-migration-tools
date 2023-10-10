# Region Migration Tools

As AWS opens up new Regions, you may look to migrate workloads from existing Regions for reasons such as improving latency or meeting new compliance requirements. Embarking on such a migration would require you to go through the migration journey of assessing the source environment, mobilizing resources to lay the foundation for the migration and finally, migrating the workloads. 

This Repository contains sample scripts to help you undertake analysis in AWS Region to Region Migrations, or when launching into a new Region.


## Installation
These scripts are primarily written in Python utilising Boto3. You'll need to install it first, if you haven't already, using pip: `pip install boto3`.

## Usage
See each individual script description below

## check_instance_types.py
This script gets the EC2 instance families from two regions and compares them. It then prints the instance families that are in the first region, along with the Instance ID to help identify, but not in the second.

Please note that this script assumes that you have set up AWS credentials in your environment or in the `~/.aws/credentials` file. If not, you need to configure it by running `aws configure` in your terminal and following the prompts.

Also, note that this script uses the `describe_instance_types` API call which may have limitations on how many times you can call it within a certain period of time. If you are working with a large number of instances, you may need to handle rate limiting; pagination is catered for.

## check_rds_types.py
This script fetches the RDS instance classes and engine version in use in a specified region, checks if they are available in a second region, and prints out the classes versions and instance IDs that are not available in the second region.

This script handles pagination and assumes you have set up AWS credentials. It does not handle rate limits, so be aware of that if you are working with a large number of instances.

Raised and resolved PFR: https://github.com/boto/boto3/issues/3752

## compare_ec2_pricing.py
This script fetches the EC2 instances in use in a specified region, checks if they are available in a second region, and looks up the pricing of each instance type (on-demand linux) to provide a total price impact of moving all available instances to the target region.

So, the AWSPricing API returns a very large and complex JSON structure that you need to navigate to find the specific price you are looking for.
Alternatively, the download of the entire EC2 pricing file as a JSON from a URL provided by AWS is very large (around 70MB), and parsing it is non-trivial due to its structure.

Given these complexities, we've used third-party service https://instances.vantage.sh/ which you will need to create an account with a get a free API Token to use this script.

This script handles pagination and assumes you have set up AWS credentials. It does not handle rate limits, so be aware of that if you are working with a large number of instances.

## aws_calc_region_swap.py
This Python script takes as input an AWS calculator JSON file and a list of AWS region codes. For each region code in the list, it updates all "region" values in the JSON file to match the region code. The modified JSON data is then posted to a specified AWS URL, and the script prints out an updated AWS calculator URL for each region.

### Usage
```python aws_calc_region_swap.py <estimate_id> <region_1> <region_2> ... <region_n>```
<estimate_id> is the ID of the source estimate.
<region_1>, <region_2>, ..., <region_n> is a space-separated list of AWS region codes.

## compare_quotas.py
This Python script takes as input two AWS Regions and compares the Service Quotas in each, printing out any differences

### Usage
```python compare_quotas.py  <region_1> <region_2>```
<region_1>, <region_2> Source and Target Region to compare

## compare_running_ec2_quotas.py
This Python script takes as input two AWS Regions and compares the Service Quotas related to Running EC2 Instances/Hosts in each, printing out any differences

### Usage
```python compare_running_ec2_quotas.py  <region_1> <region_2>```
<region_1>, <region_2> Source and Target Region to compare

## lambda_region_finder.sh  Graviton2 Function Finder
Identify Lambda functions with Graviton2 compatible and not-compatible runtimes versions.  Looks in all regions where Graviton2 Lambda is currently available.
Lambda runtimes support for Graviton2 docs: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html

## compare_service_features.py
Compares Services and Features available between source and target region based on CFN Resource Spec

# Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

# License

This library is licensed under the MIT-0 License. See the LICENSE file.
