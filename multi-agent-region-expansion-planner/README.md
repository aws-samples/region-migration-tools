# Multi-Region Expansion Planner

A sophisticated multi-agent system built with the Strands SDK that accelerates AWS infrastructure expansion across multiple regions using the AWS Knowledge Graph MCP (Model Context Protocol).

## Overview

This project demonstrates how to leverage AI agents and the AWS Knowledge Graph to intelligently plan and execute multi-region infrastructure deployments. The system analyzes existing AWS resources, identifies regional service availability gaps, and generates comprehensive expansion strategies.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for different aspects of expansion planning
- **AWS Knowledge Graph Integration**: Leverages MCP for comprehensive service availability analysis
- **CloudFormation Analysis**: Discovers and analyzes existing infrastructure patterns
- **CloudTrail Intelligence**: Extracts usage patterns from operational data
- **Regional Gap Analysis**: Identifies service availability differences across regions
- **Cost Optimization**: Provides pricing analysis for multi-region deployments
- **Automated Reporting**: Generates detailed expansion planning reports

## Architecture

The system consists of several specialized agents:

- **CFN Explorer**: Analyzes CloudFormation stacks and resources
- **CloudTrail Explorer**: Extracts service usage patterns from CloudTrail logs
- **Waypoint Explorer**: Identifies regional service availability gaps
- **Multi-Region Expansion Planner**: Orchestrates comprehensive expansion planning
- **Analysis Writer**: Consolidates findings into structured reports
- **Pricing Explorer**: Analyzes cost implications of multi-region deployment
- **Report Generator**: Creates final expansion planning documentation

## Prerequisites

- Python >= 3.10
- AWS CLI installed
- IAM user with the required permissions
- Strands SDK (Installed automatically through requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd multi-region-expansion-planner
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## AWS Profile Configuration 

Create an IAM User with the below permissions 

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudFormationAnalysis",
            "Effect": "Allow",
            "Action": [
                "cloudformation:ListStacks",
                "cloudformation:DescribeStacks",
                "cloudformation:ListStackResources",
                "cloudformation:DescribeStackResources"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudTrailAnalysis", 
            "Effect": "Allow",
            "Action": [
                "cloudtrail:LookupEvents"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BedrockAccess",
            "Effect": "Allow", 
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0"
            ]
        }
    ]
}
```

### Setup Steps
1. AWS Console → IAM → Users → Create User
2. Attach policies → Create policy → JSON tab
3. Paste the policy above → Review → Create policy
4. Attach the policy to your user
5. Security credentials → Create access key → Command Line Interface (CLI)
6. Download or copy/paste credentials for AWS CLI configuration

```bash
aws configure --profile region-planner-user
```

When prompted, enter:
- **AWS Access Key ID**: Your IAM user's access key
- **AWS Secret Access Key**: Your IAM user's secret key
- **Default region name**: us-east-1 (or your preferred source region)
- **Default output format**: json

To test profile configuration

```bash
# Verify credentials work
aws sts get-caller-identity --profile region-planner-user
```

## Code Configuration

1. Configure the Bedrock Model provider account AWS profile for authentication in `src/utils/config.py`:

```python
class Constants:
    # Replace with your actual account ID to use Bedrock Models
    INFRA_ACCOUNT = "123456789012"
    # AWS CLI profile for auth
    BEDROCK_AWS_CLI_PROFILE = "bedrock-profile" 
```

2. Configure AWS account access for Resource Discovery and Regions Expansion Planning. Add AWS profile to access the account and the target regions for planning.

```python
class ExpansionPlaningInputs:
    PROFILE_NAME = 'your-aws-profile'
    SOURCE_REGION = 'us-east-1'
    TARGET_REGIONS = ['eu-central-1', 'ap-southeast-1', 'ca-central-1']
```



## Usage

### Clean Up Previous Analysis 
Before running a new analysis, you can clean up previous results:

```bash
./cleanup.sh
```

### Basic Usage

Run the complete expansion planning workflow:

```bash
python src/main.py
```

This will:
1. Analyze CloudFormation resources in your source region
2. Extract service usage patterns from CloudTrail
3. Identify service availability gaps in target regions
4. Generate comprehensive expansion planning reports

### Individual Agent Usage

You can also run individual agents for specific analysis:

```bash
# Run CFN analysis only
python src/agents/cfn_explorer.py

# Run regional gap analysis
python src/agents/waypoint_explorer.py

# Generate expansion plan
python src/agents/multi_region_expansion_planner.py
```

## Output

The system generates several output files in the `src/analysis_results/` directory:

- `cfn_explorer_result.json`: CloudFormation resource analysis
- `cloudtrail_explorer_result.json`: Service usage patterns
- `waypoint_explorer_<region>_result.json`: Regional availability analysis
- `expansion_planning_report.md`: Final expansion planning report
- `multi_region_expansion_planning_report.md`: Detailed technical analysis

## AWS Knowledge Graph MCP Integration

This project showcases the power of the AWS Knowledge Graph MCP server for:

- **Service Availability Queries**: Real-time information about AWS service availability across regions
- **Feature Compatibility Analysis**: Understanding regional feature differences
- **Compliance and Regulatory Mapping**: Regional compliance requirements
- **Cost Optimization Insights**: Regional pricing variations and optimization opportunities

## Project Structure

```
├── src/
│   ├── agents/                 # Specialized AI agents
│   │   ├── cfn_explorer.py
│   │   ├── cloudtrail_explorer.py
│   │   ├── waypoint_explorer.py
│   │   ├── multi_region_expansion_planner.py
│   │   └── ...
│   ├── analysis_results/       # Generated analysis outputs
│   ├── utils/                  # Configuration and utilities
│   │   ├── config.py
│   │   ├── planner_inputs.py
│   │   └── prompts.py
│   └── main.py                # Main orchestration script
├── tests/                     # Test files
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Key Benefits

- **Accelerated Planning**: Reduces multi-region expansion planning from weeks to hours
- **Comprehensive Analysis**: Considers technical, operational, and cost factors
- **Risk Mitigation**: Identifies potential issues before deployment
- **Best Practices**: Incorporates AWS Well-Architected principles
- **Automation Ready**: Generates actionable deployment plans

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
1. Check the existing issues in the repository
2. Create a new issue with detailed information
3. Include relevant log files and configuration details

## Acknowledgments

- Built with the Strands SDK for multi-agent orchestration
- Powered by AWS Knowledge Graph MCP for comprehensive service intelligence
- Utilizes AWS CloudFormation and CloudTrail for infrastructure analysis