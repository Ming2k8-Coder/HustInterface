from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CriterionItem(BaseModel):
    criterion_id: str
    criterion_name: str
    max_point: float
    self_point: Optional[float] = 0.0
    class_point: Optional[float] = 0.0
    school_point: Optional[float] = 0.0
    proof_url: Optional[str] = None
    status: Optional[str] = None


class CriterionGroup(BaseModel):
    group_id: str
    group_name: str
    max_point: float
    earned_point: float = 0.0
    items: List[CriterionItem] = Field(default_factory=list)


class TrainingPointSummary(BaseModel):
    semester: str = Field(..., description="Học kỳ (ví dụ: 2023.2, 2024.1)")
    student_id: str
    student_name: Optional[str] = None
    total_point: float = Field(..., description="Điểm rèn luyện tổng kết")
    rank: Optional[str] = Field(default=None, description="Xếp loại (Xuất sắc, Tốt, Khá, TB, Yếu, Kém)")
    criteria_groups: List[CriterionGroup] = Field(default_factory=list)


class StudentContact(BaseModel):
    student_id: str = Field(..., description="MSSV")
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    home_phone: Optional[str] = None
    personal_email: Optional[str] = None
    permanent_address: Optional[str] = None
    temporary_address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None


class ActivityItem(BaseModel):
    activity_id: str = Field(..., description="Mã hoặc ID hoạt động iCTSV")
    title: str = Field(..., description="Tên hoạt động ngoại khóa")
    description: Optional[str] = None
    organizer: Optional[str] = Field(default=None, description="Đơn vị tổ chức")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    point: Optional[float] = Field(default=None, description="Điểm rèn luyện nhận được")
    criterion_group_name: Optional[str] = None
    max_participants: Optional[int] = None
    registered_count: Optional[int] = None
    is_registered: bool = False
    registration_status: Optional[str] = None  # "registered", "attended", "cancelled", "open", "closed"
    attendance_status: Optional[str] = None  # "attended", "absent", "pending"


class ActivityRegistrationResult(BaseModel):
    activity_id: str
    success: bool
    message: str
    registration_time: datetime = Field(default_factory=datetime.now)


class NotificationItem(BaseModel):
    notification_id: str
    title: str
    content: Optional[str] = None
    created_at: Optional[str] = None
    is_read: bool = False
    sender: Optional[str] = None


class JobRecruitmentItem(BaseModel):
    job_id: str = Field(..., description="Mã tuyển dụng")
    title: str = Field(..., description="Vị trí tuyển dụng")
    company_name: str = Field(..., description="Tên doanh nghiệp")
    salary_range: Optional[str] = Field(default=None, description="Mức lương")
    location: Optional[str] = Field(default=None, description="Địa điểm làm việc")
    deadline: Optional[str] = Field(default=None, description="Hạn nộp hồ sơ")
    description: Optional[str] = None
    requirements: Optional[str] = None
    contact_email: Optional[str] = None
