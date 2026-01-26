"""Centralized keyboard shortcut handling for Sageframe.

This manager registers shortcuts on the main window via `QAction`, routes
activations through context-aware checks (avoiding text-field conflicts),
and exposes metadata for the help dialog.
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

from app.utils.shortcut_definitions import ShortcutDefinition


class ShortcutManager(QObject):
    """Register and manage application-wide keyboard shortcuts."""

    shortcutActivated = Signal(str)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._parent = parent
        self._definitions: Dict[str, ShortcutDefinition] = {}
        self._callbacks: Dict[str, Callable[[], None]] = {}
        self._actions: List[QAction] = []
        self._sequence_to_action: Dict[str, str] = {}

    def register_shortcut(
        self,
        definition: ShortcutDefinition,
        callback: Callable[[], None],
    ) -> None:
        """Register a shortcut definition with its callback.

        Raises:
            ValueError: If the shortcut conflicts with an existing sequence
                or the action id is already registered.
        """
        if definition.action_id in self._definitions:
            raise ValueError(f"Shortcut '{definition.action_id}' already registered")

        # Conflict detection across all sequences
        for sequence in definition.sequences:
            normalized = self._normalize_sequence(sequence)
            if normalized in self._sequence_to_action:
                existing = self._sequence_to_action[normalized]
                if existing != definition.action_id:
                    raise ValueError(
                        f"Shortcut '{sequence}' conflicts with '{existing}'"
                    )

        # Create a single QAction with multiple sequences
        action = QAction(definition.description, self._parent)
        action.setShortcutVisibleInContextMenu(True)
        action.setWhatsThis(definition.description)
        action.triggered.connect(lambda _checked=False, aid=definition.action_id: self._activate(aid))

        # Assign all sequences to the action
        action.setShortcuts([QKeySequence(s) for s in definition.sequences])

        # Add to the window so it remains active regardless of focused child widget
        if isinstance(self._parent, QWidget):
            self._parent.addAction(action)

        # Track for updates and conflict checks
        self._actions.append(action)
        for sequence in definition.sequences:
            normalized = self._normalize_sequence(sequence)
            self._sequence_to_action[normalized] = definition.action_id

        self._definitions[definition.action_id] = definition
        self._callbacks[definition.action_id] = callback

    def register_many(
        self,
        definitions: Iterable[ShortcutDefinition],
        callbacks: Dict[str, Callable[[], None]],
    ) -> None:
        """Register multiple shortcuts from definitions and callbacks."""
        for definition in definitions:
            if definition.action_id not in callbacks:
                raise ValueError(
                    f"Missing callback for shortcut '{definition.action_id}'"
                )
            self.register_shortcut(definition, callbacks[definition.action_id])

    def activate(self, action_id: str) -> None:
        """Activate an action programmatically (primarily for tests)."""
        self._activate(action_id)

    def get_shortcuts_by_category(self) -> Dict[str, List[ShortcutDefinition]]:
        """Return registered shortcuts grouped by category."""
        grouped: Dict[str, List[ShortcutDefinition]] = {}
        for definition in self._definitions.values():
            grouped.setdefault(definition.category, []).append(definition)
        for definitions in grouped.values():
            definitions.sort(key=lambda item: item.description)
        return grouped

    def get_definitions(self) -> List[ShortcutDefinition]:
        """Return all registered shortcut definitions."""
        return list(self._definitions.values())

    def _activate(self, action_id: str) -> None:
        definition = self._definitions.get(action_id)
        if not definition:
            return

        focus_widget = QApplication.focusWidget()
        if (
            focus_widget
            and not definition.allow_in_text_fields
            and self._is_text_input(focus_widget)
        ):
            return

        callback = self._callbacks.get(action_id)
        if callback:
            callback()
            self.shortcutActivated.emit(action_id)

    @staticmethod
    def _is_text_input(widget: QWidget) -> bool:
        return isinstance(
            widget,
            (
                QLineEdit,
                QTextEdit,
                QPlainTextEdit,
                QComboBox,
                QAbstractSpinBox,
            ),
        )

    @staticmethod
    def _normalize_sequence(sequence: str) -> str:
        return QKeySequence(sequence).toString(QKeySequence.NativeText)
