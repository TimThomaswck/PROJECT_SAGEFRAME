"""PySide6 views for file import and extraction results."""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QTextEdit, QMessageBox,
    QRadioButton, QButtonGroup, QHBoxLayout, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QFont

from app.modules.file_ingestion.services import FileImportService, ExtractionService
from app.modules.tasks.view_models import TaskViewModel


class ImportDialog(QDialog):
    def __init__(self, extraction_service: ExtractionService, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("Import Document")
        self.setMinimumWidth(500)
        self._extraction_service = extraction_service
        self._current_extraction_result = None
        self._current_mode = None

        layout = QVBoxLayout(self)

        self.path_field = QLineEdit()
        self.path_field.setPlaceholderText("Select a PDF/Image file...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)

        form = QFormLayout()
        form.addRow("File:", self.path_field)
        layout.addLayout(form)
        layout.addWidget(browse_btn)

        # Mode selector
        mode_label = QLabel("Extraction Mode:")
        layout.addWidget(mode_label)
        
        self.mode_group = QButtonGroup(self)
        mode_layout = QHBoxLayout()
        
        self.bill_mode = QRadioButton("Bill/Invoice")
        self.bill_mode.setChecked(True)
        self.mode_group.addButton(self.bill_mode, 0)
        mode_layout.addWidget(self.bill_mode)
        
        self.note_mode = QRadioButton("Note/Image")
        self.mode_group.addButton(self.note_mode, 1)
        mode_layout.addWidget(self.note_mode)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #666;")
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Callbacks
        if self._extraction_service:
            self._extraction_service.on_extraction_started = lambda imported_id: self._set_status("Extracting...")
            self._extraction_service.on_extraction_completed = lambda imported_id, result_id: self._show_confirmation(result_id)
            self._extraction_service.on_extraction_failed = lambda imported_id, msg: self._set_status(f"Failed: {msg}")

    def _browse(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Documents (*.pdf *.png *.jpg *.jpeg)")
        if file_path:
            self.path_field.setText(file_path)

    def _on_ok(self):
        path = self.path_field.text().strip()
        if not path:
            QMessageBox.warning(self, "Warning", "Please select a file to import")
            return
        try:
            service = FileImportService()
            imported = service.import_file(path)
            service.close()
            self._set_status("Imported. Queuing extraction...")
            # Determine mode from radio buttons
            mode = "bill" if self.bill_mode.isChecked() else "note"
            self._current_mode = mode
            # Submit extraction using QTimer to ensure we're in the event loop
            from PySide6.QtCore import QTimer
            import asyncio
            
            def submit_extraction():
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                async def _submit():
                    await self._extraction_service.submit_extraction(imported.id, mode=mode)
                
                loop.create_task(_submit())
            
            QTimer.singleShot(100, submit_extraction)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")

    def _set_status(self, text: str):
        self.status.setText(text)

    def _show_confirmation(self, result_id: int):
        """Show confirmation dialog with extracted content."""
        # Load extraction result
        from app.database import SessionLocal
        from app.modules.file_ingestion.models import ExtractionResult
        
        db = SessionLocal()
        try:
            result = db.query(ExtractionResult).filter(ExtractionResult.id == result_id).first()
            if not result:
                self._set_status("Error: Result not found")
                return
            
            # Build extraction result dict
            extraction_data = {
                "raw_text": result.raw_text,
                "structured_fields": result.structured_fields,
                "mode": result.mode,
                "provider": result.provider
            }
            
            # Show confirmation dialog
            confirm_dialog = ExtractionConfirmationDialog(
                extraction_data, 
                self._current_mode or "note",
                parent=self
            )
            
            if confirm_dialog.exec() == QDialog.DialogCode.Accepted:
                choice = confirm_dialog.save_choice
                
                if choice == "note":
                    self._save_to_note(extraction_data)
                elif choice == "task":
                    self._save_to_task(extraction_data)
                
                # Close the import dialog
                self.accept()
            else:
                self._set_status("Cancelled")
        
        finally:
            db.close()
    
    def _save_to_note(self, extraction_data: Dict[str, Any]):
        """Save extracted content to a note."""
        try:
            from app.modules.notes.view_models import NotesViewModel
            
            # Build note title and content
            if extraction_data.get("structured_fields"):
                fields = extraction_data["structured_fields"]
                title = fields.get("vendor", "Imported Bill")
                
                # Format content with structured fields
                content = self._format_bill_as_markdown(fields, extraction_data.get("raw_text"))
            else:
                # Generic note
                raw_text = extraction_data.get("raw_text", "")
                if raw_text:
                    title = raw_text[:60].strip() + "..." if len(raw_text) > 60 else raw_text.strip()
                else:
                    title = "Imported Document"
                content = raw_text
            
            # Ensure title and content are not empty
            title = title.strip() if title else "Imported Document"
            content = content.strip() if content else "No content extracted"
            
            print(f"[FileImport] Saving note: title='{title}' ({len(title)} chars), content=({len(content)} chars)")
            
            # Create note
            notes_vm = NotesViewModel()
            
            try:
                print(f"[FileImport] Attempting to create note with NotesViewModel...")
                note_id = notes_vm.create_note(
                    title=title,
                    content=content,
                    color="yellow" if extraction_data.get("mode") == "bill" else "default"
                )
                print(f"[FileImport] create_note returned: {note_id}")
            except Exception as inner_e:
                print(f"[FileImport] create_note raised exception: {inner_e}")
                import traceback
                traceback.print_exc()
                note_id = None
            
            if note_id:
                print(f"[FileImport] Note created successfully with ID: {note_id}")
                QMessageBox.information(self, "Success", f"✅ Saved as note: '{title}'")
            else:
                print(f"[FileImport] Failed to create note - note_id is None")
                QMessageBox.warning(self, "Warning", "Failed to create note")
        
        except Exception as e:
            print(f"[FileImport] Exception while saving note: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")
    
    def _save_to_task(self, extraction_data: Dict[str, Any]):
        """Save extracted content as a task."""
        try:
            # Build task title from extraction
            if extraction_data.get("structured_fields"):
                fields = extraction_data["structured_fields"]
                vendor = fields.get("vendor", "")
                total = fields.get("total", "")
                title = f"Pay {vendor} - {total}" if vendor and total else fields.get("vendor", "Imported Bill")
            else:
                raw_text = extraction_data.get("raw_text", "")
                title = raw_text[:100] + "..." if len(raw_text) > 100 else raw_text or "Imported Document"
            
            # Create task
            tvm = TaskViewModel(parent=self)
            tvm.create_task(title=title)
            
            QMessageBox.information(self, "Success", f"✅ Created task: '{title}'")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create task: {e}")
    
    def _format_bill_as_markdown(self, fields: Dict[str, Any], raw_text: Optional[str] = None) -> str:
        """Format bill fields as markdown for note content."""
        lines = []
        
        lines.append("# 📄 Bill/Invoice")
        lines.append("")
        
        if fields.get("vendor"):
            lines.append(f"**Vendor:** {fields['vendor']}")
        
        if fields.get("date"):
            lines.append(f"**Date:** {fields['date']}")
        
        lines.append("")
        
        if fields.get("items"):
            lines.append("## Items")
            for item in fields["items"]:
                lines.append(f"- {item}")
            lines.append("")
        
        if fields.get("subtotal") or fields.get("tax") or fields.get("total"):
            lines.append("## Summary")
            if fields.get("subtotal"):
                lines.append(f"- Subtotal: {fields['subtotal']}")
            if fields.get("tax"):
                lines.append(f"- Tax: {fields['tax']}")
            if fields.get("total"):
                lines.append(f"- **Total: {fields['total']}**")
            lines.append("")
        
        if fields.get("notes"):
            lines.append("## Notes")
            lines.append(fields["notes"])
            lines.append("")
        
        if raw_text:
            lines.append("---")
            lines.append("")
            lines.append("## Raw Extracted Text")
            lines.append("```")
            lines.append(raw_text)
            lines.append("```")
        
        return "\n".join(lines)

    def _show_results(self, result_id: int):
        """Legacy method - kept for compatibility."""
        dialog = ExtractionResultsDialog(result_id, parent=self)
        dialog.exec()


class ExtractionResultsDialog(QDialog):
    def __init__(self, result_id: int, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("Extraction Results")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        # Load result
        from app.database import SessionLocal
        from app.modules.file_ingestion.models import ExtractionResult
        db = SessionLocal()
        try:
            self.result = db.query(ExtractionResult).filter(ExtractionResult.id == result_id).first()
        finally:
            db.close()

        # Raw text
        layout.addWidget(QLabel("Raw Text:"))
        self.raw_text = QTextEdit()
        self.raw_text.setPlainText(self.result.raw_text or "")
        layout.addWidget(self.raw_text)

        # Structured fields (nicely formatted)
        if self.result.structured_fields:
            layout.addWidget(QLabel("Extracted Fields:"))
            fields_widget = QWidget()
            fields_layout = QFormLayout(fields_widget)
            
            for key, value in self.result.structured_fields.items():
                field_label = key.replace("_", " ").title() + ":"
                field_value = QLineEdit(str(value) if value else "")
                fields_layout.addRow(field_label, field_value)
            
            layout.addWidget(fields_widget)

        # Create Task button
        create_btn = QPushButton("Create Task from Result")
        create_btn.clicked.connect(self._create_task)
        layout.addWidget(create_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _create_task(self):
        # Use first 120 chars of raw text as task title
        title = (self.raw_text.toPlainText() or "Imported Document").strip()
        if len(title) > 120:
            title = title[:117] + "..."
        try:
            tvm = TaskViewModel(parent=self)
            tvm.create_task(title=title)
            QMessageBox.information(self, "Success", "Task created from extraction result.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create task: {e}")


class ExtractionConfirmationDialog(QDialog):
    """Dialog to confirm extracted content and choose where to save."""
    
    def __init__(self, extraction_result: Dict[str, Any], mode: str, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.extraction_result = extraction_result
        self.mode = mode
        self.save_choice = None  # Will be "note", "task", or None
        
        self.setWindowTitle("Confirm Extracted Content")
        self.setMinimumSize(700, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the confirmation dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel("📄 Gemini has scanned your document")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Please review the extracted content below:")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(subtitle)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.StyledPanel)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)
        
        # Display extracted content based on mode
        if self.mode == "bill" and self.extraction_result.get("structured_fields"):
            self._add_bill_content(content_layout)
        else:
            self._add_note_content(content_layout)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, stretch=1)
        
        # Confirmation question
        confirm_label = QLabel("Is this information correct?")
        confirm_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
        layout.addWidget(confirm_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Save options
        save_label = QLabel("Save as:")
        save_label.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(save_label)
        
        self.save_note_btn = QPushButton("📝 Note")
        self.save_note_btn.setObjectName("saveNoteButton")
        self.save_note_btn.setMinimumHeight(40)
        self.save_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ade80;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #22c55e;
            }
        """)
        self.save_note_btn.clicked.connect(self._on_save_note)
        button_layout.addWidget(self.save_note_btn)
        
        self.save_task_btn = QPushButton("✅ Task")
        self.save_task_btn.setObjectName("saveTaskButton")
        self.save_task_btn.setMinimumHeight(40)
        self.save_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #60a5fa;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
        """)
        self.save_task_btn.clicked.connect(self._on_save_task)
        button_layout.addWidget(self.save_task_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set default for bills
        if self.mode == "bill":
            hint_label = QLabel("💡 Bills are typically saved as Notes by default")
            hint_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
            layout.addWidget(hint_label)
    
    def _add_bill_content(self, layout: QVBoxLayout):
        """Add bill structured content to layout."""
        fields = self.extraction_result.get("structured_fields", {})
        
        # Vendor
        if fields.get("vendor"):
            vendor_label = QLabel("🏢 Vendor:")
            vendor_label.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(vendor_label)
            
            vendor_value = QLabel(fields["vendor"])
            vendor_value.setStyleSheet("font-size: 13px; margin-left: 20px; margin-bottom: 8px;")
            vendor_value.setWordWrap(True)
            layout.addWidget(vendor_value)
        
        # Date
        if fields.get("date"):
            date_label = QLabel("📅 Date:")
            date_label.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(date_label)
            
            date_value = QLabel(fields["date"])
            date_value.setStyleSheet("font-size: 13px; margin-left: 20px; margin-bottom: 8px;")
            layout.addWidget(date_value)
        
        # Items
        if fields.get("items"):
            items_label = QLabel("🛒 Items:")
            items_label.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(items_label)
            
            for item in fields["items"]:
                item_label = QLabel(f"  • {item}")
                item_label.setStyleSheet("font-size: 12px; margin-left: 20px;")
                item_label.setWordWrap(True)
                layout.addWidget(item_label)
            layout.addSpacing(8)
        
        # Financial details
        financial_frame = QFrame()
        financial_frame.setFrameShape(QFrame.Shape.StyledPanel)
        financial_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 4px; padding: 8px;")
        financial_layout = QVBoxLayout(financial_frame)
        
        if fields.get("subtotal"):
            subtotal_label = QLabel(f"Subtotal: {fields['subtotal']}")
            subtotal_label.setStyleSheet("font-size: 12px;")
            financial_layout.addWidget(subtotal_label)
        
        if fields.get("tax"):
            tax_label = QLabel(f"Tax: {fields['tax']}")
            tax_label.setStyleSheet("font-size: 12px;")
            financial_layout.addWidget(tax_label)
        
        if fields.get("total"):
            total_label = QLabel(f"💰 Total: {fields['total']}")
            total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #22c55e;")
            financial_layout.addWidget(total_label)
        
        if fields.get("subtotal") or fields.get("tax") or fields.get("total"):
            layout.addWidget(financial_frame)
        
        # Additional notes
        if fields.get("notes"):
            notes_label = QLabel("📋 Additional Notes:")
            notes_label.setStyleSheet("font-weight: bold; color: #333; margin-top: 8px;")
            layout.addWidget(notes_label)
            
            notes_text = QTextEdit()
            notes_text.setPlainText(fields["notes"])
            notes_text.setReadOnly(True)
            notes_text.setMaximumHeight(100)
            notes_text.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd;")
            layout.addWidget(notes_text)
    
    def _add_note_content(self, layout: QVBoxLayout):
        """Add generic note content to layout."""
        raw_text = self.extraction_result.get("raw_text", "")
        
        content_label = QLabel("📝 Extracted Content:")
        content_label.setStyleSheet("font-weight: bold; color: #333; margin-bottom: 8px;")
        layout.addWidget(content_label)
        
        text_display = QTextEdit()
        text_display.setPlainText(raw_text or "No content extracted")
        text_display.setReadOnly(True)
        text_display.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(text_display)
    
    def _on_save_note(self):
        """Handle save as note."""
        self.save_choice = "note"
        self.accept()
    
    def _on_save_task(self):
        """Handle save as task."""
        self.save_choice = "task"
        self.accept()
