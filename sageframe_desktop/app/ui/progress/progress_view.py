"""Progress and gamification view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar,
    QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont

from app.modules.gamification.services import GamificationService


class AnimatedProgressBar(QProgressBar):
    """Progress bar with smooth animation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animated_value = 0
        self.setTextVisible(False)
        self.setMinimum(0)
        self.setMaximum(100)
        
    def get_animated_value(self):
        return self._animated_value
    
    def set_animated_value(self, value):
        self._animated_value = value
        self.setValue(int(value))
    
    animated_value = Property(float, get_animated_value, set_animated_value)
    
    def animateTo(self, target_value):
        """Animate to target value smoothly."""
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(1000)  # 1 second
        self.animation.setStartValue(self._animated_value)
        self.animation.setEndValue(target_value)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()


class AchievementBadge(QFrame):
    """Colorful achievement badge widget."""
    
    def __init__(self, emoji: str, title: str, description: str, color: str, unlocked: bool = False, parent=None):
        super().__init__(parent)
        self.unlocked = unlocked
        self._setup_ui(emoji, title, description, color)
        
    def _setup_ui(self, emoji: str, title: str, description: str, color: str):
        """Build badge UI."""
        self.setFixedHeight(180)
        self.setFixedWidth(160)
        
        # Style based on unlock status
        if self.unlocked:
            style = f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 #0b1220);
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 12px;
                }}
            """
        else:
            style = """
                QFrame {
                    background-color: #1a1a2e;
                    border: 2px solid #2a2a3e;
                    border-radius: 12px;
                    padding: 12px;
                    opacity: 0.5;
                }
            """
        self.setStyleSheet(style)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Emoji icon
        emoji_label = QLabel(emoji if self.unlocked else "🔒")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_font = QFont()
        emoji_font.setPointSize(40)
        emoji_label.setFont(emoji_font)
        emoji_label.setStyleSheet("border: none; background: transparent;")
        emoji_label.setMinimumHeight(50)
        layout.addWidget(emoji_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"""
            color: {'#ffffff' if self.unlocked else '#666666'};
            border: none;
            background: transparent;
            padding: 4px;
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_font = QFont()
        desc_font.setPointSize(9)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet(f"""
            color: {'#cccccc' if self.unlocked else '#555555'};
            border: none;
            background: transparent;
            padding: 2px;
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)


class ProgressView(QWidget):
    """Progress tracking and gamification view with animations and achievements."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gamification_service = GamificationService()
        self._setup_ui()
        self._load_data()
        
        # Auto-refresh every 5 seconds
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(5000)
    
    def _setup_ui(self):
        """Build enhanced UI with animations."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)
        
        # Title
        title_label = QLabel("📈 Your Progress")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #f0b429; margin-bottom: 10px;")
        content_layout.addWidget(title_label)
        
        # Level and XP section
        self.level_label = QLabel("Level 1")
        level_font = QFont()
        level_font.setPointSize(20)
        level_font.setBold(True)
        self.level_label.setFont(level_font)
        self.level_label.setStyleSheet("color: #4a9eff;")
        content_layout.addWidget(self.level_label)
        
        # XP info
        self.xp_label = QLabel("XP: 0")
        self.xp_label.setStyleSheet("font-size: 16px; color: #cccccc; margin-top: -5px;")
        content_layout.addWidget(self.xp_label)
        
        # Animated progress bar
        progress_container = QFrame()
        progress_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        progress_layout = QVBoxLayout(progress_container)
        
        self.next_level_label = QLabel("Next level: 0 XP remaining")
        self.next_level_label.setStyleSheet("font-size: 13px; color: #aaaaaa; margin-bottom: 8px;")
        progress_layout.addWidget(self.next_level_label)
        
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2a2a3e;
                border-radius: 8px;
                background-color: #0d1117;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f0b429, stop:0.5 #ff6b6b, stop:1 #4a9eff);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        content_layout.addWidget(progress_container)
        
        # Stats section
        stats_container = QFrame()
        stats_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(stats_container)
        
        self.tasks_label = QLabel("📋 Tasks Completed\n0")
        self.tasks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tasks_label.setStyleSheet("font-size: 14px; color: #4ecdc4; font-weight: bold;")
        stats_layout.addWidget(self.tasks_label)
        
        content_layout.addWidget(stats_container)
        
        # Achievements section
        achievements_label = QLabel("🏆 Achievements")
        achievements_font = QFont()
        achievements_font.setPointSize(20)
        achievements_font.setBold(True)
        achievements_label.setFont(achievements_font)
        achievements_label.setStyleSheet("color: #ff6b6b; margin-top: 10px;")
        content_layout.addWidget(achievements_label)
        
        # Achievement badges grid
        badges_container = QFrame()
        badges_container.setStyleSheet("background: transparent; border: none;")
        badges_layout = QGridLayout(badges_container)
        badges_layout.setSpacing(15)
        
        # Define achievements
        self.achievements = [
            {
                "emoji": "🌟",
                "title": "First Steps",
                "description": "Complete 1 task",
                "color": "#4ecdc4",
                "requirement": 1
            },
            {
                "emoji": "🔥",
                "title": "On Fire",
                "description": "Complete 10 tasks",
                "color": "#ff6b6b",
                "requirement": 10
            },
            {
                "emoji": "💪",
                "title": "Productivity Beast",
                "description": "Reach Level 5",
                "color": "#f0b429",
                "requirement": 5
            },
            {
                "emoji": "🚀",
                "title": "Sky Rocket",
                "description": "Complete 50 tasks",
                "color": "#4a9eff",
                "requirement": 50
            },
            {
                "emoji": "👑",
                "title": "Legendary",
                "description": "Reach Level 10",
                "color": "#9b59b6",
                "requirement": 10
            }
        ]
        
        self.badge_widgets = []
        for i, achievement in enumerate(self.achievements):
            badge = AchievementBadge(
                achievement["emoji"],
                achievement["title"],
                achievement["description"],
                achievement["color"],
                unlocked=False
            )
            self.badge_widgets.append(badge)
            row = i // 2  # 2 badges per row instead of 3
            col = i % 2
            badges_layout.addWidget(badge, row, col)
        
        content_layout.addWidget(badges_container)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _load_data(self):
        """Load and display progress data."""
        try:
            stats = self.gamification_service.get_progress_stats()
            
            # Update level
            self.level_label.setText(f"Level {stats['current_level']}")
            
            # Update XP
            self.xp_label.setText(f"XP: {stats['current_xp']}")
            
            # Update next level info
            xp_remaining = stats['xp_for_next_level'] - stats['xp_in_current_level']
            self.next_level_label.setText(f"Next level: {xp_remaining} XP remaining")
            
            # Animate progress bar
            self.progress_bar.animateTo(stats['progress_percentage'])
            
            # Update tasks completed
            self.tasks_label.setText(f"📋 Tasks Completed\n{stats['total_tasks_completed']}")
            
            # Update achievement unlock status
            tasks_completed = stats['total_tasks_completed']
            current_level = stats['current_level']
            
            for i, achievement in enumerate(self.achievements):
                if i < 2:  # Task-based achievements (indices 0, 1, 3)
                    if i == 0 or i == 1:
                        unlocked = tasks_completed >= achievement["requirement"]
                    else:
                        unlocked = tasks_completed >= achievement["requirement"]
                elif i == 2 or i == 4:  # Level-based achievements (indices 2, 4)
                    unlocked = current_level >= achievement["requirement"]
                else:  # index 3 - task-based
                    unlocked = tasks_completed >= achievement["requirement"]
                
                if unlocked != self.badge_widgets[i].unlocked:
                    # Rebuild badge with new status
                    old_badge = self.badge_widgets[i]
                    new_badge = AchievementBadge(
                        achievement["emoji"],
                        achievement["title"],
                        achievement["description"],
                        achievement["color"],
                        unlocked=unlocked
                    )
                    
                    # Replace in layout
                    layout = old_badge.parent().layout()
                    index = layout.indexOf(old_badge)
                    layout.removeWidget(old_badge)
                    old_badge.deleteLater()
                    
                    row = i // 2  # 2 badges per row
                    col = i % 2
                    layout.addWidget(new_badge, row, col)
                    self.badge_widgets[i] = new_badge
                    
        except Exception as e:
            print(f"Error loading progress data: {e}")
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.refresh_timer.stop()
        self.gamification_service.close()
        super().closeEvent(event)
