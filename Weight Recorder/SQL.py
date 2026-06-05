import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv


_CONFIG_LOADED = False

TABLE_CONFIG = {
    "table_name": "Weight_Log",
    "columns": [
        ("id", "BIGINT PRIMARY KEY AUTO_INCREMENT"),
        ("Name", "VARCHAR(100) NOT NULL"),
        ("Day", "VARCHAR(50) NOT NULL"),
        ("Weight", "DECIMAL(6,2) NOT NULL"),
        ("Gain_Loss", "DECIMAL(6,2) NOT NULL"),
        ("created_at", "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"),
    ],
    "insert_columns": ["Name", "Day", "Weight", "Gain_Loss"],
}


def _cfg(key: str, override=None):
    return TABLE_CONFIG[key] if override is None else override


def _is_default_local(value: str | None) -> bool:
    """Return True when value is empty or points to local defaults."""
    if not value:
        return True
    return value.strip().lower() in {"localhost", "127.0.0.1"}


def load_runtime_config() -> None:
    """Load .env file into environment variables (executed only once)."""
    global _CONFIG_LOADED
    if _CONFIG_LOADED:
        return

    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)

    # Fallback for packaged runs where .env may be missing.
    # Importing the module ensures PyInstaller can bundle it.
    try:
        import db_config as cfg  # type: ignore

        cfg_host = getattr(cfg, "DB_HOST", None)
        if _is_default_local(os.getenv("DB_HOST")) and cfg_host:
            os.environ["DB_HOST"] = str(cfg_host)

        cfg_port = getattr(cfg, "DB_PORT", None)
        if os.getenv("DB_PORT") in (None, "", "3306") and cfg_port is not None:
            os.environ["DB_PORT"] = str(cfg_port)

        for key in ("DB_USER", "DB_PASSWORD", "DB_NAME", "DB_TIMEOUT"):
            value = getattr(cfg, key, None)
            if value is not None and not os.getenv(key):
                os.environ[key] = str(value)
    except ModuleNotFoundError:
        pass

    _CONFIG_LOADED = True


def get_connection() -> pymysql.connections.Connection:
    """Establish and return a database connection."""
    load_runtime_config()
    timeout = int(os.getenv("DB_TIMEOUT", "10"))
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        db=os.getenv("DB_NAME", "defaultdb"),
        connect_timeout=timeout,
        read_timeout=timeout,
        write_timeout=timeout,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def create_table(
    table_name: str | None = None,
    columns: list[tuple[str, str]] | None = None,
) -> None:
    """Create the table if it doesn't already exist."""
    table_name = _cfg("table_name", table_name)
    columns = _cfg("columns", columns)
    column_sql = ",\n    ".join(
        f"`{name}` {definition}" for name, definition in columns
    )
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        {column_sql}
    )
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(ddl)
            cursor.execute(
                f"ALTER TABLE `{table_name}` "
                "MODIFY COLUMN `Day` VARCHAR(50) NOT NULL"
            )
        connection.commit()
    finally:
        connection.close()


def insert_data(
    rows: list[dict],
    table_name: str | None = None,
    insert_columns: list[str] | None = None,
) -> int:
    """Insert one or more rows into the database table.

    Returns:
        Number of rows inserted.
    """
    if not rows:
        return 0

    table_name = _cfg("table_name", table_name)
    insert_columns = _cfg("insert_columns", insert_columns)
    if not insert_columns:
        raise ValueError("insert_columns cannot be empty")

    column_list_sql = ", ".join(f"`{col}`" for col in insert_columns)
    placeholders_sql = ", ".join(["%s"] * len(insert_columns))
    sql = f"""
    INSERT INTO `{table_name}` ({column_list_sql})
    VALUES ({placeholders_sql})
    """

    values = []
    for row in rows:
        missing = [col for col in insert_columns if col not in row]
        if missing:
            raise ValueError(f"Row is missing required columns: {missing}")
        values.append(tuple(row[col] for col in insert_columns))

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.executemany(sql, values)
            inserted = cursor.rowcount
        connection.commit()
        return inserted
    finally:
        connection.close()


def update_data(
    row_id: int,
    updates: dict,
    table_name: str | None = None,
) -> int:
    """Update a single row by id.

    Args:
        row_id: The row id to update.
        updates: Dict of column_name -> new_value.

    Returns:
        Number of rows affected (0 or 1).
    """
    if not updates:
        return 0

    table_name = _cfg("table_name", table_name)
    set_clause = ", ".join(f"`{col}` = %s" for col in updates)
    values = list(updates.values()) + [row_id]
    sql = f"UPDATE `{table_name}` SET {set_clause} WHERE id = %s"

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            affected = cursor.rowcount
        connection.commit()
        return affected
    finally:
        connection.close()


def remove_data(table_name: str | None = None, row_id: int | None = None) -> int:
    """Delete row(s) from the database table.

    Args:
        row_id: Row id to delete; if None, deletes ALL rows.

    Returns:
        Number of rows deleted.
    """
    table_name = _cfg("table_name", table_name)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if row_id is None:
                cursor.execute(f"DELETE FROM `{table_name}`")
            else:
                cursor.execute(
                    f"DELETE FROM `{table_name}` WHERE id = %s", (row_id,)
                )
            deleted = cursor.rowcount
        connection.commit()
        return deleted
    finally:
        connection.close()


def read_latest_data(limit: int = 20, table_name: str | None = None) -> list[dict]:
    """Read the most recent rows ordered by id DESC."""
    table_name = _cfg("table_name", table_name)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM `{table_name}` ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            return cursor.fetchall()
    finally:
        connection.close()


def read_paginated_data(
    page: int = 1,
    page_size: int = 20,
    table_name: str | None = None,
) -> tuple[list[dict], int]:
    """Fetch a page of rows and total count.

    Returns:
        Tuple of (rows, total_count).
    """
    table_name = _cfg("table_name", table_name)
    offset = (page - 1) * page_size
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table_name}`")
            total = cursor.fetchone()["cnt"]
            cursor.execute(
                f"SELECT * FROM `{table_name}` ORDER BY id DESC "
                "LIMIT %s OFFSET %s",
                (page_size, offset),
            )
            rows = cursor.fetchall()
        return rows, total
    finally:
        connection.close()


def read_latest_weight_by_name(
    name: str, table_name: str | None = None, before_id: int | None = None
) -> float | None:
    """Get the most recent weight for a given Name.

    Args:
        name: The user name to look up.
        before_id: If provided, only consider rows with id < before_id.

    Returns:
        The weight as float, or None if no record exists.
    """
    table_name = _cfg("table_name", table_name)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if before_id is not None:
                cursor.execute(
                    f"SELECT `Weight` FROM `{table_name}` "
                    "WHERE `Name` = %s AND `id` < %s ORDER BY id DESC LIMIT 1",
                    (name, before_id),
                )
            else:
                cursor.execute(
                    f"SELECT `Weight` FROM `{table_name}` "
                    "WHERE `Name` = %s ORDER BY id DESC LIMIT 1",
                    (name,),
                )
            row = cursor.fetchone()
            if row:
                return float(row["Weight"])
            return None
    finally:
        connection.close()


def read_distinct_names(table_name: str | None = None) -> list[str]:
    """Get all distinct Names from the table."""
    table_name = _cfg("table_name", table_name)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT DISTINCT `Name` FROM `{table_name}` ORDER BY `Name`"
            )
            return [row["Name"] for row in cursor.fetchall()]
    finally:
        connection.close()


def read_graph_data(table_name: str | None = None) -> list[dict]:
    """Read created_at, Weight, Gain_Loss for graphing (all users, oldest first)."""
    table_name = _cfg("table_name", table_name)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT `created_at`, `Weight`, `Gain_Loss` FROM `{table_name}` "
                "ORDER BY id ASC"
            )
            return cursor.fetchall()
    finally:
        connection.close()


def read_graph_data_by_name(
    name: str, table_name: str | None = None
) -> list[dict]:
    """Read created_at, Weight, Gain_Loss for a specific Name (oldest first)."""
    table_name = _cfg("table_name", table_name)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT `created_at`, `Weight`, `Gain_Loss` FROM `{table_name}` "
                "WHERE `Name` = %s ORDER BY id ASC",
                (name,),
            )
            return cursor.fetchall()
    finally:
        connection.close()


if __name__ == "__main__":
    load_runtime_config()
    create_table()
    count = insert_data([
        {"Name": "Kevin", "Day": "2026-04-10", "Weight": 80.5, "Gain_Loss": 0.0},
        {"Name": "Kevin", "Day": "2026-04-11", "Weight": 80.0, "Gain_Loss": -0.5},
    ])
    print(f"Inserted {count} rows")
