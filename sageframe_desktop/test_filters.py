"""Test script for Story 3.4 tag filtering functionality.

This script:
1. Creates sample tasks with tags
2. Tests filter execution with single tag
3. Tests AND operator (all tags must match)
4. Tests OR operator (any tag must match)
5. Reports results and query performance
"""

import time

from app.database import SessionLocal, init_db
from app.modules.tasks.models import Task, TaskStatus, TaskPriority
from app.modules.tag_management.services import TagService
from app.modules.tag_management.filtering.models import (
    TagFilter, FilterGroup, FilterRule, FilterOperator
)


def main():
    """Run filter tests."""
    print("=== Story 3.4 Tag Filtering Test Suite ===\n")
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    session = SessionLocal()
    
    # Clean up any existing test data
    session.query(Task).delete()
    session.commit()
    
    # Initialize service
    tag_service = TagService()
    
    # Create sample tasks
    print("2. Creating sample tasks...")
    task1 = Task(
        title="Fix urgent bug",
        description="Critical production issue",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH
    )
    task2 = Task(
        title="Update documentation",
        description="Write user guide",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW
    )
    task3 = Task(
        title="Implement feature",
        description="Add new filter UI",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH
    )
    task4 = Task(
        title="Code review",
        description="Review PR #123",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM
    )
    
    session.add_all([task1, task2, task3, task4])
    session.commit()
    print(f"   Created 4 tasks (IDs: {task1.id}, {task2.id}, {task3.id}, {task4.id})")
    
    # Tag tasks
    print("3. Tagging tasks...")
    tag_service.tag_item("urgent", task1.id, "task")  # Task 1: @urgent
    tag_service.tag_item("bug", task1.id, "task")      # Task 1: @bug
    tag_service.tag_item("documentation", task2.id, "task")  # Task 2: @documentation
    tag_service.tag_item("urgent", task3.id, "task")  # Task 3: @urgent
    tag_service.tag_item("feature", task3.id, "task")  # Task 3: @feature
    tag_service.tag_item("review", task4.id, "task")  # Task 4: @review
    print("   Tagged tasks with @urgent, @bug, @documentation, @feature, @review")
    
    # Test 1: Single tag filter (@urgent)
    print("\n4. Test 1: Single tag filter (@urgent)")
    print("   Expected: Tasks 1 and 3")
    filter_urgent = TagFilter(
        groups=[
            FilterGroup(
                rules=[FilterRule(tag_name="urgent", include=True)],
                operator=FilterOperator.AND
            )
        ],
        group_operator=FilterOperator.AND
    )
    
    start = time.time()
    results = tag_service.filter_items(filter_urgent, Task, "task")
    elapsed = (time.time() - start) * 1000
    
    result_ids = sorted([t.id for t in results])
    print(f"   Results: Tasks {result_ids} ({len(results)} tasks)")
    print(f"   Query time: {elapsed:.2f}ms")
    assert result_ids == [task1.id, task3.id], f"Expected [{task1.id}, {task3.id}], got {result_ids}"
    print("   ✅ PASS")
    
    # Test 2: AND operator (must have BOTH @urgent AND @bug)
    print("\n5. Test 2: AND operator (@urgent AND @bug)")
    print("   Expected: Task 1 only")
    filter_and = TagFilter(
        groups=[
            FilterGroup(
                rules=[
                    FilterRule(tag_name="urgent", include=True),
                    FilterRule(tag_name="bug", include=True)
                ],
                operator=FilterOperator.AND
            )
        ],
        group_operator=FilterOperator.AND
    )
    
    start = time.time()
    results = tag_service.filter_items(filter_and, Task, "task")
    elapsed = (time.time() - start) * 1000
    
    result_ids = sorted([t.id for t in results])
    print(f"   Results: Tasks {result_ids} ({len(results)} task)")
    print(f"   Query time: {elapsed:.2f}ms")
    assert result_ids == [task1.id], f"Expected [{task1.id}], got {result_ids}"
    print("   ✅ PASS")
    
    # Test 3: OR operator (must have EITHER @urgent OR @documentation)
    print("\n6. Test 3: OR operator (@urgent OR @documentation)")
    print("   Expected: Tasks 1, 2, and 3")
    filter_or = TagFilter(
        groups=[
            FilterGroup(
                rules=[
                    FilterRule(tag_name="urgent", include=True),
                    FilterRule(tag_name="documentation", include=True)
                ],
                operator=FilterOperator.OR
            )
        ],
        group_operator=FilterOperator.AND
    )
    
    start = time.time()
    results = tag_service.filter_items(filter_or, Task, "task")
    elapsed = (time.time() - start) * 1000
    
    result_ids = sorted([t.id for t in results])
    print(f"   Results: Tasks {result_ids} ({len(results)} tasks)")
    print(f"   Query time: {elapsed:.2f}ms")
    assert result_ids == [task1.id, task2.id, task3.id], f"Expected [{task1.id}, {task2.id}, {task3.id}], got {result_ids}"
    print("   ✅ PASS")
    
    # Test 4: Exclude filter (NOT @urgent)
    print("\n7. Test 4: Exclude filter (NOT @urgent)")
    print("   Expected: Tasks 2 and 4")
    filter_exclude = TagFilter(
        groups=[
            FilterGroup(
                rules=[FilterRule(tag_name="urgent", include=False)],
                operator=FilterOperator.AND
            )
        ],
        group_operator=FilterOperator.AND
    )
    
    start = time.time()
    results = tag_service.filter_items(filter_exclude, Task, "task")
    elapsed = (time.time() - start) * 1000
    
    result_ids = sorted([t.id for t in results])
    print(f"   Results: Tasks {result_ids} ({len(results)} tasks)")
    print(f"   Query time: {elapsed:.2f}ms")
    assert result_ids == [task2.id, task4.id], f"Expected [{task2.id}, {task4.id}], got {result_ids}"
    print("   ✅ PASS")
    
    # Test 5: Complex nested filter
    print("\n8. Test 5: Complex filter (@urgent AND @bug) OR @documentation")
    print("   Expected: Tasks 1 and 2")
    filter_complex = TagFilter(
        groups=[
            FilterGroup(
                rules=[
                    FilterRule(tag_name="urgent", include=True),
                    FilterRule(tag_name="bug", include=True)
                ],
                operator=FilterOperator.AND
            ),
            FilterGroup(
                rules=[FilterRule(tag_name="documentation", include=True)],
                operator=FilterOperator.AND
            )
        ],
        group_operator=FilterOperator.OR
    )
    
    start = time.time()
    results = tag_service.filter_items(filter_complex, Task, "task")
    elapsed = (time.time() - start) * 1000
    
    result_ids = sorted([t.id for t in results])
    print(f"   Results: Tasks {result_ids} ({len(results)} tasks)")
    print(f"   Query time: {elapsed:.2f}ms")
    assert result_ids == [task1.id, task2.id], f"Expected [{task1.id}, {task2.id}], got {result_ids}"
    print("   ✅ PASS")
    
    # Cleanup
    session.close()
    
    print("\n=== All Tests Passed! ===")
    print("✅ Single tag filtering")
    print("✅ AND operator (all tags match)")
    print("✅ OR operator (any tag matches)")
    print("✅ Exclude filtering (NOT)")
    print("✅ Complex nested filters")
    print("\nStory 3.4 filtering functionality verified successfully!")


if __name__ == "__main__":
    main()
