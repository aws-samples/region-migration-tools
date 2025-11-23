
"""
CloudTrail Explorer Agent

This module provides functionality to analyze AWS CloudTrail logs and identify unique APIs and usage patterns.
It uses the Strands framework for AI-powered analysis and AWS SDK for CloudTrail data retrieval.
Standard library imports for type hints, JSON handling, and date operations.
"""

from typing import Dict, List, Set
import json
import boto3
from datetime import datetime, timedelta
import os
import sys
import logging

# Add parent directory to path for imports - enables relative imports from parent modules
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from strands import Agent, tool
    from strands.tools.mcp import MCPClient
    from mcp import stdio_client, StdioServerParameters
    from utils.config import Config, Constants
    from utils.prompts import WaypointPrompts
    from strands_tools import use_aws, file_read, file_write, python_repl, editor
    STRANDS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Strands not available: {e}")
    STRANDS_AVAILABLE = False
    # Define dummy decorator for when strands is not available - allows code to run without framework
    def tool(func):
        return func

# Configure logging for debugging and monitoring agent execution
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce boto3/botocore logging noise to focus on application logs
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def cloudtrail_explorer(profile: str, region: str, lookback_days: int = 7, 
                       output_directory: str = "./analysis_results") -> Dict:
    """
    Analyze CloudTrail logs to identify unique APIs and usage patterns
    """
    try:
        logger.info(f"Starting CloudTrail analysis for profile: {profile} in region: {region}")
        
        if not STRANDS_AVAILABLE:
            return {"status": "failure", "message": "Strands framework not available"}

        # Get tools
        tools = [use_aws, file_read, file_write]

        # Set required configurations
        Constants.set_tool_configurations()
        
        # Create Model
        model = Config.construct_bedrock_model(
            temperature=Constants.ORCHESTRATOR_TEMPERATURE
        )
        # Create Agent
        agent = Agent(
            model=model,
            system_prompt=WaypointPrompts.CLOUDTRAIL_DISCOVERY_PROMPT,
            tools=tools
        )
        # Run Agent analysis
        response = agent(f"Analyze the CloudTrail data and provide comprehensive list of services (event source) and api actions (event name) used in the account using the AWS profile {profile}, in region {region} and lookback days {lookback_days}. Dont write any output files. Just return the response")
        
        return {
            "status": "success",
            "agent_response": response
        }
    except Exception as e:
        return {"status": "failure", "message": str(e)}


def run_cli():
    """Handle command-line interface execution"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python cloudtrail_explorer.py <profile> <region> <lookback_days>")
        sys.exit(1)
    profile = sys.argv[1]
    region = sys.argv[2]
    lookback_days = sys.argv[3]
    result = cloudtrail_explorer(profile, region, int(lookback_days))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    run_cli()