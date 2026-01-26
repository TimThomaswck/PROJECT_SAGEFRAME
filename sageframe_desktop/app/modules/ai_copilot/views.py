"""
AI Co-Pilot UI Components

Non-intrusive notification widgets and message display panels.
Implements Atomic Design principles:
- Atoms: Message label, dismiss button, icons
- Molecules: Single message notification widget
- Organisms: Co-pilot message panel with queue management

Styling: Qt Style Sheets (QSS) with minimalist RPG aesthetic.
Accessibility: Full keyboard navigation and screen reader support (NFR7).
"""

import random
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, Signal, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor


class CopilotNotificationWidget(QWidget):
    """
    Single message notification widget (Molecule level).
    
    Non-intrusive notification displaying a co-pilot message with
    dismiss button. Supports fade-in/slide-in animations.
    
    Signals:
        dismissed(str): Emitted when user dismisses message (with message_id).
        acknowledged: Emitted when user acknowledges message.
    """
    
    # Signals
    dismissed = Signal(str)  # message_id
    acknowledged = Signal(str)  # message_id
    
    def __init__(self, message_id: str = "", message_text: str = "", parent=None):
        """
        Initialize notification widget.
        
        Args:
            message_id: Unique identifier for this message.
            message_text: The message text to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.message_id = message_id
        self.message_text = message_text
        self.animation_duration = 200  # ms, respects NFR2 (<200ms)
        
        # Setup UI
        self._setup_ui()
        self._load_stylesheet()
        self._setup_animations()
    
    def _setup_ui(self):
        """Build the widget layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Message label (Atom: text label)
        self.message_label = QLabel(self.message_text)
        self.message_label.setWordWrap(True)
        self.message_label.setAccessibleName("Co-pilot message")
        self.message_label.setFont(self._get_message_font())
        layout.addWidget(self.message_label, 1)
        
        # Dismiss button (Atom: action button)
        self.dismiss_button = QPushButton("×")
        self.dismiss_button.setFixedSize(32, 32)
        self.dismiss_button.setAccessibleName("Dismiss message")
        self.dismiss_button.setToolTip("Dismiss this message (Esc)")
        self.dismiss_button.clicked.connect(self.dismiss)
        self.dismiss_button.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.dismiss_button)
        
        self.setLayout(layout)
        self.setMinimumHeight(50)
        self.setMaximumHeight(100)
        
        # Widget should accept focus for keyboard navigation
        self.setFocusPolicy(Qt.ClickFocus)
    
    def _get_message_font(self) -> QFont:
        """Get font for message text."""
        font = QFont("Segoe UI", 11)
        font.setPointSize(11)
        return font
    
    def _load_stylesheet(self):
        """Load QSS styling from copilot.qss."""
        # Default styling (will be overridden by copilot.qss)
        self.setStyleSheet("""
            CopilotNotificationWidget {
                background-color: #0f172a;
                border: 1px solid #1f2a44;
                border-radius: 4px;
                padding: 2px;
            }
            QLabel {
                color: #c5d9ff;
                background-color: transparent;
                font-size: 11pt;
            }
            QPushButton {
                background-color: transparent;
                color: #8aa0c8;
                border: none;
                font-size: 18pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #c5d9ff;
            }
            QPushButton:pressed {
                color: #3a7afe;
            }
        """)
    
    def _setup_animations(self):
        """Setup fade-in and slide-in animations."""
        # Opacity animation (fade-in)
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(self.animation_duration)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def set_message(self, message_text: str, animate: bool = True):
        """
        Set the message text and optionally animate appearance.
        
        Args:
            message_text: Text to display.
            animate: Whether to run fade-in animation.
        """
        self.message_text = message_text
        self.message_label.setText(message_text)
        
        if animate:
            self.animate_appearance()
    
    def animate_appearance(self):
        """Play fade-in animation."""
        self.opacity_effect.setOpacity(0.0)
        self.fade_in_animation.start()
    
    def dismiss(self):
        """Dismiss this message."""
        self.dismissed.emit(self.message_id)
    
    def acknowledge(self):
        """Acknowledge this message."""
        self.acknowledged.emit(self.message_id)
    
    def keyPressEvent(self, event):
        """Handle keyboard input."""
        if event.key() == Qt.Key_Escape:
            self.dismiss()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.acknowledge()
        else:
            super().keyPressEvent(event)


class CopilotPanel(QWidget):
    """
    Co-pilot message panel (Organism level).
    
    Manages display and lifecycle of multiple co-pilot messages.
    Handles:
    - Message queuing and deferred delivery
    - Do Not Disturb (DND) mode
    - Auto-dismiss timeout
    - Flow state detection
    
    Signals:
        message_dismissed(str): Emitted when message is dismissed (with message_id).
        message_acknowledged(str): Emitted when message is acknowledged (with message_id).
    """
    
    # Signals
    message_dismissed = Signal(str)
    message_acknowledged = Signal(str)
    
    def __init__(self, parent=None):
        """
        Initialize the co-pilot message panel.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.message_queue: List[dict] = []  # Queued messages during DND
        self.do_not_disturb_until: Optional[float] = None
        self.auto_dismiss_timeout = 8000  # milliseconds
        self.displayed_widgets: List[CopilotNotificationWidget] = []
        
        # Setup UI
        self._setup_ui()
        self._load_stylesheet()
    
    def _setup_ui(self):
        """Build the panel layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Scroll area for messages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #0b1220;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #1f2a44;
                border-radius: 4px;
            }
        """)
        
        # Message container widget
        self.message_container = QWidget()
        self.message_container_layout = QVBoxLayout(self.message_container)
        self.message_container_layout.setContentsMargins(0, 0, 0, 0)
        self.message_container_layout.setSpacing(8)
        self.message_container_layout.addStretch()
        
        scroll.setWidget(self.message_container)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
    
    def message_container_count(self) -> int:
        """
        Return count of displayed message widgets.
        This is a convenience method for tests and external code.
        """
        # Count widgets in layout excluding the stretch
        return max(0, self.message_container_layout.count() - 1)
    
    def _get_message_container_count(self) -> int:
        """Get count of visible message widgets (excluding stretch)."""
        return max(0, self.message_container_layout.count() - 1)
    
    def _load_stylesheet(self):
        """Load QSS styling."""
        self.setStyleSheet("""
            CopilotPanel {
                background-color: transparent;
            }
        """)
    
    def display_message(
        self,
        message_text: str,
        message_id: str = "",
        auto_dismiss: bool = True,
    ):
        """
        Display a message in the panel.
        
        Args:
            message_text: The message to display.
            message_id: Unique identifier (generated if not provided).
            auto_dismiss: Whether to auto-dismiss after timeout.
        """
        # Generate message_id if not provided
        if not message_id:
            message_id = f"msg_{random.randint(100000, 999999)}"
        
        # Check if in Do Not Disturb mode
        if self._is_in_dnd():
            self.message_queue.append({
                "text": message_text,
                "id": message_id,
                "auto_dismiss": auto_dismiss,
            })
            return
        
        # Create and display widget
        widget = CopilotNotificationWidget(message_id, message_text)
        
        # Connect signals
        widget.dismissed.connect(self._on_message_dismissed)
        widget.acknowledged.connect(self._on_message_acknowledged)
        
        # Add to layout (before stretch)
        self.message_container_layout.insertWidget(
            self.message_container_layout.count() - 1,
            widget,
        )
        
        self.displayed_widgets.append(widget)
        
        # Animate appearance
        widget.animate_appearance()
        
        # Setup auto-dismiss if enabled
        if auto_dismiss:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._auto_dismiss_message(message_id))
            timer.start(self.auto_dismiss_timeout)
    
    def _on_message_dismissed(self, message_id: str):
        """Handle message dismissal."""
        self.message_dismissed.emit(message_id)
        self.remove_message(message_id)
    
    def _on_message_acknowledged(self, message_id: str):
        """Handle message acknowledgment."""
        self.message_acknowledged.emit(message_id)
        self.remove_message(message_id)
    
    def remove_message(self, message_id: str):
        """Remove a message widget from the panel."""
        for widget in self.displayed_widgets[:]:
            if widget.message_id == message_id:
                self.message_container_layout.removeWidget(widget)
                widget.deleteLater()
                self.displayed_widgets.remove(widget)
                break
        
        # Process queued messages if DND mode ended
        self._process_message_queue()
    
    def _auto_dismiss_message(self, message_id: str):
        """Auto-dismiss a message after timeout."""
        self.remove_message(message_id)
    
    def set_do_not_disturb(self, duration_ms: int):
        """
        Set Do Not Disturb mode.
        
        Args:
            duration_ms: Duration of DND mode in milliseconds.
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        duration_sec = duration_ms / 1000.0
        self.do_not_disturb_until = (now + timedelta(seconds=duration_sec)).timestamp()
    
    def clear_do_not_disturb(self):
        """Clear Do Not Disturb mode."""
        self.do_not_disturb_until = None
        self._process_message_queue()
    
    def _is_in_dnd(self) -> bool:
        """Check if currently in Do Not Disturb mode."""
        if not self.do_not_disturb_until:
            return False
        
        from datetime import datetime
        return datetime.now().timestamp() < self.do_not_disturb_until
    
    def _process_message_queue(self):
        """Process queued messages when DND mode ends."""
        if self._is_in_dnd():
            return
        
        while self.message_queue:
            msg = self.message_queue.pop(0)
            self.display_message(
                msg["text"],
                msg["id"],
                msg["auto_dismiss"],
            )
    
    def clear_all_messages(self):
        """Clear all displayed messages."""
        for widget in self.displayed_widgets[:]:
            self.message_container_layout.removeWidget(widget)
            widget.deleteLater()
        self.displayed_widgets.clear()
