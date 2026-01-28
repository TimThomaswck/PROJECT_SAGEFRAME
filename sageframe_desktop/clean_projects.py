"""
Script to clean up dummy projects and retain only relevant student/young professional projects.
"""
from app.database import SessionLocal, init_db
from app.modules.projects.models import Project
from app.modules.tasks.models import Task

# Initialize database first
init_db()

# Define projects to keep (student/young professional themed)
KEEP_PROJECTS = {
    "📚 Semester Project",
    "💼 Internship Portfolio",
    "🎓 Thesis Research",
    "🚀 Side Project",
    "📱 Portfolio App",
}

def clean_projects():
    """Remove dummy projects, keep only relevant ones."""
    session = SessionLocal()
    
    try:
        projects = session.query(Project).all()
        print(f"Total projects in database: {len(projects)}")
        
        # List all projects
        print("\nCurrent projects:")
        for p in projects:
            print(f"  - {p.name} (ID: {p.id}, Description: {p.description or 'None'})")
        
        # Delete projects not in keep list
        deleted_count = 0
        for project in projects:
            if project.name not in KEEP_PROJECTS:
                print(f"\nDeleting: {project.name}")
                session.delete(project)
                deleted_count += 1
        
        session.commit()
        print(f"\n✓ Deleted {deleted_count} projects")
        
        # Create new projects if needed
        keep_names = {p.name for p in projects if p.name in KEEP_PROJECTS}
        for project_name in KEEP_PROJECTS:
            if project_name not in keep_names:
                # Extract emoji and name
                parts = project_name.split(' ', 1)
                emoji = parts[0]
                name = parts[1] if len(parts) > 1 else project_name
                
                descriptions = {
                    "📚 Semester Project": "Academic coursework and semester assignments",
                    "💼 Internship Portfolio": "Projects and experience from internship",
                    "🎓 Thesis Research": "Research and thesis project work",
                    "🚀 Side Project": "Personal project for learning and portfolio building",
                    "📱 Portfolio App": "Application to showcase skills and work",
                }
                
                new_project = Project(
                    name=project_name,
                    description=descriptions.get(project_name, "")
                )
                session.add(new_project)
                print(f"✓ Created: {project_name}")
        
        session.commit()
        
        # Show final state
        final_projects = session.query(Project).all()
        print(f"\nFinal project count: {len(final_projects)}")
        print("Final projects:")
        for p in final_projects:
            print(f"  - {p.name}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clean_projects()
