#!/usr/bin/env python3
"""
FastMCP Client - Prompt Operations Example

This example demonstrates how to work with MCP prompts using FastMCP 2.x,
including prompt discovery, execution, and advanced prompt patterns.

Usage:
    python examples/mcp_server/clients/prompt_operations.py

This example covers:
- Prompt discovery and listing
- Prompt execution with arguments
- Dynamic prompt generation
- Prompt templates and variables
- Error handling for prompt operations
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import Client, FastMCP
from fastmcp.client.transports import PythonStdioTransport, FastMCPTransport
from fastmcp.exceptions import PromptError, McpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_prompt_server() -> FastMCP:
    """
    Create a mock MCP server with various prompt examples.
    
    Returns:
        FastMCP server instance with prompt examples
    """
    server = FastMCP("Prompt Examples Server")
    
    @server.prompt
    def code_review(language: str = "python", style: str = "detailed") -> str:
        """Generate a code review prompt for the specified programming language."""
        return f"""
Please review the following {language} code with a {style} analysis:

Focus on:
- Code quality and best practices
- Performance considerations
- Security vulnerabilities
- Maintainability and readability
- Testing recommendations

Provide specific suggestions for improvement.
"""
    
    @server.prompt
    def meeting_summary(meeting_type: str = "standup", participants: int = 5) -> str:
        """Generate a meeting summary template."""
        return f"""
{meeting_type.title()} Meeting Summary

Participants: {participants}
Date: {{date}}
Duration: {{duration}}

## Key Discussion Points
- 

## Decisions Made
- 

## Action Items
- [ ] 

## Next Steps
- 
"""
    
    @server.prompt
    def creative_writing(genre: str = "sci-fi", tone: str = "optimistic") -> str:
        """Generate a creative writing prompt."""
        prompts = {
            "sci-fi": {
                "optimistic": "Write a story about humanity's first successful colony on Mars, focusing on the breakthrough that made it possible.",
                "dark": "Describe a future where AI has replaced most human jobs, but one person discovers a way to fight back."
            },
            "fantasy": {
                "optimistic": "Tell the tale of a young mage who discovers their power can heal the ancient rift between warring kingdoms.",
                "dark": "Write about a world where magic is dying, and the last wizard must make an impossible choice."
            }
        }
        
        return prompts.get(genre, {}).get(tone, "Write a compelling story that explores the human condition.")
    
    @server.prompt
    def data_analysis(dataset_type: str = "sales", analysis_type: str = "trend") -> str:
        """Generate a data analysis prompt."""
        return f"""
Analyze the {dataset_type} dataset with focus on {analysis_type} analysis.

Please provide:
1. Data quality assessment
2. Key metrics and KPIs
3. {analysis_type.title()} analysis with visualizations
4. Insights and recommendations
5. Statistical significance of findings

Format the response with clear sections and actionable insights.
"""
    
    return server


async def demonstrate_prompt_discovery() -> Dict[str, Any]:
    """
    Demonstrate discovering available prompts on an MCP server.
    
    Returns:
        Dict containing prompt discovery results
    """
    logger.info("Discovering available prompts...")
    
    # Create server with prompts
    server = await create_prompt_server()
    transport = FastMCPTransport(server)
    
    try:
        async with Client(transport) as client:
            # List all available prompts
            prompts = await client.list_prompts()
            
            prompt_details = []
            for prompt in prompts:
                prompt_info = {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": []
                }
                
                # Extract argument information if available
                if hasattr(prompt, 'arguments') and prompt.arguments:
                    for arg in prompt.arguments:
                        prompt_info["arguments"].append({
                            "name": arg.name,
                            "description": getattr(arg, 'description', ''),
                            "required": arg.required,
                            "type": getattr(arg, 'type', 'string')
                        })
                
                prompt_details.append(prompt_info)
            
            logger.info(f"✓ Discovered {len(prompts)} prompts")
            
            return {
                "status": "success",
                "prompt_count": len(prompts),
                "prompts": prompt_details
            }
            
    except Exception as e:
        logger.error(f"Prompt discovery failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_prompt_execution() -> Dict[str, Any]:
    """
    Demonstrate executing prompts with various arguments.
    
    Returns:
        Dict containing prompt execution results
    """
    logger.info("Executing prompts with different arguments...")
    
    server = await create_prompt_server()
    transport = FastMCPTransport(server)
    
    execution_results = []
    
    try:
        async with Client(transport) as client:
            
            # Test cases for prompt execution
            test_cases = [
                {
                    "prompt": "code_review",
                    "arguments": {"language": "javascript", "style": "concise"},
                    "description": "JavaScript code review prompt"
                },
                {
                    "prompt": "meeting_summary", 
                    "arguments": {"meeting_type": "retrospective", "participants": 8},
                    "description": "Retrospective meeting summary"
                },
                {
                    "prompt": "creative_writing",
                    "arguments": {"genre": "fantasy", "tone": "dark"},
                    "description": "Dark fantasy writing prompt"
                },
                {
                    "prompt": "data_analysis",
                    "arguments": {"dataset_type": "customer", "analysis_type": "segmentation"},
                    "description": "Customer segmentation analysis"
                }
            ]
            
            for test_case in test_cases:
                try:
                    logger.info(f"Executing prompt: {test_case['prompt']}")
                    
                    result = await client.get_prompt(
                        test_case["prompt"],
                        test_case["arguments"]
                    )
                    
                    execution_results.append({
                        "prompt": test_case["prompt"],
                        "arguments": test_case["arguments"],
                        "description": test_case["description"],
                        "status": "success",
                        "content_length": len(result.messages[0].content.text) if result.messages else 0,
                        "preview": result.messages[0].content.text[:100] + "..." if result.messages else ""
                    })
                    
                    logger.info(f"✓ {test_case['prompt']} executed successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to execute {test_case['prompt']}: {e}")
                    execution_results.append({
                        "prompt": test_case["prompt"],
                        "arguments": test_case["arguments"],
                        "description": test_case["description"],
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "executions": execution_results,
                "successful_executions": len([r for r in execution_results if r["status"] == "success"])
            }
            
    except Exception as e:
        logger.error(f"Prompt execution demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_prompt_error_handling() -> Dict[str, Any]:
    """
    Demonstrate error handling for prompt operations.
    
    Returns:
        Dict containing error handling results
    """
    logger.info("Demonstrating prompt error handling...")
    
    server = await create_prompt_server()
    transport = FastMCPTransport(server)
    
    error_scenarios = []
    
    try:
        async with Client(transport) as client:
            
            # Test error scenarios
            test_scenarios = [
                {
                    "name": "non_existent_prompt",
                    "prompt": "non_existent_prompt",
                    "arguments": {},
                    "expected_error": "Prompt not found"
                },
                {
                    "name": "invalid_argument_type",
                    "prompt": "meeting_summary",
                    "arguments": {"participants": "invalid_number"},
                    "expected_error": "Invalid argument type"
                },
                {
                    "name": "missing_required_argument",
                    "prompt": "code_review",
                    "arguments": {},  # Missing required arguments
                    "expected_error": "Missing required argument"
                }
            ]
            
            for scenario in test_scenarios:
                try:
                    logger.info(f"Testing error scenario: {scenario['name']}")
                    
                    result = await client.get_prompt(
                        scenario["prompt"],
                        scenario["arguments"]
                    )
                    
                    # If we get here, the error wasn't caught
                    error_scenarios.append({
                        "scenario": scenario["name"],
                        "status": "unexpected_success",
                        "message": "Expected error but operation succeeded"
                    })
                    
                except (PromptError, McpError) as e:
                    logger.info(f"✓ Caught expected error for {scenario['name']}: {e}")
                    error_scenarios.append({
                        "scenario": scenario["name"],
                        "status": "expected_error",
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    })
                    
                except Exception as e:
                    logger.warning(f"Unexpected error type for {scenario['name']}: {e}")
                    error_scenarios.append({
                        "scenario": scenario["name"],
                        "status": "unexpected_error",
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    })
            
            return {
                "status": "success",
                "error_scenarios": error_scenarios,
                "expected_errors_caught": len([s for s in error_scenarios if s["status"] == "expected_error"])
            }
            
    except Exception as e:
        logger.error(f"Error handling demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating FastMCP prompt operations.
    
    Returns:
        Dict containing all demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Prompt Operations Examples")
    print("=" * 60)
    
    results = {}
    
    try:
        # 1. Prompt discovery
        logger.info("\n1. Prompt Discovery")
        discovery_result = await demonstrate_prompt_discovery()
        results["discovery"] = discovery_result
        
        # 2. Prompt execution
        logger.info("\n2. Prompt Execution")
        execution_result = await demonstrate_prompt_execution()
        results["execution"] = execution_result
        
        # 3. Error handling
        logger.info("\n3. Error Handling")
        error_handling_result = await demonstrate_prompt_error_handling()
        results["error_handling"] = error_handling_result
        
        print("\n" + "=" * 60)
        print("Prompt operations examples completed!")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the prompt operations examples
    result = asyncio.run(main())
    print(f"\nFinal Results: {json.dumps(result, indent=2, default=str)}")
