from typing import Optional, List, Dict, Any
from ..crawlers.ehust_crawler import EhustCrawler
from ..crawlers.ictsv_crawler import IctsvCrawler
from ..crawlers.ctms_crawler import CtmsCrawler
from ..models.ehust_models import StudentOverview


def register_ehust_tools(mcp):
    """
    Registers eHUST and QLĐT tools into the FastMCP server.
    """
    crawler = EhustCrawler()
    ictsv_crawler = IctsvCrawler()
    ctms_crawler = CtmsCrawler()

    @mcp.tool(
        name="ehust_get_student_profile",
        description="Lấy thông tin sinh viên từ QLĐT / eHUST: Họ tên, MSSV, Lớp, Trường/Viện, Ngành học, Trạng thái học tập."
    )
    async def get_student_profile() -> Dict[str, Any]:
        profile = await crawler.get_student_profile()
        return profile.model_dump(mode="json")

    @mcp.tool(
        name="ehust_get_schedule",
        description="Lấy thời khóa biểu học tập theo học kỳ và tuần học cụ thể (ví dụ: week=1). Nếu không truyền semester, hệ thống sẽ tự động lấy theo học kỳ đang active hiện tại."
    )
    async def get_schedule(semester: Optional[str] = None, week: int = 1) -> Dict[str, Any]:
        schedule = await crawler.get_schedule(semester=semester, week=week)
        return schedule.model_dump(mode="json")

    @mcp.tool(
        name="ehust_get_full_semester_schedule",
        description="Lấy toàn bộ lịch học và tất cả các môn học đã đăng ký trong suốt học kỳ (gồm thông tin tất cả các tuần, ca học, phòng học, giảng viên, điểm danh vắng). Nếu không truyền semester, hệ thống tự động lấy theo học kỳ đang active hiện tại."
    )
    async def get_full_semester_schedule(semester: Optional[str] = None) -> Dict[str, Any]:
        schedule = await crawler.get_full_semester_schedule(semester=semester)
        return schedule.model_dump(mode="json")



    @mcp.tool(
        name="ehust_get_grades",
        description="Tra cứu bảng điểm môn học, điểm quá trình, điểm thi, điểm chữ và GPA/CPA của sinh viên từ cổng đào tạo QLĐT theo học kỳ hoặc kỳ hiện tại."
    )
    async def get_grades(semester: Optional[str] = None) -> Dict[str, Any]:
        grades = await crawler.get_grades(semester=semester)
        return grades.model_dump(mode="json")

    @mcp.tool(
        name="ehust_get_all_semesters_grades",
        description="Tra cứu lịch sử điểm toàn bộ các học kỳ từ trước đến nay, phục vụ phân tích xu hướng học tập."
    )
    async def get_all_semesters_grades() -> List[Dict[str, Any]]:
        all_grades = await crawler.get_all_semesters_grades()
        return [g.model_dump(mode="json") for g in all_grades]

    @mcp.tool(
        name="ehust_get_exam_schedule",
        description="Lấy lịch thi học kỳ (ngày thi, ca thi/kíp thi, phòng thi, số báo danh) của các môn học."
    )
    async def get_exam_schedule(semester: Optional[str] = None) -> List[Dict[str, Any]]:
        exams = await crawler.get_exam_schedule(semester=semester)
        return [ex.model_dump(mode="json") for ex in exams]

    @mcp.tool(
        name="ehust_get_upcoming_exams",
        description="Lọc danh sách các môn thi sắp diễn ra trong vòng N ngày tới (mặc định 30 ngày)."
    )
    async def get_upcoming_exams(days_ahead: int = 30) -> List[Dict[str, Any]]:
        exams = await crawler.get_upcoming_exams(days_ahead=days_ahead)
        return [ex.model_dump(mode="json") for ex in exams]

    @mcp.tool(
        name="ehust_get_tuition",
        description="Tra cứu tình trạng đóng học phí, số tiền phải nộp, số tiền đã đóng và số nợ học phí theo học kỳ."
    )
    async def get_tuition() -> List[Dict[str, Any]]:
        fees = await crawler.get_tuition_fees()
        return [f.model_dump(mode="json") for f in fees]

    @mcp.tool(
        name="ehust_get_registration_plan",
        description="Xem kế hoạch đăng ký học phần / khung chương trình đào tạo gợi ý cho học kỳ kèm tình trạng đã học/chưa học."
    )
    async def get_registration_plan(semester: Optional[str] = None) -> List[Dict[str, Any]]:
        plans = await crawler.get_registration_plan(semester=semester)
        return [p.model_dump(mode="json") for p in plans]

    @mcp.tool(
        name="ehust_get_course_syllabus",
        description="Tra cứu Đề cương chi tiết học phần, Mô tả tóm tắt, Nội dung tóm tắt môn học, Sách giáo trình, Sách tham khảo, Slide bài giảng và file đề cương đính kèm của một mã học phần (ví dụ: 'MI1111', 'IT3040')."
    )
    async def get_course_syllabus(course_id: str) -> Dict[str, Any]:
        syllabus = await crawler.get_course_syllabus(course_id=course_id)
        return syllabus.model_dump(mode="json")

    @mcp.tool(
        name="ehust_check_graduation_eligibility",
        description="Kiểm tra điều kiện tốt nghiệp (tổng số tín chỉ đã tích lũy, CPA tối thiểu, số tín chỉ còn thiếu)."
    )
    async def check_graduation_eligibility() -> Dict[str, Any]:

        result = await crawler.check_graduation_eligibility()
        return result.model_dump(mode="json")

    @mcp.tool(
        name="hust_summarize_student",
        description="Tổng hợp toàn diện bức tranh sinh viên HUST: Thông tin cá nhân, CPA, GPA, ĐRL, Lịch thi sắp tới, Học phí nợ, Cảnh báo học tập (All-in-one summary)."
    )
    async def summarize_student() -> Dict[str, Any]:
        # 1. Profile & Grades
        try:
            profile = await crawler.get_student_profile()
        except Exception:
            profile = None

        try:
            grades = await crawler.get_grades()
        except Exception:
            grades = None

        # 2. DRL from CTSV
        drl_val = None
        drl_rank = None
        try:
            drl = await ictsv_crawler.get_training_points()
            drl_val = drl.total_point
            drl_rank = drl.rank
        except Exception:
            pass

        # 3. Upcoming exams
        upcoming_exams = []
        try:
            upcoming_exams = await crawler.get_upcoming_exams(days_ahead=30)
        except Exception:
            pass

        # 4. Tuition
        tuition_debt = 0.0
        try:
            fees = await crawler.get_tuition_fees()
            tuition_debt = sum(f.debt_amount for f in fees)
        except Exception:
            pass

        # 5. Deadlines from CTMS
        upcoming_deadlines = []
        try:
            upcoming_deadlines = await ctms_crawler.get_upcoming_deadlines(days_ahead=7)
        except Exception:
            pass

        accumulated_credits = grades.accumulated_credits if grades and grades.accumulated_credits else (
            sum(c.credits for c in grades.courses if c.letter_grade not in ("F", None)) if grades else 0.0
        )

        overview = StudentOverview(
            student_id=profile.student_id if profile else "Unknown",
            full_name=profile.full_name if profile else "Sinh viên HUST",
            class_name=profile.class_name if profile else None,
            cpa=grades.cpa if grades else None,
            gpa_latest=grades.gpa if grades else None,
            training_points_latest=drl_val,
            drl_rank=drl_rank,
            accumulated_credits=accumulated_credits,
            tuition_debt=tuition_debt,
            upcoming_exams_count=len(upcoming_exams),
            upcoming_deadlines_count=len(upcoming_deadlines),
            academic_warning_level=grades.academic_warning_level if grades else None
        )
        return overview.model_dump(mode="json")

    @mcp.tool(
        name="ehust_get_semesters",
        description="Lấy danh sách tất cả các học kỳ học tập của ĐHBK Hà Nội từ API (mã kỳ, tên học kỳ, ngày bắt đầu/kết thúc, tuần học hiện tại, đợt mở đăng ký học phần, học kỳ hiện tại)."
    )
    async def get_semesters() -> List[Dict[str, Any]]:
        semesters = await crawler.get_semesters()
        return [s.model_dump(mode="json") for s in semesters]

