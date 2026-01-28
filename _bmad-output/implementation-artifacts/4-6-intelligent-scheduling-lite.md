# Story 4.6: Intelligent Scheduling (Lite)

Status: ready-for-dev

## Story

As a user,
I want the system to provide basic intelligent scheduling suggestions,
so that I can get help with planning my day.

## Acceptance Criteria

1. **Given** my connected calendar, **When** I ask for scheduling suggestions, **Then** the system can identify my free slots (relying on functionality from Story 4.2).

2. **Given** my task list, **When** I ask for scheduling suggestions, **Then** the system can suggest which tasks to work on based on their due date and my free slots.

## Dev Notes

**Dependencies:**
- Story 4.2 (free/busy analysis)
- Epic 2 (task management)
- Epic 1 Story 1.4 (AI Co-Pilot)

**Implementation:**
- Add "Suggest Schedule" button to task list or calendar view
- Use AI Co-Pilot (Gemini 2.5 Flash) to analyze tasks + availability
- Generate daily/weekly schedule suggestions
- Consider task priority, due dates, complexity, and user's energy levels (from mood check-ins)

**AI Prompting for Intelligent Scheduling:**
```
System: You are Jarvis, helping the user plan their day.
Context:
- Free slots today: 9-11am, 2-4pm, 7-9pm
- Tasks: 
  1. "Write report" (due tomorrow, complexity: high, est: 2 hours)
  2. "Review PR" (due Friday, complexity: low, est: 30 min)
  3. "Team meeting prep" (due today 3pm, complexity: medium, est: 1 hour)
- User mood: focused, high energy

Suggest: How should the user schedule their day?
```

**Suggested Schedule Output:**
```
📅 Today's Intelligent Schedule:

Morning (9-11am):
- 🎯 Write report [9:00-11:00] - High priority, matches your focus energy

Afternoon (2-4pm):
- 📋 Team meeting prep [2:00-3:00] - Due today at 3pm
- ✅ Review PR [3:00-3:30] - Quick win after prep

Evening (7-9pm):
- ⏰ Buffer time - Keep open for flexibility

Tip: Your most important task (Write report) is scheduled for your peak focus time!
```

**Common Mistakes to AVOID:**
- ❌ Don't over-schedule - leave buffer time
- ❌ Don't

 ignore task dependencies
- ❌ Don't schedule complex tasks during low-energy periods
- ❌ Don't forget to respect user's work hours preferences

## Dev Agent Record
_To be filled by dev agent_
