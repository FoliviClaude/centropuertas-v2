import pytest

from src import database, snap


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_snap.db")
    database.init_db()


def test_shorten_url_generates_code():
    code = snap.shorten_url("https://example.com/pagina-larga")
    assert len(code) == snap.CODE_LENGTH
    assert database.get_url(code) == "https://example.com/pagina-larga"


def test_shorten_url_empty_raises():
    with pytest.raises(ValueError):
        snap.shorten_url("")


def test_shorten_url_invalid_scheme_raises():
    with pytest.raises(ValueError):
        snap.shorten_url("ftp://example.com")


def test_resolve_short_code():
    code = snap.shorten_url("https://example.com")
    assert snap.resolve_short_code(code) == "https://example.com"


def test_resolve_short_code_not_found_raises():
    with pytest.raises(ValueError):
        snap.resolve_short_code("doesnotexist")


def test_get_all_urls():
    snap.shorten_url("https://a.com")
    snap.shorten_url("https://b.com")
    assert len(snap.get_all_urls()) == 2
