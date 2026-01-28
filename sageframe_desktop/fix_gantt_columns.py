"""Add Gantt-related columns to tasks table if missing.

Columns added:
- start_date (DATETIME, nullable)
- end_date (DATETIME, nullable)
- depends_on_task_id (INTEGER, nullable)
- dependency_type (VARCHAR(32), nullable)
"""

from pathlib import Path
from sqlalchemy import create_engine, text, inspect

APP_DATA_DIR = Path.home() / ".sageframe"
DB_PATH = APP_DATA_DIR / "sageframe.db"

COLUMNS = [
    ("start_date", "DATETIME"),
    ("end_date", "DATETIME"),
    ("depends_on_task_id", "INTEGER"),
    ("dependency_type", "VARCHAR(32)"),
]


def has_column(inspector, table_name: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table_name))


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Skipping.")
        return

    engine = create_engine(f"sqlite:///{DB_PATH}")
    inspector = inspect(engine)

    if "tasks" not in inspector.get_table_names():
        print("tasks table not found; nothing to migrate.")
        return

    with engine.connect() as conn:
        for col_name, col_type in COLUMNS:
            inspector = inspect(engine)  # refresh per iteration
            if has_column(inspector, "tasks", col_name):
                print(f"✓ Column '{col_name}' already exists")
                continue
            try:
                conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"✓ Added column '{col_name}' ({col_type})")
            except Exception as exc:
                print(f"⚠️ Failed to add column '{col_name}': {exc}")
                conn.rollback()

        # Show resulting schema
        inspector = inspect(engine)
        print("\nUpdated tasks columns:")
        for col in inspector.get_columns("tasks"):
            print(f"  {col['name']}: {col['type']}")


if __name__ == "__main__":
    main()
