# 🤖 How to See the AI Co-Pilot in Action

## Overview
The AI Co-Pilot ("Jarvis") is now integrated into the SageFrame application. It provides empathetic, context-aware communication that responds to your mood and creates a supportive environment.

---

## Quick Start: Seeing the Co-Pilot

### Step 1: Look at the Application Window
When the app launches, you should see:
- **Main window** with projects, tasks, and other panels
- **"AI Co-Pilot" dock panel** on the right side (empty initially)
- **"Mood Check-in" button** in the top-left corner (blue button)

### Step 2: Trigger a Mood Check-in
1. Click the **"Mood Check-in"** button (Ctrl+Shift+M)
2. A dialog opens asking about your:
   - **Mood**: How you're feeling (Happy, Sad, Stressed, Focused, Neutral, Tired)
   - **Energy Level**: Your current energy (1-10 scale)
   - **Optional Notes**: What you've been doing

### Step 3: Watch the Co-Pilot Respond!
After you submit your mood check-in:

1. **Co-Pilot Dock appears** with an **empathetic message tailored to your mood**
2. The message will:
   - ✅ Be **calm and supportive** (never harsh or technical)
   - ✅ Consider your **mood and energy level**
   - ✅ **Automatically fade out** after 8 seconds
   - ✅ Show **dismiss** or **acknowledge** buttons

---

## What to Notice: Co-Pilot Features

### 🎯 Mood-Aware Responses

| Mood | Co-Pilot Response |
|------|-------------------|
| **Happy + High Energy** | 🎉 Celebratory message: "That's wonderful energy! Keep up the momentum!" |
| **Stressed** | 🧘 Calming message: "I'm here to support you. Let's take this one step at a time." |
| **Low Energy** | 💪 Gentle encouragement: "Rest when you can. You're doing better than you think." |
| **Focused** | 🎯 Respectful message: "I notice you're in flow—continuing to respect your focus." |
| **Tired** | 😴 Supportive: "Your well-being matters. Consider taking a break when you're ready." |

### ✨ Key Characteristics You'll See:

1. **Non-Intrusive Design**
   - Message appears in a small panel on the right
   - Doesn't interrupt your work
   - Auto-dismisses after 8 seconds

2. **Calm, Supportive Tone**
   - No technical jargon (no "errors", "failures", "bugs")
   - Uses empathetic language ("I notice", "let's try")
   - Celebrates progress, not just wins

3. **Context-Aware Delivery**
   - If you're in "focus mode", message respects that
   - Can defer messages if you're in a flow state
   - Respects "Do Not Disturb" preferences

4. **Message Variety**
   - Multiple message templates for each mood
   - You'll see different messages if you do multiple check-ins
   - Prevents repetitive, generic responses

---

## The Co-Pilot Architecture (What's Happening Behind the Scenes)

### Signal Flow
```
1. You click "Mood Check-in" button
   ↓
2. You fill in mood/energy and submit
   ↓
3. MoodCheckInViewModel emits moodCheckInCompleted signal
   ↓
4. MainWindow._on_mood_checkin_completed() catches signal
   ↓
5. CopilotCommunicationService.generate_mood_response() generates empathetic message
   ↓
6. Message is validated for tone compliance (checks for forbidden phrases, jargon)
   ↓
7. Message is stored in SQLite database (CommunicationEvent table)
   ↓
8. CopilotViewModel receives message and emits messageReady signal
   ↓
9. CopilotPanel displays message in dock widget with fade-in animation
   ↓
10. Message auto-dismisses after 8 seconds or user clicks dismiss
```

### Key Components

**Service Layer** (`CopilotCommunicationService`):
- 📝 Generates messages with 40+ empathetic templates
- ✅ Validates tone (forbidden phrases, jargon filtering, anxiety triggers)
- 💾 Stores communication history in database
- ⏰ Manages delivery timing (respects flow states, DND mode)

**ViewModel Layer** (`CopilotViewModel`):
- 📊 Manages UI state (current message, pending status, queue)
- 🔔 Emits signals for UI reactions
- 🎯 Handles message display with context awareness
- 📱 Provides Qt properties for reactive data binding

**View Layer** (`CopilotPanel`):
- 🎨 Displays messages in a minimalist RPG-style design
- ⚡ Smooth fade-in/slide-in animations (200ms)
- ⌨️ Full keyboard accessibility
- 🔘 Dismiss and acknowledge buttons

**Integration** (`MoodAwareCopilotIntegration`):
- 🔗 Connects mood check-in (Story 1.3) to co-pilot (Story 1.4)
- 📋 Maps mood/energy to appropriate tone levels
- 💾 Stores mood context with messages for learning

---

## Try These Different Moods

### 1. Happy + High Energy (7-10)
- **Expected Response**: Celebratory tone, encouraging momentum
- **Example**: "That's wonderful energy! Let's channel it into something meaningful!"

### 2. Stressed (Any Energy)
- **Expected Response**: Gentle, calming tone
- **Example**: "I'm here to support you. Let's take this one step at a time."

### 3. Focused/Flow State
- **Expected Response**: Respectful, non-intrusive
- **Example**: "I notice you're in the zone. Keep going—I'll be here if you need anything."

### 4. Low Energy + Tired
- **Expected Response**: Gentle, supportive
- **Example**: "Your well-being matters. Rest when you can. You're doing better than you think."

### 5. Neutral/Medium
- **Expected Response**: Normal encouraging tone
- **Example**: "You're doing great today. One step at a time!"

---

## The Tone Validation System (Behind the Scenes)

The co-pilot has **strict tone enforcement** to ensure every message is empathetic:

### ✅ **Allowed Phrases**
- "Let's try...", "I notice...", "You're doing...", "How can I help..."
- "I believe in you", "Taking things one step at a time"

### ❌ **Forbidden Phrases** (NEVER appear)
- "error", "failed", "warning", "critical", "bug", "crash"
- "unable to", "couldn't", "problem", "disaster"

### 🔄 **Jargon Replacement**
- "exception" → "unexpected result"
- "debug" → "investigate"
- "optimization" → "improvement"
- "API endpoint" → "connection"

### 😰 **Anxiety Triggers Avoided**
- "fatal" → "needs attention"
- "disabled" → "temporarily unavailable"
- "corrupt" → "needs recovery"

---

## Database: See the History

The co-pilot stores all communication events in SQLite:

```sql
SELECT 
    message_id,
    message_text,
    category,
    status,
    created_at,
    metadata
FROM communication_events
ORDER BY created_at DESC
LIMIT 10;
```

**Fields Stored:**
- `message_id`: Unique identifier
- `message_text`: The actual message
- `category`: Type (mood_response, greeting, encouragement, etc.)
- `status`: GENERATED, DELIVERED, DISMISSED, ACKNOWLEDGED
- `activity_state`: User's activity at delivery time
- `metadata`: Mood, energy, timestamp
- `created_at`, `updated_at`: Audit timestamps

---

## UI Elements You'll See

### Co-Pilot Dock Panel
```
┌─────────────────────────────┐
│ 🤖 AI Co-Pilot              │
├─────────────────────────────┤
│ That's wonderful energy!     │
│ Let's channel it into        │
│ something meaningful.        │
│                              │
│ [Dismiss]  [Acknowledge]     │
└─────────────────────────────┘
```

### Animations
- **Fade-in**: 200ms smooth opacity transition
- **Auto-dismiss**: 8 seconds with fade-out
- **Interaction**: Immediate response to dismiss/acknowledge

---

## What's Next (Future Enhancements)

### Phase 2: LLM Integration
- Replace templates with **Google Gemini 2.5 Flash** AI
- Maintain persona guidelines as system prompt
- Keep tone validation on AI outputs
- Add API key management

### Phase 3: Advanced Context
- Real-time mood tracking (beyond check-ins)
- Calendar integration for focus detection
- Productivity pattern learning
- Personalized message generation

### Phase 4: Gamification Integration
- Celebratory messages for achievements
- Progress milestone recognition
- Custom celebration variations

---

## Troubleshooting

### Co-Pilot panel not showing?
1. Click "Mood Check-in" button
2. Complete the mood check-in form
3. Panel should appear on the right side
4. Check the "View" menu for dock visibility

### Messages look generic?
- This is the **template-based MVP** phase
- Messages are pre-written for quality assurance
- Phase 2 will add AI-generated personalization

### Messages disappearing too quickly?
- Default auto-dismiss is 8 seconds
- Click "Acknowledge" to keep it visible
- Click "Dismiss" to hide immediately

### See more details?
- Check console output for debug info
- Look at database for communication history
- Check logs at: `C:\Users\LEGION\.sageframe\` directory

---

## Summary: The Co-Pilot Experience

✅ **Empathetic**: Messages are always calm and supportive  
✅ **Context-Aware**: Respects your flow state and focus  
✅ **Non-Intrusive**: Appears gently, disappears gracefully  
✅ **Quality-Assured**: Every message validated for tone  
✅ **Data-Backed**: All interactions stored for learning  
✅ **Accessible**: Full keyboard navigation and screen reader support  

---

**Try it now!** Complete a mood check-in and watch Jarvis, the empathetic co-pilot, respond with a message perfectly calibrated to your current state. 🎯
