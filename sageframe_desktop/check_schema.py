from sqlalchemy import create_engine, inspect
from pathlib import Path

# Check the actual database file the app uses
app_data_dir = Path.home() / ".sageframe"
db_path = app_data_dir / "sageframe.db"

print(f"Checking database: {db_path}")
print(f"Database exists: {db_path.exists()}")
print("-" * 40)

engine = create_engine(f'sqlite:///{db_path}')
inspector = inspect(engine)

if 'tasks' in inspector.get_table_names():
    print("Tasks table columns:")
    columns = inspector.get_columns('tasks')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
else:
    print("ERROR: tasks table does not exist!")
    print(f"Available tables: {inspector.get_table_names()}")
