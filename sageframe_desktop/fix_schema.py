from sqlalchemy import create_engine, text
from pathlib import Path

# Use the actual database file the app uses
app_data_dir = Path.home() / ".sageframe"
db_path = app_data_dir / "sageframe.db"

print(f"Adding missing columns to: {db_path}")

engine = create_engine(f'sqlite:///{db_path}')

with engine.connect() as conn:
    try:
        # Add priority column
        conn.execute(text("ALTER TABLE tasks ADD COLUMN priority VARCHAR(6) NOT NULL DEFAULT 'MEDIUM'"))
        conn.commit()
        print("✓ Added priority column")
    except Exception as e:
        print(f"Priority column: {e}")
    
    try:
        # Add complexity column  
        conn.execute(text("ALTER TABLE tasks ADD COLUMN complexity VARCHAR(8) NOT NULL DEFAULT 'MODERATE'"))
        conn.commit()
        print("✓ Added complexity column")
    except Exception as e:
        print(f"Complexity column: {e}")

print("\nVerifying...")
from sqlalchemy import inspect
inspector = inspect(engine)
columns = inspector.get_columns('tasks')
print("\nCurrent columns:")
for col in columns:
    print(f"  {col['name']}: {col['type']}")
