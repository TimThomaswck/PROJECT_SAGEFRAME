"""Shortcut help dialog listing keyboard shortcuts with categories."""

from typing import Dict, Iterable, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.utils.shortcut_definitions import ShortcutDefinition


class ShortcutHelpDialog(QDialog):
    """Modal dialog showing keyboard shortcuts grouped by category."""

    def __init__(
        self,
        shortcuts_by_category: Dict[str, List[ShortcutDefinition]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.setObjectName("shortcutHelpDialog")
        self.setMinimumSize(540, 360)

        self._shortcuts_by_category = shortcuts_by_category
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        header = QLabel("Keyboard shortcut reference")
        header.setObjectName("shortcutHelpHeader")
        header.setAccessibleName("Shortcut help header")
        layout.addWidget(header)

        description = QLabel(
            "Quickly navigate Sageframe using these keyboard shortcuts."
        )
        description.setWordWrap(True)
        description.setAccessibleDescription(
            "List of keyboard shortcuts grouped by category"
        )
        layout.addWidget(description)

        self._tree = QTreeWidget()
        self._tree.setObjectName("shortcutTree")
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["Action", "Shortcut"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self._tree.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self._tree, 1)

        self._populate_tree(self._shortcuts_by_category)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setTabOrder(self._tree, buttons)

    def _populate_tree(
        self, shortcuts_by_category: Dict[str, List[ShortcutDefinition]]
    ) -> None:
        self._tree.clear()
        for category in sorted(shortcuts_by_category.keys()):
            category_item = QTreeWidgetItem([category, ""])
            category_item.setFirstColumnSpanned(True)
            self._tree.addTopLevelItem(category_item)

            for definition in shortcuts_by_category[category]:
                shortcut_text = ", ".join(definition.sequences)
                item = QTreeWidgetItem([definition.description, shortcut_text])
                category_item.addChild(item)

        self._tree.expandAll()
        self._tree.resizeColumnToContents(0)

    def update_shortcuts(
        self, shortcuts_by_category: Dict[str, List[ShortcutDefinition]]
    ) -> None:
        """Refresh the tree with a new set of shortcuts."""
        self._shortcuts_by_category = shortcuts_by_category
        self._populate_tree(shortcuts_by_category)
