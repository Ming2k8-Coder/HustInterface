import pytest
from datetime import datetime
from hust_interface.models.auth_models import TokenInfo, ServiceSessionData
from hust_interface.models.ehust_models import (
    StudentProfile,
    ScheduleClassItem,
    WeeklySchedule,
    GradeItem,
    SemesterGradeSummary,
    TuitionFeeItem,
    GraduationEligibility,
    StudentOverview,
)
from hust_interface.models.ictsv_models import (
    TrainingPointSummary,
    CriterionGroup,
    CriterionItem,
    StudentContact,
    ActivityItem,
    JobRecruitmentItem,
)


def test_token_info_expiration():
    valid_token = TokenInfo(
        access_token="sample_token",
        expires_at=datetime(2099, 1, 1)
    )
    assert not valid_token.is_expired()

    expired_token = TokenInfo(
        access_token="expired_token",
        expires_at=datetime(2020, 1, 1)
    )
    assert expired_token.is_expired()


def test_student_profile_model():
    profile = StudentProfile(
        student_id="20210000",
        full_name="Nguyễn Văn A",
        class_name="Khoa học máy tính 01",
        school_faculty="Trường CNTT & TT"
    )
    assert profile.student_id == "20210000"
    assert profile.school_faculty == "Trường CNTT & TT"


def test_schedule_model():
    item = ScheduleClassItem(
        course_id="IT3040",
        course_name="Kỹ thuật lập trình",
        class_id="145001",
        day_of_week=2,
        day_name="Thứ Hai",
        start_period=1,
        end_period=3,
        time_range="06:45 - 09:10",
        room="D9-401"
    )
    schedule = WeeklySchedule(semester="2024.1", week_number=3, classes=[item])
    assert len(schedule.classes) == 1
    assert schedule.classes[0].course_id == "IT3040"


def test_training_point_model():
    criterion = CriterionItem(
        criterion_id="c1",
        criterion_name="Ý thức học tập",
        max_point=30.0,
        self_point=28.0,
        school_point=28.0
    )
    group = CriterionGroup(
        group_id="g1",
        group_name="Nhóm 1",
        max_point=30.0,
        earned_point=28.0,
        items=[criterion]
    )
    summary = TrainingPointSummary(
        semester="2024.1",
        student_id="20210000",
        total_point=88.0,
        rank="Tốt",
        criteria_groups=[group]
    )
    assert summary.total_point == 88.0
    assert summary.rank == "Tốt"


def test_extended_models():
    tuition = TuitionFeeItem(
        semester="2024.1",
        tuition_amount=15000000.0,
        paid_amount=15000000.0,
        debt_amount=0.0,
        payment_status="Đã hoàn thành"
    )
    assert tuition.debt_amount == 0.0

    grad = GraduationEligibility(
        student_id="20210000",
        total_accumulated_credits=135.0,
        cpa=3.2,
        is_eligible=True
    )
    assert grad.is_eligible is True

    contact = StudentContact(
        student_id="20210000",
        phone="0912345678",
        email="a.nv210000@sis.hust.edu.vn"
    )
    assert contact.phone == "0912345678"

    job = JobRecruitmentItem(
        job_id="J1",
        title="AI Engineer",
        company_name="Viettel"
    )
    assert job.company_name == "Viettel"

    overview = StudentOverview(
        student_id="20210000",
        full_name="Nguyễn Văn A",
        cpa=3.5,
        training_points_latest=90.0
    )
    assert overview.cpa == 3.5
