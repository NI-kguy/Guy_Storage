"""One-time migration: convert YYYY-MM-DD date strings in the Day column to weekday names."""

import datetime

from SQL import get_connection, load_runtime_config, TABLE_CONFIG


def migrate_days_to_weekday_names() -> int:
    """Update all rows where Day looks like a date (YYYY-MM-DD) to the weekday name."""
    table_name = TABLE_CONFIG["table_name"]
    load_runtime_config()
    connection = get_connection()
    updated = 0

    try:
        with connection.cursor() as cursor:
            # Fetch all rows that have a date-like Day value
            cursor.execute(
                f"SELECT `id`, `Day` FROM `{table_name}` "
                "WHERE `Day` REGEXP '^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$'"
            )
            rows = cursor.fetchall()

            print(f"Found {len(rows)} row(s) with date format to migrate.")

            for row in rows:
                row_id = row["id"]
                date_str = row["Day"]
                try:
                    d = datetime.date.fromisoformat(date_str)
                    weekday_name = d.strftime("%A")
                except (ValueError, TypeError):
                    print(f"  Skipping row {row_id}: cannot parse '{date_str}'")
                    continue

                cursor.execute(
                    f"UPDATE `{table_name}` SET `Day` = %s WHERE `id` = %s",
                    (weekday_name, row_id),
                )
                updated += 1
                print(f"  Row {row_id}: '{date_str}' -> '{weekday_name}'")

        connection.commit()
        print(f"\nMigration complete. Updated {updated} row(s).")
    finally:
        connection.close()

    return updated


if __name__ == "__main__":
    migrate_days_to_weekday_names()
