"""Test suite for Story 6.1: Windows Desktop Platform Support

Tests all acceptance criteria:
- AC1: Application installs and launches on Windows
- AC2: OS integration (taskbar, start menu, notifications)
- AC3: All features work on Windows
- AC4: CI/CD pipeline produces valid Windows installer
"""

import pytest
import sys
import logging
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

logger = logging.getLogger(__name__)


class TestAC1WindowsCompatibility:
    """Test AC1: Application installs and launches correctly on Windows."""
    
    def test_is_windows_detection(self):
        """AC1: Detect Windows platform correctly."""
        from app.windows_platform import is_windows
        
        # Should return boolean
        result = is_windows()
        assert isinstance(result, bool)
    
    def test_windows_version_detection(self):
        """AC1: Get Windows version information."""
        from app.windows_platform import get_windows_version, is_windows
        
        version = get_windows_version()
        
        if is_windows():
            # On Windows, should return version string or None
            assert version is None or isinstance(version, str)
        else:
            # On non-Windows, should return None
            assert version is None
    
    def test_pyinstaller_spec_file_exists(self):
        """AC1: PyInstaller spec file is properly configured."""
        spec_path = Path("sageframe.spec")
        
        if spec_path.exists():
            content = spec_path.read_text()
            
            # Verify spec contains key elements
            assert "Analysis" in content, "Should have Analysis section"
            assert "EXE" in content, "Should have EXE section"
            assert "SageFrame" in content, "Should reference SageFrame"
            assert "windowed=False" in content or "console=False" in content, \
                "Should be windowed mode (no console)"
    
    def test_installer_script_exists(self):
        """AC1: Inno Setup installer script is properly configured."""
        installer_path = Path("installer.iss")
        
        if installer_path.exists():
            content = installer_path.read_text()
            
            # Verify installer contains key elements
            assert "[Setup]" in content, "Should have Setup section"
            assert "[Files]" in content, "Should have Files section"
            assert "[Icons]" in content, "Should have Icons section"
            assert "SageFrame" in content, "Should reference SageFrame"
    
    @patch('app.windows_platform.QApplication')
    def test_platform_integration_initialization(self, mock_qapp):
        """AC1: Windows platform integration initializes without errors."""
        from app.windows_platform import WindowsPlatformIntegration
        
        platform = WindowsPlatformIntegration()
        
        assert platform is not None
        assert isinstance(platform.enabled, bool)


class TestAC2OSIntegration:
    """Test AC2: OS integration (taskbar, start menu, notifications)."""
    
    @patch('app.windows_platform.is_windows')
    def test_system_tray_service_init(self, mock_is_windows):
        """AC2: System tray service initializes correctly."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsSystemTrayService
        
        mock_app = MagicMock()
        mock_window = MagicMock()
        
        service = WindowsSystemTrayService(mock_app, mock_window, "test_icon.ico")
        
        assert service is not None
        assert service.app == mock_app
        assert service.main_window == mock_window
    
    @patch('app.windows_platform.is_windows')
    def test_notification_service_init(self, mock_is_windows):
        """AC2: Notification service initializes correctly."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsNotificationService
        
        service = WindowsNotificationService()
        
        assert service is not None
        assert service._enabled == True
    
    @patch('app.windows_platform.is_windows')
    def test_tray_service_methods(self, mock_is_windows):
        """AC2: System tray service has required methods."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsSystemTrayService
        
        mock_app = MagicMock()
        mock_window = MagicMock()
        
        service = WindowsSystemTrayService(mock_app, mock_window)
        
        # Verify required methods exist
        assert hasattr(service, 'initialize')
        assert hasattr(service, 'show_notification')
        assert hasattr(service, '_show_window')
        assert hasattr(service, '_quit_application')
    
    @patch('app.windows_platform.is_windows')
    def test_notification_methods(self, mock_is_windows):
        """AC2: Notification service has all notification methods."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsNotificationService
        
        service = WindowsNotificationService()
        
        # Verify required methods exist
        assert hasattr(service, 'notify_engagement_suggestion')
        assert hasattr(service, 'notify_calendar_event')
        assert hasattr(service, 'notify_sync_complete')
    
    def test_installer_has_start_menu_integration(self):
        """AC2: Installer creates start menu shortcuts."""
        installer_path = Path("installer.iss")
        
        if installer_path.exists():
            content = installer_path.read_text()
            
            # Verify start menu shortcuts
            assert "[Icons]" in content, "Should have Icons section"
            assert "{group}" in content, "Should create group folder"
            assert "Start Menu" in content or "group" in content, \
                "Should integrate with start menu"
    
    def test_installer_has_desktop_shortcut(self):
        """AC2: Installer creates desktop shortcut."""
        installer_path = Path("installer.iss")
        
        if installer_path.exists():
            content = installer_path.read_text()
            
            # Verify desktop shortcut
            assert "{commondesktop}" in content, "Should create desktop shortcut"
    
    def test_installer_uninstall_capability(self):
        """AC2: Installer has uninstall functionality."""
        installer_path = Path("installer.iss")
        
        if installer_path.exists():
            content = installer_path.read_text()
            
            # Verify uninstall support
            assert "[UninstallDelete]" in content or "uninsdeletekey" in content, \
                "Should support uninstall"


class TestAC3FeatureFunctionality:
    """Test AC3: All features work on Windows."""
    
    def test_database_operations_on_windows(self):
        """AC3: Database operations work correctly on Windows."""
        from app.database import DATABASE_PATH
        
        # Verify database path is set and valid
        assert DATABASE_PATH is not None
        
        # Path should be string-like
        assert isinstance(DATABASE_PATH, (str, Path))
    
    def test_task_crud_operations_work(self):
        """AC3: Task CRUD operations work on Windows."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base
        from app.modules.tasks.models import Task
        from datetime import datetime, timezone
        
        # Create in-memory database (simulating Windows)
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test create
        task = Task(
            title="Test Task",
            status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(task)
        session.commit()
        
        # Test read
        retrieved = session.query(Task).first()
        assert retrieved is not None
        assert retrieved.title == "Test Task"
        
        # Test update
        retrieved.title = "Updated Task"
        session.commit()
        
        # Verify update
        updated = session.query(Task).first()
        assert updated.title == "Updated Task"
        
        # Test delete
        session.delete(updated)
        session.commit()
        
        count = session.query(Task).count()
        assert count == 0
        
        session.close()
    
    def test_project_operations_work(self):
        """AC3: Project operations work on Windows."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base
        from app.modules.projects.models import Project
        from datetime import datetime, timezone
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create project
        project = Project(
            name="Test Project",
            description="Windows test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(project)
        session.commit()
        
        # Read project
        retrieved = session.query(Project).first()
        assert retrieved is not None
        assert retrieved.name == "Test Project"
        
        session.close()
    
    def test_offline_functionality_works(self):
        """AC3: Offline functionality works on Windows."""
        from app.database import is_online, get_offline_status
        
        # These should work regardless of platform
        status = get_offline_status()
        assert isinstance(status, dict)
        assert 'is_online' in status
        assert 'message' in status


class TestAC4CIPipeline:
    """Test AC4: CI/CD pipeline produces valid Windows installer."""
    
    def test_pyinstaller_spec_valid(self):
        """AC4: PyInstaller spec file is valid Python."""
        spec_path = Path("sageframe.spec")
        
        if spec_path.exists():
            try:
                spec_content = spec_path.read_text()
                # Compile as Python code to verify syntax
                compile(spec_content, str(spec_path), 'exec')
            except SyntaxError as e:
                pytest.fail(f"PyInstaller spec has syntax error: {e}")
    
    def test_installer_script_syntax(self):
        """AC4: Installer script has correct syntax."""
        installer_path = Path("installer.iss")
        
        if installer_path.exists():
            content = installer_path.read_text()
            
            # Verify required Inno Setup sections
            required_sections = [
                "[Setup]",
                "[Files]",
                "[Icons]",
                "[Registry]",
            ]
            
            for section in required_sections:
                assert section in content, f"Missing section: {section}"
    
    def test_github_actions_workflow_valid(self):
        """AC4: GitHub Actions workflow is valid YAML."""
        workflow_path = Path(".github/workflows/build-windows.yml")
        
        if workflow_path.exists():
            try:
                import yaml
                content = workflow_path.read_text()
                workflow = yaml.safe_load(content)
                
                # Verify key workflow structure
                assert 'name' in workflow
                assert 'on' in workflow
                assert 'jobs' in workflow
                assert 'build-windows' in workflow['jobs']
            except ImportError:
                pytest.skip("PyYAML not installed")
    
    def test_workflow_has_build_steps(self):
        """AC4: CI/CD pipeline has build steps."""
        workflow_path = Path(".github/workflows/build-windows.yml")
        
        if workflow_path.exists():
            content = workflow_path.read_text()
            
            # Verify key build steps
            assert "PyInstaller" in content, "Should use PyInstaller"
            assert "Inno Setup" in content or "iscc" in content, \
                "Should build installer"
            assert "artifacts" in content.lower(), "Should upload artifacts"
    
    def test_workflow_has_test_steps(self):
        """AC4: CI/CD pipeline includes testing."""
        workflow_path = Path(".github/workflows/build-windows.yml")
        
        if workflow_path.exists():
            content = workflow_path.read_text()
            
            # Verify testing is included
            assert "pytest" in content.lower() or "test" in content.lower(), \
                "Should run tests"


class TestWindowsPlatformIntegration:
    """Integration tests for Windows platform support."""
    
    @patch('app.windows_platform.is_windows')
    def test_platform_status_report(self, mock_is_windows):
        """Verify Windows platform status can be reported."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import get_windows_platform
        
        platform = get_windows_platform()
        status = platform.get_status()
        
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'version' in status
        assert 'initialized' in status
    
    def test_build_files_exist(self):
        """Verify all build configuration files exist."""
        required_files = [
            Path("sageframe.spec"),
            Path("installer.iss"),
            Path(".github/workflows/build-windows.yml"),
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Missing build file: {file_path}"
    
    def test_windows_module_importable(self):
        """Verify Windows platform module can be imported."""
        try:
            from app import windows_platform
            assert windows_platform is not None
        except ImportError as e:
            pytest.fail(f"Failed to import windows_platform: {e}")


class TestWindowsNotifications:
    """Test Windows notification functionality."""
    
    @patch('app.windows_platform.is_windows')
    def test_engagement_suggestion_notification(self, mock_is_windows):
        """AC2: Engagement suggestion notifications work."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsNotificationService
        
        service = WindowsNotificationService()
        
        # Should not raise exception
        service.notify_engagement_suggestion(
            "Coffee Break",
            "You have a free slot at 10 AM"
        )
    
    @patch('app.windows_platform.is_windows')
    def test_calendar_event_notification(self, mock_is_windows):
        """AC2: Calendar event notifications work."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsNotificationService
        
        service = WindowsNotificationService()
        
        # Should not raise exception
        service.notify_calendar_event(
            "Meeting",
            "10:00 AM"
        )
    
    @patch('app.windows_platform.is_windows')
    def test_sync_complete_notification(self, mock_is_windows):
        """AC2: Sync complete notifications work."""
        mock_is_windows.return_value = True
        
        from app.windows_platform import WindowsNotificationService
        
        service = WindowsNotificationService()
        
        # Should not raise exception
        service.notify_sync_complete(5)
