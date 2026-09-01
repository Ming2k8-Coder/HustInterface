import pytest
from pathlib import Path
from hust_interface.core.session_manager import session_manager

@pytest.fixture(autouse=True)
def isolate_session_manager(tmp_path, monkeypatch):
    """
    Isolates pytest tests from the real user's ~/.hust_interface/session_cache.json
    so that unit tests do not overwrite the user's live cookies.
    """
    test_storage = tmp_path / "test_session_cache.json"
    monkeypatch.setattr(session_manager, "storage_path", test_storage)
    session_manager.cache = session_manager._load_cache()
    yield

