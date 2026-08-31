import pytest
import respx
import httpx
from hust_interface.server import mcp_server
from hust_interface.auth.manual_auth import ManualAuthenticator
from hust_interface.config import settings


@pytest.fixture(autouse=True)
def setup_sessions():
    ManualAuthenticator.set_ehust_cookie("JSESSIONID=dummy_123", student_id="20210001")
    ManualAuthenticator.set_ictsv_token("dummy_token_123")
    ManualAuthenticator.set_ctms_cookie("MoodleSession=dummy_moodle")


@respx.mock
@pytest.mark.asyncio
async def test_all_mcp_tools_execution():
    # Mock eHUST endpoints
    respx.get(f"{settings.QLDT_BASE_URL}/Student/Profile").mock(
        return_value=httpx.Response(200, text="<table><tr><td>MSSV</td><td>20210001</td></tr></table>")
    )
    respx.get(f"{settings.QLDT_BASE_URL}/Grade/StudentGrade").mock(
        return_value=httpx.Response(200, text="<div>GPA: 3.5</div><div>CPA: 3.2</div>")
    )
    respx.get(f"{settings.QLDT_BASE_URL}/Schedule/StudentSchedule").mock(
        return_value=httpx.Response(200, text="<table id='tblStudentSchedule'></table>")
    )
    respx.get(f"{settings.QLDT_BASE_URL}/Exam/StudentExamSchedule").mock(
        return_value=httpx.Response(200, text="<table></table>")
    )
    respx.get(f"{settings.QLDT_BASE_URL}/Tuition/StudentTuition").mock(
        return_value=httpx.Response(200, text="<table></table>")
    )
    respx.get(f"{settings.QLDT_BASE_URL}/Registration/CoursePlan").mock(
        return_value=httpx.Response(200, text="<table></table>")
    )

    # Mock iCTSV endpoints
    respx.post(f"{settings.CTSV_API_BASE_URL}/User/GetUserInfo").mock(
        return_value=httpx.Response(200, json={"RespCode": 0, "FullName": "Nguyễn Văn A"})
    )
    respx.post(f"{settings.CTSV_API_BASE_URL}/User/GetStudentContact").mock(
        return_value=httpx.Response(200, json={"Data": {"Phone": "0912345678"}})
    )
    respx.post(f"{settings.CTSV_API_BASE_URL}/Criteria/GetCriteriaStudent").mock(
        return_value=httpx.Response(200, json={"RespCode": 0, "TotalPoint": 85.0})
    )
    respx.post(f"{settings.CTSV_API_BASE_URL}/Activity/GetListActivity").mock(
        return_value=httpx.Response(200, json={"Data": []})
    )
    respx.post(f"{settings.CTSV_API_BASE_URL}/User/GetUserMessage").mock(
        return_value=httpx.Response(200, json={"Data": []})
    )
    respx.post(f"{settings.CTSV_API_BASE_URL}/HWRecruitment/GetPublishRecruitment").mock(
        return_value=httpx.Response(200, json={"Data": []})
    )

    # Mock CTMS endpoints
    respx.get(f"{settings.CTMS_BASE_URL}/my/").mock(
        return_value=httpx.Response(200, text="<div></div>")
    )
    respx.get(f"{settings.CTMS_BASE_URL}/calendar/view.php?view=upcoming").mock(
        return_value=httpx.Response(200, text="<div></div>")
    )

    # Test tools via call_tool
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]
    assert len(tool_names) >= 20

    # Call summarizer
    res = await mcp_server.call_tool("hust_summarize_student", {})
    assert res is not None

    # Call ehust tools
    res_prof = await mcp_server.call_tool("ehust_get_student_profile", {})
    assert res_prof is not None

    res_tuition = await mcp_server.call_tool("ehust_get_tuition", {})
    assert res_tuition is not None

    res_grad = await mcp_server.call_tool("ehust_check_graduation_eligibility", {})
    assert res_grad is not None

    # Call ictsv tools
    res_drl = await mcp_server.call_tool("ictsv_get_training_points", {})
    assert res_drl is not None

    res_contact = await mcp_server.call_tool("ictsv_get_student_contact", {})
    assert res_contact is not None

    res_jobs = await mcp_server.call_tool("ictsv_search_jobs", {})
    assert res_jobs is not None
