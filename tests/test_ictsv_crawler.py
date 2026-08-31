import pytest
import respx
import httpx
from hust_interface.crawlers.ictsv_crawler import IctsvCrawler
from hust_interface.auth.manual_auth import ManualAuthenticator
from hust_interface.config import settings


@pytest.fixture
def ictsv_auth():
    ManualAuthenticator.set_ictsv_token("dummy_token_123")


@respx.mock
@pytest.mark.asyncio
async def test_ictsv_training_points(ictsv_auth):
    json_response = {
        "RespCode": 0,
        "TotalPoint": 88.5,
        "Semester": "2024.1",
        "FullName": "Nguyễn Văn A",
        "Groups": [
            {
                "Id": "g1",
                "Name": "Ý thức học tập",
                "MaxPoint": 30.0,
                "EarnedPoint": 28.0,
                "Items": [
                    {
                        "Id": "c1",
                        "Name": "Đi học đầy đủ",
                        "MaxPoint": 10.0,
                        "SchoolPoint": 10.0
                    }
                ]
            }
        ]
    }
    respx.post(f"{settings.CTSV_API_BASE_URL}/Criteria/GetCriteriaStudent").mock(
        return_value=httpx.Response(200, json=json_response)
    )

    crawler = IctsvCrawler()
    drl = await crawler.get_training_points(semester="2024.1")
    assert drl.total_point == 88.5
    assert drl.rank == "Tốt"
    assert len(drl.criteria_groups) == 1
    assert drl.criteria_groups[0].earned_point == 28.0


@respx.mock
@pytest.mark.asyncio
async def test_ictsv_activities(ictsv_auth):
    json_response = {
        "Data": [
            {
                "Id": "ACT01",
                "Title": "Hiến máu nhân đạo",
                "Score": 5.0,
                "UnitName": "Hội Sinh viên",
                "CriterionName": "Ý thức cộng đồng",
                "IsRegistered": True
            }
        ]
    }
    respx.post(f"{settings.CTSV_API_BASE_URL}/Activity/GetListActivity").mock(
        return_value=httpx.Response(200, json=json_response)
    )

    crawler = IctsvCrawler()
    activities = await crawler.get_activities(page=1, page_size=10)
    assert len(activities) == 1
    assert activities[0].activity_id == "ACT01"
    assert activities[0].point == 5.0
    assert activities[0].is_registered is True


@respx.mock
@pytest.mark.asyncio
async def test_ictsv_register_activity(ictsv_auth):
    json_response = {
        "RespCode": 0,
        "RespText": "Đăng ký thành công!"
    }
    respx.post(f"{settings.CTSV_API_BASE_URL}/Activity/StudentRegisterActivity").mock(
        return_value=httpx.Response(200, json=json_response)
    )

    crawler = IctsvCrawler()
    res = await crawler.register_activity(activity_id="ACT01")
    assert res.success is True
    assert "thành công" in res.message


@respx.mock
@pytest.mark.asyncio
async def test_ictsv_jobs(ictsv_auth):
    json_response = {
        "Data": [
            {
                "Id": "JOB01",
                "Position": "AI Engineer",
                "Company": "FPT Software",
                "SalaryRange": "15 - 25 Triệu",
                "Location": "Hà Nội"
            }
        ]
    }
    respx.post(f"{settings.CTSV_API_BASE_URL}/HWRecruitment/GetPublishRecruitment").mock(
        return_value=httpx.Response(200, json=json_response)
    )

    crawler = IctsvCrawler()
    jobs = await crawler.search_jobs(keyword="AI")
    assert len(jobs) == 1
    assert jobs[0].title == "AI Engineer"
    assert jobs[0].company_name == "FPT Software"
