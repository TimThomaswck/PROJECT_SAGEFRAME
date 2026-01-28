from sqlalchemy import create_engine, text
from pathlib import Path

# Use the actual database file the app uses
app_data_dir = Path.home() / ".sageframe"
db_path = app_data_dir / "sageframe.db"

print(f"Checking database: {db_path}")

engine = create_engine(f'sqlite:///{db_path}')

with engine.connect() as conn:
    # Check if there are any tasks
    result = conn.execute(text("SELECT COUNT(*) FROM tasks"))
    count = result.scalar()
    print(f"\nTotal tasks: {count}")
    
    if count > 0:
        # Check actual values in priority/complexity columns
        result = conn.execute(text("SELECT id, title, priority, complexity FROM tasks LIMIT 10"))
        print("\nTask values:")
        for row in result:
            print(f"  ID {row[0]}: {row[1]}")
            print(f"    priority: '{row[2]}' (type: {type(row[2]).__name__})")
            print(f"    complexity: '{row[3]}' (type: {type(row[3]).__name__})")
