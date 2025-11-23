
"""
Technical Analysis Agent for AWS Waypoint AI

This module provides functionality for generating comprehensive technical analysis reports
for AWS workload migration and regional expansion. It processes analysis results from
various explorers (CFN, CloudTrail, Waypoint) and generates structured documentation
with migration strategies, gap analysis, and implementation roadmaps.

Key Features:
- Processes JSON analysis results from multiple sources
- Generates comprehensive technical analysis documents
- Includes throttling protection for AWS Bedrock API calls
- Provides regional availability assessments and migration strategies

Author: AWS Waypoint AI Team
Version: 1.0.0
"""

import os
import sys
import logging
import time
import random
from typing import Dict, List
from botocore.exceptions import ClientError

# Dynamic path configuration for module imports
# This allows the script to be run from different locations while maintaining access
# to the amzn_waypoint_ai package modules
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))  # Add src/amzn_waypoint_ai to path
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))  # Add src to path

# Import dependencies with graceful fallback handling
# The Strands framework and related tools are required for AI agent functionality
try:
    from strands import Agent, tool  # Core AI agent framework
    from strands.tools.mcp import MCPClient  # Model Context Protocol client
    from mcp import stdio_client, StdioServerParameters  # MCP communication protocols
    from utils.config import Config, Constants # Application configuration
    from utils.prompts import WaypointPrompts # AI agent prompts
    from utils.throttling_utils import with_throttling_retry, ThrottlingHandler  # Throttling utilities
    from strands_tools import use_aws, file_read, file_write, python_repl, editor, shell  # Available tools for agent
    STRANDS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Strands framework not available: {e}")
    print("This may occur in environments where Strands is not installed.")
    print("The script will exit gracefully with an error message.")
    STRANDS_AVAILABLE = False
    
    # Define dummy decorator to prevent import errors when Strands is unavailable
    def tool(func):
        """Dummy tool decorator for environments without Strands framework."""
        return func

# Configure comprehensive logging for debugging and monitoring
# Format includes timestamp, logger name, log level, and message for better traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce AWS SDK (botocore) logging verbosity to minimize noise in application logs
# This prevents excessive debug messages from AWS API calls while maintaining error visibility
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)


@tool
def tech_analysis_writer(analysis_directory: str, output_directory: str = "analysis_results") -> Dict:
    """
    Technical Analysis Writer Agent - Generates comprehensive migration analysis documentation
    
    This function orchestrates an AI agent to process multiple JSON analysis results and generate
    a comprehensive technical analysis document for AWS workload migration. The agent reads
    analysis results from CFN Explorer, CloudTrail Explorer, and Waypoint Explorer to create
    a unified migration strategy document.
    
    The generated document includes:
    - Executive Summary with key findings and recommendations
    - Regional Availability Assessment with service/API/CFN resource matrices
    - Gap Analysis highlighting critical service and feature gaps
    - Impact Assessment for migration complexity and risks
    - Migration Strategy with phased implementation approach
    - Implementation Roadmap with timelines and dependencies
    
    Args:
        analysis_directory (str): Directory containing JSON analysis results from various explorers
                                 Expected files: cfn_explorer_result.json, cloudtrail_explorer_result.json,
                                waypoint_explorer_*.json, combined_input.json
        output_directory (str): Directory where the technical analysis document will be saved
                               Defaults to "analysis_results"
        
    Returns:
        Dict: Status dictionary containing:
            - status (str): "success" or "failure"
            - agent_response (str): AI agent's response (on success)
            - message (str): Error message (on failure)
            
    Raises:
        Exception: Various exceptions related to file I/O, AWS API calls, or AI agent execution
                  All exceptions are caught and returned in the status dictionary
    """
    try:
        logger.info(f"Starting Technical Analysis Writer Agent for directory: {analysis_directory}")

        # Validate Strands framework availability before proceeding
        # This prevents runtime errors in environments where Strands is not installed
        if not STRANDS_AVAILABLE:
            error_msg = "Strands framework not available. Please install Strands to use this functionality."
            logger.error(error_msg)
            return {"status": "failure", "message": error_msg}

        # Define the comprehensive toolset available to the AI agent
        # These tools enable the agent to interact with AWS services, read/write files, and execute commands
        tools = [
            use_aws,      # AWS service interactions (CloudFormation, CloudTrail, etc.)
            file_read,    # Read analysis result files
            file_write,   # Write the technical analysis document
            editor,       # Text editing capabilities
            shell         # Shell command execution if needed
        ]

        # Configure environment variables and tool settings
        # This sets up AWS credentials, console mode, and bypasses tool consent prompts
        Constants.set_tool_configurations()
        logger.info("Tool configurations set successfully")

        # Initialize AWS Bedrock model with optimized settings for analysis tasks
        # Temperature is set to balance creativity with factual accuracy for technical documentation
        model = Config.construct_bedrock_model(
            temperature=Constants.ORCHESTRATOR_TEMPERATURE  # 0.7 - balanced creativity/accuracy
        )
        logger.info(f"Bedrock model initialized with temperature: {Constants.ORCHESTRATOR_TEMPERATURE}")

        # Create the AI agent with specialized prompt for technical analysis
        # The system prompt defines the agent's expertise in AWS migration analysis
        agent = Agent(
            model=model,
            system_prompt=WaypointPrompts.ANALYSIS_WRITER_PROMPT,
            tools=tools
        )
        logger.info("AI agent created with technical analysis prompt and tools")
        
        # Execute the agent with comprehensive throttling protection
        # This prevents AWS Bedrock API throttling issues during document generation
        logger.info("Executing agent with throttling protection...")
        with ThrottlingHandler(
            delay_between_calls=Constants.REQUEST_DELAY,  # Delay between API calls
            max_retries=Constants.MAX_RETRIES             # Maximum retry attempts
        ) as handler:
            
            # Detailed instruction prompt for comprehensive technical analysis
            analysis_prompt = f"""
            Read all the analysis results from the JSON files located in {analysis_directory} and create a comprehensive 
            technical analysis document called `technical_analysis.md` for AWS workload migration to a new region.
            
            The document must include the following sections:
            
            1. **Executive Summary**: Key findings, recommendations, and migration feasibility overview
            2. **Regional Availability Assessment**: 
               - Service availability matrix comparing source and target regions
               - API availability comparison tables
               - CloudFormation resource availability matrices
            3. **Gap Analysis**: 
               - Critical service gaps that block migration
               - API gaps that affect application functionality
               - CloudFormation resource gaps that impact infrastructure deployment
            4. **Impact Assessment**: 
               - Migration complexity analysis
               - Risk assessment for identified gaps
               - Business impact evaluation
            5. **Migration Strategy**: 
               - Recommended migration approach
               - Alternative solutions for service gaps
               - Risk mitigation strategies
            6. **Implementation Roadmap**: 
               - Phased implementation approach
               - Timeline and dependencies
               - Success criteria and validation steps
            
            Ensure all tables are properly formatted in Markdown and include specific service names, 
            API operations, and CloudFormation resource types from the analysis data.
            """
            
            response = handler.execute_with_throttling(agent, analysis_prompt)

        logger.info("Technical analysis document generated successfully")
        return {
            "status": "success",
            "agent_response": response,
            "message": "Technical analysis document created successfully"
        }

    except Exception as e:
        # Comprehensive error handling with detailed logging
        # This captures all types of errors: AWS API, file I/O, agent execution, etc.
        error_msg = f"Error in tech_analysis_writer: {str(e)}"
        logger.error(error_msg, exc_info=True)  # Include stack trace in logs
        
        # Return structured error response for calling applications
        return {
            "status": "failure", 
            "message": error_msg,
            "error_type": type(e).__name__
        }


def run_cli():
    """
    Command-line interface entry point for the Technical Analysis Writer Agent
    
    This function provides a CLI interface for testing and running the technical analysis
    writer agent. It's designed to be used during development, testing, and standalone
    execution of the analysis functionality.
    
    The function:
    1. Sets up the analysis directory path (relative to script location)
    2. Executes the tech_analysis_writer function
    3. Prints the results to console for immediate feedback
    4. Handles any execution errors gracefully
    
    Expected Directory Structure:
    - analysis_results/
      ├── cfn_explorer_result.json
      ├── cloudtrail_explorer_result.json
      ├── waypoint_explorer_*.json
      └── combined_input.json
    
    Output:
    - technical_analysis.md (comprehensive migration analysis document)
    - Console output with execution status and any error messages
    """
    try:
        # Set the analysis directory relative to the script location
        # This assumes the analysis results are in a sibling directory to the agents folder
        analysis_dir = '../analysis_results'
        
        logger.info(f"Starting CLI execution with analysis directory: {analysis_dir}")
        
        # Execute the technical analysis writer agent
        result = tech_analysis_writer(analysis_directory=analysis_dir)
        
        # Display results to console with formatting
        print("\n" + "="*60)
        print("TECHNICAL ANALYSIS WRITER - EXECUTION RESULTS")
        print("="*60)
        print(f"Status: {result.get('status', 'unknown').upper()}")
        
        if result.get('status') == 'success':
            print("✅ Technical analysis document generated successfully!")
            print(f"📄 Check the analysis directory for 'technical_analysis.md'")
        else:
            print("❌ Execution failed!")
            print(f"Error: {result.get('message', 'Unknown error')}")
            if 'error_type' in result:
                print(f"Error Type: {result['error_type']}")
        
        print("="*60 + "\n")
        
        return result
        
    except Exception as e:
        error_msg = f"CLI execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ {error_msg}")
        return {"status": "failure", "message": error_msg}

# Main execution entry point
# This enables the script to be run directly from the command line for testing,
# development, and standalone execution scenarios
if __name__ == "__main__":
    print("AWS Waypoint AI - Technical Analysis Writer Agent")
    print("=" * 50)
    run_cli()