"""
FastMCP Resource Operations Examples

This example demonstrates comprehensive resource operations with FastMCP client:
- Resource discovery and metadata inspection
- Static resource access patterns
- Templated resource usage
- Binary and text content handling
- Resource URI patterns and conventions

Usage:
    python examples/mcp_server/clients/resource_operations.py

This example covers:
- Resource discovery with list_resources()
- Resource access with read_resource()
- Different content types (text, binary, JSON)
- Resource templates and URI patterns
- Error handling for resource operations
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from fastmcp.exceptions import ResourceError

# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def discover_resources() -> dict[str, Any]:
    """
    Demonstrate comprehensive resource discovery and metadata inspection.

    Shows how to:
    1. List all available resources
    2. Inspect resource metadata and URIs
    3. Analyze resource types and capabilities
    4. Understand resource naming patterns

    Returns:
        Dict containing resource discovery results
    """
    logger.info("Discovering and analyzing available resources...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # 1. Basic resource discovery
            resources = await client.list_resources()
            logger.info(f"Discovered {len(resources)} resources")

            resource_analysis: list[Any] = []

            for resource in resources:
                # Analyze each resource's metadata
                analysis = {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mime_type": getattr(resource, "mimeType", None),
                    "uri_scheme": str(resource.uri).split("://")[0]
                    if "://" in str(resource.uri)
                    else "unknown",
                    "is_templated": "{" in str(resource.uri) and "}" in str(resource.uri),
                }

                resource_analysis.append(analysis)

                logger.info(f"Resource: {resource.name}")
                logger.info(f"  URI: {resource.uri}")
                logger.info(f"  Description: {resource.description}")
                logger.info(f"  MIME Type: {analysis['mime_type']}")
                logger.info(f"  Scheme: {analysis['uri_scheme']}")
                logger.info(f"  Templated: {analysis['is_templated']}")

            # 2. Categorize resources
            static_resources = [r for r in resource_analysis if not r["is_templated"]]
            templated_resources = [r for r in resource_analysis if r["is_templated"]]

            # 3. Analyze URI schemes
            schemes = set(r["uri_scheme"] for r in resource_analysis)

            return {
                "status": "success",
                "total_resources": len(resources),
                "static_resources": len(static_resources),
                "templated_resources": len(templated_resources),
                "uri_schemes": list(schemes),
                "resource_details": resource_analysis,
                "discovery_method": "list_resources",
            }

    except Exception as e:
        logger.error(f"Resource discovery failed: {e}")
        return {"status": "failed", "error": str(e)}


async def access_static_resources() -> dict[str, Any]:
    """
    Demonstrate access to static resources.

    Shows how to:
    1. Access resources with fixed URIs
    2. Handle different content types
    3. Parse JSON and text content
    4. Manage resource access errors

    Returns:
        Dict containing static resource access results
    """
    logger.info("Accessing static resources...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    access_results: list[Any] = []

    try:
        async with Client(transport) as client:
            # Get available resources
            resources = await client.list_resources()
            static_resources = [
                r for r in resources if not ("{" in str(r.uri) and "}" in str(r.uri))
            ]

            logger.info(f"Found {len(static_resources)} static resources")

            for resource in static_resources:
                logger.info(f"Accessing resource: {resource.uri}")

                try:
                    # Access the resource
                    content = await client.read_resource(resource.uri)

                    if content:
                        # Analyze content blocks
                        content_info = {
                            "uri": resource.uri,
                            "name": resource.name,
                            "blocks": len(content),
                            "content_types": [],
                            "total_size": 0,
                            "parsed_data": None,
                        }

                        for i, block in enumerate(content):
                            if hasattr(block, "text") and block.text:
                                content_info["content_types"].append("text")
                                content_info["total_size"] += len(block.text)

                                # Try to parse as JSON
                                if str(resource.uri).endswith("/info") or "config" in str(
                                    resource.uri
                                ):  # [attr-defined]
                                    try:
                                        parsed = json.loads(block.text)
                                        content_info["parsed_data"] = parsed
                                        logger.info(f"  ✓ Parsed JSON data with {len(parsed)} keys")
                                    except json.JSONDecodeError:
                                        logger.info(
                                            f"  ✓ Text content: {len(block.text)} characters"
                                        )
                                else:
                                    logger.info(f"  ✓ Text content: {len(block.text)} characters")

                            elif hasattr(block, "blob") and block.blob:
                                content_info["content_types"].append("binary")
                                content_info["total_size"] += len(block.blob)
                                logger.info(f"  ✓ Binary content: {len(block.blob)} bytes")

                        access_results.append(content_info)
                        logger.info(f"  Total content size: {content_info['total_size']} bytes")

                except ResourceError as e:
                    logger.warning(f"  ✗ Resource access failed: {e}")
                    access_results.append(
                        {
                            "uri": resource.uri,
                            "name": resource.name,
                            "error": str(e),
                            "status": "failed",
                        }
                    )

            successful_accesses = [r for r in access_results if "error" not in r]
            failed_accesses = [r for r in access_results if "error" in r]

            return {
                "status": "success",
                "total_attempts": len(access_results),
                "successful": len(successful_accesses),
                "failed": len(failed_accesses),
                "total_content_size": sum(r.get("total_size", 0) for r in successful_accesses),
                "access_results": access_results,
            }

    except Exception as e:
        logger.error(f"Static resource access failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_templated_resources() -> dict[str, Any]:
    """
    Demonstrate templated resource usage patterns.

    Shows how to:
    1. Identify templated resources
    2. Substitute template parameters
    3. Access resources with dynamic URIs
    4. Handle template parameter validation

    Returns:
        Dict containing templated resource demonstration results
    """
    logger.info("Demonstrating templated resource usage...")

    # For this example, we'll use the GitHound server which has templated resources
    githound_server_script = Path(__file__).parent.parent / "servers" / "githound_server.py"

    if not githound_server_script.exists():
        logger.warning("GitHound server not available, using simple server")
        server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    else:
        server_script = githound_server_script

    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # Get available resources
            resources = await client.list_resources()
            templated_resources = [r for r in resources if "{" in str(r.uri) and "}" in str(r.uri)]

            logger.info(f"Found {len(templated_resources)} templated resources")

            template_results: list[Any] = []

            for resource in templated_resources:
                logger.info(f"Templated resource: {resource.uri}")

                # Extract template parameters
                import re

                template_params = re.findall(r"\{([^}]+)\}", resource.uri)
                logger.info(f"  Template parameters: {template_params}")

                # Try to access with sample parameters
                if "repo_path" in template_params:
                    # Use current directory as repo path
                    sample_uri = resource.uri.replace("{repo_path}", ".")

                    try:
                        logger.info(f"  Accessing: {sample_uri}")
                        content = await client.read_resource(sample_uri)

                        if content and content[0].text:
                            # Try to parse as JSON
                            try:
                                data = json.loads(content[0].text)
                                logger.info(
                                    f"  ✓ Retrieved templated resource with {len(data)} keys"
                                )

                                template_results.append(
                                    {
                                        "original_uri": resource.uri,
                                        "resolved_uri": sample_uri,
                                        "template_params": template_params,
                                        "status": "success",
                                        "content_size": len(content[0].text),
                                        "data_keys": list(data.keys())
                                        if isinstance(data, dict)
                                        else None,
                                    }
                                )

                            except json.JSONDecodeError:
                                logger.info("  ✓ Retrieved templated resource (non-JSON)")
                                template_results.append(
                                    {
                                        "original_uri": resource.uri,
                                        "resolved_uri": sample_uri,
                                        "template_params": template_params,
                                        "status": "success",
                                        "content_size": len(content[0].text),
                                        "content_type": "text",
                                    }
                                )

                    except Exception as e:
                        logger.warning(f"  ✗ Templated resource access failed: {e}")
                        template_results.append(
                            {
                                "original_uri": resource.uri,
                                "resolved_uri": sample_uri,
                                "template_params": template_params,
                                "status": "failed",
                                "error": str(e),
                            }
                        )
                else:
                    # Unknown template parameters
                    template_results.append(
                        {
                            "original_uri": resource.uri,
                            "template_params": template_params,
                            "status": "skipped",
                            "reason": "Unknown template parameters",
                        }
                    )

            successful_templates = [r for r in template_results if r.get("status") == "success"]

            return {
                "status": "success",
                "templated_resources_found": len(templated_resources),
                "template_attempts": len(template_results),
                "successful_accesses": len(successful_templates),
                "template_results": template_results,
            }

    except Exception as e:
        logger.error(f"Templated resource demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_content_types() -> dict[str, Any]:
    """
    Demonstrate handling of different content types.

    Shows how to:
    1. Handle text content
    2. Process binary data
    3. Parse structured data (JSON, XML)
    4. Manage content encoding

    Returns:
        Dict containing content type handling results
    """
    logger.info("Demonstrating content type handling...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            resources = await client.list_resources()

            content_type_results = {
                "text_content": [],
                "json_content": [],
                "binary_content": [],
                "unknown_content": [],
            }

            for resource in resources:
                if "{" in str(resource.uri) and "}" in str(resource.uri):
                    continue  # Skip templated resources for this demo

                try:
                    content = await client.read_resource(resource.uri)

                    for block in content:
                        if hasattr(block, "text") and block.text:
                            # Text content
                            try:
                                # Try to parse as JSON
                                json_data = json.loads(block.text)
                                content_type_results["json_content"].append(
                                    {
                                        "uri": resource.uri,
                                        "size": len(block.text),
                                        "keys": list(json_data.keys())
                                        if isinstance(json_data, dict)
                                        else None,
                                        "type": type(json_data).__name__,
                                    }
                                )
                                logger.info(
                                    f"  JSON content from {resource.uri}: {len(json_data)} items"
                                )

                            except json.JSONDecodeError:
                                # Plain text
                                content_type_results["text_content"].append(
                                    {
                                        "uri": resource.uri,
                                        "size": len(block.text),
                                        "preview": block.text[:100] + "..."
                                        if len(block.text) > 100
                                        else block.text,
                                    }
                                )
                                logger.info(
                                    f"  Text content from {resource.uri}: {len(block.text)} chars"
                                )

                        elif hasattr(block, "blob") and block.blob:
                            # Binary content
                            content_type_results["binary_content"].append(
                                {"uri": resource.uri, "size": len(block.blob), "type": "binary"}
                            )
                            logger.info(
                                f"  Binary content from {resource.uri}: {len(block.blob)} bytes"
                            )

                        else:
                            # Unknown content type
                            content_type_results["unknown_content"].append(
                                {"uri": resource.uri, "block_type": type(block).__name__}
                            )
                            logger.info(f"  Unknown content type from {resource.uri}")

                except Exception as e:
                    logger.warning(f"Content type analysis failed for {resource.uri}: {e}")

            return {
                "status": "success",
                "content_types": {
                    "text_files": len(content_type_results["text_content"]),
                    "json_files": len(content_type_results["json_content"]),
                    "binary_files": len(content_type_results["binary_content"]),
                    "unknown_files": len(content_type_results["unknown_content"]),
                },
                "total_text_size": sum(
                    item["size"] for item in content_type_results["text_content"]
                ),
                "total_json_size": sum(
                    item["size"] for item in content_type_results["json_content"]
                ),
                "total_binary_size": sum(
                    item["size"] for item in content_type_results["binary_content"]
                ),
                "content_details": content_type_results,
            }

    except Exception as e:
        logger.error(f"Content type demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_resource_patterns() -> dict[str, Any]:
    """
    Demonstrate common resource URI patterns and conventions.

    Shows how to:
    1. Understand resource naming conventions
    2. Work with hierarchical resource structures
    3. Handle resource versioning
    4. Implement resource caching strategies

    Returns:
        Dict containing resource pattern analysis
    """
    logger.info("Analyzing resource URI patterns and conventions...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            resources = await client.list_resources()

            pattern_analysis = {
                "schemes": {},
                "hierarchies": {},
                "naming_patterns": [],
                "template_patterns": [],
            }

            for resource in resources:
                uri = str(resource.uri)

                # Analyze URI scheme
                if "://" in uri:
                    scheme = uri.split("://")[0]
                    pattern_analysis["schemes"][scheme] = (
                        pattern_analysis["schemes"].get(scheme, 0) + 1
                    )

                # Analyze hierarchy (path segments)
                if "://" in uri:
                    path = uri.split("://", 1)[1]
                    segments = path.split("/")
                    depth = len(segments)
                    pattern_analysis["hierarchies"][depth] = (
                        pattern_analysis["hierarchies"].get(depth, 0) + 1
                    )

                # Analyze naming patterns
                if resource.name:
                    pattern_analysis["naming_patterns"].append(
                        {
                            "name": resource.name,
                            "uri": uri,
                            "has_extension": "." in uri.split("/")[-1],
                            "is_config": "config" in uri.lower()
                            or "settings" in uri.lower(),  # [attr-defined]
                            "is_info": "info" in uri.lower() or "status" in uri.lower(),
                        }
                    )

                # Analyze template patterns
                if "{" in str(uri) and "}" in str(uri):
                    import re

                    params = re.findall(r"\{([^}]+)\}", uri)
                    pattern_analysis["template_patterns"].append(
                        {"uri": uri, "parameters": params, "parameter_count": len(params)}
                    )

            logger.info("Resource pattern analysis:")
            logger.info(f"  URI schemes: {list(pattern_analysis['schemes'].keys())}")
            logger.info(f"  Hierarchy depths: {list(pattern_analysis['hierarchies'].keys())}")
            logger.info(f"  Template resources: {len(pattern_analysis['template_patterns'])}")

            return {
                "status": "success",
                "total_resources": len(resources),
                "pattern_analysis": pattern_analysis,
                "recommendations": {
                    "most_common_scheme": max(
                        pattern_analysis["schemes"].items(), key=lambda x: x[1]
                    )[0]
                    if pattern_analysis["schemes"]
                    else None,
                    "average_hierarchy_depth": sum(
                        k * v for k, v in pattern_analysis["hierarchies"].items()
                    )
                    / sum(pattern_analysis["hierarchies"].values())
                    if pattern_analysis["hierarchies"]
                    else 0,
                    "template_usage": len(pattern_analysis["template_patterns"]) / len(resources)
                    if resources
                    else 0,
                },
            }

    except Exception as e:
        logger.error(f"Resource pattern analysis failed: {e}")
        return {"status": "failed", "error": str(e)}


async def main() -> dict[str, Any]:
    """
    Main function demonstrating comprehensive resource operations.

    Returns:
        Dict containing all resource operation demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Resource Operations Examples")
    print("=" * 60)

    results: dict[str, Any] = {}

    try:
        # 1. Resource Discovery
        logger.info("\n1. Resource Discovery and Analysis")
        discovery_result = await discover_resources()
        results["discovery"] = discovery_result

        # 2. Static Resource Access
        logger.info("\n2. Static Resource Access")
        static_result = await access_static_resources()
        results["static_access"] = static_result

        # 3. Templated Resources
        logger.info("\n3. Templated Resource Usage")
        template_result = await demonstrate_templated_resources()
        results["templated_resources"] = template_result

        # 4. Content Types
        logger.info("\n4. Content Type Handling")
        content_result = await demonstrate_content_types()
        results["content_types"] = content_result

        # 5. Resource Patterns
        logger.info("\n5. Resource Pattern Analysis")
        pattern_result = await demonstrate_resource_patterns()
        results["resource_patterns"] = pattern_result

        print("\n" + "=" * 60)
        print("Resource operations examples completed!")
        print("=" * 60)

        return results

    except Exception as e:
        logger.error(f"Resource operations examples failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the resource operations examples
    result = asyncio.run(main())
    print("\nResource Operations Summary:")
    for category, result_data in result.items():
        if isinstance(result_data, dict) and "status" in result_data:
            print(f"  {category}: {result_data['status']}")
        else:
            print(f"  {category}: completed")
