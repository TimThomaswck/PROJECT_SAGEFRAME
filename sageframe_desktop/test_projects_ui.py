#!/usr/bin/env python
"""Quick test script to preview project management dialogs.

This demonstrates the implemented UI components before main window integration.
Run: python test_projects_ui.py
"""

import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from app.modules.projects.view_models import ProjectViewModel
from app.modules.projects.views import (
    ProjectCreateDialog,
    ProjectViewWidget,
    ProjectEditDialog
)


class ProjectTestWindow(QWidget):
    """Simple test window to demonstrate project dialogs."""
    
    def __init__(self):
        super().__init__()
        self.view_model = ProjectViewModel()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the test UI."""
        self.setWindowTitle("Project Management Test")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Test buttons
        create_btn = QPushButton("Test Create Project Dialog")
        create_btn.clicked.connect(self.show_create_dialog)
        
        view_btn = QPushButton("Test View Project Widget")
        view_btn.clicked.connect(self.show_view_widget)
        
        edit_btn = QPushButton("Test Edit Project Dialog")
        edit_btn.clicked.connect(self.show_edit_dialog)
        
        list_btn = QPushButton("Test List Projects")
        list_btn.clicked.connect(self.test_list_projects)
        
        layout.addWidget(create_btn)
        layout.addWidget(view_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(list_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def show_create_dialog(self):
        """Show the create project dialog."""
        dialog = ProjectCreateDialog(self.view_model, self)
        if dialog.exec():
            print("✅ Project created successfully!")
        else:
            print("❌ Project creation cancelled")
    
    def show_view_widget(self):
        """Show the view project widget."""
        # First, create a test project if none exist
        self.view_model.create_project("Sample Project", "This is a test project")
        
        # Get the first project
        projects = self.view_model.get_projects_list()
        if projects:
            widget = ProjectViewWidget(self.view_model)
            widget.set_project_id(projects[0]['id'])
            widget.show()
        else:
            print("⚠️ No projects exist. Create one first!")
    
    def show_edit_dialog(self):
        """Show the edit project dialog."""
        projects = self.view_model.get_projects_list()
        if projects:
            dialog = ProjectEditDialog(self.view_model, self)
            dialog.set_project_id(projects[0]['id'])
            if dialog.exec():
                print("✅ Project updated successfully!")
            else:
                print("❌ Project edit cancelled")
        else:
            print("⚠️ No projects exist. Create one first!")
    
    def test_list_projects(self):
        """List all projects to console."""
        self.view_model.refresh_projects()
        projects = self.view_model.get_projects_list()
        
        print("\n" + "="*50)
        print(f"📋 PROJECTS LIST ({len(projects)} total)")
        print("="*50)
        
        if projects:
            for i, p in enumerate(projects, 1):
                print(f"\n{i}. {p['name']}")
                print(f"   ID: {p['id']}")
                print(f"   Description: {p['description'] or '(none)'}")
                print(f"   Created: {p['created_at']}")
        else:
            print("\n⚠️ No projects found. Create some using the dialog!")
        
        print("="*50 + "\n")


def main():
    """Run the test window."""
    app = QApplication(sys.argv)
    
    window = ProjectTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
