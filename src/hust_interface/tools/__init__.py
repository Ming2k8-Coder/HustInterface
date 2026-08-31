from .auth_tools import register_auth_tools
from .ictsv_tools import register_ictsv_tools
from .ehust_tools import register_ehust_tools
from .ctms_tools import register_ctms_tools


def register_all_tools(mcp):
    """
    Registers all HUST tools (Auth, iCTSV, eHUST/QLĐT, CTMS) into the MCP Server.
    """
    register_auth_tools(mcp)
    register_ictsv_tools(mcp)
    register_ehust_tools(mcp)
    register_ctms_tools(mcp)
