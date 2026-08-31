from typing import Optional, List, Dict, Any
from ..crawlers.ictsv_crawler import IctsvCrawler


def register_ictsv_tools(mcp):
    """
    Registers iCTSV tools into the FastMCP server.
    """
    crawler = IctsvCrawler()

    @mcp.tool(
        name="ictsv_get_training_points",
        description="Lấy điểm rèn luyện (ĐRL) sinh viên HUST từ iCTSV theo học kỳ (ví dụ: '2023.2', '2024.1') hoặc học kỳ hiện tại kèm chi tiết các nhóm tiêu chí."
    )
    async def get_training_points(semester: Optional[str] = None) -> Dict[str, Any]:
        result = await crawler.get_training_points(semester=semester)
        return result.model_dump(mode="json")

    @mcp.tool(
        name="ictsv_get_drl_history",
        description="Lấy lịch sử Điểm rèn luyện (ĐRL) qua các học kỳ trước đây từ iCTSV."
    )
    async def get_drl_history() -> List[Dict[str, Any]]:
        history = await crawler.get_drl_history()
        return [h.model_dump(mode="json") for h in history]

    @mcp.tool(
        name="ictsv_get_student_contact",
        description="Lấy thông tin liên hệ sinh viên từ iCTSV: Số điện thoại, email cá nhân, địa chỉ thường trú, tạm trú, thông tin liên hệ khẩn cấp."
    )
    async def get_student_contact() -> Dict[str, Any]:
        contact = await crawler.get_student_contact()
        return contact.model_dump(mode="json")

    @mcp.tool(
        name="ictsv_get_activities",
        description="Lấy danh sách hoạt động ngoại khóa, sự kiện CTSV. Hỗ trợ lọc theo số điểm ĐRL tối thiểu (min_point) hoặc nhóm tiêu chí (criterion_group)."
    )
    async def get_activities(
        page: int = 1,
        page_size: int = 20,
        status_filter: str = "all",
        min_point: Optional[float] = None,
        criterion_group: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        activities = await crawler.get_activities(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            min_point=min_point,
            criterion_group=criterion_group
        )
        return [act.model_dump(mode="json") for act in activities]

    @mcp.tool(
        name="ictsv_register_activity",
        description="Đăng ký tham gia một hoạt động ngoại khóa trên iCTSV bằng mã/ID hoạt động."
    )
    async def register_activity(activity_id: str) -> Dict[str, Any]:
        res = await crawler.register_activity(activity_id=activity_id)
        return res.model_dump(mode="json")

    @mcp.tool(
        name="ictsv_get_my_activities",
        description="Lấy danh sách các hoạt động ngoại khóa mà sinh viên đã đăng ký tham gia trên iCTSV."
    )
    async def get_my_activities() -> List[Dict[str, Any]]:
        activities = await crawler.get_my_registered_activities()
        return [act.model_dump(mode="json") for act in activities]

    @mcp.tool(
        name="ictsv_get_notifications",
        description="Lấy danh sách thông báo mới nhất từ Ban CTSV trên cổng iCTSV."
    )
    async def get_notifications(page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        notifs = await crawler.get_notifications(page=page, page_size=page_size)
        return [n.model_dump(mode="json") for n in notifs]

    @mcp.tool(
        name="ictsv_search_jobs",
        description="Tìm kiếm cơ hội việc làm, thực tập doanh nghiệp dành riêng cho sinh viên HUST từ hệ thống HUST Career."
    )
    async def search_jobs(keyword: Optional[str] = None, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        jobs = await crawler.search_jobs(keyword=keyword, page=page, page_size=page_size)
        return [j.model_dump(mode="json") for j in jobs]
