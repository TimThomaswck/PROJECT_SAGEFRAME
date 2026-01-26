import time

from PySide6.QtWidgets import QApplication, QWidget

from app.core.shortcut_manager import ShortcutManager
from app.utils.shortcut_definitions import ShortcutDefinition, CATEGORY_GENERAL


def test_shortcut_activation_latency_under_100ms(qtbot):
    """Validate activation path latency meets NFR1 (<100ms)."""
    app = QApplication.instance() or QApplication([])
    parent = QWidget()
    qtbot.addWidget(parent)

    mgr = ShortcutManager(parent)

    called = {"count": 0}

    def on_trigger():
        called["count"] += 1

        
    definition = ShortcutDefinition(
        action_id="perf_action",
        sequences=["Ctrl+Alt+P"],
        description="Performance test action",
        category=CATEGORY_GENERAL,
        allow_in_text_fields=True,
    )

    mgr.register_shortcut(definition, on_trigger)

    start = time.perf_counter()
    mgr.activate("perf_action")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert called["count"] == 1
    # Target comfortably below 100ms for logic path
    assert elapsed_ms < 100.0
