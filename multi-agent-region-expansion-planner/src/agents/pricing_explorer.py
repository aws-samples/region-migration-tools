"""
AWS Pricing Explorer Agent

This module provides an AWS pricing analysis agent that connects to AWS
through MCP (Model Context Protocol) to discover and analyze pricing information
across different services and regions. It's designed to help with cost optimization
and pricing analysis for infrastructure planning.
"""

import os
import sys
import logging
from typing import Dict, List

# Add parent directory to path for imports to access amzn_waypoint_ai modules
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

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

# Configure logging for the pricing explorer with structured output
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce boto3/botocore noise in logs
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def compare_regional_pricing(profile: str, services: List[str], regions: List[str], output_directory: str = "./analysis_results") -> Dict:
    """
    Compare pricing for a specific AWS service across multiple regions.
    
    Args:
        profile: AWS CLI profile name for authentication
        services: AWS service to analyze (e.g., 'EC2', 'S3', 'RDS')
        regions: List of AWS regions to compare
        output_directory: Directory to store comparison results
        
    Returns:
        Dict containing regional pricing comparison results
    """
    try:
        logger.info(f"Starting regional pricing comparison for {services} across regions: {regions}")
        
        if not STRANDS_AVAILABLE:
            return {"status": "failure", "message": "Strands framework not available"}
        
        results = {}
        
        for region in regions:
            logger.info(f"Analyzing pricing for {services} in {region}")
            
            # Connect to pricing MCP server for each region
            awslabs_pricing_mcp_server = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uvx",
                        args=["awslabs.aws-pricing-mcp-server@latest"],
                        env={
                            "AWS_PROFILE": profile,
                            "AWS_REGION": region,
                            "FASTMCP_LOG_LEVEL": "ERROR"
                        }
                    )
                )
            )
            
            with awslabs_pricing_mcp_server:
                tools = awslabs_pricing_mcp_server.list_tools_sync() + [use_aws, file_read, file_write, python_repl]
                
                Constants.set_tool_configurations()
                model = Config.construct_bedrock_model(temperature=Constants.ORCHESTRATOR_TEMPERATURE)
                
                agent = Agent(
                    model=model,
                    system_prompt=WaypointPrompts.PRICING_COMPARISON_PROMPT,
                    tools=tools
                )
                
                response = agent(f"Get detailed pricing information for {services} in {region}. ")
                
                results[region] = response
        
        # Create comparison summary
        comparison_result = {
            "services": services,
            "regions": regions,
            "regional_data": results,
            "status": "success"
        }
        
        return comparison_result

    except Exception as e:
        logger.error(f"Error in compare_regional_pricing: {e}")
        return {"status": "failure", "message": str(e)}


def run_cli():
    """
    Handle command-line interface execution for standalone usage.
    
    Parses command-line arguments and executes the pricing explorer with the
    provided AWS profile and region. Useful for running the explorer
    outside of the Strands framework or for testing purposes.
    """
    import sys

    # Validate command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python pricing_explorer.py <profile> <region> [service]")
        print("Example: python pricing_explorer.py kfadmin us-east-1")
        print("Example: python pricing_explorer.py kfadmin us-east-1 EC2")
        sys.exit(1)

    # Extract arguments
    profile = sys.argv[1]  # AWS CLI profile name
    regions = sys.argv[2]   # AWS regions to analyze
    services = sys.argv[3] #

    regions = [regions, "us-west-2", "eu-west-1"]  # Default comparison regions
    result = compare_regional_pricing(profile, services, regions)
 
    
    print(result)

# Entry point for direct script execution
if __name__ == "__main__":
    run_cli()