import pytest
import asyncio
from hust_interface.server import create_mcp_server


def test_mcp_server_initialization():
    mcp = create_mcp_server()
    assert mcp.name == "hust-interface"

    # Verify registered tool names
    # FastMCP stores tools in _tool_manager._tools or async tool definitions
    tools = asyncio.run(mcp.list_tools())
    tool_names = [t.name for t in tools]

    expected_tools = [
        "hust_check_auth_status",
        "hust_set_token",
        "hust_login_sso",
        "hust_clear_session",
        "ictsv_get_training_points",
        "ictsv_get_activities",
        "ictsv_register_activity",
        "ictsv_get_my_activities",
        "ictsv_get_notifications",
        "ehust_get_student_profile",
        "ehust_get_schedule",
        "ehust_get_grades",
        "ehust_get_exam_schedule",
        "ctms_get_enrolled_courses",
        "ctms_get_assignments",
    ]

    for tool in expected_tools:
        assert tool in tool_names, f"Expected tool '{tool}' not found in MCP server tool registry"


def test_mcp_prompts_and_resources():
    mcp = create_mcp_server()
    prompts = asyncio.run(mcp.list_prompts())
    prompt_names = [p.name for p in prompts]
    assert "daily_student_briefing" in prompt_names
    assert "academic_evaluation" in prompt_names

    resources = asyncio.run(mcp.list_resources())
    resource_uris = [str(r.uri) for r in resources]
    assert any("hust://auth/status" in uri for uri in resource_uris)
