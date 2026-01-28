"""Create user_progress table for gamification.

This script creates the user_progress table to track XP, levels, and task completion counts.
"""

import sqlite3
from pathlib import Path


def create_user_progress_table():
    """Create user_progress table if it doesn't exist."""
    # Get database path
    db_path = Path.home() / ".sageframe" / "sageframe.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='user_progress'
    """)
    
    if cursor.fetchone() is None:
        print("Creating user_progress table...")
        
        cursor.execute("""
            CREATE TABLE user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                current_xp INTEGER NOT NULL DEFAULT 0,
                current_level INTEGER NOT NULL DEFAULT 1,
                total_tasks_completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on user_id
        cursor.execute("""
            CREATE INDEX ix_user_progress_user_id ON user_progress (user_id)
        """)
        
        # Insert default record for single-user mode
        cursor.execute("""
            INSERT INTO user_progress (user_id, current_xp, current_level, total_tasks_completed)
            VALUES (1, 0, 1, 0)
        """)
        
        conn.commit()
        print("user_progress table created successfully.")
    else:
        print("user_progress table already exists.")
    
    conn.close()


if __name__ == "__main__":
    create_user_progress_table()
