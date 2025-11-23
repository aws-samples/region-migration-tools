"""
Planning Report Generator Agent

This module provides a multi-region expansion planning agent that analyzes AWS infrastructure
and generates comprehensive reports for expanding services across different AWS regions.
It leverages the AWS Knowledge Graph through MCP (Model Context Protocol) to understand
service dependencies, regional availability, and infrastructure requirements for successful
multi-region deployments.

The agent takes a source region and target regions, along with analysis input data,
to produce detailed planning reports that help teams make informed decisions about
regional expansion strategies.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List
import os



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

# Configure logging for the planning report generator with structured output
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce boto3/botocore noise in logs
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def planning_report_generator(source_region: str, target_regions: List, analysis_input_data: Dict, ):
    """
    Generate comprehensive multi-region expansion planning reports.

    This function uses outputs from other agents to analyze
    service dependencies, regional availability, and infrastructure requirements for
    expanding AWS services from a source region to multiple target regions.

    Args:
        source_region: The AWS region currently hosting the infrastructure (e.g., 'us-east-1')
        target_regions: List of AWS regions to expand to (e.g., ['eu-central-1', 'ap-southeast-1'])
        analysis_input_data: Dictionary containing pre-analyzed infrastructure data and requirements

    Saves the Outout as a markdown file
    """
    try:
        logger.info(f"Starting planning_report_generator for {target_regions} regions and source region {source_region}")

        # Check if Strands framework is available for agent orchestration
        if not STRANDS_AVAILABLE:
            return {"status": "failure", "message": "Strands framework not available"}

        # Connect to AWS Knowledge Graph MCP Server for regional analysis capabilities
        aws_knowledge_mcp_server = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="npx",  # Use npx to run the MCP server
                    args=["mcp-remote", "https://knowledge-mcp.global.api.aws"],  # AWS Knowledge Graph MCP server
                )
            )
        )

        # Use the MCP server within a context manager for proper cleanup
        with aws_knowledge_mcp_server:
            # Combine AWS Knowledge Graph MCP tools with standard Strands tools
            # This gives the agent access to regional analysis capabilities and general AWS operations
            tools = aws_knowledge_mcp_server.list_tools_sync() + [use_aws, file_read, file_write]

            # Configure the agent with required settings for planning analysis
            Constants.set_tool_configurations()

            # Create the language model with appropriate temperature for planning and analysis tasks
            model = Config.construct_bedrock_model(
                temperature=Constants.ORCHESTRATOR_TEMPERATURE
            )

            # Create the agent with multi-region planning and analysis capabilities
            agent = Agent(
                model=model,
                system_prompt=WaypointPrompts.PLANNING_REPORT_GENERATOR,
                tools=tools
            )
            output_directory= "./analysis_results"

            # Execute the multi-region expansion planning analysis
            response = agent(f"Perform multi-region expansion planning for {target_regions} regions and source region {source_region} using the input data {analysis_input_data}. write any output to `expansion_planning_report.md` as markdown file to `/.analysis_results` directory. Ensure you dont burn out max token limits in responding")

        return response

    except Exception as e:
        logger.error(f"Error in planning_report_generator: {e}")
        return {"status": "failure", "message": str(e)}


def run_cli():
    """
    Handle command-line interface execution for standalone usage.

    Loads analysis input data from JSON files and executes the planning report
    generator with predefined source and target regions. Useful for running
    the planning generator outside of the Strands framework or for testing
    multi-region expansion scenarios.
    """
    input_data = {}

    for file_path in Path("./analysis_results").glob("*.json"):
        with open(file_path, 'r') as f:
            input_data[file_path.name] = json.load(f)

    target_regions = ['eu-central-1', 'ap-southeast-7', 'ca-central-1']

    # Execute the planning report generation and display results
    result = planning_report_generator(source_region='us-east-1', target_regions=target_regions, analysis_input_data=input_data)
    print(result)


# Entry point for direct script execution
if __name__ == "__main__":
    run_cli()