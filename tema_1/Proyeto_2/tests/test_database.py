import pytest

from src import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_snap.db")
    database.init_db()


def test_save_and_get_url():
    database.save_url("abc123", "https://example.com")
    assert database.get_url("abc123") == "https://example.com"


def test_get_url_not_found():
    assert database.get_url("nope") is None


def test_code_exists():
    database.save_url("xyz789", "https://example.com")
    assert database.code_exists("xyz789") is True
    assert database.code_exists("nothere") is False


def test_list_urls():
    database.save_url("a1", "https://a.com")
    database.save_url("b2", "https://b.com")
    assert len(database.list_urls()) == 2
