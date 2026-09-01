from typing import Optional, Dict, Any
from ..core.session_manager import session_manager
from ..auth.manual_auth import ManualAuthenticator


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
        description="Tự động đăng nhập trực tiếp các cổng HUST (eHUST, iCTSV) qua Direct HTTP API/Form POST và lưu token/cookie vào cache."
    )
    async def login_sso(
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        from ..auth.direct_http_auth import DirectHttpAuthenticator
        authenticator = DirectHttpAuthenticator(email=email, password=password)
        results = await authenticator.login_all_direct()
        return {
            "results": results,
            "summary": session_manager.get_auth_summary()
        }


    @mcp.tool(
        name="hust_reauthenticate",
        description="Thực hiện tái xác thực tự động (Auto-Reauthenticate) cho một dịch vụ cụ thể hoặc tất cả dịch vụ (service_name: 'ehust', 'ictsv', 'all') bằng thông tin tài khoản đã cấu hình."
    )
    async def reauthenticate(service_name: str = "all") -> Dict[str, Any]:
        from ..crawlers.ehust_crawler import EhustCrawler
        from ..crawlers.ictsv_crawler import IctsvCrawler
        results = {}
        s_name = service_name.lower().strip()
        if s_name in ["ehust", "qldt", "all"]:
            crawler = EhustCrawler()
            ok = await crawler.auto_reauthenticate()
            results["ehust"] = "Thành công" if ok else "Thất bại (cần HUST_EMAIL & HUST_PASSWORD)"
        if s_name in ["ictsv", "all"]:
            ictsv_crawler = IctsvCrawler()
            ok = await ictsv_crawler.auto_reauthenticate()
            results["ictsv"] = "Thành công" if ok else "Thất bại (cần HUST_EMAIL & HUST_PASSWORD)"
        
        return {
            "reauthentication_results": results,
            "current_auth_status": session_manager.get_auth_summary()
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
