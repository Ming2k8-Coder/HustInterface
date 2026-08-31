import pytest
from datetime import datetime
from hust_interface.auth.manual_auth import ManualAuthenticator
from hust_interface.core.session_manager import session_manager


def test_manual_set_ictsv_token():
    token = "Bearer test_dummy_token_123"
    sess = ManualAuthenticator.set_ictsv_token(token)
    assert sess.token is not None
    assert sess.token.access_token == "test_dummy_token_123"
    assert sess.headers["Authorization"] == "Bearer test_dummy_token_123"


def test_manual_set_ehust_cookie():
    cookie_str = "JSESSIONID=dummy_jsession_id_123; token=dummy_token_abc"
    sess = ManualAuthenticator.set_ehust_cookie(cookie_str, student_id="20210001")
    assert sess.cookies["JSESSIONID"] == "dummy_jsession_id_123"
    assert sess.cookies["token"] == "dummy_token_abc"
    assert sess.student_id == "20210001"


def test_manual_set_ctms_cookie():
    cookie_str = "MoodleSession=moodle_session_val_999"
    sess = ManualAuthenticator.set_ctms_cookie(cookie_str, student_id="20210002")
    assert sess.cookies["MoodleSession"] == "moodle_session_val_999"
    assert sess.student_id == "20210002"
