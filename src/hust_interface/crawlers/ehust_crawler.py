import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger

from ..config import settings
from ..core.http_client import AsyncHustHttpClient
from .base import BaseCrawler

from ..models.ehust_models import (
    StudentProfile,
    ScheduleClassItem,
    WeeklySchedule,
    FullSemesterSchedule,
    GradeItem,
    SemesterGradeSummary,
    ExamScheduleItem,
    TuitionFeeItem,
    TextbookItem,
    CourseSyllabusDetail,
    CourseRegistrationPlanItem,
    GraduationEligibility,
    StudentOverview,
    SemesterInfo,
)


class EhustCrawler(BaseCrawler):
    """
    Crawler for eHUST & QLĐT portals (https://qldt.hust.edu.vn / https://ehust.edu.vn).
    Extracts:
    - Weekly Course Schedule (Thời khóa biểu)
    - Transcript & Grades (Điểm thi & Điểm quá trình)
    - Exam Schedule & Upcoming Exams (Lịch thi học kỳ)
    - Tuition Fee status (Học phí & nợ)
    - Course Registration Plan (Kế hoạch học tập)
    - Graduation Eligibility Check (Điều kiện tốt nghiệp)
    - Student Profile Info
    """

    def __init__(self):
        super().__init__(service_name="ehust", base_url=settings.QLDT_BASE_URL)

    async def get_student_profile(self) -> StudentProfile:
        """
        Extract student profile information from QLĐT / eHUST portal.
        """
        self.require_auth()
        async with self.get_http_client() as client:
            soup = await client.get_soup("/Student/Profile")
            
            student_id = ""
            full_name = ""
            class_name = None
            school_faculty = None
            major = None
            program = None
            cohort = None

            # Parse standard table / div profile format
            for row in soup.find_all("tr"):
                text = row.get_text(separator=" ", strip=True)
                if "Mã sinh viên" in text or "MSSV" in text:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        student_id = cols[1].get_text(strip=True)
                elif "Họ và tên" in text or "Họ tên" in text:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        full_name = cols[1].get_text(strip=True)
                elif "Lớp" in text:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        class_name = cols[1].get_text(strip=True)
                elif "Khoa" in text or "Viện" in text or "Trường" in text:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        school_faculty = cols[1].get_text(strip=True)
                elif "Ngành" in text:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        major = cols[1].get_text(strip=True)

            sess = self.get_session()
            if not student_id and sess and sess.student_id:
                student_id = sess.student_id
            if not full_name and sess:
                if sess.student_name:
                    full_name = sess.student_name
                elif sess.cookies and "token" in sess.cookies:
                    try:
                        import jwt
                        claims = jwt.decode(sess.cookies["token"], options={"verify_signature": False})
                        email_val = claims.get("email")
                        if email_val:
                            # e.g. minh.nt2611037@sis.hust.edu.vn -> MSSV: 202611037
                            digits_match = re.search(r"(\d{6,9})", email_val)
                            if digits_match and not student_id:
                                raw_d = digits_match.group(1)
                                student_id = f"20{raw_d}" if len(raw_d) == 7 and raw_d.startswith("26") else raw_d
                    except Exception:
                        pass

            email_addr = sess.cookies.get("token") if sess and sess.cookies else None
            user_email = None
            if email_addr:
                try:
                    import jwt
                    claims = jwt.decode(email_addr, options={"verify_signature": False})
                    user_email = claims.get("email")
                except Exception:
                    pass

            sess = self.get_session()
            if not student_id and sess and sess.student_id:
                student_id = sess.student_id
            if not full_name and sess and sess.student_name:
                full_name = sess.student_name

            if not student_id and not full_name:
                raise ValueError("Không thể lấy thông tin sinh viên từ eHUST. Vui lòng kiểm tra lại phiên đăng nhập.")

            return StudentProfile(
                student_id=student_id or "",
                full_name=full_name or "",
                email=user_email,
                class_name=class_name,
                school_faculty=school_faculty,
                major=major,
                program=program,
                cohort=cohort
            )




    async def get_current_active_semester(self) -> str:
        """
        Helper method to retrieve the currently active academic semester ID (e.g. '2026.1' or '2024.1').
        """
        try:
            semesters = await self.get_semesters()
            for s in semesters:
                if s.is_current:
                    # Convert '20261' to '2026.1' if necessary
                    sid = s.id
                    if len(sid) == 5 and sid[4] in ("1", "2", "3"):
                        return f"{sid[:4]}.{sid[4]}"
                    return sid
        except Exception as e:
            logger.warning(f"Could not auto-resolve active semester: {e}")
        return "2024.1"

    async def get_schedule(self, semester: Optional[str] = None, week: int = 1) -> WeeklySchedule:
        """
        Extract weekly class schedule from QLĐT (/Schedule/StudentSchedule) or eHUST (/students/learn/timetable).
        If semester is not specified, automatically fetches the currently active semester.
        """
        self.require_auth()
        if not semester:
            semester = await self.get_current_active_semester()

        async with self.get_http_client() as client:
            # 1. Try QLĐT / eHUST timetable URL
            params = {"semester": semester, "week": week}
            soup = await client.get_soup("/Schedule/StudentSchedule", params=params)
            if not soup.find("table"):
                # Fallback to direct eHUST timetable portal
                async with AsyncHustHttpClient(base_url=settings.EHUST_BASE_URL) as ehust_client:
                    try:
                        soup = await ehust_client.get_soup("/students/learn/timetable")
                    except Exception:

                        pass

            classes: List[ScheduleClassItem] = []
            table = soup.find("table", {"id": "tblStudentSchedule"}) or soup.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for r in rows:
                    cols = r.find_all("td")
                    if len(cols) >= 9:
                        # e.hust.edu.vn format: ["STT", "Học phần", "Hình thức giảng dạy", "Điểm", "Lịch học", "Vắng", "Giảng viên", "Trạng thái thi", "Phản hồi"]
                        raw_course = cols[1].get_text(separator=" ", strip=True)
                        course_id_match = re.search(r"([A-Z]{2,4}\d{4})", raw_course)
                        cid = course_id_match.group(1) if course_id_match else raw_course
                        cname = raw_course.replace(cid, "").strip(" -:") if course_id_match else raw_course
                        
                        teaching_type = cols[2].get_text(strip=True)
                        schedule_txt = cols[4].get_text(separator=" ", strip=True)
                        absence_str = re.sub(r"[^\d]", "", cols[5].get_text(strip=True))
                        absence_cnt = int(absence_str) if absence_str else 0
                        gv = cols[6].get_text(strip=True)
                        exam_st = cols[7].get_text(strip=True)
                        feedback = cols[8].get_text(strip=True) if len(cols) > 8 else None

                        classes.append(
                            ScheduleClassItem(
                                course_id=cid,
                                course_name=cname or cid,
                                class_id="Class",
                                teaching_type=teaching_type,
                                day_of_week=2,
                                day_name="Theo lịch",
                                time_range=schedule_txt or "Xem chi tiết",
                                room="Giảng đường",
                                lecturer=gv,
                                absence_count=absence_cnt,
                                exam_status=exam_st,
                                student_feedback=feedback
                            )
                        )
                    elif len(cols) >= 7:
                        # QLĐT standard format
                        course_id = cols[0].get_text(strip=True)
                        course_name = cols[1].get_text(strip=True)
                        class_id = cols[2].get_text(strip=True)
                        day_str = cols[3].get_text(strip=True)
                        time_str = cols[4].get_text(strip=True)
                        room = cols[5].get_text(strip=True)
                        lecturer = cols[6].get_text(strip=True) if len(cols) > 6 else ""

                        day_of_week = 2
                        if "Hai" in day_str or "2" in day_str:
                            day_of_week = 2
                        elif "Ba" in day_str or "3" in day_str:
                            day_of_week = 3
                        elif "Tư" in day_str or "4" in day_str:
                            day_of_week = 4
                        elif "Năm" in day_str or "5" in day_str:
                            day_of_week = 5
                        elif "Sáu" in day_str or "6" in day_str:
                            day_of_week = 6
                        elif "Bảy" in day_str or "7" in day_str:
                            day_of_week = 7
                        elif "Chủ Nhật" in day_str or "CN" in day_str or "8" in day_str:
                            day_of_week = 8

                        classes.append(
                            ScheduleClassItem(
                                course_id=course_id,
                                course_name=course_name,
                                class_id=class_id,
                                day_of_week=day_of_week,
                                day_name=day_str,
                                start_period=1,
                                end_period=3,
                                time_range=time_str,
                                room=room,
                                weeks=[week],
                                lecturer=lecturer
                            )
                        )

            return WeeklySchedule(
                semester=semester,
                week_number=week,
                classes=classes
            )

    async def get_full_semester_schedule(self, semester: Optional[str] = None) -> FullSemesterSchedule:
        """
        Extract full semester class schedule containing all enrolled courses and their full schedule across all weeks.
        Combines and aggregates classes from eHUST timetable and QLĐT.
        If semester is not provided, automatically uses the currently active semester.
        """
        self.require_auth()
        if not semester:
            semester = await self.get_current_active_semester()

        classes: List[ScheduleClassItem] = []
        sess = self.get_session()
        token = sess.cookies.get("token") if sess and sess.cookies else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 1. Query official encrypted student-classes API (https://student.hust.edu.vn/api/v2/timetables/student-classes)
        try:
            from ..core.crypto_helper import TimetableCryptoHelper
            enc_payload = TimetableCryptoHelper.encrypt_payload({"semester": str(semester)})
            
            async with AsyncHustHttpClient(base_url="https://student.hust.edu.vn", default_headers=headers) as api_client:
                res = await api_client.get(f"/api/v2/timetables/student-classes?payload={enc_payload}")
                if res.status_code == 200:
                    data = res.json()
                    raw_items = []
                    if isinstance(data, dict) and "payload" in data:
                        raw_items = TimetableCryptoHelper.decrypt_payload(data["payload"])
                    elif isinstance(data, list):
                        raw_items = data

                    for item in raw_items:
                        c_code = item.get("courseId") or item.get("courseCode") or ""
                        c_name = item.get("courseName") or c_code
                        class_id = str(item.get("classId") or item.get("classCode") or "")
                        t_type = item.get("classType") or item.get("teachingType") or "Offline"
                        
                        # Extract schedule details from timePlaces or calendarInfo
                        time_places = item.get("timePlaces", [])
                        cal_info = item.get("calendarInfo", "")
                        
                        time_str = "Chưa xếp lịch"
                        room_str = "Giảng đường"
                        weeks_list = []
                        day_of_week = 2

                        if time_places and isinstance(time_places, list) and len(time_places) > 0:
                            tp = time_places[0]
                            day_of_week = int(tp.get("day", 2))
                            room_str = str(tp.get("place", "Giảng đường"))
                            weeks_list = tp.get("weeks", [])
                            f_time = tp.get("from", "")
                            t_time = tp.get("to", "")
                            time_str = f"Thứ {day_of_week} Tiết {f_time}-{t_time} [{room_str}]"
                        elif cal_info:
                            time_str = cal_info

                        classes.append(
                            ScheduleClassItem(
                                course_id=c_code,
                                course_name=c_name,
                                class_id=class_id,
                                teaching_type=t_type,
                                day_of_week=day_of_week,
                                day_name=f"Thứ {day_of_week}" if day_of_week < 8 else "Chủ Nhật",
                                time_range=time_str,
                                room=room_str,
                                weeks=weeks_list,
                                lecturer=item.get("lecturerName") or "Chưa phân công",
                                absence_count=0,
                                exam_status="Đủ điều kiện"
                            )
                        )
        except Exception as e:
            logger.warning(f"Encrypted student-classes API fetch error: {e}")

        # 2. Fallback to static HTML parse if API yielded empty
        if not classes:
            try:
                async with AsyncHustHttpClient(base_url=settings.EHUST_BASE_URL) as ehust_client:
                    soup = await ehust_client.get_soup("/students/learn/timetable")
            except Exception:
                soup = None



        # Parse extracted table rows from soup
        if soup:
            tbody = soup.find("tbody") or soup
            rows = tbody.find_all("tr", class_=re.compile(r"ant-table-row")) or tbody.find_all("tr")
            for r in rows:
                cols = r.find_all(["td", "th"])
                if not cols or r.find_parent("thead"):
                    continue
                if len(cols) >= 6:
                    # e.hust.edu.vn timetable format: [STT, Học phần, Hình thức, Điểm, Lịch học, Vắng, Giảng viên, ...]
                    raw_course = cols[1].get_text(separator="\n", strip=True)
                    if not raw_course or "Không có lịch học" in raw_course:
                        continue
                    
                    lines = [line.strip() for line in raw_course.split("\n") if line.strip()]
                    cname = lines[0] if lines else ""
                    second_line = lines[1] if len(lines) > 1 else ""

                    cid_match = re.search(r"([A-Z]{2,4}\d{4})", second_line or raw_course)
                    cid = cid_match.group(1) if cid_match else raw_course
                    uid_match = re.search(r"(\d{5,7})", second_line or raw_course)
                    class_id = uid_match.group(1) if uid_match else cid

                    teaching_type = cols[2].get_text(strip=True) if len(cols) > 2 else "Offline"
                    schedule_txt = cols[4].get_text(separator=" | ", strip=True) if len(cols) > 4 else ""
                    absence_str = re.sub(r"[^\d]", "", cols[5].get_text(strip=True)) if len(cols) > 5 else "0"
                    absence_cnt = int(absence_str) if absence_str else 0
                    gv = cols[6].get_text(separator=" ", strip=True) if len(cols) > 6 else ""
                    exam_st = cols[7].get_text(strip=True) if len(cols) > 7 else None
                    feedback = cols[8].get_text(strip=True) if len(cols) > 8 else None

                    # Extract day of week from schedule string (e.g. "Chiều T5, Tuần: 3-19" -> 5)
                    day_of_week = 2
                    day_match = re.search(r"T([2-7])", schedule_txt)
                    if day_match:
                        day_of_week = int(day_match.group(1))
                    elif "CN" in schedule_txt or "Chủ Nhật" in schedule_txt:
                        day_of_week = 8

                    # Extract room (e.g. "D5-101" or "TC-401")
                    room_match = re.search(r"([A-Z]\d+-\d+|TC-\d+)", schedule_txt)
                    room_val = room_match.group(1) if room_match else "Giảng đường"

                    # Extract weeks (e.g. "3-19" -> [3, 4, ..., 19])
                    weeks_match = re.search(r"Tuần:\s*(\d+)\s*-\s*(\d+)", schedule_txt)
                    weeks_list = []
                    if weeks_match:
                        start_w, end_w = int(weeks_match.group(1)), int(weeks_match.group(2))
                        weeks_list = list(range(start_w, end_w + 1))

                    classes.append(
                        ScheduleClassItem(
                            course_id=cid,
                            course_name=cname or cid,
                            class_id=class_id,
                            teaching_type=teaching_type or "Offline",
                            day_of_week=day_of_week,
                            day_name=f"Thứ {day_of_week}" if day_of_week < 8 else "Chủ Nhật",
                            time_range=schedule_txt or "Chưa xếp lịch",
                            room=room_val,
                            weeks=weeks_list,
                            lecturer=gv or "Chưa phân công",
                            absence_count=absence_cnt,
                            exam_status=exam_st or "Đủ điều kiện",
                            student_feedback=feedback
                        )
                    )

        return FullSemesterSchedule(
            semester=semester,
            total_courses=len(classes),
            classes=classes
        )



    async def get_grades(self, semester: Optional[str] = None) -> SemesterGradeSummary:
        """
        Extract academic grades and CPA/GPA.
        """
        self.require_auth()
        async with self.get_http_client() as client:
            params = {}
            if semester:
                params["semester"] = semester
            soup = await client.get_soup("/Grade/StudentGrade", params=params)

            courses: List[GradeItem] = []
            gpa = None
            cpa = None

            table = soup.find("table", {"id": "tblStudentGrade"}) or soup.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for r in rows:
                    cols = r.find_all("td")
                    if len(cols) >= 6:
                        cid = cols[0].get_text(strip=True)
                        cname = cols[1].get_text(strip=True)
                        try:
                            credits_val = float(cols[2].get_text(strip=True))
                        except ValueError:
                            credits_val = 0.0

                        midterm_str = cols[3].get_text(strip=True)
                        final_str = cols[4].get_text(strip=True)
                        letter = cols[5].get_text(strip=True)

                        midterm_val = float(midterm_str) if midterm_str.replace(".", "", 1).isdigit() else None
                        final_val = float(final_str) if final_str.replace(".", "", 1).isdigit() else None

                        courses.append(
                            GradeItem(
                                course_id=cid,
                                course_name=cname,
                                credits=credits_val,
                                semester=semester or "Current",
                                midterm_score=midterm_val,
                                final_score=final_val,
                                letter_grade=letter
                            )
                        )

            for span in soup.find_all(["span", "div", "td", "p"]):
                text = span.get_text(strip=True)
                if "GPA:" in text or "Điểm TB học kỳ:" in text:
                    match = re.search(r"(\d+\.\d+)", text)
                    if match:
                        gpa = float(match.group(1))
                if "CPA:" in text or "Điểm TB tích lũy:" in text:
                    match = re.search(r"(\d+\.\d+)", text)
                    if match:
                        cpa = float(match.group(1))

            return SemesterGradeSummary(
                semester=semester or "All",
                gpa=gpa,
                cpa=cpa,
                courses=courses
            )

    async def get_all_semesters_grades(self) -> List[SemesterGradeSummary]:
        """
        Fetch grades across all semesters.
        """
        self.require_auth()
        semesters = ["2024.1", "2023.2", "2023.1", "2022.2", "2022.1", "2021.2", "2021.1"]
        summaries: List[SemesterGradeSummary] = []
        for sem in semesters:
            try:
                g = await self.get_grades(semester=sem)
                if g.courses or g.gpa is not None:
                    summaries.append(g)
            except Exception:
                continue
        if not summaries:
            # Return current summary if specific semesters are empty
            summaries.append(await self.get_grades())
        return summaries

    async def get_exam_schedule(self, semester: Optional[str] = None) -> List[ExamScheduleItem]:
        """
        Extract exam schedule (Lịch thi học kỳ).
        """
        self.require_auth()
        async with self.get_http_client() as client:
            params = {}
            if semester:
                params["semester"] = semester
            soup = await client.get_soup("/Exam/StudentExamSchedule", params=params)

            exams: List[ExamScheduleItem] = []
            table = soup.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for r in rows:
                    cols = r.find_all("td")
                    if len(cols) >= 6:
                        exams.append(
                            ExamScheduleItem(
                                course_id=cols[0].get_text(strip=True),
                                course_name=cols[1].get_text(strip=True),
                                exam_date=cols[2].get_text(strip=True),
                                exam_shift=cols[3].get_text(strip=True),
                                exam_time=cols[3].get_text(strip=True),
                                room=cols[4].get_text(strip=True),
                                seat_number=cols[5].get_text(strip=True) if len(cols) > 5 else None
                            )
                        )
            return exams

    async def get_upcoming_exams(self, days_ahead: int = 30) -> List[ExamScheduleItem]:
        """
        Filter upcoming exams within the next N days.
        """
        exams = await self.get_exam_schedule()
        now = datetime.now()
        upcoming: List[ExamScheduleItem] = []

        for ex in exams:
            try:
                # Parse DD/MM/YYYY or YYYY-MM-DD
                d_str = ex.exam_date.strip()
                if "/" in d_str:
                    exam_dt = datetime.strptime(d_str, "%d/%m/%Y")
                elif "-" in d_str:
                    exam_dt = datetime.strptime(d_str, "%Y-%m-%d")
                else:
                    upcoming.append(ex)
                    continue

                diff = (exam_dt.date() - now.date()).days
                if 0 <= diff <= days_ahead:
                    upcoming.append(ex)
            except Exception:
                upcoming.append(ex)

        return upcoming

    async def get_tuition_fees(self) -> List[TuitionFeeItem]:
        """
        Extract tuition payment details and debt status (/Tuition/StudentTuition).
        """
        self.require_auth()
        async with self.get_http_client() as client:
            soup = await client.get_soup("/Tuition/StudentTuition")
            fees: List[TuitionFeeItem] = []

            table = soup.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for r in rows:
                    cols = r.find_all("td")
                    if len(cols) >= 4:
                        sem = cols[0].get_text(strip=True)
                        amount_str = re.sub(r"[^\d]", "", cols[1].get_text(strip=True))
                        paid_str = re.sub(r"[^\d]", "", cols[2].get_text(strip=True))
                        debt_str = re.sub(r"[^\d]", "", cols[3].get_text(strip=True)) if len(cols) > 3 else "0"

                        amount = float(amount_str) if amount_str else 0.0
                        paid = float(paid_str) if paid_str else 0.0
                        debt = float(debt_str) if debt_str else max(0.0, amount - paid)
                        status = "Đã hoàn thành" if debt <= 0 else "Còn nợ học phí"

                        fees.append(
                            TuitionFeeItem(
                                semester=sem,
                                tuition_amount=amount,
                                paid_amount=paid,
                                debt_amount=debt,
                                payment_status=status
                            )
                        )
            return fees



    async def get_course_syllabus(self, course_id_or_uid: str) -> CourseSyllabusDetail:
        """
        Extract complete course syllabus, distribution, bilingual description/outline, textbooks, multiple slides, and syllabus files dynamically via student.hust.edu.vn API and QLĐT.
        """
        self.require_auth()
        # Parse Class UID / Course Code: e.g. "172154 - NE2000" or "NE2000" or "172154"
        raw_str = str(course_id_or_uid).strip()
        cid_match = re.search(r"([A-Z]{2,4}\d{4})", raw_str.upper())
        uid_match = re.search(r"(\d{5,7})", raw_str)
        
        course_code = cid_match.group(1) if cid_match else None
        class_uid = uid_match.group(1) if uid_match else None
        
        # If user passed only class_uid (e.g. "172154"), resolve to course_code via schedule
        if not course_code and class_uid:
            try:
                schedule = await self.get_schedule()
                for c in schedule.classes:
                    if c.class_id == class_uid or class_uid in (c.course_name or "") or class_uid in (c.course_id or ""):
                        course_code = c.course_id
                        break
            except Exception:
                pass

        # Fallback to the raw string if no course code resolved
        clean_cid = course_code or class_uid or raw_str.upper()

        async with self.get_http_client() as client:
            # 1. Fetch real structured course data from student.hust.edu.vn API
            api_url = f"https://student.hust.edu.vn/api/v1/courses/{clean_cid}?includeDepartments=true&includeProgram=true&includeTeachers=true"
            api_data = {}
            try:
                res = await client.get(api_url)
                if res.status_code == 200:
                    api_data = res.json()
            except Exception as e:
                logger.warning(f"Failed to fetch course API for {clean_cid}: {e}")

            # Extract fields from API data if available
            if api_data:
                course_name = api_data.get("name") or clean_cid
                course_name_en = api_data.get("nameEn")
                credit_val = float(api_data.get("credit", 3.0))
                credit_struct = api_data.get("creditInfo")
                coord_name = api_data.get("coordName")
                
                # Departments / Faculties
                departments = [d.get("name") for d in api_data.get("_departments", []) if d.get("name")]
                root_unit = api_data.get("_rootUnit", {})
                faculty = root_unit.get("name") or (departments[0] if departments else "Khoa / Viện chuyên ngành")
                sub_faculty = ", ".join(departments) if departments else None
                
                # Strip HTML tags helper (preserve paragraph breaks)
                def strip_html(html_str: Optional[str]) -> Optional[str]:
                    if not html_str:
                        return None
                    soup_obj = BeautifulSoup(html_str, "html.parser")
                    # Replace <p>, <br>, <div> with explicit line breaks for clean multi-sentence structure
                    for br in soup_obj.find_all(["br", "p", "div"]):
                        br.append("\n")
                    text = soup_obj.get_text()
                    # Clean up multiple consecutive empty lines
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    return "\n\n".join(lines) if lines else None


                # In HUST system: 'resume' is "Mô tả tóm tắt học phần", 'description' is "Nội dung tóm tắt học phần"
                desc_vi = strip_html(api_data.get("resume")) or strip_html(api_data.get("description"))
                desc_en = strip_html(api_data.get("resumeEn")) or strip_html(api_data.get("descriptionEn"))
                outline_vi = strip_html(api_data.get("description")) or desc_vi
                outline_en = strip_html(api_data.get("descriptionEn")) or desc_en



                # Attachments: syllabus, slides, textbooks, other references
                outline_urls = api_data.get("outlineUrls") or []
                syllabus_url = outline_urls[0] if outline_urls else None

                # Slides
                slide_urls = api_data.get("slideUrls") or []
                slides: List[TextbookItem] = []
                for s_url in slide_urls:
                    filename = s_url.split("/")[-1]
                    # Format display title from filename
                    clean_title = re.sub(r"_\d+(\.\d+)?[kKmMgG]\.pdf$", "", filename).replace("_", " ").title()
                    slides.append(
                        TextbookItem(
                            title=clean_title or f"Bài giảng {course_name}",
                            author=coord_name,
                            is_main_textbook=False,
                            url_or_file=s_url
                        )
                    )

                # Practice / Lab slides
                practice_urls = api_data.get("practiceUrls") or []
                for p_url in practice_urls:
                    filename = p_url.split("/")[-1]
                    clean_title = re.sub(r"_\d+(\.\d+)?[kKmMgG]\.pdf$", "", filename).replace("_", " ").title()
                    slides.append(
                        TextbookItem(
                            title=f"Thực hành / Thí nghiệm: {clean_title}",
                            author=coord_name,
                            is_main_textbook=False,
                            url_or_file=p_url
                        )
                    )

                # Textbooks (Giáo trình chính)
                textbooks: List[TextbookItem] = []
                # Check JSON string list in 'textBooks' first for docUrls/link attachments
                raw_tb_list = api_data.get("textBooks") or []
                parsed_tb_list = []
                for item in raw_tb_list:
                    if isinstance(item, str):
                        try:
                            parsed_tb_list.append(json.loads(item))
                        except Exception:
                            pass
                    elif isinstance(item, dict):
                        parsed_tb_list.append(item)
                
                if not parsed_tb_list:
                    parsed_tb_list = api_data.get("_textBooks", [])

                for tb in parsed_tb_list:
                    title = tb.get("title") or tb.get("name")
                    if title:
                        author = tb.get("authors") or tb.get("author") or ""
                        author = author.lstrip("] ").strip()
                        pub = tb.get("publisher") or ""
                        year = tb.get("year") or ""
                        pub_str = f"{pub} ({year})" if (pub and year) else (pub or year or None)
                        
                        # Check docUrls or link
                        tb_url = None
                        if tb.get("docUrls") and len(tb["docUrls"]) > 0:
                            tb_url = tb["docUrls"][0]
                        elif tb.get("link"):
                            tb_url = tb["link"] if tb["link"].startswith("http") else f"{settings.EHUST_BASE_URL}{tb['link']}"

                        textbooks.append(
                            TextbookItem(
                                title=title,
                                author=author or None,
                                publisher=pub_str,
                                is_main_textbook=True,
                                url_or_file=tb_url
                            )
                        )

                # Reference books (_refBooks)
                for rb in api_data.get("_refBooks", []):
                    title = rb.get("title") or rb.get("name")
                    if title:
                        author = rb.get("authors") or rb.get("author") or ""
                        author = author.lstrip("] ").strip()
                        pub = rb.get("publisher") or ""
                        year = rb.get("year") or ""
                        pub_str = f"{pub} ({year})" if (pub and year) else (pub or year or None)
                        rb_link = rb.get("link")
                        rb_url = (rb_link if rb_link.startswith("http") else f"{settings.EHUST_BASE_URL}{rb_link}") if rb_link else None

                        textbooks.append(
                            TextbookItem(
                                title=title,
                                author=author or None,
                                publisher=pub_str,
                                is_main_textbook=False,
                                url_or_file=rb_url
                            )
                        )

                # Other documents / references
                other_refs: List[TextbookItem] = []
                for d_url in api_data.get("docUrls") or []:
                    filename = d_url.split("/")[-1]
                    clean_title = re.sub(r"_\d+(\.\d+)?[kKmMgG]\.(docx|pdf|doc)$", "", filename).replace("_", " ").title()
                    other_refs.append(
                        TextbookItem(
                            title=clean_title or "Tài liệu tham khảo",
                            author=coord_name,
                            is_main_textbook=False,
                            url_or_file=d_url
                        )
                    )


                return CourseSyllabusDetail(
                    faculty=faculty,
                    sub_faculty=sub_faculty,
                    course_id=clean_cid,
                    course_name=course_name,
                    course_name_en=course_name_en,
                    training_programs="Kỹ sư chính quy, Chương trình tài năng, Chương trình tiên tiến, Kỹ sư chất lượng cao, Cử nhân, Vừa làm vừa học",
                    majors="Toàn trường / Khối Kỹ thuật",
                    course_type="Lớp",
                    coordinator=coord_name,
                    specialized_group=coord_name,
                    related_courses=str(api_data.get("relatedCourseId") or "Không"),
                    practical_coeff=float(api_data.get("practiceCoeff") or 0.0),
                    credits=credit_val,
                    lecture_hours=int(api_data.get("theoryHour") or 2),
                    exercise_hours=int(api_data.get("assignmentHour") or 0),
                    lab_hours=int(api_data.get("practiceHour") or 0),
                    self_study_hours=int(api_data.get("selfStudyHour") or 6),
                    final_exam_type="Thi viết (thi tập trung)",
                    credit_structure=credit_struct,
                    course_description_vi=desc_vi,
                    course_description_en=desc_en,
                    course_outline_vi=outline_vi,
                    course_outline_en=outline_en,
                    syllabus_file_url=syllabus_url,
                    textbooks=textbooks,
                    lecture_slides=slides,
                    other_references=other_refs
                )

            # 2. Fallback to scraping QLĐT HTML if API returns 404 or incomplete
            soup = await client.get_soup(f"/Course/Detail?courseId={clean_cid}")
            
            faculty = "Khoa / Viện phụ trách"
            sub_faculty = None
            course_name = clean_cid
            course_name_en = None
            coord_name = None
            desc_vi = None
            desc_en = None
            outline_vi = None
            outline_en = None
            syllabus_url = None
            textbooks = []
            slides = []
            other_refs = []

            for row in soup.find_all(["tr", "div", "p", "li"]):
                txt = row.get_text(separator=" ", strip=True)
                if "Đơn vị:" in txt:
                    faculty = txt.split("Đơn vị:", 1)[1].strip()
                elif "Đơn vị con:" in txt:
                    sub_faculty = txt.split("Đơn vị con:", 1)[1].strip()
                elif "Tên học phần:" in txt:
                    course_name = txt.split("Tên học phần:", 1)[1].strip()
                elif "Tên tiếng anh:" in txt or "Tên tiếng Anh:" in txt:
                    course_name_en = txt.split(":", 1)[1].strip()
                elif "Điều phối viên:" in txt:
                    coord_name = txt.split("Điều phối viên:", 1)[1].strip()
                elif "Mô tả tóm tắt học phần (Tiếng Việt)" in txt:
                    desc_vi = txt.replace("Mô tả tóm tắt học phần (Tiếng Việt)", "").strip()
                elif "Mô tả tóm tắt học phần (Tiếng Anh)" in txt:
                    desc_en = txt.replace("Mô tả tóm tắt học phần (Tiếng Anh)", "").strip()
                elif "Nội dung tóm tắt của học phần (Tiếng Việt)" in txt:
                    outline_vi = txt.replace("Nội dung tóm tắt của học phần (Tiếng Việt)", "").strip()
                elif "Nội dung tóm tắt của học phần (Tiếng Anh)" in txt:
                    outline_en = txt.replace("Nội dung tóm tắt của học phần (Tiếng Anh)", "").strip()

            for a in soup.find_all("a", href=True):
                href = a["href"]
                link_text = a.get_text(strip=True)
                full_link = href if href.startswith("http") else f"{settings.QLDT_BASE_URL}{href}"
                
                t_lower = link_text.lower()
                if any(ext in href.lower() for ext in [".pdf", ".docx", "decuong", "syllabus"]):
                    syllabus_url = full_link
                elif "slide" in t_lower or "bài giảng" in t_lower:
                    slides.append(TextbookItem(title=link_text, url_or_file=full_link, is_main_textbook=False))
                elif "giáo trình" in t_lower or "sách" in t_lower or "bài tập" in t_lower:
                    textbooks.append(TextbookItem(title=link_text, url_or_file=full_link, is_main_textbook=True))
                elif "tham khảo" in t_lower:
                    other_refs.append(TextbookItem(title=link_text, url_or_file=full_link, is_main_textbook=False))

            if not api_data and not soup.find("table") and not soup.find("div", class_="content"):
                # If neither API nor QLĐT page returns syllabus data, raise error
                raise FileNotFoundError(f"Không tìm thấy đề cương chi tiết hoặc dữ liệu cho học phần/mã lớp '{clean_cid}'.")

            return CourseSyllabusDetail(
                faculty=faculty,
                sub_faculty=sub_faculty,
                course_id=clean_cid,
                course_name=course_name,
                course_name_en=course_name_en,
                training_programs=None,
                majors=None,
                course_type="Lớp",
                coordinator=coord_name,
                specialized_group=coord_name,
                related_courses=None,
                practical_coeff=0.0,
                credits=0.0,
                lecture_hours=0,
                exercise_hours=0,
                lab_hours=0,
                self_study_hours=0,
                final_exam_type=None,
                credit_structure=None,
                course_description_vi=desc_vi,
                course_description_en=desc_en,
                course_outline_vi=outline_vi,
                course_outline_en=outline_en,
                syllabus_file_url=syllabus_url,
                textbooks=textbooks,
                lecture_slides=slides,
                other_references=other_refs
            )




    async def get_registration_plan(self, semester: Optional[str] = None) -> List[CourseRegistrationPlanItem]:
        """
        Get course registration plan or suggested curriculum with syllabus details for each course.
        """
        self.require_auth()
        async with self.get_http_client() as client:
            params = {"semester": semester} if semester else {}
            soup = await client.get_soup("/Registration/CoursePlan", params=params)
            if not soup.find("table"):
                async with AsyncHustHttpClient(base_url=settings.EHUST_BASE_URL) as ehust_client:
                    try:
                        soup = await ehust_client.get_soup("/students/learn/education-program")
                    except Exception:
                        pass

            plans: List[CourseRegistrationPlanItem] = []
            table = soup.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for r in rows:
                    cols = r.find_all("td")
                    if len(cols) >= 3:
                        # Parse course row
                        raw_cid = cols[1].get_text(strip=True) if len(cols) >= 4 else cols[0].get_text(strip=True)
                        raw_cname = cols[2].get_text(strip=True) if len(cols) >= 4 else cols[1].get_text(strip=True)
                        
                        cid_match = re.search(r"([A-Z]{2,4}\d{4})", raw_cid)
                        cid = cid_match.group(1) if cid_match else raw_cid
                        cname = raw_cname or cid
                        
                        try:
                            creds = float(re.sub(r"[^\d\.]", "", cols[3].get_text(strip=True) if len(cols) >= 5 else cols[2].get_text(strip=True)))
                        except (ValueError, IndexError):
                            creds = 3.0
                            
                        prereq = cols[4].get_text(strip=True) if len(cols) > 4 else None
                        status_str = cols[6].get_text(strip=True) if len(cols) > 6 else "Chưa học"
                        
                        plans.append(
                            CourseRegistrationPlanItem(
                                course_id=cid,
                                course_name=cname,
                                credits=creds,
                                prerequisites=prereq,
                                recommended_semester=semester,
                                status=status_str or "Chưa học"
                            )
                        )
            return plans


    async def check_graduation_eligibility(self) -> GraduationEligibility:
        """
        Evaluate graduation eligibility based on credits and CPA.
        """
        grades_summary = await self.get_grades()
        profile = await self.get_student_profile()

        accumulated_creds = sum(c.credits for c in grades_summary.courses if c.letter_grade not in ("F", None))
        cpa = grades_summary.cpa or 0.0
        required_credits = 130.0  # HUST bachelor standard
        min_cpa = 2.0

        is_eligible = (accumulated_creds >= required_credits) and (cpa >= min_cpa)
        missing = max(0.0, required_credits - accumulated_creds)
        notes = []
        if missing > 0:
            notes.append(f"Còn thiếu {missing:.1f} tín chỉ tích lũy.")
        if cpa < min_cpa:
            notes.append(f"CPA hiện tại ({cpa:.2f}) chưa đạt mức tối thiểu {min_cpa}.")
        if is_eligible:
            notes.append("Đủ điều kiện xét tốt nghiệp cơ bản.")

        return GraduationEligibility(
            student_id=profile.student_id,
            total_accumulated_credits=accumulated_creds,
            required_credits=required_credits,
            cpa=cpa,
            min_cpa_required=min_cpa,
            is_eligible=is_eligible,
            missing_credits=missing,
            notes=notes
        )

    async def get_semesters(self) -> List[SemesterInfo]:
        """
        Fetch all academic semesters configuration from HUST student API (https://student.hust.edu.vn/api/v1/semesters).
        Provides real-time information on current semester, project semester, teaching weeks, and course enrollment periods.
        """
        async with self.get_http_client() as client:
            res = await client.get("https://student.hust.edu.vn/api/v1/semesters")
            if res.status_code != 200:
                return []

            data = res.json()
            if not isinstance(data, list):
                return []

            def format_timestamp(ts: Optional[int]) -> Optional[str]:
                if ts and ts > 0:
                    try:
                        return datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d")
                    except Exception:
                        return None
                return None

            semesters: List[SemesterInfo] = []
            for item in data:
                raw_id = str(item.get("id") or item.get("semester") or "")
                if not raw_id:
                    continue

                # Format human readable name (e.g. 20261 -> "Học kỳ 2026.1", 20253 -> "Học kỳ Hè 2025.3")
                year_part = raw_id[:4] if len(raw_id) >= 4 else raw_id
                sem_part = raw_id[4:] if len(raw_id) > 4 else ""
                if sem_part == "3":
                    name = f"Học kỳ Hè {year_part}.3"
                elif sem_part:
                    name = f"Học kỳ {year_part}.{sem_part}"
                else:
                    name = f"Học kỳ {raw_id}"

                is_curr = bool(item.get("isCurrentForClass") or item.get("currentForClass"))
                is_next = bool(item.get("isNextForProject") or item.get("nextForProject"))

                semesters.append(
                    SemesterInfo(
                        id=raw_id,
                        semester_name=name,
                        is_current=is_curr,
                        is_next=is_next,
                        start_date=format_timestamp(item.get("startDate")),
                        end_date=format_timestamp(item.get("endDate")),
                        current_week=item.get("currentWeek") if item.get("currentWeek", 0) > 0 else None,
                        start_week=item.get("startWeek") if item.get("startWeek", 0) > 0 else None,
                        start_enroll_date=format_timestamp(item.get("startEnroll")),
                        end_enroll_date=format_timestamp(item.get("endEnroll")),
                        can_enroll=bool(item.get("_canEnroll", False))
                    )
                )

            return semesters


