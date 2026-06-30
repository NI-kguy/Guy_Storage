"""Unit tests for SQL.py database functions (mocked connection)."""

from unittest.mock import MagicMock, patch

import pytest

from SQL import (
    insert_data,
    read_distinct_names,
    read_graph_data,
    read_graph_data_by_name,
    read_latest_data,
    read_latest_weight_by_name,
    read_paginated_data,
    remove_data,
    update_data,
)


@pytest.fixture()
def mock_conn():
    """Provide a mocked database connection and cursor."""
    with patch("SQL.get_connection") as mock_get:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = conn
        yield conn, cursor


class TestInsertData:
    def test_insert_empty_returns_zero(self, mock_conn):
        assert insert_data([]) == 0

    def test_insert_missing_column_raises(self, mock_conn):
        with pytest.raises(ValueError, match="missing required columns"):
            insert_data([{"Name": "Alice"}])

    def test_insert_calls_executemany(self, mock_conn):
        conn, cursor = mock_conn
        cursor.rowcount = 1
        result = insert_data([
            {"Name": "A", "Day": "2026-05-19", "Weight": 70.0, "Gain_Loss": 0.0}
        ])
        assert result == 1
        cursor.executemany.assert_called_once()


class TestUpdateData:
    def test_update_empty_returns_zero(self, mock_conn):
        assert update_data(1, {}) == 0

    def test_update_calls_execute(self, mock_conn):
        conn, cursor = mock_conn
        cursor.rowcount = 1
        result = update_data(42, {"Weight": 75.0, "Gain_Loss": -1.0})
        assert result == 1
        cursor.execute.assert_called_once()
        sql_arg = cursor.execute.call_args[0][0]
        assert "UPDATE" in sql_arg
        assert "WHERE id = %s" in sql_arg


class TestRemoveData:
    def test_remove_by_id(self, mock_conn):
        conn, cursor = mock_conn
        cursor.rowcount = 1
        result = remove_data(row_id=5)
        assert result == 1
        sql_arg = cursor.execute.call_args[0][0]
        assert "WHERE id = %s" in sql_arg

    def test_remove_all(self, mock_conn):
        conn, cursor = mock_conn
        cursor.rowcount = 10
        result = remove_data(row_id=None)
        assert result == 10


class TestReadLatestData:
    def test_returns_list(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchall.return_value = [
            {"id": 1, "Name": "X", "Day": "2026-01-01", "Weight": 70}
        ]
        rows = read_latest_data(5)
        assert len(rows) == 1
        assert rows[0]["Name"] == "X"


class TestReadPaginatedData:
    def test_returns_rows_and_count(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchone.return_value = {"cnt": 50}
        cursor.fetchall.return_value = [{"id": 1}]
        rows, total = read_paginated_data(page=1, page_size=20)
        assert total == 50
        assert len(rows) == 1

    def test_offset_calculation(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchone.return_value = {"cnt": 100}
        cursor.fetchall.return_value = []
        read_paginated_data(page=3, page_size=20)
        # Second execute call should have LIMIT 20 OFFSET 40
        calls = cursor.execute.call_args_list
        assert len(calls) == 2
        params = calls[1][0][1]
        assert params == (20, 40)


class TestReadLatestWeightByName:
    def test_returns_weight(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchone.return_value = {"Weight": 72.5}
        result = read_latest_weight_by_name("Alice")
        assert result == 72.5

    def test_returns_none_when_no_record(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchone.return_value = None
        result = read_latest_weight_by_name("Nobody")
        assert result is None


class TestReadDistinctNames:
    def test_returns_names(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchall.return_value = [
            {"Name": "Alice"},
            {"Name": "Bob"},
        ]
        names = read_distinct_names()
        assert names == ["Alice", "Bob"]


class TestReadGraphData:
    def test_returns_all_data(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchall.return_value = [
            {"Day": "2026-01-01", "Weight": 70, "Gain_Loss": 0}
        ]
        rows = read_graph_data()
        assert len(rows) == 1


class TestReadGraphDataByName:
    def test_filters_by_name(self, mock_conn):
        conn, cursor = mock_conn
        cursor.fetchall.return_value = [
            {"Day": "2026-01-01", "Weight": 70, "Gain_Loss": 0}
        ]
        rows = read_graph_data_by_name("Alice")
        assert len(rows) == 1
        sql_arg = cursor.execute.call_args[0][0]
        assert "WHERE `Name` = %s" in sql_arg
