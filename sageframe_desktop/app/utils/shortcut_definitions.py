"""Default shortcut definitions for Sageframe desktop.

Central location for declaring keyboard shortcuts so both the shortcut
manager and help dialog can rely on a single source of truth. Each
shortcut definition includes display metadata to support in-product
help and accessibility documentation.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ShortcutDefinition:
    """Metadata describing a single keyboard shortcut."""

    action_id: str
    sequences: List[str]
    description: str
    category: str
    allow_in_text_fields: bool = True


# Categories used for grouping in the help dialog
CATEGORY_GENERAL = "General"
CATEGORY_NAVIGATION = "Navigation"
CATEGORY_ACTIONS = "Actions"


def get_default_shortcuts() -> List[ShortcutDefinition]:
    """Return the default keyboard shortcuts supported by the app."""
    return [
        ShortcutDefinition(
            action_id="open_shortcut_help",
            sequences=["F1", "Ctrl+/"],
            description="Open keyboard shortcut help menu",
            category=CATEGORY_GENERAL,
            allow_in_text_fields=True,
        ),
        ShortcutDefinition(
            action_id="open_mood_checkin",
            sequences=["Ctrl+Shift+M"],
            description="Start a mood check-in",
            category=CATEGORY_ACTIONS,
            allow_in_text_fields=True,
        ),
        ShortcutDefinition(
            action_id="toggle_suggestion_panel",
            sequences=["Ctrl+Shift+S"],
            description="Show or hide AI suggestion panel",
            category=CATEGORY_NAVIGATION,
            allow_in_text_fields=True,
        ),
        ShortcutDefinition(
            action_id="refresh_suggestions",
            sequences=["Ctrl+Shift+R"],
            description="Regenerate AI suggestions for the current mood",
            category=CATEGORY_ACTIONS,
            allow_in_text_fields=False,
        ),
        ShortcutDefinition(
            action_id="undo",
            sequences=["Ctrl+Z"],
            description="Undo last action",
            category=CATEGORY_ACTIONS,
            allow_in_text_fields=True,
        ),
        ShortcutDefinition(
            action_id="redo",
            sequences=["Ctrl+Shift+Z", "Ctrl+Y"],
            description="Redo last undone action",
            category=CATEGORY_ACTIONS,
            allow_in_text_fields=True,
        ),
    ]
