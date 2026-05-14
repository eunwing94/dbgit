import os

import pytest

from dbgit import db as db_module


def test_odbc_login_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DBGIT_ODBC_LOGIN_TIMEOUT_SEC", raising=False)
    assert db_module._odbc_login_timeout_sec() == 60


def test_odbc_login_timeout_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DBGIT_ODBC_LOGIN_TIMEOUT_SEC", "9999")
    assert db_module._odbc_login_timeout_sec() == 600
    monkeypatch.setenv("DBGIT_ODBC_LOGIN_TIMEOUT_SEC", "2")
    assert db_module._odbc_login_timeout_sec() == 5
