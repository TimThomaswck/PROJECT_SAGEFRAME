import pytest

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QKeySequence

from app.core.shortcut_manager import ShortcutManager
from app.utils.shortcut_definitions import ShortcutDefinition, CATEGORY_GENERAL


@pytest.mark.parametrize("key_text", ["Ctrl+Alt+T"]) 
def test_shortcut_manager_programmatic_activation(qtbot, key_text):
    app = QApplication.instance() or QApplication([])
    parent = QWidget()
    qtbot.addWidget(parent)

    mgr = ShortcutManager(parent)

    triggered = {"count": 0}

    def on_trigger():
        triggered["count"] += 1

    definition = ShortcutDefinition(
        action_id="test_action",
        sequences=[key_text],
        description="Test action",
        category=CATEGORY_GENERAL,
        allow_in_text_fields=True,
    )

    mgr.register_shortcut(definition, on_trigger)

    # Activate programmatically without sending a key event
    mgr.activate("test_action")

    assert triggered["count"] == 1
