# Domain-Specific Requirements

## Compliance & Data Privacy

*   **Local-First Data Storage:** All user data will be stored on the user's local device by default. This is a foundational principle to ensure user privacy and control.
*   **User-Controlled Cloud Sync:** Users will have the option to sync their data to a personal cloud storage provider of their choice (e.g., Google Drive), putting them in full control of their cloud data.

## Technical Constraints

*   **Technology Stack:** The application will be developed using Python and Python-related libraries.
*   **Platform Priority:** Development will prioritize the Windows desktop platform first, with the Android mobile platform to follow.
*   **UI/UX Design:** The user interface will feature a minimalist design with RPG-style elements to maintain a focus on performance and user engagement.

## Integration Requirements

*   **Automation & Extensibility via API:** The system will provide a user-accessible API to enable connections with third-party automation tools like IFTTT and Zapier. This allows power users to create their own workflows and extend Sageframe's capabilities.

## Industry Best Practices & Patterns

*   **Ethical AI & Transparency:** The "Jarvis" AI will be transparent about why it makes certain suggestions. Users will have clear controls to override AI recommendations and provide feedback to improve the system.
*   **Data Portability & No Lock-in:** Users will be able to export all their data at any time in a common, non-proprietary format (e.g., Markdown for notes, JSON or CSV for tasks), ensuring they are never locked into the platform.
*   **Forgiving & Reversible Actions:** Key actions will be reversible. The system will support "undo" functionality and may include version history for critical items like projects or notes.
*   **Keyboard-First Navigation:** For the Windows application, a comprehensive set of keyboard shortcuts will be implemented to allow for efficient, keyboard-driven navigation and operation. A handy, easily accessible menu or "command palette" will be available for users to reference these shortcuts.
