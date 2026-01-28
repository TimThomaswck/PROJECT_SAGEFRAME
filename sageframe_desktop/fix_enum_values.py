from sqlalchemy import create_engine, text
from pathlib import Path

# Use the actual database file the app uses
app_data_dir = Path.home() / ".sageframe"
db_path = app_data_dir / "sageframe.db"

print(f"Fixing enum values in: {db_path}")

engine = create_engine(f'sqlite:///{db_path}')

with engine.connect() as conn:
    # Update priority values to lowercase
    result = conn.execute(text("UPDATE tasks SET priority = LOWER(priority)"))
    print(f"✓ Updated {result.rowcount} priority values to lowercase")
    
    # Update complexity values to lowercase
    result = conn.execute(text("UPDATE tasks SET complexity = LOWER(complexity)"))
    print(f"✓ Updated {result.rowcount} complexity values to lowercase")
    
    conn.commit()

print("\nVerifying values...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT DISTINCT priority, complexity FROM tasks"))
    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"  priority: {row[0]}, complexity: {row[1]}")
    else:
        print("  (no tasks in database)")
