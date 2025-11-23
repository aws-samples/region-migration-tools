# config.py
import os
import boto3
from strands.models import BedrockModel


class ExpansionPlaningInputs:
    """
    All Expansion planning Inputs are configured here
    """
    PROFILE_NAME = '<your_cli_profile>'  # AWS CLI profile to access account where workloads are deployed
    SOURCE_REGION = 'us-east-1'  # Source region where workloads are deployed
    TARGET_REGIONS = ['ap-southeast-7', 'ap-southeast-5', 'eu-south-1',
                      'mx-central-1']  # Target regions where workloads need to be expanded to
    CTRAIL_LOOKBACK_DAYS = 7


class Constants:
    """Constants that don't change between environments"""
    # Bedrock Agent constants
    INFRA_REGION = "us-east-1"
    INFRA_ACCOUNT = "<your_account_ID>"  # Replace with your actual account ID to use Bedrock Models
    BEDROCK_AWS_CLI_PROFILE = "<your_cli_profile_for_Bedrock>"  # Replace with actual AWS CLI Profile to access Bedrock Models

    # Agent-specific configurations
    ORCHESTRATOR_TEMPERATURE = 0.7
    DEPENDENCY_COLLECTOR_TEMPERATURE = 0.9
    DEPENDENCY_AUDITOR_TEMPERATURE = 0.7
    RECOMMENDER_TEMPERATURE = 0.2

    # Rate limiting configurations
    REQUEST_DELAY = 1.0  # Delay between requests in seconds
    MAX_RETRIES = 3  # Maximum retry attempts for throttling

    # Timeout configurations for Bedrock API calls
    READ_TIMEOUT = 600  # 10 minutes for reading streaming responses
    CONNECT_TIMEOUT = 60  # 1 minute for initial connection

    # Output directories
    OUTPUT_DIR = "analysis_output"

    @classmethod
    def set_tool_configurations(cls):
        """Sets up required environment variables for tool configurations."""
        os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"
        os.environ["BYPASS_TOOL_CONSENT"] = "true"


class Config:
    @staticmethod
    def get_infra_account_id() -> str:
        """Get the infrastructure account ID."""
        return Constants.INFRA_ACCOUNT

    @staticmethod
    def get_bedrock_model_id() -> str:
        """Get the Bedrock model ID. Returns default if not specified."""
        return os.environ.get(
            "BEDROCK_MODEL_ID",
            "global.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Alternative model with potentially higher limits
        )

    @classmethod
    def construct_bedrock_model(cls, temperature: float, profile: str = None) -> BedrockModel:
        """
        Constructs a BedrockModel with the specified temperature and retry configuration.
        """
        # Use provided profile or fall back to configured constant
        bedrock_profile = profile if profile is not None else Constants.BEDROCK_AWS_CLI_PROFILE

        model_id = (
            f"arn:aws:bedrock:{Constants.INFRA_REGION}:"
            f"{cls.get_infra_account_id()}:inference-profile/"
            f"{cls.get_bedrock_model_id()}"
        )
        bedrock_session = boto3.Session(profile_name=bedrock_profile,
                                        region_name=Constants.INFRA_REGION)

        # Configure retry settings and timeouts for the boto3 client
        from botocore.config import Config as BotocoreConfig
        retry_config = BotocoreConfig(
            retries={
                'max_attempts': Constants.MAX_RETRIES,
                'mode': 'adaptive'  # Use adaptive retry mode for better throttling handling
            },
            read_timeout=Constants.READ_TIMEOUT,
            connect_timeout=Constants.CONNECT_TIMEOUT
        )

        return BedrockModel(
            model_id=model_id,
            boto_session=bedrock_session,
            temperature=temperature,
            # Add retry configuration to the underlying boto3 client
            boto_client_config=retry_config
        )