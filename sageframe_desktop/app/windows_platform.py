"""Windows platform integration for SageFrame.

This module provides Windows-specific functionality including:
- System tray icon support
- Windows notifications
- Windows OS integration (start menu, taskbar)
- Platform detection and compatibility checks
"""

import sys
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


def is_windows() -> bool:
    """Check if running on Windows platform.
    
    Returns:
        bool: True if on Windows, False otherwise
    """
    return sys.platform.startswith('win')


def get_windows_version() -> Optional[str]:
    """Get Windows version information.
    
    Returns:
        str: Windows version (e.g., "10", "11") or None if not Windows
    """
    if not is_windows():
        return None
    
    try:
        import platform
        version_info = platform.win32_ver()
        # version_info format: (release, version, csd, ptype)
        if version_info and version_info[0]:
            return version_info[0]  # e.g., "10" or "11"
    except Exception as e:
        logger.warning(f"Could not determine Windows version: {e}")
    
    return None


class WindowsSystemTrayService:
    """Windows system tray icon integration.
    
    Implements AC2: OS integration with taskbar and tray icon support.
    """
    
    def __init__(self, app, main_window, icon_path: str = None):
        """Initialize system tray service.
        
        Args:
            app: QApplication instance
            main_window: Main application window
            icon_path: Path to icon file (optional)
        """
        self.app = app
        self.main_window = main_window
        self.icon_path = icon_path or "resources/icon.ico"
        self.tray_icon = None
        self.tray_menu = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize system tray icon.
        
        Implements AC2: Taskbar and tray integration.
        
        Returns:
            bool: True if initialization successful
        """
        if not is_windows():
            logger.debug("Not on Windows platform, skipping tray initialization")
            return False
        
        try:
            from PySide6.QtWidgets import QSystemTrayIcon, QMenu
            from PySide6.QtGui import QIcon, QAction
            
            # Create tray icon
            try:
                icon = QIcon(self.icon_path)
            except Exception as e:
                logger.warning(f"Could not load icon from {self.icon_path}: {e}")
                icon = QIcon()
            
            self.tray_icon = QSystemTrayIcon(icon, self.app)
            
            # Create context menu
            self.tray_menu = QMenu()
            
            # Show/Hide action
            show_action = QAction("Show SageFrame", self.app)
            show_action.triggered.connect(self._show_window)
            self.tray_menu.addAction(show_action)
            
            # Separator
            self.tray_menu.addSeparator()
            
            # Quit action
            quit_action = QAction("Quit SageFrame", self.app)
            quit_action.triggered.connect(self._quit_application)
            self.tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(self.tray_menu)
            
            # Connect signals
            self.tray_icon.activated.connect(self._on_tray_icon_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
            logger.info("Windows system tray initialized successfully")
            self._initialized = True
            return True
            
        except ImportError:
            logger.warning("PySide6 not available or incomplete")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize system tray: {e}")
            return False
    
    def _show_window(self):
        """Show main window from tray."""
        self.main_window.showNormal()
        self.main_window.activateWindow()
    
    def _quit_application(self):
        """Quit application."""
        self.app.quit()
    
    def _on_tray_icon_activated(self, reason):
        """Handle tray icon activation.
        
        Args:
            reason: QSystemTrayIcon activation reason
        """
        from PySide6.QtWidgets import QSystemTrayIcon
        
        if reason == QSystemTrayIcon.DoubleClick:
            # Double-click: show/hide main window
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self._show_window()
        elif reason == QSystemTrayIcon.MiddleClick:
            # Middle-click: toggle
            self._show_window()
    
    def show_notification(self, title: str, message: str, duration_ms: int = 5000):
        """Show Windows notification via tray icon.
        
        Implements AC2: Windows notifications support.
        
        Args:
            title: Notification title
            message: Notification message
            duration_ms: Duration in milliseconds (default 5000)
        """
        if not self._initialized or not self.tray_icon:
            logger.debug("Tray not initialized, skipping notification")
            return
        
        try:
            from PySide6.QtWidgets import QSystemTrayIcon
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                duration_ms
            )
            logger.debug(f"Notification shown: {title}")
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")


class WindowsNotificationService:
    """Windows notifications service.
    
    Provides notification display for engagement suggestions, calendar events, etc.
    Implements AC2: Windows notification support.
    """
    
    def __init__(self, tray_service: Optional[WindowsSystemTrayService] = None):
        """Initialize notification service.
        
        Args:
            tray_service: SystemTrayService instance (optional)
        """
        self.tray_service = tray_service
        self._enabled = is_windows()
    
    def notify_engagement_suggestion(self, suggestion_title: str, suggestion_desc: str):
        """Notify user of engagement suggestion.
        
        Args:
            suggestion_title: Suggestion title
            suggestion_desc: Suggestion description
        """
        if not self._enabled:
            return
        
        message = suggestion_desc[:100] + "..." if len(suggestion_desc) > 100 else suggestion_desc
        self._show_notification(
            "SageFrame Suggestion",
            message,
            duration_ms=8000
        )
    
    def notify_calendar_event(self, event_title: str, event_time: str):
        """Notify user of upcoming calendar event.
        
        Args:
            event_title: Event title
            event_time: Event time string
        """
        if not self._enabled:
            return
        
        self._show_notification(
            "Calendar Event",
            f"{event_title} at {event_time}",
            duration_ms=6000
        )
    
    def notify_sync_complete(self, items_synced: int):
        """Notify user of sync completion.
        
        Args:
            items_synced: Number of items synced
        """
        if not self._enabled:
            return
        
        self._show_notification(
            "Sync Complete",
            f"Synced {items_synced} items",
            duration_ms=4000
        )
    
    def _show_notification(self, title: str, message: str, duration_ms: int = 5000):
        """Show notification.
        
        Args:
            title: Notification title
            message: Notification message
            duration_ms: Duration in milliseconds
        """
        if self.tray_service:
            self.tray_service.show_notification(title, message, duration_ms)
        else:
            logger.info(f"Notification: {title} - {message}")


class WindowsPlatformIntegration:
    """Main Windows platform integration coordinator.
    
    Provides all Windows-specific features for Story 6.1 AC1-4.
    """
    
    def __init__(self):
        """Initialize Windows platform integration."""
        self.enabled = is_windows()
        self.version = get_windows_version() if self.enabled else None
        self.tray_service: Optional[WindowsSystemTrayService] = None
        self.notification_service: Optional[WindowsNotificationService] = None
        self._initialized = False
    
    def initialize(self, app, main_window, icon_path: str = None) -> bool:
        """Initialize all Windows platform features.
        
        Implements AC1, AC2: Windows compatibility and OS integration.
        
        Args:
            app: QApplication instance
            main_window: Main application window
            icon_path: Path to icon file
            
        Returns:
            bool: True if initialization successful
        """
        if not self.enabled:
            logger.info("Not on Windows platform")
            return False
        
        try:
            # Initialize tray service
            self.tray_service = WindowsSystemTrayService(app, main_window, icon_path)
            tray_initialized = self.tray_service.initialize()
            
            # Initialize notification service
            self.notification_service = WindowsNotificationService(self.tray_service)
            
            logger.info(f"Windows platform initialized (version {self.version})")
            logger.info(f"Tray service: {'OK' if tray_initialized else 'Failed'}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Windows platform: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get Windows platform status.
        
        Returns:
            dict: Status information
        """
        return {
            'enabled': self.enabled,
            'version': self.version,
            'initialized': self._initialized,
            'tray_available': self.tray_service is not None and self.tray_service._initialized,
            'notifications_available': self.notification_service is not None,
        }
    
    def show_suggestion_notification(self, title: str, description: str):
        """Show engagement suggestion notification.
        
        Args:
            title: Suggestion title
            description: Suggestion description
        """
        if self.notification_service:
            self.notification_service.notify_engagement_suggestion(title, description)
    
    def show_calendar_notification(self, event_title: str, event_time: str):
        """Show calendar event notification.
        
        Args:
            event_title: Event title
            event_time: Event time
        """
        if self.notification_service:
            self.notification_service.notify_calendar_event(event_title, event_time)


# Global instance
_platform_integration: Optional[WindowsPlatformIntegration] = None


def get_windows_platform() -> WindowsPlatformIntegration:
    """Get global Windows platform integration instance.
    
    Returns:
        WindowsPlatformIntegration: Global instance
    """
    global _platform_integration
    if _platform_integration is None:
        _platform_integration = WindowsPlatformIntegration()
    return _platform_integration


def initialize_platform(app, main_window, icon_path: str = None) -> bool:
    """Initialize Windows platform support.
    
    Implements AC1, AC2, AC3: Windows compatibility, OS integration, and features.
    
    Args:
        app: QApplication instance
        main_window: Main application window
        icon_path: Path to icon file
        
    Returns:
        bool: True if initialization successful
    """
    platform = get_windows_platform()
    return platform.initialize(app, main_window, icon_path)
