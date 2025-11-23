"""
Multi-Region Expansion Planner Agent

This module provides an intelligent agent for planning AWS infrastructure expansion
across multiple regions. It leverages the AWS Knowledge Graph through MCP (Model Context Protocol)
to analyze existing infrastructure patterns, service availability, and regional constraints
to recommend optimal expansion strategies for multi-region deployments.

Key Features:
- Cross-region service availability analysis
- Infrastructure pattern recognition and replication planning
- Regional constraint and compliance assessment
- Cost optimization recommendations for multi-region architectures
- Dependency mapping for complex distributed systems
"""
import json
import os
import sys
import logging
from pathlib import Path
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

# Configure logging for the multi-region expansion planner with structured output
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce boto3/botocore noise in logs to focus on expansion planning activities
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def multi_region_expansion_planner(source_region: str, target_regions: List, analysis_input_data: Dict, ) -> Dict:
    """
    Orchestrates multi-region expansion planning using AWS Knowledge Graph analysis.

    This function leverages the AWS Knowledge Graph MCP server to analyze existing
    infrastructure in a source region and develop comprehensive expansion plans
    for target regions. It considers service availability, regional constraints,
    compliance requirements, and cost optimization opportunities.

    Args:
        source_region: The AWS region containing the existing infrastructure to replicate (e.g., 'us-east-1')
        target_regions: List of target AWS regions for expansion (e.g., ['eu-central-1', 'ap-southeast-1'])
        analysis_input_data: Dictionary containing pre-analyzed infrastructure data and constraints

    Returns:
        Dict containing comprehensive expansion plan with recommendations, constraints,
        cost estimates, and implementation roadmap, or error information if planning fails
    """
    try:
        logger.info(f"Starting multi_region_expansion_planner for {target_regions} regions and source region {source_region}")

        # Check if Strands framework is available for agent orchestration
        if not STRANDS_AVAILABLE:
            return {"status": "failure", "message": "Strands framework not available"}

        # Connect to AWS Knowledge Graph MCP Server for comprehensive infrastructure analysis
        aws_knowledge_mcp_server = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="npx",  # Use npx to run the MCP server
                    args=["mcp-remote", "https://knowledge-mcp.global.api.aws"],  # AWS Knowledge Graph MCP server endpoint
                )
            )
        )

        # Use the MCP server within a context manager for proper resource cleanup
        with aws_knowledge_mcp_server:
            # Combine AWS Knowledge Graph MCP tools with standard Strands utilities
            # This provides access to both knowledge graph queries and file/AWS operations
            tools = aws_knowledge_mcp_server.list_tools_sync() + [use_aws, file_read, file_write]

            # Configure the agent with expansion planning-specific settings
            Constants.set_tool_configurations()

            # Create the language model optimized for strategic planning and analysis
            model = Config.construct_bedrock_model(
                temperature=Constants.ORCHESTRATOR_TEMPERATURE
            )

            # Initialize the expansion planning agent with specialized prompt and toolset
            agent = Agent(
                model=model,
                system_prompt=WaypointPrompts.MULTI_REGION_EXPANSION_PROMPT,
                tools=tools
            )

            # Execute comprehensive multi-region expansion analysis
            response = agent(f"Perform multi-region expansion planning for {target_regions} regions and source region {source_region} using analysis input data {analysis_input_data}")

        return response

    except Exception as e:
        logger.error(f"Error in multi_region_expansion_planner: {e}")
        return {"status": "failure", "message": str(e)}


def run_cli():
    """
    Handle command-line interface execution for standalone expansion planning.

    Loads analysis results from the local analysis_results directory and executes
    the multi-region expansion planner with predefined target regions. Useful for
    running expansion planning outside of the Strands framework, testing scenarios,
    or batch processing multiple expansion plans.
    """
    # Load pre-analyzed infrastructure data from local analysis results
    input_data = {}

    for file_path in Path("./analysis_results").glob("*.json"):
        with open(file_path, 'r') as f:
            input_data[file_path.name] = json.load(f)

    # Define target regions for expansion planning (example regions)
    target_regions = ['eu-central-1', 'ap-southeast-7', 'ca-central-1']

    # Execute the multi-region expansion planning and display comprehensive results
    result = multi_region_expansion_planner(source_region='us-east-1', target_regions=target_regions, analysis_input_data=input_data)
    print(result)


# Entry point for direct script execution
if __name__ == "__main__":
    run_cli()