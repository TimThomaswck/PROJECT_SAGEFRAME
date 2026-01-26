# Non-Functional Requirements

## Performance

*   **NFR1: Core Action Responsiveness:** User interactions for core actions (e.g., creating a task, logging mood, marking task complete) shall have an immediate visual response, perceived as instantaneous (<100ms visual feedback).
*   **NFR2: UI Fluidity:** Transitions between different application tabs, sections, and views shall be fluid and smooth, with no noticeable lag or stutter (<200ms for full content load and display).

## Security

*   **NFR3: Data Isolation (Local-First):** All user data stored locally on the device shall be isolated from other applications and protected by standard operating system security measures.
*   **NFR4: Cloud Sync Security:** Data synchronized to user-controlled cloud storage (e.g., Google Drive) shall utilize secure authentication protocols (e.g., OAuth 2.0) and data encryption during transit. For the initial MVP, encryption at rest for cloud data relies on the cloud provider's capabilities.

## Scalability

*   **NFR5: Modular Feature Scalability:** The system architecture shall be designed to allow for the addition of new modular features and API integrations without requiring significant re-architecting of the core platform.
*   **NFR6: Single User Focus:** The system shall prioritize optimal performance and stability for a single, individual user. High concurrent user load is not a primary scalability concern for the MVP.

## Accessibility

*   **NFR7: Basic Accessibility Standards:** The application shall adhere to basic accessibility guidelines (e.g., keyboard navigability, clear focus indicators, readable font sizes and contrast) to ensure usability for a broad audience. (Based on our target audience and general best practices).

## Integration

*   **NFR8: Integration Failure Handling:** In the event of an integration failure (e.g., calendar sync error), the system shall automatically attempt to retry the operation a configurable number of times.
*   **NFR9: Manual Reconnection/Intervention:** If automatic retries fail, the system shall provide clear user prompts for manual reconnection or intervention to resolve integration issues.

## Reliability

*   **NFR10: System Availability:** Sageframe shall aim for 99.9% availability during active use, minimizing unexpected crashes or unresponsiveness.
*   **NFR11: Data Recovery:** In the event of an application crash or unexpected shutdown, the system shall automatically recover to the last known consistent state of user data and application settings. User data loss should be prevented as much as technically feasible.

## LLM Integration Requirements

**Provider:** Google Gemini 2.5 Flash API

**User Requirements:**
*   Users must provide their own Gemini API key (free tier available at makersuite.google.com)
*   API key can be configured via Settings → AI Features UI
*   Optional: Users can choose to use template-only mode without LLM features

**Cost Transparency:**
*   Estimated user cost: $0.10-$0.50 per month for typical usage
*   Cost displayed in API key setup UI
*   Usage statistics available in Settings for user monitoring

**Privacy Guarantees:**
*   API keys stored locally in system keychain (never transmitted to Sageframe servers)
*   User data sent to Google Gemini API only with explicit user consent
*   Clear opt-in/opt-out controls for LLM features
*   Full functionality available in offline mode with template fallback