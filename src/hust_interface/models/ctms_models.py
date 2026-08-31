from typing import Optional, List
from pydantic import BaseModel, Field


class CTMSCourse(BaseModel):
    course_code: str = Field(..., description="Mã lớp học phần (ví dụ: 145020)")
    course_name: str = Field(..., description="Tên môn học")
    semester: str = Field(..., description="Học kỳ")
    lecturer: Optional[str] = None
    materials_count: int = 0
    announcements_count: int = 0
    url: Optional[str] = None


class CTMSAssignment(BaseModel):
    assignment_id: str
    course_name: str
    title: str = Field(..., description="Tên bài tập / Đề tài đồ án")
    deadline: Optional[str] = None
    status: Optional[str] = None  # "submitted", "pending", "overdue"
    score: Optional[float] = None
    feedback: Optional[str] = None
