from sqlalchemy import create_engine, text
from pathlib import Path

# Use the actual database file the app uses
app_data_dir = Path.home() / ".sageframe"
db_path = app_data_dir / "sageframe.db"

print(f"Updating default values in: {db_path}")

engine = create_engine(f'sqlite:///{db_path}')

with engine.connect() as conn:
    # SQLite doesn't support ALTER COLUMN DEFAULT, so we need to:
    # 1. Create new columns with correct defaults
    # 2. Copy data
    # 3. Drop old columns
    # 4. Rename new columns
    
    # But since there's no data, simpler to just recreate with correct defaults
    print("Recreating columns with lowercase defaults...")
    
    # Drop and recreate priority column
    conn.execute(text("CREATE TABLE tasks_temp AS SELECT * FROM tasks"))
    conn.execute(text("DROP TABLE tasks"))
    
    # Recreate with correct schema
    conn.execute(text("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            due_date DATETIME,
            status VARCHAR(50) NOT NULL DEFAULT 'todo',
            project_id INTEGER,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            user_id INTEGER,
            priority VARCHAR(6) NOT NULL DEFAULT 'medium',
            complexity VARCHAR(8) NOT NULL DEFAULT 'moderate',
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
    """))
    
    # Copy data back if any existed
    conn.execute(text("INSERT INTO tasks SELECT * FROM tasks_temp"))
    conn.execute(text("DROP TABLE tasks_temp"))
    
    # Recreate indexes
    conn.execute(text("CREATE INDEX ix_tasks_project_id ON tasks(project_id)"))
    conn.execute(text("CREATE INDEX ix_tasks_user_id ON tasks(user_id)"))
    conn.execute(text("CREATE INDEX ix_tasks_status ON tasks(status)"))
    
    conn.commit()
    print("✓ Schema recreated with correct defaults")

print("\nVerifying schema...")
from sqlalchemy import inspect
inspector = inspect(engine)
columns = inspector.get_columns('tasks')
for col in columns:
    default = col.get('default', 'No default')
    print(f"  {col['name']}: {col['type']} (default: {default})")
