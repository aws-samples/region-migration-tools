
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import json
from urllib.parse import urlencode

import boto3
from datetime import datetime, timedelta

import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

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

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('botocore').setLevel(logging.WARNING)


@tool
def waypoint_explorer(input_data: Dict, target_region: str, output_directory: str = "./analysis_results") -> Dict:

    try:
        logger.info(f"Starting Waypoint Exploration for target regions: {target_region}")

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


        
        # Use the MCP server within a context manager for proper cleanup
        with aws_knowledge_mcp_server:
            # Get tools
            tools = aws_knowledge_mcp_server.list_tools_sync() + [file_read, file_write]

            # Set required configurations
            Constants.set_tool_configurations()

            # Create Model
            model = Config.construct_bedrock_model(
                temperature=Constants.ORCHESTRATOR_TEMPERATURE
            )
            # Create Agent
            agent = Agent(
                model=model,
                system_prompt=WaypointPrompts.WAYPOINT_EXPLORER_PROMPT,
                tools=tools
            )
            # Run Agent analysis
            response = agent(
                f"Check API and Service availability is target region: {target_region}. using the CFN Explorer results and CloudTrail explorer results here {input_data}.  Dont write any output files. Just return the response")

            return {
                "status": "success",
                "agent_response": response
            }

    except Exception as e:
        logger.error(f"Error in waypoint_explorer: {e}")
        return {"status": "failure", "message": str(e)}


if __name__ == "__main__":
    try:
        input_data = {}

        for file_path in Path("./analysis_results").glob("*.json"):
            with open(file_path, 'r') as f:
                input_data[file_path.name] = json.load(f)

        print(input_data)

        result = waypoint_explorer(input_data=input_data, target_region='ap-southeast-7')
        

        if result:
            exit(0)
        else:
            exit(1)

    except Exception as e:
        error = {
            "status": "error",
            "error_message": f"System error: {str(e)}"
        }
        print(json.dumps(error, indent=2))
        exit(2)
