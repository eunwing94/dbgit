from unittest.mock import MagicMock, patch

import pytest

from dbgit.config import EnvConfig
from dbgit.db import open_connection


@pytest.fixture
def cfg():
    return EnvConfig(
        name="T",
        host="127.0.0.1",
        port=1433,
        user="u",
        password="p",
        database="d",
        driver="ODBC Driver 18 for SQL Server",
    )


def test_open_connection_succeeds_first_try(cfg):
    mock_conn = MagicMock()
    with patch("dbgit.db.pyodbc.connect", return_value=mock_conn) as m:
        c = open_connection(cfg)
        assert c is mock_conn
        m.assert_called_once()


def test_open_connection_retries_then_success(cfg):
    mock_conn = MagicMock()
    with patch("dbgit.db.pyodbc.connect", side_effect=[ConnectionError("x"), mock_conn]) as m:
        with patch("dbgit.db.time.sleep"):
            c = open_connection(cfg)
            assert c is mock_conn
            assert m.call_count == 2


def test_open_connection_raises_after_retries(cfg):
    with patch("dbgit.db.pyodbc.connect", side_effect=ConnectionError("fail")):
        with patch("dbgit.db.time.sleep"):
            with pytest.raises(ConnectionError):
                open_connection(cfg)
