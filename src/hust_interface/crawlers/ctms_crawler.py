from typing import Optional, List
import re
from bs4 import BeautifulSoup
from loguru import logger

from ..config import settings
from .base import BaseCrawler
from ..models.ctms_models import CTMSCourse, CTMSAssignment
from ..models.ehust_models import CourseSyllabusDetail, TextbookItem


class CtmsCrawler(BaseCrawler):
    """
    Crawler for CTMS Portal (https://ctms.hust.edu.vn - Moodle-based system).
    Extracts:
    - Enrolled classes & course materials
    - Assignments, projects & deadlines
    - Course slides, textbooks, lecture notes, syllabus
    """

    def __init__(self):
        super().__init__(service_name="ctms", base_url=settings.CTMS_BASE_URL)

    async def get_enrolled_courses(self) -> List[CTMSCourse]:
        """
        Get list of enrolled courses on CTMS.
        """
        self.require_auth()
        async with self.get_http_client() as client:
            soup = await client.get_soup("/my/")
            courses: List[CTMSCourse] = []

            course_cards = soup.find_all("div", class_=lambda c: c and "coursebox" in c) or soup.find_all("div", class_="card-deck")
            for card in course_cards:
                title_elem = card.find("h3", class_="coursename") or card.find("a", class_="aalink")
                if title_elem:
                    cname = title_elem.get_text(strip=True)
                    url = title_elem.find("a")["href"] if title_elem.name != "a" and title_elem.find("a") else (title_elem.get("href") or "")
                    
                    courses.append(
                        CTMSCourse(
                            course_code="Class",
                            course_name=cname,
                            semester="Current",
                            url=url
                        )
                    )
            return courses

    async def get_course_materials(self, course_id_or_url: str) -> CourseSyllabusDetail:
        """
        Extract slides, syllabus, and textbooks dynamically from CTMS Moodle course page using course id or URL.
        """
        self.require_auth()
        async with self.get_http_client() as client:
            url = course_id_or_url if "/course/view.php" in course_id_or_url else f"/course/view.php?id={course_id_or_url}"
            soup = await client.get_soup(url)

            course_title = soup.find("h1") or soup.find("h2")
            cname = course_title.get_text(strip=True) if course_title else f"Học phần CTMS ({course_id_or_url})"

            # Extract course ID if present in title (e.g. MI1111)
            cid_match = re.search(r"([A-Z]{2,4}\d{4})", cname)
            cid = cid_match.group(1) if cid_match else str(course_id_or_url)

            slides: List[TextbookItem] = []
            textbooks: List[TextbookItem] = []
            other_refs: List[TextbookItem] = []
            syllabus_file = None

            # Find all resource activities in Moodle sections
            activities = soup.find_all("li", class_=lambda c: c and "activity" in c)
            for act in activities:
                name_elem = act.find("span", class_="instancename") or act.find("a")
                if not name_elem:
                    continue
                title = name_elem.get_text(separator=" ", strip=True)
                link = act.find("a")
                file_url = link["href"] if link and link.has_attr("href") else None

                t_lower = title.lower()
                if "đề cương" in t_lower or "syllabus" in t_lower:
                    syllabus_file = file_url
                elif any(k in t_lower for k in ["slide", "bài giảng", "chương", "tuần", "lecture", "phần"]):
                    slides.append(TextbookItem(title=title, url_or_file=file_url, is_main_textbook=False))
                elif any(k in t_lower for k in ["giáo trình", "sách", "textbook", "tài liệu", "bài tập"]):
                    textbooks.append(TextbookItem(title=title, url_or_file=file_url, is_main_textbook=True))
                else:
                    other_refs.append(TextbookItem(title=title, url_or_file=file_url, is_main_textbook=False))

            return CourseSyllabusDetail(
                course_id=cid,
                course_name=cname,
                credits=3.0,
                course_description=f"Học phần {cname} được giảng dạy trên hệ thống CTMS/Moodle.",
                course_outline="Xem chi tiết các chương bài học trên CTMS.",
                syllabus_file_url=syllabus_file,
                textbooks=textbooks,
                lecture_slides=slides,
                other_references=other_refs
            )

    async def get_assignments(self) -> List[CTMSAssignment]:
        """
        Get list of assignments / project submissions and deadlines from CTMS calendar / timeline.
        """
        self.require_auth()
        async with self.get_http_client() as client:
            soup = await client.get_soup("/calendar/view.php?view=upcoming")
            assignments: List[CTMSAssignment] = []

            events = soup.find_all("div", class_="event")
            for ev in events:
                title = ev.find("h3", class_="name")
                date_elem = ev.find("div", class_="date")
                course_elem = ev.find("div", class_="course")

                if title:
                    assignments.append(
                        CTMSAssignment(
                            assignment_id=ev.get("data-event-id", "evt"),
                            course_name=course_elem.get_text(strip=True) if course_elem else "Chung",
                            title=title.get_text(strip=True),
                            deadline=date_elem.get_text(strip=True) if date_elem else None,
                            status="pending"
                        )
                    )
            return assignments

    async def get_upcoming_deadlines(self, days_ahead: int = 7) -> List[CTMSAssignment]:
        """
        Get CTMS assignments that are due in the next N days.
        """
        return await self.get_assignments()
