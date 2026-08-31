import pytest
import respx
import httpx
from hust_interface.crawlers.ehust_crawler import EhustCrawler
from hust_interface.auth.manual_auth import ManualAuthenticator
from hust_interface.config import settings


@pytest.fixture
def ehust_auth():
    ManualAuthenticator.set_ehust_cookie("JSESSIONID=dummy_123", student_id="202611037")


@respx.mock
@pytest.mark.asyncio
async def test_ehust_crawler_real_profile(ehust_auth):
    # Real DOM structure inspected from eHUST / QLĐT
    html_content = """
    <html>
        <body>
            <table class="table table-bordered">
                <tr><td>Mã sinh viên:</td><td>202611037</td></tr>
                <tr><td>Họ và tên:</td><td>NGUYỄN TUẤN MINH</td></tr>
                <tr><td>Lớp:</td><td>Kỹ thuật hạt nhân 01-K69</td></tr>
                <tr><td>Khoa / Viện:</td><td>Khoa Vật lý kỹ thuật</td></tr>
                <tr><td>Ngành:</td><td>Kỹ thuật hạt nhân (7520402)</td></tr>
                <tr><td>Khóa:</td><td>K69</td></tr>
            </table>
        </body>
    </html>
    """
    respx.get(f"{settings.QLDT_BASE_URL}/Student/Profile").mock(
        return_value=httpx.Response(200, text=html_content)
    )

    crawler = EhustCrawler()
    profile = await crawler.get_student_profile()
    assert profile.student_id == "202611037"
    assert profile.full_name == "NGUYỄN TUẤN MINH"
    assert profile.school_faculty == "Khoa Vật lý kỹ thuật"
    assert "Kỹ thuật hạt nhân" in profile.major


@respx.mock
@pytest.mark.asyncio
async def test_ehust_crawler_real_schedule(ehust_auth):
    # Real schedule classes extracted from live inspection
    html_content = """
    <html>
        <body>
            <table id="tblStudentSchedule">
                <tr><th>Mã HP</th><th>Tên học phần</th><th>Mã lớp</th><th>Thứ</th><th>Khung giờ</th><th>Phòng</th><th>GV</th></tr>
                <tr>
                    <td>MI1111</td><td>Giải tích I</td><td>152001</td>
                    <td>Thứ Hai</td><td>06:45 - 09:10</td><td>D9-401</td><td>TS. Đào Quang Khải</td>
                </tr>
                <tr>
                    <td>MI1141</td><td>Đại số</td><td>152002</td>
                    <td>Thứ Tư</td><td>09:20 - 11:45</td><td>D9-201</td><td>TS. Nguyễn Thị Thu</td>
                </tr>
                <tr>
                    <td>NE2000</td><td>Nhập môn KT Hạt nhân và VLMT</td><td>152003</td>
                    <td>Thứ Sáu</td><td>12:30 - 15:00</td><td>TC-203</td><td>PGS. TS. Trần Hoài Nam</td>
                </tr>
            </table>
        </body>
    </html>
    """
    respx.get(f"{settings.QLDT_BASE_URL}/Schedule/StudentSchedule").mock(
        return_value=httpx.Response(200, text=html_content)
    )

    crawler = EhustCrawler()
    sched = await crawler.get_schedule(semester="2026.1", week=1)
    assert len(sched.classes) == 3
    assert sched.classes[0].course_id == "MI1111"
    assert sched.classes[0].day_of_week == 2
    assert sched.classes[1].course_id == "MI1141"
    assert sched.classes[1].day_of_week == 4
    assert sched.classes[2].course_id == "NE2000"
    assert sched.classes[2].day_of_week == 6


@respx.mock
@pytest.mark.asyncio
async def test_ehust_crawler_freshman_grades(ehust_auth):
    # Freshman with in-progress semester (no GPA yet)
    html_content = """
    <html>
        <body>
            <table id="tblStudentGrade">
                <tr><th>Mã</th><th>Tên</th><th>TC</th><th>GK</th><th>CK</th><th>Điểm chữ</th></tr>
                <tr><td>MI1111</td><td>Giải tích I</td><td>4.0</td><td>--</td><td>--</td><td>--</td></tr>
                <tr><td>MI1141</td><td>Đại số</td><td>4.0</td><td>--</td><td>--</td><td>--</td></tr>
                <tr><td>EM1010</td><td>Quản trị học đại cương</td><td>2.0</td><td>--</td><td>--</td><td>--</td></tr>
            </table>
            <div>Điểm TB học kỳ: 0.0</div>
            <div>Điểm TB tích lũy: 0.0</div>
        </body>
    </html>
    """
    respx.get(f"{settings.QLDT_BASE_URL}/Grade/StudentGrade").mock(
        return_value=httpx.Response(200, text=html_content)
    )

    crawler = EhustCrawler()
    grades = await crawler.get_grades(semester="2026.1")
    assert len(grades.courses) == 3
    assert grades.courses[0].course_id == "MI1111"
    assert grades.courses[0].credits == 4.0
    assert grades.courses[0].letter_grade == "--"
