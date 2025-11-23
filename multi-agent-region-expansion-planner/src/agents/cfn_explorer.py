
"""
CloudFormation Explorer Agent

This module provides a CloudFormation stack analysis agent that connects to AWS
through MCP (Model Context Protocol) to discover and analyze CloudFormation resources
across multiple regions. It's designed to help with multi-region expansion planning
and infrastructure analysis.
"""

import os
import sys
import logging
from typing import Dict, List

# Add parent directory to path for imports to access amzn_waypoint_ai modules
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
    # Define dummy decorator for when strands is not available
    def tool(func):
        return func

# Configure logging for the CFN explorer with structured output
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce boto3/botocore noise in logs
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def cfn_explorer(profile: str, region: str, output_directory: str = "./analysis_results") -> Dict:
    """
    Main CloudFormation exploration function that analyzes AWS infrastructure.
    
    This function connects to AWS through an MCP server to discover and analyze
    CloudFormation stacks, resources, and dependencies in a specified region.
    
    Args:
        profile: AWS CLI profile name for authentication
        region: AWS region to analyze (e.g., 'us-east-1')
        output_directory: Directory to store analysis results
        
    Returns:
        Dict containing analysis results or error information
    """
    try:
        logger.info(f"Starting analysis for account profile: {profile} in region: {region}")
        
        # Check if Strands framework is available for agent orchestration
        if not STRANDS_AVAILABLE:
            return {"status": "failure", "message": "Strands framework not available"}
        
        # Connect to AWS Labs CloudFormation MCP server
        awslabs_cfn_mcp_server = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",  # Use uvx to run the MCP server
                    args=["awslabs.cfn-mcp-server@latest"],  # Latest version of CFN MCP server
                    env={"AWS_PROFILE": profile}  # Pass AWS profile for authentication
                )
            )
        )
        
        # Use the MCP server within a context manager for proper cleanup
        with awslabs_cfn_mcp_server:
            # Combine MCP server tools with standard Strands tools
            # This gives the agent access to both CFN-specific and general AWS operations
            tools = awslabs_cfn_mcp_server.list_tools_sync() + [use_aws, file_read, file_write]

            # Configure the agent with required settings
            Constants.set_tool_configurations()
            
            # Create the language model with appropriate temperature for analysis tasks
            model = Config.construct_bedrock_model(
                temperature=Constants.ORCHESTRATOR_TEMPERATURE
            )

            # Create the agent with CFN discovery capabilities
            agent = Agent(
                model=model,
                system_prompt=WaypointPrompts.CFN_DISCOVERY_PROMPT,
                tools=tools
            )

            # Execute the analysis with a clear instruction
            response = agent(f"Analyze CloudFormation stacks deployed to my account in region {region} using AWS profile {profile}. ")

        return response

    except Exception as e:
        logger.error(f"Error in cfn_explorer: {e}")
        return {"status": "failure", "message": str(e)}


def run_cli():
    """
    Handle command-line interface execution for standalone usage.
    
    Parses command-line arguments and executes the CFN explorer with the
    provided AWS profile and region. Useful for running the explorer
    outside of the Strands framework or for testing purposes.
    """
    import sys

    # Validate command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python cfn_explorer.py <profile> <region>")
        print("Example: python cfn_explorer.py kfadmin us-east-1")
        sys.exit(1)

    # Extract arguments
    profile = sys.argv[1]  # AWS CLI profile name
    region = sys.argv[2]   # AWS region to analyze

    # Execute the analysis and display results
    result = cfn_explorer(profile, region)
    print(result)

# Entry point for direct script execution
if __name__ == "__main__":
    run_cli()