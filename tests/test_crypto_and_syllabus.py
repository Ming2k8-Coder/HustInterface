import pytest
import httpx
import respx
from hust_interface.core.crypto_helper import TimetableCryptoHelper
from hust_interface.crawlers.ehust_crawler import EhustCrawler
from hust_interface.auth.manual_auth import ManualAuthenticator
from hust_interface.config import settings


@pytest.fixture
def ehust_auth():
    ManualAuthenticator.set_ehust_cookie("token=test_jwt_123", student_id="202611037")


def test_timetable_crypto_encrypt_and_decrypt():

    # Test arbitrary JSON payload
    payload = {"semester": "20261", "studentId": "202611037"}
    encrypted = TimetableCryptoHelper.encrypt_payload(payload)
    assert isinstance(encrypted, str)
    assert len(encrypted) > 0

    decrypted = TimetableCryptoHelper.decrypt_payload(encrypted)
    assert decrypted == payload


def test_timetable_crypto_empty_and_corrupt():
    assert TimetableCryptoHelper.decrypt_payload("") == {}
    assert TimetableCryptoHelper.decrypt_payload("invalid_base64_or_corrupt_data") == {}


@respx.mock
@pytest.mark.asyncio
async def test_ehust_crawler_full_semester_encrypted_api():
    ManualAuthenticator.set_ehust_cookie("token=test_jwt_123", student_id="202611037")
    
    # Mock real encrypted data response
    mock_classes = [
        {
            "classId": "172153",
            "courseId": "EM1010",
            "courseName": "Quản trị học đại cương",
            "classType": "LT+BT",
            "calendarInfo": "1,524,526,3-19,D5-101;",
            "timePlaces": [
                {
                    "place": "D5-101",
                    "day": 5,
                    "from": 4,
                    "to": 6,
                    "weeks": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
                }
            ]
        },
        {
            "classId": "172147",
            "courseId": "MI1111",
            "courseName": "Giải tích I",
            "classType": "LT",
            "calendarInfo": "1,424,426,3-19,D3-201;",
            "timePlaces": [
                {
                    "place": "D3-201",
                    "day": 4,
                    "from": 4,
                    "to": 6,
                    "weeks": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
                }
            ]
        }
    ]
    
    encrypted_resp_payload = TimetableCryptoHelper.encrypt_payload(mock_classes)
    
    respx.get("https://student.hust.edu.vn/api/v1/semesters").mock(
        return_value=httpx.Response(200, json=[{"id": 20261, "isCurrent": True}])
    )
    
    respx.get("https://student.hust.edu.vn/api/v2/timetables/student-classes").mock(
        return_value=httpx.Response(200, json={"payload": encrypted_resp_payload})
    )
    
    crawler = EhustCrawler()
    res = await crawler.get_full_semester_schedule(semester="2026.1")
    assert res.total_courses == 2
    assert res.classes[0].course_id == "EM1010"
    assert res.classes[0].day_of_week == 5
    assert "D5-101" in res.classes[0].room
    assert res.classes[1].course_id == "MI1111"
    assert res.classes[1].day_of_week == 4


@respx.mock
@pytest.mark.asyncio
async def test_ehust_crawler_course_syllabus(ehust_auth):
    ManualAuthenticator.set_ehust_cookie("token=test_jwt_123", student_id="202611037")
    mock_course_data = {
        "id": "EM1010",
        "name": "Quản trị học đại cương",
        "nameEn": "Introduction to Management",
        "credit": 2.0,
        "creditInfo": "2(2-1-0-4)",
        "coordName": "Nguyễn Thị Thanh Dần",
        "_rootUnit": {"name": "Trường Kinh tế"},
        "_departments": [{"name": "Khoa Quản lý"}],
        "resume": "<p>Mô tả học phần tóm tắt</p>",
        "description": "<div>Nội dung chi tiết học phần</div>",
        "outlineUrls": ["https://storage.googleapis.com/hust-files/syllabus_em1010.pdf"],
        "slideUrls": ["https://storage.googleapis.com/hust-files/slide_em1010_ch1.pdf"],
        "textBooks": [
            '{"title": "Fundamentals of Management", "authors": "Robbins", "publisher": "Pearson", "year": "2020"}'
        ]
    }
    
    respx.get("https://student.hust.edu.vn/api/v1/courses/EM1010").mock(
        return_value=httpx.Response(200, json=mock_course_data)
    )
    
    crawler = EhustCrawler()
    syllabus = await crawler.get_course_syllabus("EM1010")
    assert syllabus.course_name == "Quản trị học đại cương"
    assert syllabus.course_name_en == "Introduction to Management"
    assert syllabus.credits == 2.0
    assert syllabus.faculty == "Trường Kinh tế"
    assert syllabus.coordinator == "Nguyễn Thị Thanh Dần"
    assert len(syllabus.lecture_slides) == 1
    assert len(syllabus.textbooks) == 1
    assert syllabus.textbooks[0].title == "Fundamentals of Management"


@respx.mock
@pytest.mark.asyncio
async def test_ehust_crawler_tuition_and_exams(ehust_auth):
    ManualAuthenticator.set_ehust_cookie("token=test_jwt_123", student_id="202611037")
    tuition_html = """

    <html>
        <body>
            <table>
                <tr><th>Học kỳ</th><th>Học phí</th><th>Đã đóng</th><th>Còn nợ</th></tr>
                <tr><td>2026.1</td><td>8,500,000</td><td>8,500,000</td><td>0</td></tr>
            </table>
        </body>
    </html>
    """
    respx.get(f"{settings.QLDT_BASE_URL}/Tuition/StudentTuition").mock(
        return_value=httpx.Response(200, text=tuition_html)
    )
    
    crawler = EhustCrawler()
    tuition = await crawler.get_tuition_fees()
    assert len(tuition) == 1
    assert tuition[0].semester == "2026.1"
    assert tuition[0].tuition_amount == 8500000.0
    assert tuition[0].debt_amount == 0.0
    assert tuition[0].payment_status == "Đã hoàn thành"
