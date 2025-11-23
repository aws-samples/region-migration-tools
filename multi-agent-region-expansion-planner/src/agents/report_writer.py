import os
import sys
import logging
from typing import Dict, List

# Add parent directory to path for imports to enable relative imports
# This allows the module to import from the parent amzn_waypoint_ai package
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from strands import Agent, tool
    from strands.tools.mcp import MCPClient
    from mcp import stdio_client, StdioServerParameters
    from utils.config import Config, Constants
    from utils.prompts import WaypointPrompts
    from strands_tools import use_aws, file_read, file_write, python_repl, editor, shell

    STRANDS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Strands not available: {e}")
    STRANDS_AVAILABLE = False


    # Define dummy decorator for when strands is not available
    def tool(func):
        return func

# Configure logging with timestamp, logger name, level, and message format
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce botocore (AWS SDK) logging verbosity to avoid noise in logs
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def report_writer(agent_response: str, agent_name: str, output_directory: str = "analysis_results") -> Dict:
    """
    Report Writer Agent - Processes and formats agent responses into structured output files

    This function takes the raw response from another agent (like cfn_explorer) and uses an AI agent
    to process, format, and write the results to a Markdown file in the specified output directory.

    Args:
        agent_response (str): The raw response text from another agent to be processed
        agent_name (str): Name of the source agent (used for filename generation)
        output_directory (str): Directory where the processed results will be saved

    Returns:
        Dict: Status dictionary with success/failure and response/error message
    """
    try:
        logger.info(f"Processing {agent_name} ")

        # Check if Strands framework is available before proceeding
        if not STRANDS_AVAILABLE:
            return {"status": "failure", "message": "Strands framework not available"}

        # Define the tools available to the analysis writer agent
        tools = [use_aws, file_read, file_write, editor, shell]

        # Set required configurations for tool usage (AWS credentials, etc.)
        Constants.set_tool_configurations()

        # Create the AI model instance using Bedrock with configured temperature
        # Temperature controls the randomness/creativity of the model's responses
        model = Config.construct_bedrock_model(
            temperature=Constants.ORCHESTRATOR_TEMPERATURE
        )

        # Create the AI agent with the model, system prompt, and available tools
        # The system prompt defines the agent's role and behavior
        agent = Agent(
            model=model,
            system_prompt=WaypointPrompts.ANALYSIS_WRITER_PROMPT,
            tools=tools
        )

        # Execute the agent with instructions to process the response and write to file
        # The agent will format the response and save it as {agent_name}_result.json
        response = agent(
            f"Process the response {agent_response} produced by {agent_name} agent and write to the filename {agent_name}.md to the directory {output_directory}")

        return {
            "status": "success",
            "agent_response": response
        }

    except Exception as e:
        # Log any errors that occur during processing and return failure status
        logger.error(f"Error in cfn_explorer: {e}")
        return {"status": "failure", "message": str(e)}


def run_cli():
    """
    Handle command-line interface execution for testing the analysis writer

    This function provides a CLI entry point for testing the analysis_writer function
    with sample CloudFormation analysis data. It demonstrates how the agent processes
    and formats complex AWS infrastructure analysis results.
    """
    # Sample agent response containing CloudFormation stack analysis data
    # This represents the type of data that would be produced by the cfn_explorer agent
    agent_response = """
    Based on the information gathered, I'll now compile a comprehensive analysis of the CloudFormation stacks in the us-east-1 region using the kfadmin AWS profile. Let me format the output according to your requirements:

```json
{
  "analysis_metadata": {
    "region": "us-east-1",
    "profile": "kfadmin",
    "timestamp": "2025-08-19T21:40:00Z",
    "total_stacks": 23
  },
  "running_stacks": [
    {
      "stack_name": "CDKToolkit",
      "stack_status": "CREATE_COMPLETE",
      "creation_time": "2025-02-13 17:29:35+0000",
      "last_updated": "2025-02-13 17:29:42+0000",
      "resource_types": [
        "AWS::SSM::Parameter",
        "AWS::IAM::Role",
        "AWS::ECR::Repository",
        "AWS::IAM::Policy",
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy"
      ],
      "parameters": {
        "FileAssetsBucketKmsKeyId": "AWS_MANAGED_KEY",
        "PublicAccessBlockConfiguration": "true",
        "UseExamplePermissionsBoundary": "false",
        "FileAssetsBucketName": "",
        "InputPermissionsBoundary": "",
        "BootstrapVariant": "AWS CDK: Default Resources",
        "CloudFormationExecutionPolicies": "",
        "TrustedAccountsForLookup": "",
        "Qualifier": "hnb659fds",
        "ContainerAssetsRepositoryName": "",
        "TrustedAccounts": ""
      },
      "outputs": {
        "ImageRepositoryName": "cdk-hnb659fds-container-assets-637423355473-us-east-1",
        "BucketName": "cdk-hnb659fds-assets-637423355473-us-east-1",
        "BootstrapVersion": "25",
        "BucketDomainName": "cdk-hnb659fds-assets-637423355473-us-east-1.s3.us-east-1.amazonaws.com",
        "FileAssetKeyArn": "AWS_MANAGED_KEY"
      },
      "tags": {},
      "resource_details": [
        {
          "logical_id": "CdkBootstrapVersion",
          "physical_id": "/cdk-bootstrap/hnb659fds/version",
          "resource_type": "AWS::SSM::Parameter"
        },
        {
          "logical_id": "CloudFormationExecutionRole",
          "physical_id": "cdk-hnb659fds-cfn-exec-role-637423355473-us-east-1",
          "resource_type": "AWS::IAM::Role"
        },
        {
          "logical_id": "ContainerAssetsRepository",
          "physical_id": "cdk-hnb659fds-container-assets-637423355473-us-east-1",
          "resource_type": "AWS::ECR::Repository"
        },
        {
          "logical_id": "StagingBucket",
          "physical_id": "cdk-hnb659fds-assets-637423355473-us-east-1",
          "resource_type": "AWS::S3::Bucket"
        }
      ]
    },
    {
      "stack_name": "DependencyAssuranceDAREDataPlane-personal-637423355473",
      "stack_status": "CREATE_COMPLETE",
      "creation_time": "2025-08-11 21:06:20+0000",
      "last_updated": "2025-08-11 21:06:31+0000",
      "resource_types": [
        "AWS::ECR::Repository",
        "AWS::ECS::ClusterCapacityProviderAssociations",
        "AWS::ECS::Cluster",
        "AWS::EC2::SecurityGroup",
        "AWS::ECS::TaskDefinition",
        "AWS::Logs::LogGroup",
        "AWS::Lambda::Function",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::CDK::Metadata",
        "AWS::CloudTrail::Trail",
        "AWS::Glue::Job",
        "AWS::Lambda::EventInvokeConfig",
        "AWS::KMS::Key",
        "AWS::StepFunctions::StateMachine",
        "AWS::Events::Rule",
        "AWS::DynamoDB::Table",
        "Custom::S3AutoDeleteObjects",
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy",
        "Custom::S3BucketNotifications"
      ],
      "parameters": {
        "PackagingS3KeyPrefix": "local_development_resources",
        "AmazonPipelinesEmergencyDeploymentFlag": "false",
        "AmazonPipelinesRollbackFlag": "false",
        "PackagingTransformId": "default_aggregate_id_transform",
        "PackagingAggregateId": "default_aggregate_id"
      },
      "outputs": {},
      "tags": {},
      "resource_details": [
        {
          "logical_id": "AgenticApiValidatorDareEcrRepository965CFCC4",
          "physical_id": "dare-api-validation-personal",
          "resource_type": "AWS::ECR::Repository"
        },
        {
          "logical_id": "StorageDareStorageBucketA8F0C074",
          "physical_id": "dare-personal-us-west-1-storage-637423355473",
          "resource_type": "AWS::S3::Bucket"
        },
        {
          "logical_id": "StorageApiCacheD3112F5C",
          "physical_id": "dare-api-cache",
          "resource_type": "AWS::DynamoDB::Table"
        }
      ]
    },
    {
      "stack_name": "BONESBootstrap-DependencyAssuranceDAREDataPlane-dev-637423355473-us-east-1",
      "stack_status": "CREATE_COMPLETE",
      "creation_time": "2025-08-11 20:56:59+0000",
      "last_updated": "2025-08-11 20:57:04+0000",
      "resource_types": [
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy",
        "AWS::KMS::Key",
        "AWS::KMS::Alias",
        "AWS::ECR::Repository",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::CDK::Metadata",
        "AWS::IAM::ManagedPolicy"
      ],
      "parameters": [],
      "outputs": {
        "BARSKeyArnExport": "arn:aws:kms:REGION:ACCOUNT_ID:key/KEY_ID"
      },
      "tags": {},
      "resource_details": [
        {
          "logical_id": "BARS772963B4",
          "physical_id": "deploymentbucket-146481c5cdb2468ff969242f065c976a5d945d50",
          "resource_type": "AWS::S3::Bucket"
        },
        {
          "logical_id": "BARSBARSKey008C869E",
          "physical_id": "316e8b3b-ea4a-4be0-87a0-04550570221a",
          "resource_type": "AWS::KMS::Key"
        },
        {
          "logical_id": "BARSImageRepoC9741AEA",
          "physical_id": "barsecrrepo-eb853a9de606b5705eb6b641e394ac488bb610b1",
          "resource_type": "AWS::ECR::Repository"
        }
      ]
    },
    {
      "stack_name": "AtlasNeptuneGlobalDatabase-637423355473-Dev-IAD",
      "stack_status": "UPDATE_COMPLETE",
      "creation_time": "2025-02-17 16:19:04+0000",
      "last_updated": "2025-08-18 19:27:12+0000",
      "resource_types": [
        "AWS::Neptune::DBInstance",
        "AWS::SageMaker::NotebookInstance",
        "AWS::CDK::Metadata",
        "AWS::SSM::Parameter",
        "AWS::Logs::LogGroup",
        "AWS::EC2::SecurityGroupIngress",
        "AWS::Lambda::Function",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::Neptune::DBCluster",
        "AWS::CloudFormation::CustomResource",
        "AWS::EC2::SecurityGroup",
        "AWS::Neptune::DBClusterParameterGroup",
        "AWS::Neptune::DBParameterGroup",
        "AWS::Neptune::DBSubnetGroup",
        "AWS::SageMaker::NotebookInstanceLifecycleConfig"
      ],
      "parameters": {
        "PackagingS3KeyPrefix": "pipelines_aggregate_transform_5372566",
        "AmazonPipelinesEmergencyDeploymentFlag": "false",
        "AmazonPipelinesRollbackFlag": "false",
        "PackagingTransformId": "5c62190b-aaa5-47e1-9f71-a30c0ad48682_transform",
        "PackagingAggregateId": "5c62190b-aaa5-47e1-9f71-a30c0ad48682"
      },
      "outputs": {},
      "tags": {},
      "resource_details": [
        {
          "logical_id": "AtlasKnowledgeMapGlobalInstance",
          "physical_id": "AtlasKnowledgeMapGlobal",
          "resource_type": "AWS::Neptune::DBInstance"
        },
        {
          "logical_id": "NeptuneGlobalCluster",
          "physical_id": "atlasknowledgemapglobal",
          "resource_type": "AWS::Neptune::DBCluster"
        },
        {
          "logical_id": "AtlasKnowledgeMapGlobalNotebookInstance",
          "physical_id": "arn:aws:sagemaker:us-east-1:637423355473:notebook-instance/AtlasKnowledgeMapGlobalNotebookInstance",
          "resource_type": "AWS::SageMaker::NotebookInstance"
        }
      ]
    }
  ],
  "service_summary": {
    "unique_services": [
      "AWS::CDK",
      "AWS::CloudFormation",
      "AWS::CloudTrail",
      "AWS::DynamoDB",
      "AWS::EC2",
      "AWS::ECR",
      "AWS::ECS",
      "AWS::Events",
      "AWS::Glue",
      "AWS::IAM",
      "AWS::KMS",
      "AWS::Lambda",
      "AWS::Logs",
      "AWS::Neptune",
      "AWS::S3",
      "AWS::SageMaker",
      "AWS::SSM",
      "AWS::StepFunctions"
    ],
    "resource_type_counts": {
      "AWS::CDK::Metadata": 4,
      "AWS::CloudFormation::CustomResource": 1,
      "AWS::CloudTrail::Trail": 1,
      "AWS::DynamoDB::Table": 1,
      "AWS::EC2::SecurityGroup": 2,
      "AWS::EC2::SecurityGroupIngress": 3,
      "AWS::ECR::Repository": 3,
      "AWS::ECS::Cluster": 1,
      "AWS::ECS::ClusterCapacityProviderAssociations": 1,
      "AWS::ECS::TaskDefinition": 1,
      "AWS::Events::Rule": 1,
      "AWS::Glue::Job": 1,
      "AWS::IAM::ManagedPolicy": 4,
      "AWS::IAM::Policy": 10,
      "AWS::IAM::Role": 14,
      "AWS::KMS::Alias": 1,
      "AWS::KMS::Key": 5,
      "AWS::Lambda::EventInvokeConfig": 1,
      "AWS::Lambda::Function": 5,
      "AWS::Lambda::LayerVersion": 1,
      "AWS::Logs::LogGroup": 3,
      "AWS::Neptune::DBCluster": 1,
      "AWS::Neptune::DBClusterParameterGroup": 1,
      "AWS::Neptune::DBInstance": 3,
      "AWS::Neptune::DBParameterGroup": 1,
      "AWS::Neptune::DBSubnetGroup": 1,
      "AWS::S3::Bucket": 8,
      "AWS::S3::BucketPolicy": 8,
      "AWS::SageMaker::NotebookInstance": 1,
      "AWS::SageMaker::NotebookInstanceLifecycleConfig": 1,
      "AWS::SSM::Parameter": 5,
      "AWS::StepFunctions::StateMachine": 1,
      "Custom::S3AutoDeleteObjects": 2,
      "Custom::S3BucketNotifications": 1
    },
    "potential_regional_dependencies": [
      "AWS::Neptune::DBCluster - Neptune database clusters have regional endpoints",
      "AWS::S3::Bucket - S3 bucket names are globally unique but access points are regional",
      "AWS::Lambda::Function - Lambda functions are regional and may have dependencies on other regional resources",
      "AWS::EC2::SecurityGroup - Security groups are region-specific",
      "AWS::SageMaker::NotebookInstance - SageMaker instances are regional resources"
    ]
  }
}
```

## Key Findings from Analysis:

1. **Infrastructure Composition**:
   - The account contains 23 CloudFormation stacks in the us-east-1 region
   - Most stacks are part of an application called "Atlas Knowledge Graph" with related components
   - The infrastructure uses Neptune (graph database), S3, Lambda, and other AWS services

2. **Service Dependencies**:
   - Strong reliance on Neptune database services for graph data storage
   - Integration between SageMaker notebooks and Neptune databases
   - ETL processes using AWS Glue for data processing
   - Step Functions for workflow orchestration

3. **Regional Considerations**:
   - Neptune database clusters are regionally deployed
   - Several S3 buckets with cross-region references (note bucket names with "us-west-1" despite being deployed in us-east-1)
   - Security groups and VPC configurations that would need regional adjustments if migrating

4. **Key Infrastructure Components**:
   - CDK deployment infrastructure (CDKToolkit stack)
   - Neptune graph databases for knowledge mapping
   - Data processing pipelines with ETL components
   - Integration with SageMaker for analytics

The infrastructure appears to be primarily supporting a knowledge graph application with data processing capabilities, analytics integration, and API validation components.Based on the information gathered, I'll now compile a comprehensive analysis of the CloudFormation stacks in the us-east-1 region using the kfadmin AWS profile. Let me format the output according to your requirements:

```json
{
  "analysis_metadata": {
    "region": "us-east-1",
    "profile": "kfadmin",
    "timestamp": "2025-08-19T21:40:00Z",
    "total_stacks": 23
  },
  "running_stacks": [
    {
      "stack_name": "CDKToolkit",
      "stack_status": "CREATE_COMPLETE",
      "creation_time": "2025-02-13 17:29:35+0000",
      "last_updated": "2025-02-13 17:29:42+0000",
      "resource_types": [
        "AWS::SSM::Parameter",
        "AWS::IAM::Role",
        "AWS::ECR::Repository",
        "AWS::IAM::Policy",
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy"
      ],
      "parameters": {
        "FileAssetsBucketKmsKeyId": "AWS_MANAGED_KEY",
        "PublicAccessBlockConfiguration": "true",
        "UseExamplePermissionsBoundary": "false",
        "FileAssetsBucketName": "",
        "InputPermissionsBoundary": "",
        "BootstrapVariant": "AWS CDK: Default Resources",
        "CloudFormationExecutionPolicies": "",
        "TrustedAccountsForLookup": "",
        "Qualifier": "hnb659fds",
        "ContainerAssetsRepositoryName": "",
        "TrustedAccounts": ""
      },
      "outputs": {
        "ImageRepositoryName": "cdk-hnb659fds-container-assets-637423355473-us-east-1",
        "BucketName": "cdk-hnb659fds-assets-637423355473-us-east-1",
        "BootstrapVersion": "25",
        "BucketDomainName": "cdk-hnb659fds-assets-637423355473-us-east-1.s3.us-east-1.amazonaws.com",
        "FileAssetKeyArn": "AWS_MANAGED_KEY"
      },
      "tags": {},
      "resource_details": [
        {
          "logical_id": "CdkBootstrapVersion",
          "physical_id": "/cdk-bootstrap/hnb659fds/version",
          "resource_type": "AWS::SSM::Parameter"
        },
        {
          "logical_id": "CloudFormationExecutionRole",
          "physical_id": "cdk-hnb659fds-cfn-exec-role-637423355473-us-east-1",
          "resource_type": "AWS::IAM::Role"
        },
        {
          "logical_id": "ContainerAssetsRepository",
          "physical_id": "cdk-hnb659fds-container-assets-637423355473-us-east-1",
          "resource_type": "AWS::ECR::Repository"
        },
        {
          "logical_id": "StagingBucket",
          "physical_id": "cdk-hnb659fds-assets-637423355473-us-east-1",
          "resource_type": "AWS::S3::Bucket"
        }
      ]
    },
    {
      "stack_name": "DependencyAssuranceDAREDataPlane-personal-637423355473",
      "stack_status": "CREATE_COMPLETE",
      "creation_time": "2025-08-11 21:06:20+0000",
      "last_updated": "2025-08-11 21:06:31+0000",
      "resource_types": [
        "AWS::ECR::Repository",
        "AWS::ECS::ClusterCapacityProviderAssociations",
        "AWS::ECS::Cluster",
        "AWS::EC2::SecurityGroup",
        "AWS::ECS::TaskDefinition",
        "AWS::Logs::LogGroup",
        "AWS::Lambda::Function",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::CDK::Metadata",
        "AWS::CloudTrail::Trail",
        "AWS::Glue::Job",
        "AWS::Lambda::EventInvokeConfig",
        "AWS::KMS::Key",
        "AWS::StepFunctions::StateMachine",
        "AWS::Events::Rule",
        "AWS::DynamoDB::Table",
        "Custom::S3AutoDeleteObjects",
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy",
        "Custom::S3BucketNotifications"
      ],
      "parameters": {
        "PackagingS3KeyPrefix": "local_development_resources",
        "AmazonPipelinesEmergencyDeploymentFlag": "false",
        "AmazonPipelinesRollbackFlag": "false",
        "PackagingTransformId": "default_aggregate_id_transform",
        "PackagingAggregateId": "default_aggregate_id"
      },
      "outputs": {},
      "tags": {},
      "resource_details": [
        {
          "logical_id": "AgenticApiValidatorDareEcrRepository965CFCC4",
          "physical_id": "dare-api-validation-personal",
          "resource_type": "AWS::ECR::Repository"
        },
        {
          "logical_id": "StorageDareStorageBucketA8F0C074",
          "physical_id": "dare-personal-us-west-1-storage-637423355473",
          "resource_type": "AWS::S3::Bucket"
        },
        {
          "logical_id": "StorageApiCacheD3112F5C",
          "physical_id": "dare-api-cache",
          "resource_type": "AWS::DynamoDB::Table"
        }
      ]
    },
    {
      "stack_name": "BONESBootstrap-DependencyAssuranceDAREDataPlane-dev-637423355473-us-east-1",
      "stack_status": "CREATE_COMPLETE",
      "creation_time": "2025-08-11 20:56:59+0000",
      "last_updated": "2025-08-11 20:57:04+0000",
      "resource_types": [
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy",
        "AWS::KMS::Key",
        "AWS::KMS::Alias",
        "AWS::ECR::Repository",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::CDK::Metadata",
        "AWS::IAM::ManagedPolicy"
      ],
      "parameters": [],
      "outputs": {
        "BARSKeyArnExport": "arn:aws:kms:REGION:ACCOUNT_ID:key/KEY_ID"
      },
      "tags": {},
      "resource_details": [
        {
          "logical_id": "BARS772963B4",
          "physical_id": "deploymentbucket-146481c5cdb2468ff969242f065c976a5d945d50",
          "resource_type": "AWS::S3::Bucket"
        },
        {
          "logical_id": "BARSBARSKey008C869E",
          "physical_id": "316e8b3b-ea4a-4be0-87a0-04550570221a",
          "resource_type": "AWS::KMS::Key"
        },
        {
          "logical_id": "BARSImageRepoC9741AEA",
          "physical_id": "barsecrrepo-eb853a9de606b5705eb6b641e394ac488bb610b1",
          "resource_type": "AWS::ECR::Repository"
        }
      ]
    },
    {
      "stack_name": "AtlasNeptuneGlobalDatabase-637423355473-Dev-IAD",
      "stack_status": "UPDATE_COMPLETE",
      "creation_time": "2025-02-17 16:19:04+0000",
      "last_updated": "2025-08-18 19:27:12+0000",
      "resource_types": [
        "AWS::Neptune::DBInstance",
        "AWS::SageMaker::NotebookInstance",
        "AWS::CDK::Metadata",
        "AWS::SSM::Parameter",
        "AWS::Logs::LogGroup",
        "AWS::EC2::SecurityGroupIngress",
        "AWS::Lambda::Function",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::Neptune::DBCluster",
        "AWS::CloudFormation::CustomResource",
        "AWS::EC2::SecurityGroup",
        "AWS::Neptune::DBClusterParameterGroup",
        "AWS::Neptune::DBParameterGroup",
        "AWS::Neptune::DBSubnetGroup",
        "AWS::SageMaker::NotebookInstanceLifecycleConfig"
      ],
      "parameters": {
        "PackagingS3KeyPrefix": "pipelines_aggregate_transform_5372566",
        "AmazonPipelinesEmergencyDeploymentFlag": "false",
        "AmazonPipelinesRollbackFlag": "false",
        "PackagingTransformId": "5c62190b-aaa5-47e1-9f71-a30c0ad48682_transform",
        "PackagingAggregateId": "5c62190b-aaa5-47e1-9f71-a30c0ad48682"
      },
      "outputs": {},
      "tags": {},
      "resource_details": [
        {
          "logical_id": "AtlasKnowledgeMapGlobalInstance",
          "physical_id": "AtlasKnowledgeMapGlobal",
          "resource_type": "AWS::Neptune::DBInstance"
        },
        {
          "logical_id": "NeptuneGlobalCluster",
          "physical_id": "atlasknowledgemapglobal",
          "resource_type": "AWS::Neptune::DBCluster"
        },
        {
          "logical_id": "AtlasKnowledgeMapGlobalNotebookInstance",
          "physical_id": "arn:aws:sagemaker:us-east-1:637423355473:notebook-instance/AtlasKnowledgeMapGlobalNotebookInstance",
          "resource_type": "AWS::SageMaker::NotebookInstance"
        }
      ]
    }
  ],
  "service_summary": {
    "unique_services": [
      "AWS::CDK",
      "AWS::CloudFormation",
      "AWS::CloudTrail",
      "AWS::DynamoDB",
      "AWS::EC2",
      "AWS::ECR",
      "AWS::ECS",
      "AWS::Events",
      "AWS::Glue",
      "AWS::IAM",
      "AWS::KMS",
      "AWS::Lambda",
      "AWS::Logs",
      "AWS::Neptune",
      "AWS::S3",
      "AWS::SageMaker",
      "AWS::SSM",
      "AWS::StepFunctions"
    ],
    "resource_type_counts": {
      "AWS::CDK::Metadata": 4,
      "AWS::CloudFormation::CustomResource": 1,
      "AWS::CloudTrail::Trail": 1,
      "AWS::DynamoDB::Table": 1,
      "AWS::EC2::SecurityGroup": 2,
      "AWS::EC2::SecurityGroupIngress": 3,
      "AWS::ECR::Repository": 3,
      "AWS::ECS::Cluster": 1,
      "AWS::ECS::ClusterCapacityProviderAssociations": 1,
      "AWS::ECS::TaskDefinition": 1,
      "AWS::Events::Rule": 1,
      "AWS::Glue::Job": 1,
      "AWS::IAM::ManagedPolicy": 4,
      "AWS::IAM::Policy": 10,
      "AWS::IAM::Role": 14,
      "AWS::KMS::Alias": 1,
      "AWS::KMS::Key": 5,
      "AWS::Lambda::EventInvokeConfig": 1,
      "AWS::Lambda::Function": 5,
      "AWS::Lambda::LayerVersion": 1,
      "AWS::Logs::LogGroup": 3,
      "AWS::Neptune::DBCluster": 1,
      "AWS::Neptune::DBClusterParameterGroup": 1,
      "AWS::Neptune::DBInstance": 3,
      "AWS::Neptune::DBParameterGroup": 1,
      "AWS::Neptune::DBSubnetGroup": 1,
      "AWS::S3::Bucket": 8,
      "AWS::S3::BucketPolicy": 8,
      "AWS::SageMaker::NotebookInstance": 1,
      "AWS::SageMaker::NotebookInstanceLifecycleConfig": 1,
      "AWS::SSM::Parameter": 5,
      "AWS::StepFunctions::StateMachine": 1,
      "Custom::S3AutoDeleteObjects": 2,
      "Custom::S3BucketNotifications": 1
    },
    "potential_regional_dependencies": [
      "AWS::Neptune::DBCluster - Neptune database clusters have regional endpoints",
      "AWS::S3::Bucket - S3 bucket names are globally unique but access points are regional",
      "AWS::Lambda::Function - Lambda functions are regional and may have dependencies on other regional resources",
      "AWS::EC2::SecurityGroup - Security groups are region-specific",
      "AWS::SageMaker::NotebookInstance - SageMaker instances are regional resources"
    ]
  }
}
```

## Key Findings from Analysis:

1. **Infrastructure Composition**:
   - The account contains 23 CloudFormation stacks in the us-east-1 region
   - Most stacks are part of an application called "Atlas Knowledge Graph" with related components
   - The infrastructure uses Neptune (graph database), S3, Lambda, and other AWS services

2. **Service Dependencies**:
   - Strong reliance on Neptune database services for graph data storage
   - Integration between SageMaker notebooks and Neptune databases
   - ETL processes using AWS Glue for data processing
   - Step Functions for workflow orchestration

3. **Regional Considerations**:
   - Neptune database clusters are regionally deployed
   - Several S3 buckets with cross-region references (note bucket names with "us-west-1" despite being deployed in us-east-1)
   - Security groups and VPC configurations that would need regional adjustments if migrating

4. **Key Infrastructure Components**:
   - CDK deployment infrastructure (CDKToolkit stack)
   - Neptune graph databases for knowledge mapping
   - Data processing pipelines with ETL components
   - Integration with SageMaker for analytics

The infrastructure appears to be primarily supporting a knowledge graph application with data processing capabilities, analytics integration, and API validation components.

    """

    # Execute the analysis writer with the sample CloudFormation explorer response
    # This will process the JSON data and write it to cfn_explorer_result.json
    result = analysis_writer(agent_response=agent_response, agent_name='cfn_explorer')
    print(result)


# Entry point for command-line execution
# This allows the script to be run directly for testing purposes
if __name__ == "__main__":
    run_cli()