import pytest

from PySide6.QtWidgets import QApplication, QTreeWidget

from app.ui.shortcut_help_dialog import ShortcutHelpDialog
from app.utils.shortcut_definitions import (
    ShortcutDefinition,
    CATEGORY_GENERAL,
    CATEGORY_ACTIONS,
)


def test_shortcut_help_dialog_renders_categories_and_items(qtbot):
    app = QApplication.instance() or QApplication([])

    shortcuts = {
        CATEGORY_GENERAL: [
            ShortcutDefinition(
                action_id="open_help",
                sequences=["F1", "Ctrl+/"],
                description="Open help",
                category=CATEGORY_GENERAL,
                allow_in_text_fields=True,
            )
        ],
        CATEGORY_ACTIONS: [
            ShortcutDefinition(
                action_id="do_thing",
                sequences=["Ctrl+D"],
                description="Do thing",
                category=CATEGORY_ACTIONS,
                allow_in_text_fields=False,
            )
        ],
    }

    dialog = ShortcutHelpDialog(shortcuts)
    qtbot.addWidget(dialog)

    dialog.show()
    assert dialog.isVisible()

    # Verify that there are two top-level categories
    tree = dialog.findChild(QTreeWidget, "shortcutTree")
    assert tree is not None
    assert tree.topLevelItemCount() == 2

    # Verify child items exist under each category
    for idx in range(tree.topLevelItemCount()):
        category_item = tree.topLevelItem(idx)
        assert category_item.childCount() >= 1
