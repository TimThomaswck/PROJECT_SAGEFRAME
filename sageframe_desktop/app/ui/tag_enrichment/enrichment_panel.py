"""Enrichment display components for tag UI.

Components:
- EnrichmentPanel: Main panel showing enrichment status and data
- EnrichmentDetailView: Expandable details viewer
- EnrichmentLoadingSpinner: Loading indicator during enrichment
"""

from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)


class EnrichmentLoadingSpinner(QWidget):
    """Animated loading spinner for enrichment status."""
    
    def __init__(self, parent=None):
        """Initialize loading spinner.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumSize(24, 24)
        self.setMaximumSize(24, 24)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.spinner_label = QLabel("⟳")
        self.spinner_label.setStyleSheet("font-size: 16px; color: #007AFF;")
        layout.addWidget(self.spinner_label)
    
    def start(self) -> None:
        """Start spinning animation."""
        self.show()
    
    def stop(self) -> None:
        """Stop spinning animation."""
        self.hide()


class EnrichmentDetailView(QFrame):
    """Detailed enrichment data viewer."""
    
    def __init__(self, parent=None):
        """Initialize enrichment detail view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            EnrichmentDetailView {
                background-color: #f5f5f5;
                border-radius: 4px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(6)
        scroll.setWidget(self.content_widget)
        
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMaximumWidth(100)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:pressed {
                background-color: #003A7A;
            }
        """)
        
        self.collapse_button = QPushButton("Collapse")
        self.collapse_button.setMaximumWidth(100)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.collapse_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.hide()
    
    def set_enrichment_data(self, data: Dict[str, Any]) -> None:
        """Display enrichment data.
        
        Args:
            data: Enrichment data dictionary
        """
        # Clear previous content
        while self.content_layout.count():
            self.content_layout.takeAt(0).widget().deleteLater()
        
        # Set title
        title = data.get("title") or data.get("book_title") or "Unknown"
        self.title_label.setText(title)
        
        # Add provider-specific details
        if data.get("api_provider") == "tmdb":
            self._display_movie_details(data)
        elif data.get("api_provider") == "google_books":
            self._display_book_details(data)
        
        # Add common metadata
        self._display_common_metadata(data)
        
        self.content_layout.addStretch()
        self.show()
    
    def _display_movie_details(self, data: Dict[str, Any]) -> None:
        """Display movie-specific enrichment data.
        
        Args:
            data: Movie enrichment data
        """
        if data.get("director"):
            self.content_layout.addWidget(
                self._create_info_row("Director", data["director"])
            )
        
        if data.get("cast"):
            cast_str = ", ".join(data["cast"][:3])
            self.content_layout.addWidget(
                self._create_info_row("Cast", cast_str)
            )
        
        if data.get("runtime"):
            self.content_layout.addWidget(
                self._create_info_row("Runtime", f"{data['runtime']} minutes")
            )
        
        if data.get("rating"):
            self.content_layout.addWidget(
                self._create_info_row("Rating", f"{data['rating']}/10")
            )
        
        if data.get("genres"):
            genres_str = ", ".join(data["genres"])
            self.content_layout.addWidget(
                self._create_info_row("Genres", genres_str)
            )
        
        if data.get("release_date"):
            self.content_layout.addWidget(
                self._create_info_row("Release Date", data["release_date"])
            )
        
        if data.get("overview"):
            overview_label = QLabel(data["overview"])
            overview_label.setWordWrap(True)
            overview_label.setStyleSheet("color: #666;")
            self.content_layout.addWidget(overview_label)
    
    def _display_book_details(self, data: Dict[str, Any]) -> None:
        """Display book-specific enrichment data.
        
        Args:
            data: Book enrichment data
        """
        if data.get("authors"):
            authors_str = ", ".join(data["authors"])
            self.content_layout.addWidget(
                self._create_info_row("Authors", authors_str)
            )
        
        if data.get("publisher"):
            self.content_layout.addWidget(
                self._create_info_row("Publisher", data["publisher"])
            )
        
        if data.get("published_date"):
            self.content_layout.addWidget(
                self._create_info_row("Published", data["published_date"])
            )
        
        if data.get("isbn_13"):
            self.content_layout.addWidget(
                self._create_info_row("ISBN-13", data["isbn_13"])
            )
        
        if data.get("page_count"):
            self.content_layout.addWidget(
                self._create_info_row("Pages", str(data["page_count"]))
            )
        
        if data.get("average_rating"):
            self.content_layout.addWidget(
                self._create_info_row("Rating", f"{data['average_rating']}/5")
            )
        
        if data.get("categories"):
            categories_str = ", ".join(data["categories"][:3])
            self.content_layout.addWidget(
                self._create_info_row("Categories", categories_str)
            )
        
        if data.get("description"):
            desc_label = QLabel(data["description"])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666;")
            self.content_layout.addWidget(desc_label)
    
    def _display_common_metadata(self, data: Dict[str, Any]) -> None:
        """Display common metadata fields.
        
        Args:
            data: Enrichment data
        """
        if data.get("fetched_at"):
            self.content_layout.addWidget(
                self._create_info_row("Updated", data["fetched_at"])
            )
        
        if data.get("api_provider"):
            provider_name = "TMDB" if data["api_provider"] == "tmdb" else "Google Books"
            self.content_layout.addWidget(
                self._create_info_row("Source", provider_name)
            )
    
    def _create_info_row(self, label: str, value: str) -> QWidget:
        """Create a label-value info row.
        
        Args:
            label: Label text
            value: Value text
        
        Returns:
            Widget containing the row
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label_widget = QLabel(label + ":")
        label_widget.setStyleSheet("font-weight: bold; min-width: 80px;")
        
        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet("color: #333;")
        
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        
        return widget


class EnrichmentPanel(QWidget):
    """Main enrichment display panel with status and details.
    
    Signals:
        refreshRequested: Emitted when user clicks refresh
        retryRequested: Emitted when user clicks retry
    """
    
    refreshRequested = Signal()
    retryRequested = Signal()
    
    def __init__(self, parent=None):
        """Initialize enrichment panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header with status
        header_layout = QHBoxLayout()
        
        self.status_label = QLabel("Not Enriched")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        header_layout.addWidget(self.status_label)
        
        self.spinner = EnrichmentLoadingSpinner()
        header_layout.addWidget(self.spinner)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Detail view
        self.detail_view = EnrichmentDetailView()
        self.detail_view.collapse_button.clicked.connect(self._on_collapse)
        self.detail_view.refresh_button.clicked.connect(self.refreshRequested.emit)
        layout.addWidget(self.detail_view)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
            color: #FF3B30;
            background-color: #FFE5E5;
            padding: 8px;
            border-radius: 4px;
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.enrich_button = QPushButton("Enrich")
        self.enrich_button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #248A3D;
            }
        """)
        
        self.retry_button = QPushButton("Retry")
        self.retry_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9500;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C67200;
            }
        """)
        self.retry_button.hide()
        self.retry_button.clicked.connect(self.retryRequested.emit)
        
        button_layout.addWidget(self.enrich_button)
        button_layout.addWidget(self.retry_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    @Slot(str)
    def set_enriching(self, provider: str) -> None:
        """Show enriching status.
        
        Args:
            provider: Provider being enriched from
        """
        self.status_label.setText(f"Enriching from {provider.upper()}...")
        self.spinner.start()
        self.enrich_button.setEnabled(False)
        self.retry_button.hide()
        self.error_label.hide()
    
    @Slot(dict)
    def set_enrichment_data(self, data: dict) -> None:
        """Display enriched data.
        
        Args:
            data: Enrichment data
        """
        provider = data.get("api_provider", "unknown")
        self.status_label.setText(f"Enriched from {provider.upper()}")
        self.spinner.stop()
        self.detail_view.set_enrichment_data(data)
        self.enrich_button.setEnabled(False)
        self.error_label.hide()
    
    @Slot(str)
    def set_error(self, error_msg: str) -> None:
        """Display enrichment error.
        
        Args:
            error_msg: Error message
        """
        self.status_label.setText("Enrichment Failed")
        self.spinner.stop()
        self.error_label.setText(error_msg)
        self.error_label.show()
        self.enrich_button.setEnabled(True)
        self.retry_button.show()
    
    def reset(self) -> None:
        """Reset panel to default state."""
        self.status_label.setText("Not Enriched")
        self.spinner.stop()
        self.detail_view.hide()
        self.error_label.hide()
        self.enrich_button.setEnabled(True)
        self.retry_button.hide()
    
    def _on_collapse(self) -> None:
        """Handle collapse button click."""
        self.detail_view.hide()
        self.status_label.setText("Enriched (collapsed)")
