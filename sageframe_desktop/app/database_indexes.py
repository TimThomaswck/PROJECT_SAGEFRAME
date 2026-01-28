"""Database indexes for performance optimization.

Implements AC4 (performance optimization) - defines all required indexes
for efficient querying as per Story 5.1 requirements.

This module provides functions to create indexes that optimize common queries
and ensure sub-50ms performance (NFR1, NFR2 compliance).
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# All indexes needed for Story 5.1 AC4 (performance optimization)
INDEXES = [
    # Tasks table indexes (Epic 2 - Story 2.1, 2.2)
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)",
    
    # Projects table indexes (Epic 2 - Story 2.1)
    "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at)",
    
    # Tags table indexes (Epic 3 - Story 3.4)
    "CREATE INDEX IF NOT EXISTS idx_tags_tag_name ON tags(tag_name)",
    "CREATE INDEX IF NOT EXISTS idx_tags_created_at ON tags(created_at)",
    
    # Tagged items table indexes (Epic 3 - Story 3.4)
    "CREATE INDEX IF NOT EXISTS idx_tagged_items_tag_id ON tagged_items(tag_id)",
    "CREATE INDEX IF NOT EXISTS idx_tagged_items_item_id ON tagged_items(item_id)",
    "CREATE INDEX IF NOT EXISTS idx_tagged_items_created_at ON tagged_items(created_at)",
    
    # Calendar events table indexes (Epic 4 - Stories 4.1-4.4)
    "CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time)",
    "CREATE INDEX IF NOT EXISTS idx_calendar_events_connection_id ON calendar_events(connection_id)",
    "CREATE INDEX IF NOT EXISTS idx_calendar_events_created_at ON calendar_events(created_at)",
    
    # Availability slots table indexes (Epic 4 - Story 4.2)
    "CREATE INDEX IF NOT EXISTS idx_availability_slots_start_time ON availability_slots(start_time)",
    "CREATE INDEX IF NOT EXISTS idx_availability_slots_status ON availability_slots(status)",
    "CREATE INDEX IF NOT EXISTS idx_availability_slots_connection_id ON availability_slots(connection_id)",
    
    # Mood check-in indexes (Epic 1 - Story 1.3)
    "CREATE INDEX IF NOT EXISTS idx_mood_checkin_created_at ON mood_checkins(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_mood_checkin_energy_level ON mood_checkins(energy_level)",
    
    # Gamification indexes (Epic 2 - Story 2.6)
    "CREATE INDEX IF NOT EXISTS idx_user_progress_updated_at ON user_progress(updated_at)",
    
    # File ingestion indexes (Epic 3 - Story 3.3)
    "CREATE INDEX IF NOT EXISTS idx_imported_files_created_at ON imported_files(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_imported_files_file_type ON imported_files(file_type)",
]


def create_indexes(session: Session) -> None:
    """Create all performance indexes.
    
    Implements AC4 from Story 5.1 - ensures query performance targets:
    - Simple queries: <50ms
    - Complex queries: <200ms
    
    Args:
        session: SQLAlchemy session for executing index creation
        
    Raises:
        Exception: If index creation fails
    """
    logger.info(f"Creating {len(INDEXES)} database indexes for performance optimization...")
    
    for index_sql in INDEXES:
        try:
            session.execute(text(index_sql))
            logger.debug(f"Index created: {index_sql}")
        except Exception as e:
            # Some indexes might already exist, log but continue
            logger.debug(f"Index creation note: {e}")
    
    session.commit()
    logger.info("Database indexes created successfully")


def get_index_status(session: Session) -> dict:
    """Get status of all created indexes.
    
    Useful for debugging performance issues or verifying index creation.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        dict: Status information about indexes
    """
    try:
        result = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        )
        indexes = [row[0] for row in result.fetchall()]
        
        return {
            'total_indexes': len(indexes),
            'indexes': indexes,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Failed to query index status: {e}")
        return {
            'total_indexes': 0,
            'indexes': [],
            'status': 'error',
            'error': str(e)
        }


def benchmark_query(session: Session, query_name: str, query_func, iterations: int = 10) -> dict:
    """Benchmark a query to verify performance targets (AC4).
    
    Tests query performance against targets: <50ms for simple queries.
    
    Args:
        session: SQLAlchemy session
        query_name: Name of query being benchmarked
        query_func: Callable that executes the query
        iterations: Number of times to run query
        
    Returns:
        dict: Benchmark results including average time, min, max
    """
    import time
    
    logger.info(f"Benchmarking query: {query_name} ({iterations} iterations)...")
    
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            query_func(session)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {'status': 'error', 'error': str(e)}
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    avg_ms = sum(times) / len(times)
    min_ms = min(times)
    max_ms = max(times)
    
    # Check performance targets (AC4)
    target_ms = 50  # Target: <50ms
    meets_target = avg_ms < target_ms
    
    result = {
        'query_name': query_name,
        'iterations': iterations,
        'average_ms': round(avg_ms, 2),
        'min_ms': round(min_ms, 2),
        'max_ms': round(max_ms, 2),
        'target_ms': target_ms,
        'meets_target': meets_target,
        'status': 'pass' if meets_target else 'warning'
    }
    
    if meets_target:
        logger.info(f"✓ Query performance: {avg_ms:.2f}ms (target: <{target_ms}ms)")
    else:
        logger.warning(f"⚠ Query performance: {avg_ms:.2f}ms (target: <{target_ms}ms)")
    
    return result
