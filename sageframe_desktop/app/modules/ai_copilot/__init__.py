"""
AI Co-Pilot Communication Module.

Implements the empathetic "Jarvis" co-pilot persona with calm, supportive,
and non-intrusive communication. This module manages:
- Message generation and tone validation
- Context-aware delivery (respects flow states)
- Integration with mood check-in system
- SQLite-backed communication history
"""

# Lazy imports - components will be imported as they're implemented
# from app.modules.ai_copilot.services import CopilotCommunicationService
# from app.modules.ai_copilot.view_models import CopilotViewModel
# from app.modules.ai_copilot.views import CopilotMessageWidget, CopilotPanel

__all__ = [
    "CopilotCommunicationService",
    "CopilotViewModel",
    "CopilotMessageWidget",
    "CopilotPanel",
]
