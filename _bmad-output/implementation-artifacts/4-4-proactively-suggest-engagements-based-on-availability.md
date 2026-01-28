# Story 4.4: Proactively Suggest Engagements Based on Availability

Status: ready-for-dev

## Story

As a user,
I want Sageframe to proactively suggest social or professional engagements based on my calendar availability and user tasks,
so that I can maintain a balanced life, nurture relationships, and optimize my schedule without manual effort.

## Acceptance Criteria

1. **Given** an external calendar is connected (from Story 4.1) and free/busy times are identified (from Story 4.2), **When** the AI Co-Pilot recognizes opportunities for scheduling (e.g., a long free block, a pending task related to social outreach), **Then** it proactively suggests a social or professional engagement.

2. **Given** a suggestion is made, **When** I accept the suggestion, **Then** Sageframe uses its event creation capabilities (from Story 4.3) to schedule the engagement in my external calendar.

3. **Given** a suggestion is made, **When** I decline or dismiss the suggestion, **Then** Sageframe learns from my preferences and adjusts future proactive suggestions.

4. **Given** Sageframe suggests an engagement, **Then** the suggestion is non-intrusive and aligned with the empathetic communication style (from Story 1.4).

5. **Given** I am receiving proactive suggestions, **Then** the process is responsive and fluid (NFR1, NFR2).

## Dev Notes

**Dependencies:**
- Story 4.1 (calendar connection)
- Story 4.2 (free/busy analysis)
- Story 4.3 (event creation)
- Epic 1 Story 1.4 (AI Co-Pilot empathetic communication)

**Implementation:**
- Integrate with AI Co-Pilot (Gemini 2.5 Flash per architecture)
- Use availability data from Story 4.2 to identify scheduling opportunities
- Use task data to suggest task-related engagements
- Implement suggestion filtering (don't over-suggest, respect user preferences)

**AI Prompting:**
```
System: You are Jarvis, the empathetic co-pilot. The user has a 2-hour free block on Tuesday 2-4pm. Suggest a professional or social engagement that would be valuable.
User context: Has pending task "Schedule coffee with mentor", mood: energized
```

**Suggestion Acceptance Flow:**
1. User accepts suggestion → Create event via Story 4.3
2. User declines → Store preference (e.g., "don't suggest coffee meetings on Tuesdays")
3. User dismisses → Don't learn preference, but reduce frequency of similar suggestions

**Common Mistakes to AVOID:**
- ❌ Don't over-suggest - limit to 1-2 suggestions per day
- ❌ Don't ignore user mood/energy (from Story 1.3)
- ❌ Don't suggest during user's focus time or work blocks
- ❌ Don't forget empathetic tone - suggestions should feel helpful, not pushy

## Dev Agent Record
_To be filled by dev agent_
