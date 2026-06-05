"""Recalculate all Gain/Loss values based on the prior record for the same Name."""

from SQL import get_connection, load_runtime_config, TABLE_CONFIG


def fix_gain_loss() -> int:
    """Recalculate Gain/Loss for every row based on the previous row (by id) for the same Name."""
    table_name = TABLE_CONFIG["table_name"]
    load_runtime_config()
    connection = get_connection()
    updated = 0

    try:
        with connection.cursor() as cursor:
            # Fetch all rows ordered by id ASC
            cursor.execute(
                f"SELECT `id`, `Name`, `Weight`, `Gain_Loss` FROM `{table_name}` "
                "ORDER BY id ASC"
            )
            rows = cursor.fetchall()

            # Track the latest weight per Name
            latest_weight_by_name: dict[str, float] = {}

            for row in rows:
                row_id = row["id"]
                name = row["Name"]
                weight = float(row["Weight"])
                current_gain_loss = float(row["Gain_Loss"])

                # Calculate correct gain/loss
                if name in latest_weight_by_name:
                    correct_gain_loss = round(weight - latest_weight_by_name[name], 2)
                else:
                    correct_gain_loss = 0.0

                # Update if different
                if abs(correct_gain_loss - current_gain_loss) > 0.001:
                    cursor.execute(
                        f"UPDATE `{table_name}` SET `Gain_Loss` = %s WHERE `id` = %s",
                        (correct_gain_loss, row_id),
                    )
                    updated += 1
                    print(
                        f"  Row {row_id} ({name}): {current_gain_loss:+.2f} -> {correct_gain_loss:+.2f} "
                        f"(weight={weight}, prev={latest_weight_by_name.get(name, 'N/A')})"
                    )

                # Update tracking
                latest_weight_by_name[name] = weight

        connection.commit()
        print(f"\nFixed {updated} row(s).")
    finally:
        connection.close()

    return updated


if __name__ == "__main__":
    fix_gain_loss()
