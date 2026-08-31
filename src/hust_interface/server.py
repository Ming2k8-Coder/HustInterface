import json
from loguru import logger
from mcp.server import MCPServer

from .config import settings
from .core.session_manager import session_manager
from .tools import register_all_tools


def create_mcp_server() -> MCPServer:
    """
    Creates and configures the HUST Interface MCP Server instance.
    """
    mcp = MCPServer(
        name=settings.MCP_SERVER_NAME,
        instructions="MCP Server cung cấp giao diện tương tác dữ liệu sinh viên Đại học Bách khoa Hà Nội (HUST): iCTSV (Điểm rèn luyện, hoạt động ngoại khóa, việc làm), eHUST/QLĐT (Thời khóa biểu, bảng điểm, lịch thi, học phí, tốt nghiệp) và CTMS (Deadline bài tập).",
        version=settings.MCP_SERVER_VERSION,
    )

    # Register all Tools (Auth, iCTSV, eHUST, CTMS)
    register_all_tools(mcp)

    # Register MCP Resources for quick read-only access
    @mcp.resource("hust://auth/status")
    def resource_auth_status() -> str:
        """Returns JSON representation of current authentication status for all services."""
        return json.dumps(session_manager.get_auth_summary(), indent=2, ensure_ascii=False)

    # Register MCP Prompts for AI reasoning
    @mcp.prompt("daily_student_briefing")
    def prompt_daily_briefing() -> str:
        """Tạo bản tóm tắt lịch học hôm nay, hạn nộp bài tập CTMS và các hoạt động CTSV cần lưu ý."""
        return (
            "Hãy kiểm tra thời khóa biểu tuần hiện tại (ehust_get_schedule), "
            "hạn nộp bài tập CTMS sắp tới (ctms_get_upcoming_deadlines), "
            "và điểm rèn luyện iCTSV (ictsv_get_training_points). "
            "Sau đó tổng hợp thành bản tin tóm tắt ngắn gọn, rõ ràng cho sinh viên HUST."
        )

    @mcp.prompt("academic_evaluation")
    def prompt_academic_evaluation() -> str:
        """Đánh giá chi tiết kết quả học tập và rèn luyện của sinh viên HUST."""
        return (
            "Hãy lấy bảng điểm (ehust_get_grades) và điểm rèn luyện (ictsv_get_training_points). "
            "Phân tích GPA/CPA, các môn cần cải thiện, tình trạng học phí/cảnh báo học tập và đề xuất kế hoạch học tập."
        )

    @mcp.prompt("weekly_study_planner")
    def prompt_weekly_study_planner() -> str:
        """Lập kế hoạch học tập chi tiết trong tuần."""
        return (
            "Hãy kiểm tra thời khóa biểu tuần (ehust_get_schedule), "
            "các lịch thi sắp diễn ra (ehust_get_upcoming_exams) và deadline bài tập CTMS (ctms_get_upcoming_deadlines). "
            "Lập một kế hoạch học tập và ôn thi từng ngày chi tiết, tối ưu thời gian tự học cho sinh viên."
        )

    @mcp.prompt("academic_risk_alert")
    def prompt_academic_risk_alert() -> str:
        """Kiểm tra và cảnh báo rủi ro học thuật (GPA thấp, thiếu ĐRL, nợ học phí, nguy cơ cảnh cáo học tập)."""
        return (
            "Hãy gọi tool hust_summarize_student để có cái nhìn tổng quan. "
            "Kiểm tra CPA/GPA, ĐRL, tình trạng nợ học phí (ehust_get_tuition) và nguy cơ cảnh cáo học tập. "
            "Đưa ra các cảnh báo đỏ và hướng dẫn khắc phục cụ thể cho sinh viên HUST."
        )

    return mcp


mcp_server = create_mcp_server()
