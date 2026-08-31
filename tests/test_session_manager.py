import pytest
from pathlib import Path
from hust_interface.core.session_manager import SessionManager
from hust_interface.models.auth_models import TokenInfo


def test_session_manager_save_and_load(tmp_path: Path):
    test_file = tmp_path / "test_session.json"
    mgr = SessionManager(storage_path=test_file)

    token = TokenInfo(access_token="abc123jwttoken")
    mgr.set_service_session(
        service_name="ictsv",
        token=token,
        student_id="20210001",
        student_name="Test Student"
    )

    # Re-instantiate session manager from same path
    mgr2 = SessionManager(storage_path=test_file)
    sess = mgr2.get_service_session("ictsv")
    assert sess is not None
    assert sess.is_authenticated is True
    assert sess.student_id == "20210001"
    assert sess.token is not None
    assert sess.token.access_token == "abc123jwttoken"

    # Test clear
    mgr2.clear_service_session("ictsv")
    assert mgr2.get_service_session("ictsv") is None
