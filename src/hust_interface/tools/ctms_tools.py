from typing import List, Dict, Any
from ..crawlers.ctms_crawler import CtmsCrawler


def register_ctms_tools(mcp):
    """
    Registers CTMS tools into the FastMCP server.
    """
    crawler = CtmsCrawler()

    @mcp.tool(
        name="ctms_get_enrolled_courses",
        description="Lấy danh sách các khóa học / lớp học phần đang tham gia trên hệ thống CTMS (Moodle)."
    )
    async def get_enrolled_courses() -> List[Dict[str, Any]]:
        courses = await crawler.get_enrolled_courses()
        return [c.model_dump(mode="json") for c in courses]

    @mcp.tool(
        name="ctms_get_assignments",
        description="Tra cứu các bài tập, đồ án và hạn nộp (deadline) sắp tới trên CTMS."
    )
    async def get_assignments() -> List[Dict[str, Any]]:
        assignments = await crawler.get_assignments()
        return [a.model_dump(mode="json") for a in assignments]

    @mcp.tool(
        name="ctms_get_upcoming_deadlines",
        description="Lọc và tra cứu danh sách các bài tập / deadline CTMS cần hoàn thành trong vòng N ngày tới (mặc định 7 ngày)."
    )
    async def get_upcoming_deadlines(days_ahead: int = 7) -> List[Dict[str, Any]]:
        assignments = await crawler.get_upcoming_deadlines(days_ahead=days_ahead)
        return [a.model_dump(mode="json") for a in assignments]

    @mcp.tool(
        name="ctms_get_course_materials",
        description="Bóc tách toàn bộ tài liệu học tập, slide bài giảng, giáo trình PDF và file đính kèm của một khóa học trên cổng CTMS/Moodle."
    )
    async def get_course_materials(course_id_or_url: str) -> Dict[str, Any]:
        materials = await crawler.get_course_materials(course_id_or_url=course_id_or_url)
        return materials.model_dump(mode="json")

