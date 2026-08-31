from typing import Optional, Dict, Any
from ..core.session_manager import session_manager
from ..auth.manual_auth import ManualAuthenticator
from ..auth.sso_authenticator import HustSSOAuthenticator


def register_auth_tools(mcp):
    """
    Registers Authentication & Session Management tools into the FastMCP server.
    """

    @mcp.tool(
        name="hust_check_auth_status",
        description="Kiểm tra trạng thái xác thực và phiên làm việc hiện tại của các dịch vụ HUST (iCTSV, eHUST, CTMS)."
    )
    def check_auth_status() -> Dict[str, Any]:
        return session_manager.get_auth_summary()

    @mcp.tool(
        name="hust_set_token",
        description="Cấu hình Token hoặc Cookie thủ công cho dịch vụ HUST (service_name: 'ictsv', 'ehust', 'ctms')."
    )
    def set_token(service_name: str, token_or_cookie: str, student_id: Optional[str] = None) -> str:
        s_name = service_name.lower().strip()
        if s_name == "ictsv":
            ManualAuthenticator.set_ictsv_token(token_or_cookie)
            return "Đã cập nhật Bearer Token cho iCTSV thành công!"
        elif s_name in ["ehust", "qldt"]:
            ManualAuthenticator.set_ehust_cookie(token_or_cookie, student_id=student_id)
            return "Đã cập nhật Session Cookie cho eHUST/QLĐT thành công!"
        elif s_name == "ctms":
            ManualAuthenticator.set_ctms_cookie(token_or_cookie, student_id=student_id)
            return "Đã cập nhật Moodle Session Cookie cho CTMS thành công!"
        else:
            return f"Không hỗ trợ dịch vụ '{service_name}'. Vui lòng chọn một trong: ictsv, ehust, ctms."

    @mcp.tool(
        name="hust_login_sso",
        description="Tự động đăng nhập qua HUST Microsoft SSO bằng Playwright Headless Browser và lưu token/cookie vào cache."
    )
    async def login_sso(
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = True
    ) -> Dict[str, Any]:
        authenticator = HustSSOAuthenticator(email=email, password=password, headless=headless)
        results = await authenticator.login_all()
        return {
            "results": results,
            "summary": session_manager.get_auth_summary()
        }

    @mcp.tool(
        name="hust_clear_session",
        description="Xóa phiên làm việc / Token đã lưu cho một dịch vụ cụ thể hoặc tất cả (service_name: 'ictsv', 'ehust', 'ctms', hoặc 'all')."
    )
    def clear_session(service_name: str = "all") -> str:
        s_name = service_name.lower().strip()
        if s_name == "all":
            session_manager.clear_all()
            return "Đã xóa toàn bộ token và cookie của tất cả các dịch vụ HUST."
        else:
            session_manager.clear_service_session(s_name)
            return f"Đã xóa phiên làm việc của dịch vụ {s_name}."
