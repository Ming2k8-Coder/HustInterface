import pytest
import respx
import httpx
from hust_interface.crawlers.ctms_crawler import CtmsCrawler
from hust_interface.auth.manual_auth import ManualAuthenticator
from hust_interface.config import settings


@pytest.fixture
def ctms_auth():
    ManualAuthenticator.set_ctms_cookie("MoodleSession=dummy_moodle_session")


@respx.mock
@pytest.mark.asyncio
async def test_ctms_enrolled_courses(ctms_auth):
    html_content = """
    <html>
        <body>
            <div class="coursebox">
                <h3 class="coursename"><a href="https://ctms.hust.edu.vn/course/view.php?id=1234">Học máy và ứng dụng - IT4040</a></h3>
            </div>
        </body>
    </html>
    """
    respx.get(f"{settings.CTMS_BASE_URL}/my/").mock(
        return_value=httpx.Response(200, text=html_content)
    )

    crawler = CtmsCrawler()
    courses = await crawler.get_enrolled_courses()
    assert len(courses) == 1
    assert "Học máy" in courses[0].course_name
    assert "id=1234" in courses[0].url


@respx.mock
@pytest.mark.asyncio
async def test_ctms_assignments(ctms_auth):
    html_content = """
    <html>
        <body>
            <div class="event" data-event-id="evt101">
                <h3 class="name">Nộp Báo cáo Giữa kỳ</h3>
                <div class="course">IT4040</div>
                <div class="date">Thứ Sáu, 15 tháng 10, 23:59</div>
            </div>
        </body>
    </html>
    """
    respx.get(f"{settings.CTMS_BASE_URL}/calendar/view.php?view=upcoming").mock(
        return_value=httpx.Response(200, text=html_content)
    )

    crawler = CtmsCrawler()
    assignments = await crawler.get_assignments()
    assert len(assignments) == 1
    assert assignments[0].title == "Nộp Báo cáo Giữa kỳ"
    assert assignments[0].course_name == "IT4040"
