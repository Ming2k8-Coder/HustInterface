from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from ..config import settings
from .base import BaseCrawler
from ..models.ictsv_models import (
    TrainingPointSummary,
    CriterionGroup,
    CriterionItem,
    StudentContact,
    ActivityItem,
    ActivityRegistrationResult,
    NotificationItem,
    JobRecruitmentItem,
)


class IctsvCrawler(BaseCrawler):
    """
    Crawler & API Client for CTSV / iCTSV (https://ctsv.hust.edu.vn/api-t).
    Endpoints:
    - User Profile & Info: /User/GetUserInfo
    - Student Contact: /User/GetStudentContact
    - Training Points (ĐRL): /Criteria/GetCriteriaStudent, /Criteria/GetPointCriteria
    - Activities: /Activity/GetListActivity, /Activity/StudentRegisterActivity
    - Messages: /User/GetUserMessage
    - Recruitment / Jobs: /HWRecruitment/GetPublishRecruitment
    """

    def __init__(self):
        super().__init__(service_name="ictsv", base_url=settings.CTSV_API_BASE_URL)

    def _get_auth_payload(self) -> Dict[str, Any]:
        sess = self.get_session()
        token = sess.token.access_token if sess and sess.token else ""
        username = sess.student_id if sess and sess.student_id else ""
        return {
            "TokenCode": token,
            "UserName": username
        }

    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Fetch user basic info from CTSV API (/User/GetUserInfo).
        """
        self.require_auth()
        payload = self._get_auth_payload()
        async with self.get_http_client() as client:
            try:
                res = await client.post("/User/GetUserInfo", json_data=payload)
                data = res.json() if res.is_success else {}
                return data
            except Exception as e:
                logger.error(f"Failed to get CTSV profile: {e}")
                raise

    async def get_student_contact(self) -> StudentContact:
        """
        Fetch student contact info (phone, address, emergency contact) from CTSV (/User/GetStudentContact).
        """
        self.require_auth()
        payload = self._get_auth_payload()
        sess = self.get_session()
        student_id = (sess.student_id if sess and sess.student_id else None) or "unknown"
        student_name = sess.student_name if sess else ""


        async with self.get_http_client() as client:
            try:
                res = await client.post("/User/GetStudentContact", json_data=payload)
                data = res.json() if res.is_success else {}
                c_data = data.get("Data", data.get("ContactInfo", data))

                return StudentContact(
                    student_id=student_id,
                    full_name=student_name or c_data.get("FullName"),
                    phone=c_data.get("Phone", c_data.get("MobilePhone")),
                    email=c_data.get("Email", c_data.get("HustEmail")),
                    home_phone=c_data.get("HomePhone"),
                    personal_email=c_data.get("PersonalEmail", c_data.get("SecondEmail")),
                    permanent_address=c_data.get("PermanentAddress", c_data.get("Address")),
                    temporary_address=c_data.get("TemporaryAddress", c_data.get("CurrentAddress")),
                    emergency_contact_name=c_data.get("EmergencyContactName", c_data.get("ParentName")),
                    emergency_contact_phone=c_data.get("EmergencyContactPhone", c_data.get("ParentPhone")),
                    emergency_contact_relation=c_data.get("EmergencyContactRelation", c_data.get("ParentRelation"))
                )
            except Exception as e:
                logger.error(f"Error fetching CTSV contact info: {e}")
                raise

    async def get_training_points(self, semester: Optional[str] = None) -> TrainingPointSummary:
        """
        Fetch student training points (Điểm rèn luyện) from CTSV.
        """
        self.require_auth()
        sess = self.get_session()
        student_id = (sess.student_id if sess and sess.student_id else None) or "unknown"
        student_name = sess.student_name if sess else ""


        payload = self._get_auth_payload()
        if semester:
            payload["Semester"] = semester

        async with self.get_http_client() as client:
            try:
                res = await client.post("/Criteria/GetCriteriaStudent", json_data=payload)
                res_data = res.json() if res.is_success else {}

                total_point = float(res_data.get("TotalPoint", res_data.get("Point", res_data.get("total_point", 0.0))))
                sem_str = semester or res_data.get("Semester", "2024.1")
                rank = (
                    "Xuất sắc" if total_point >= 90
                    else "Tốt" if total_point >= 80
                    else "Khá" if total_point >= 65
                    else "Trung bình" if total_point >= 50
                    else "Yếu"
                )

                groups: List[CriterionGroup] = []
                for g_data in res_data.get("Groups", res_data.get("CriteriaGroups", [])):
                    items: List[CriterionItem] = []
                    for it in g_data.get("Items", g_data.get("Criteria", [])):
                        items.append(
                            CriterionItem(
                                criterion_id=str(it.get("Id", it.get("CriterionId", ""))),
                                criterion_name=it.get("Name", it.get("Title", "")),
                                max_point=float(it.get("MaxPoint", 0.0)),
                                self_point=float(it.get("SelfPoint", 0.0)),
                                class_point=float(it.get("ClassPoint", 0.0)),
                                school_point=float(it.get("SchoolPoint", 0.0)),
                                proof_url=it.get("ProofUrl"),
                                status=it.get("Status")
                            )
                        )
                    groups.append(
                        CriterionGroup(
                            group_id=str(g_data.get("Id", g_data.get("GroupId", ""))),
                            group_name=g_data.get("Name", g_data.get("GroupName", "")),
                            max_point=float(g_data.get("MaxPoint", 0.0)),
                            earned_point=float(g_data.get("EarnedPoint", g_data.get("Point", 0.0))),
                            items=items
                        )
                    )

                return TrainingPointSummary(
                    semester=sem_str,
                    student_id=student_id,
                    student_name=student_name or res_data.get("FullName"),
                    total_point=total_point,
                    rank=rank,
                    criteria_groups=groups
                )
            except Exception as e:
                logger.error(f"Error fetching CTSV training points: {e}")
                raise

    async def get_drl_history(self) -> List[TrainingPointSummary]:
        """
        Fetch DRL training point history across multiple semesters.
        """
        self.require_auth()
        # Common HUST semesters
        semesters = ["2024.1", "2023.2", "2023.1", "2022.2", "2022.1"]
        history: List[TrainingPointSummary] = []
        for sem in semesters:
            try:
                summary = await self.get_training_points(semester=sem)
                if summary.total_point > 0 or summary.criteria_groups:
                    history.append(summary)
            except Exception:
                continue
        return history

    async def get_activities(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = "all",
        min_point: Optional[float] = None,
        criterion_group: Optional[str] = None
    ) -> List[ActivityItem]:
        """
        List extracurricular activities from CTSV (/Activity/GetListActivity) with advanced filtering.
        """
        self.require_auth()
        payload = self._get_auth_payload()
        payload.update({
            "Page": page,
            "PageSize": page_size,
            "Status": status_filter
        })

        async with self.get_http_client() as client:
            try:
                res = await client.post("/Activity/GetListActivity", json_data=payload)
                res_data = res.json() if res.is_success else {}
                items_raw = res_data.get("Data", res_data.get("Items", res_data if isinstance(res_data, list) else []))

                activities: List[ActivityItem] = []
                for item in items_raw:
                    act_point = float(item.get("Point", item.get("Score", 0.0)))
                    group_name = item.get("CriterionGroupName", item.get("CriterionName", ""))
                    
                    if min_point is not None and act_point < min_point:
                        continue
                    if criterion_group and criterion_group.lower() not in group_name.lower():
                        continue

                    activities.append(
                        ActivityItem(
                            activity_id=str(item.get("Id", item.get("ActivityId", ""))),
                            title=item.get("Name", item.get("Title", "Hoạt động CTSV")),
                            description=item.get("Description", item.get("Content")),
                            organizer=item.get("Organizer", item.get("UnitName")),
                            start_time=item.get("StartTime", item.get("FromDate")),
                            end_time=item.get("EndTime", item.get("ToDate")),
                            location=item.get("Location", item.get("Place")),
                            point=act_point,
                            criterion_group_name=group_name,
                            max_participants=item.get("MaxParticipants", item.get("Limit")),
                            registered_count=item.get("RegisteredCount", item.get("CurrentRegistered")),
                            is_registered=bool(item.get("IsRegistered", item.get("Registered", False))),
                            registration_status=item.get("RegistrationStatus", "open"),
                            attendance_status=item.get("AttendanceStatus")
                        )
                    )
                return activities
            except Exception as e:
                logger.error(f"Error fetching CTSV activities: {e}")
                raise

    async def register_activity(self, activity_id: str) -> ActivityRegistrationResult:
        """
        Register for an extracurricular activity on CTSV.
        """
        self.require_auth()
        payload = self._get_auth_payload()
        payload["ActivityId"] = activity_id

        async with self.get_http_client() as client:
            try:
                res = await client.post("/Activity/StudentRegisterActivity", json_data=payload)
                data_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
                success = res.is_success and data_json.get("RespCode", 0) == 0
                msg = data_json.get("RespText", data_json.get("Message", "Đăng ký thành công!" if success else "Thất bại"))
                return ActivityRegistrationResult(
                    activity_id=activity_id,
                    success=success,
                    message=msg
                )
            except Exception as e:
                logger.error(f"Failed to register activity {activity_id}: {e}")
                return ActivityRegistrationResult(
                    activity_id=activity_id,
                    success=False,
                    message=str(e)
                )

    async def get_my_registered_activities(self) -> List[ActivityItem]:
        """
        Get activities that the student has registered for.
        """
        return await self.get_activities(status_filter="registered")

    async def get_notifications(self, page: int = 1, page_size: int = 10) -> List[NotificationItem]:
        """
        Get messages/notifications for the student from CTSV (/User/GetUserMessage).
        """
        self.require_auth()
        payload = self._get_auth_payload()
        payload.update({"Page": page, "PageSize": page_size})

        async with self.get_http_client() as client:
            try:
                res = await client.post("/User/GetUserMessage", json_data=payload)
                res_data = res.json() if res.is_success else {}
                items_raw = res_data.get("Data", res_data.get("Items", []))
                notifications: List[NotificationItem] = []
                for n in items_raw:
                    notifications.append(
                        NotificationItem(
                            notification_id=str(n.get("Id", "")),
                            title=n.get("Title", n.get("Subject", "Thông báo")),
                            content=n.get("Content", n.get("Body", "")),
                            created_at=n.get("CreatedAt", n.get("SendTime")),
                            is_read=bool(n.get("IsRead", False)),
                            sender=n.get("Sender", "Ban CTSV")
                        )
                    )
                return notifications
            except Exception as e:
                logger.error(f"Error fetching CTSV notifications: {e}")
                raise

    async def search_jobs(self, keyword: Optional[str] = None, page: int = 1, page_size: int = 10) -> List[JobRecruitmentItem]:
        """
        Search job opportunities and internships from HUST Career (/HWRecruitment/GetPublishRecruitment).
        """
        self.require_auth()
        payload = self._get_auth_payload()
        payload.update({
            "Page": page,
            "PageSize": page_size,
            "Keyword": keyword or ""
        })

        async with self.get_http_client() as client:
            try:
                res = await client.post("/HWRecruitment/GetPublishRecruitment", json_data=payload)
                res_data = res.json() if res.is_success else {}
                items_raw = res_data.get("Data", res_data.get("Items", []))
                jobs: List[JobRecruitmentItem] = []
                for j in items_raw:
                    jobs.append(
                        JobRecruitmentItem(
                            job_id=str(j.get("Id", j.get("RecruitmentId", ""))),
                            title=j.get("Title", j.get("Position", "Vị trí tuyển dụng")),
                            company_name=j.get("CompanyName", j.get("Company", "Doanh nghiệp đối tác")),
                            salary_range=j.get("Salary", j.get("SalaryRange")),
                            location=j.get("Location", j.get("WorkPlace")),
                            deadline=j.get("Deadline", j.get("ExpiredDate")),
                            description=j.get("Description", j.get("Summary")),
                            requirements=j.get("Requirement"),
                            contact_email=j.get("ContactEmail")
                        )
                    )
                return jobs
            except Exception as e:
                logger.error(f"Error searching CTSV recruitment jobs: {e}")
                raise
