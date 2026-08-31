from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    student_id: str = Field(..., description="Mã số sinh viên (MSSV)")
    full_name: str = Field(..., description="Họ và tên sinh viên")
    email: Optional[str] = Field(default=None, description="Email sinh viên")
    class_name: Optional[str] = Field(default=None, description="Lớp sinh viên")
    school_faculty: Optional[str] = Field(default=None, description="Trường / Khoa / Viện")
    major: Optional[str] = Field(default=None, description="Ngành đào tạo")
    program: Optional[str] = Field(default=None, description="Chương trình đào tạo (Chuẩn, Elitech, v.v.)")
    academic_status: Optional[str] = Field(default=None, description="Tình trạng học tập")
    cohort: Optional[str] = Field(default=None, description="Khóa sinh viên (ví dụ K66)")


class ScheduleClassItem(BaseModel):
    course_id: str = Field(..., description="Mã học phần (ví dụ MI1111, IT3040)")
    course_name: str = Field(..., description="Tên học phần")
    class_id: str = Field(..., description="Mã lớp học / Lớp học phần")
    teaching_type: Optional[str] = Field(default="Trực tiếp", description="Hình thức giảng dạy (Trực tiếp, Trực tuyến, Kết hợp, LT+BT)")
    class_type: Optional[str] = Field(default="LT+BT", description="Loại lớp (LT, BT, TN, ĐA)")
    day_of_week: int = Field(..., description="Thứ trong tuần (2 -> 8, với 8 là Chủ Nhật)")
    day_name: str = Field(..., description="Thứ hai, Thứ ba,...")
    start_period: int = Field(default=1, description="Tiết bắt đầu (1-12)")
    end_period: int = Field(default=3, description="Tiết kết thúc (1-12)")
    time_range: str = Field(..., description="Khung giờ học (ví dụ: 06:45 - 09:10)")
    room: str = Field(..., description="Phòng học (ví dụ: D9-401, TC-203)")
    weeks: List[int] = Field(default_factory=list, description="Danh sách các tuần học")
    weeks_str: Optional[str] = Field(default=None, description="Chuỗi tuần học (ví dụ: 1-9, 11-18)")
    lecturer: Optional[str] = Field(default=None, description="Giảng viên phụ trách")
    absence_count: Optional[int] = Field(default=0, description="Số buổi vắng mặt")
    exam_status: Optional[str] = Field(default="Đủ điều kiện", description="Trạng thái thi / Đủ điều kiện dự thi")
    student_feedback: Optional[str] = Field(default=None, description="Phản hồi của sinh viên về học phần")


class WeeklySchedule(BaseModel):
    semester: str = Field(..., description="Học kỳ (ví dụ: 2024.1, 2024.2)")
    week_number: int = Field(..., description="Tuần học số mấy trong kỳ")
    classes: List[ScheduleClassItem] = Field(default_factory=list)


class FullSemesterSchedule(BaseModel):
    semester: str = Field(..., description="Học kỳ (ví dụ: 2024.1, 2024.2)")
    total_courses: int = Field(default=0, description="Tổng số môn học trong kỳ")
    classes: List[ScheduleClassItem] = Field(default_factory=list, description="Danh sách toàn bộ các lớp học phần trong kỳ kèm thời gian, phòng học, các tuần học")



class GradeItem(BaseModel):
    course_id: str = Field(..., description="Mã học phần")
    course_name: str = Field(..., description="Tên học phần")
    credits: float = Field(..., description="Số tín chỉ")
    class_id: Optional[str] = None
    semester: str = Field(..., description="Học kỳ")
    midterm_score: Optional[float] = Field(default=None, description="Điểm quá trình / GK")
    final_score: Optional[float] = Field(default=None, description="Điểm thi cuối kỳ")
    letter_grade: Optional[str] = Field(default=None, description="Điểm chữ (A+, A, B+, B, C+, C, D+, D, F)")
    scale4_score: Optional[float] = Field(default=None, description="Điểm hệ 4")


class SemesterGradeSummary(BaseModel):
    semester: str
    gpa: Optional[float] = Field(default=None, description="Điểm trung bình học kỳ (GPA)")
    cpa: Optional[float] = Field(default=None, description="Điểm trung bình tích lũy (CPA)")
    passed_credits_semester: Optional[float] = None
    accumulated_credits: Optional[float] = None
    academic_warning_level: Optional[str] = None
    courses: List[GradeItem] = Field(default_factory=list)


class ExamScheduleItem(BaseModel):
    course_id: str = Field(..., description="Mã học phần")
    course_name: str = Field(..., description="Tên học phần")
    exam_group: Optional[str] = None
    exam_date: str = Field(..., description="Ngày thi (YYYY-MM-DD hoặc DD/MM/YYYY)")
    exam_shift: str = Field(..., description="Kíp thi (ví dụ: Kíp 1, Kíp 2, Kíp 3)")
    exam_time: str = Field(..., description="Giờ thi (ví dụ: 07:00, 09:30)")
    room: str = Field(..., description="Phòng thi")
    seat_number: Optional[str] = Field(default=None, description="Số báo danh / Số thứ tự phòng thi")
    notes: Optional[str] = None


class TuitionFeeItem(BaseModel):
    semester: str = Field(..., description="Học kỳ")
    tuition_amount: float = Field(default=0.0, description="Học phí phải đóng")
    paid_amount: float = Field(default=0.0, description="Số tiền đã đóng")
    debt_amount: float = Field(default=0.0, description="Số tiền còn nợ")
    payment_status: str = Field(default="Đã hoàn thành", description="Tình trạng (Đã hoàn thành, Chưa nộp, Nợ)")
    deadline: Optional[str] = None


class TextbookItem(BaseModel):
    title: str = Field(..., description="Tên giáo trình / slide / tài liệu")
    author: Optional[str] = Field(default=None, description="Tác giả / Bộ môn phụ trách")
    publisher: Optional[str] = Field(default=None, description="Nhà xuất bản / Năm phát hành")
    is_main_textbook: bool = Field(default=True, description="Giáo trình chính hay tài liệu tham khảo")
    url_or_file: Optional[str] = Field(default=None, description="Link tải / Tệp đính kèm nếu có")


class CourseSyllabusDetail(BaseModel):
    # Thông tin chung
    faculty: Optional[str] = Field(default="Khoa Toán - Tin", description="Đơn vị (Khoa / Viện / Trường)")
    sub_faculty: Optional[str] = Field(default=None, description="Đơn vị con (Bộ môn, Viện)")
    course_id: str = Field(..., description="Mã học phần (ví dụ MI1111)")
    course_name: str = Field(..., description="Tên học phần (Tiếng Việt)")
    course_name_en: Optional[str] = Field(default=None, description="Tên tiếng Anh (ví dụ: Calculus I)")
    training_programs: Optional[str] = Field(default=None, description="Hệ đào tạo (Kỹ sư, Cử nhân, Tiên tiến,...)")
    majors: Optional[str] = Field(default=None, description="Ngành đào tạo")
    course_type: Optional[str] = Field(default="Lớp", description="Loại hình (Lớp, Đồ án, TN)")
    coordinator: Optional[str] = Field(default=None, description="Điều phối viên học phần (ví dụ: Bùi Xuân Diệu)")
    specialized_group: Optional[str] = Field(default=None, description="Nhóm chuyên môn")
    related_courses: Optional[str] = Field(default=None, description="Học phần liên quan / tiên quyết")

    # Phân bổ học phần
    practical_coeff: Optional[float] = Field(default=0.0, description="Hệ số điểm thực hành")
    credits: float = Field(default=4.0, description="Số tín chỉ")
    lecture_hours: Optional[int] = Field(default=3, description="Số giờ lý thuyết (LT)")
    exercise_hours: Optional[int] = Field(default=2, description="Số giờ bài tập (BT)")
    lab_hours: Optional[int] = Field(default=0, description="Số giờ thực hành / thí nghiệm (TH/TN)")
    self_study_hours: Optional[int] = Field(default=8, description="Số giờ tự học")
    final_exam_type: Optional[str] = Field(default="Thi viết (thi tập trung)", description="Hình thức thi cuối kỳ")
    internship_hours: Optional[str] = None
    internship_plan: Optional[str] = None
    project_plan: Optional[str] = None
    credit_structure: Optional[str] = Field(default="4(3-2-0-8)", description="Phân bổ tín chỉ: TC(LT-BT-TH-Tự học)")

    # Mô tả & Nội dung
    course_description_vi: Optional[str] = Field(default=None, description="Mô tả tóm tắt học phần (Tiếng Việt)")
    course_description_en: Optional[str] = Field(default=None, description="Mô tả tóm tắt học phần (Tiếng Anh)")
    course_outline_vi: Optional[str] = Field(default=None, description="Nội dung tóm tắt của học phần (Tiếng Việt)")
    course_outline_en: Optional[str] = Field(default=None, description="Nội dung tóm tắt của học phần (Tiếng Anh)")

    # Đề cương & Tài liệu
    syllabus_file_url: Optional[str] = Field(default=None, description="Link / tệp kèm của Đề cương chi tiết của học phần")
    textbooks: List[TextbookItem] = Field(default_factory=list, description="Sách giáo trình, sách tham khảo")
    lecture_slides: List[TextbookItem] = Field(default_factory=list, description="Bài giảng hoặc slide bài giảng (gồm 3+ slide/phần)")
    other_references: List[TextbookItem] = Field(default_factory=list, description="Tài liệu tham khảo khác (nếu có)")


class CourseRegistrationPlanItem(BaseModel):
    course_id: str = Field(..., description="Mã học phần")
    course_name: str = Field(..., description="Tên học phần")
    credits: float = Field(default=0.0, description="Số tín chỉ")
    prerequisites: Optional[str] = None
    recommended_semester: Optional[str] = None
    status: Optional[str] = "Chưa học"  # "Đã qua", "Đang học", "Chưa học"
    syllabus_detail: Optional[CourseSyllabusDetail] = None


class GraduationEligibility(BaseModel):
    student_id: str
    total_accumulated_credits: float = Field(default=0.0, description="Số tín chỉ đã tích lũy")
    required_credits: float = Field(default=130.0, description="Số tín chỉ yêu cầu tối thiểu")
    cpa: float = Field(default=0.0, description="CPA hiện tại")
    min_cpa_required: float = Field(default=2.0, description="CPA tối thiểu để tốt nghiệp")
    is_eligible: bool = False
    missing_credits: float = 0.0
    notes: List[str] = Field(default_factory=list)


class StudentOverview(BaseModel):
    student_id: str
    full_name: str
    class_name: Optional[str] = None
    cpa: Optional[float] = None
    gpa_latest: Optional[float] = None
    training_points_latest: Optional[float] = None
    drl_rank: Optional[str] = None
    accumulated_credits: Optional[float] = None
    tuition_debt: float = 0.0
    upcoming_exams_count: int = 0
    upcoming_deadlines_count: int = 0
    academic_warning_level: Optional[str] = None
