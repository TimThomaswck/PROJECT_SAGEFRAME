"""Seed database with dummy PG/young professional tasks for testing."""

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.modules.tasks.models import Task, TaskStatus, TaskPriority, TaskComplexity
from app.modules.projects.models import Project

def seed_tasks():
    """Create dummy tasks related to PG studies and professional development."""
    session = SessionLocal()
    
    try:
        # Clear existing tasks
        session.query(Task).delete()
        session.query(Project).delete()
        
        # Create sample projects
        project_research = Project(
            name="Research Project",
            description="Postgraduate research project"
        )
        project_coursework = Project(
            name="Coursework & Assignments",
            description="PG coursework and academic assignments"
        )
        project_career = Project(
            name="Career Development",
            description="Professional development and networking"
        )
        
        session.add_all([project_research, project_coursework, project_career])
        session.commit()
        
        today = datetime.now().date()
        
        # Research-related tasks
        tasks = [
            Task(
                title="Literature review on machine learning applications",
                description="Read and summarize 15 key papers on ML in healthcare",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                complexity=TaskComplexity.COMPLEX,
                due_date=today + timedelta(days=7),
                project_id=project_research.id,
            ),
            Task(
                title="Prepare research proposal presentation",
                description="Create slides and speaker notes for supervisor meeting",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=3),
                project_id=project_research.id,
            ),
            Task(
                title="Analyze experimental data",
                description="Process and visualize results from experiment batch 3",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.COMPLEX,
                due_date=today + timedelta(days=5),
                project_id=project_research.id,
            ),
            Task(
                title="Write methodology section",
                description="Draft the methodology chapter for thesis (2000-2500 words)",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=10),
                project_id=project_research.id,
            ),
            
            # Coursework tasks
            Task(
                title="Complete advanced statistics assignment",
                description="Solve problem set 5 and submit",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=2),
                project_id=project_coursework.id,
            ),
            Task(
                title="Read textbook chapters 8-10",
                description="Read and annotate 'Advanced Data Science Concepts'",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.SIMPLE,
                due_date=today + timedelta(days=4),
                project_id=project_coursework.id,
            ),
            Task(
                title="Peer review group project",
                description="Review 2 peer projects and provide feedback",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.SIMPLE,
                due_date=today + timedelta(days=6),
                project_id=project_coursework.id,
            ),
            Task(
                title="Attend seminar on research ethics",
                description="Attend Wednesday 2pm seminar + submit reflection",
                status=TaskStatus.DONE,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.SIMPLE,
                due_date=today - timedelta(days=1),
                project_id=project_coursework.id,
            ),
            
            # Career development tasks
            Task(
                title="Update CV and LinkedIn profile",
                description="Add recent publications and project work",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.SIMPLE,
                due_date=today + timedelta(days=8),
                project_id=project_career.id,
            ),
            Task(
                title="Prepare for industry networking event",
                description="Research companies attending, prepare pitch",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=3),
                project_id=project_career.id,
            ),
            Task(
                title="Apply for internship opportunities",
                description="Research and apply to 3 relevant internships",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=14),
                project_id=project_career.id,
            ),
            Task(
                title="Schedule meeting with career advisor",
                description="Book 1-hour session to discuss postdoc options",
                status=TaskStatus.TODO,
                priority=TaskPriority.LOW,
                complexity=TaskComplexity.SIMPLE,
                due_date=today + timedelta(days=21),
                project_id=project_career.id,
            ),
            Task(
                title="Complete Python skills certification",
                description="Online course: Advanced Python for Data Science",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=30),
                project_id=project_career.id,
            ),
            
            # Additional mixed tasks
            Task(
                title="Fix bugs in experimental code",
                description="Debug data pipeline issues from last run",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                complexity=TaskComplexity.MODERATE,
                due_date=today + timedelta(days=1),
                project_id=project_research.id,
            ),
            Task(
                title="Attend lab meeting and present progress",
                description="Monthly lab meeting - 15 min presentation slot",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.SIMPLE,
                due_date=today + timedelta(days=2),
                project_id=project_research.id,
            ),
        ]
        
        session.add_all(tasks)
        session.commit()
        
        print(f"\n✅ Seeded database with {len(tasks)} tasks!")
        print(f"Projects created: {len([project_research, project_coursework, project_career])}")
        print("\nSample tasks created:")
        for i, task in enumerate(tasks, 1):
            priority_str = task.priority if isinstance(task.priority, str) else task.priority.value
            due_str = task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A"
            print(f"  {i}. {task.title} (Priority: {priority_str}, Due: {due_str})")
        
    except Exception as e:
        print(f"❌ Error seeding tasks: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_tasks()
