# Calendar Generator Module

A Python module for generating iCalendar (.ics) files compatible with Apple Calendar, Google Calendar, and Microsoft Outlook. Designed for the Meeting to Project Pipeline skill.

## Features

- ✅ **Cross-platform compatibility** - Works with Apple Calendar, Google Calendar, Outlook
- ✅ **Timezone support** - Default Asia/Kolkata (GMT+5:30), customizable
- ✅ **Attendee management** - Support for multiple attendees with proper email formatting
- ✅ **Line folding** - RFC 5545 compliant line wrapping (75 char limit)
- ✅ **Text escaping** - Proper escaping of special characters
- ✅ **Multiple events** - Generate single or batch calendar files
- ✅ **Meeting proposals** - Create multiple optional time slots

## Installation

No external dependencies required. Uses only Python standard library:

```bash
# Python 3.9+ recommended
python --version
```

## Quick Start

```python
from datetime import datetime
from calendar_generator import create_calendar_event, save_ics_to_file

# Create a calendar event
ics_content = create_calendar_event(
    title="Project Kickoff",
    start_time=datetime(2024, 3, 15, 10, 0),
    end_time=datetime(2024, 3, 15, 11, 0),
    attendees=["alice@example.com", "bob@example.com"],
    description="Kickoff meeting for the new project",
    location="Conference Room A"
)

# Save to file
save_ics_to_file(ics_content, "/path/to/output", "kickoff.ics")
```

## API Reference

### `create_calendar_event()`

Create an .ics calendar event string.

```python
def create_calendar_event(
    title: str,
    start_time: datetime,
    end_time: datetime,
    attendees: list[str],
    description: str,
    location: str = "",
    organizer_name: str = DEFAULT_ORGANIZER_NAME,
    organizer_email: str = DEFAULT_ORGANIZER_EMAIL,
) -> str
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | `str` | Event title/summary |
| `start_time` | `datetime` | Event start time (naive = UTC, aware = converted) |
| `end_time` | `datetime` | Event end time (must be after start) |
| `attendees` | `list[str]` | List of attendee email addresses |
| `description` | `str` | Event description |
| `location` | `str` | Optional location (physical or URL) |
| `organizer_name` | `str` | Event organizer display name |
| `organizer_email` | `str` | Event organizer email |

**Returns:** String containing valid iCalendar (.ics) content

**Example:**

```python
ics = create_calendar_event(
    title="Team Standup",
    start_time=datetime(2024, 3, 15, 9, 30),
    end_time=datetime(2024, 3, 15, 10, 0),
    attendees=["team@company.com"],
    description="Daily standup meeting",
    location="https://meet.google.com/abc-defg-hij"
)
```

---

### `create_calendar_from_meeting()`

Generate multiple .ics events from meeting extraction data.

```python
def create_calendar_from_meeting(
    meeting_data: dict[str, Any],
    organizer_name: str = DEFAULT_ORGANIZER_NAME,
    organizer_email: str = DEFAULT_ORGANIZER_EMAIL,
) -> list[str]
```

**Expected `meeting_data` structure:**

```python
{
    "meeting_title": "Q1 Planning Session",  # Optional, adds context
    "extracted_date": "2024-03-15",          # Optional
    "events": [                              # Required, list of events
        {
            "title": "Sprint Planning",
            "start_time": "2024-03-15T10:00:00",  # ISO 8601 format
            "end_time": "2024-03-15T11:30:00",    # Optional (use duration)
            "duration_minutes": 90,                # Alternative to end_time
            "attendees": ["dev@example.com"],      # Event-specific
            "description": "Plan the sprint",
            "location": "Conference Room A"
        },
        # ... more events
    ],
    "participants": ["alice@example.com"],   # Default attendees for all
    "default_location": "Main Office"        # Default if not specified
}
```

**Returns:** List of .ics content strings (one per event)

**Example:**

```python
meeting_data = {
    "meeting_title": "Project Review",
    "participants": ["pm@company.com"],
    "default_location": "Zoom",
    "events": [
        {
            "title": "Design Review",
            "start_time": "2024-03-15T10:00:00",
            "duration_minutes": 60,
            "attendees": ["designer@company.com"],
            "description": "Review UI mockups"
        },
        {
            "title": "Code Review",
            "start_time": "2024-03-15T14:00:00",
            "end_time": "2024-03-15T15:30:00",
            "attendees": ["dev@company.com"],
            "description": "Review implementation"
        }
    ]
}

ics_list = create_calendar_from_meeting(meeting_data)
for i, ics in enumerate(ics_list):
    with open(f"event_{i}.ics", "w") as f:
        f.write(ics)
```

---

### `generate_meeting_invite()`

Generate multiple .ics files for proposed meeting slots (time polling).

```python
def generate_meeting_invite(
    meeting_title: str,
    proposed_slots: list[tuple[datetime, datetime]],
    attendees: list[str],
    description: str = "",
    location: str = "",
) -> list[str]
```

**Use case:** Send multiple time options and let attendees choose.

**Example:**

```python
from datetime import datetime, timedelta

slots = [
    (datetime(2024, 3, 15, 10, 0), datetime(2024, 3, 15, 11, 0)),
    (datetime(2024, 3, 15, 14, 0), datetime(2024, 3, 15, 15, 0)),
    (datetime(2024, 3, 16, 10, 0), datetime(2024, 3, 16, 11, 0)),
]

ics_options = generate_meeting_invite(
    meeting_title="Client Meeting",
    proposed_slots=slots,
    attendees=["client@example.com", "sales@example.com"],
    description="Please choose one of the available slots",
    location="https://zoom.us/j/123456"
)

# Each .ics will be labeled as "Option 1", "Option 2", etc.
```

---

### `save_ics_to_file()`

Save .ics content to a file with automatic directory creation.

```python
def save_ics_to_file(
    ics_content: str,
    filepath: str | Path,
    filename: str | None = None
) -> Path
```

**Example:**

```python
# Save to directory with filename
path = save_ics_to_file(ics_content, "/tmp/calendar", "event.ics")

# Or with full path
path = save_ics_to_file(ics_content, "/tmp/calendar/my-event.ics")

# Automatically creates nested directories
path = save_ics_to_file(ics_content, "/tmp/a/b/c", "deep.ics")
```

---

## Advanced Usage

### Custom ICSGenerator

For more control, use the `ICSGenerator` class directly:

```python
from calendar_generator import ICSGenerator, CalendarEvent

generator = ICSGenerator(
    timezone="America/New_York",  # Custom timezone
    prod_id="-//MyCompany//Custom App//EN"  # Custom product ID
)

event = CalendarEvent(
    title="Custom Event",
    start_time=datetime(2024, 3, 15, 10, 0),
    end_time=datetime(2024, 3, 15, 11, 0),
    attendees=["user@example.com"],
    description="A custom event",
    organizer_name="Custom Org",
    organizer_email="custom@example.com"
)

ics = generator.generate(event)
```

### Batch Events

Generate a single .ics file with multiple events:

```python
events = [
    CalendarEvent(
        title=f"Event {i}",
        start_time=datetime(2024, 3, 15, 10 + i, 0),
        end_time=datetime(2024, 3, 15, 11 + i, 0),
        attendees=["user@example.com"],
        description=f"Description {i}",
    )
    for i in range(5)
]

ics = generator.generate_batch(events)
```

---

## Timezone Handling

### Default Behavior

- **Default timezone:** Asia/Kolkata (IST, GMT+5:30)
- Naive datetimes: Assumed to be UTC, converted accordingly
- Timezone-aware datetimes: Converted to UTC in output

### Timezone Formats Supported

| Format | Example | Notes |
|--------|---------|-------|
| ISO 8601 | `2024-03-15T10:00:00` | Assumed UTC |
| With TZ | `2024-03-15T10:00:00+05:30` | Parsed with timezone |
| Space sep | `2024-03-15 10:00:00` | Also supported |
| Date only | `2024-03-15` | Assumes 00:00:00 |

### Custom Timezone

```python
from datetime import datetime, timezone, timedelta

# Create timezone-aware datetime
ist = timezone(timedelta(hours=5, minutes=30))
start = datetime(2024, 3, 15, 10, 0, tzinfo=ist)

ics = create_calendar_event(
    title="IST Meeting",
    start_time=start,
    end_time=start + timedelta(hours=1),
    attendees=["user@example.com"],
    description="Meeting in IST timezone"
)
# Output will be in UTC: 20240315T043000Z
```

---

## Testing

Run the test suite:

```bash
# Using pytest
python -m pytest test_calendar_generator.py -v

# Using unittest
python -m unittest test_calendar_generator

# Run specific test class
python -m pytest test_calendar_generator.py::TestCreateCalendarEvent -v

# With coverage
python -m pytest test_calendar_generator.py --cov=calendar_generator --cov-report=html
```

### Test Coverage

- ✅ Calendar event dataclass
- ✅ ICS format generation
- ✅ Line folding (RFC 5545)
- ✅ Text escaping
- ✅ Timezone handling
- ✅ Attendee normalization
- ✅ Meeting data parsing
- ✅ File operations
- ✅ Integration workflows

---

## RFC 5545 Compliance

This module generates iCalendar data compliant with RFC 5545:

- **Line folding:** Lines > 75 characters are folded with CRLF + space
- **Character escaping:** Backslash, semicolon, comma, newline escaped
- **Date formats:** Uses UTC format (`YYYYMMDDTHHMMSSZ`) for max compatibility
- **Required fields:** UID, DTSTAMP, DTSTART, DTEND all present
- **CRLF line endings:** Required by spec, always used

---

## File Structure

```
meeting-pipeline/
├── calendar_generator.py      # Main module
├── test_calendar_generator.py # Unit tests
└── CALENDAR_GENERATOR.md      # This documentation
```

---

## Integration with Meeting Pipeline

Example integration in the main pipeline:

```python
from meeting_pipeline import extract_events
from calendar_generator import create_calendar_from_meeting, save_ics_to_file

# Step 1: Extract events from meeting transcription
meeting_data = extract_events(transcription_text)

# Step 2: Generate calendar invites
ics_list = create_calendar_from_meeting(meeting_data)

# Step 3: Save to output directory
output_dir = "/output/calendar_invites"
for i, ics_content in enumerate(ics_list):
    event_title = meeting_data["events"][i]["title"]
    filename = f"{event_title.replace(' ', '_')}.ics"
    save_ics_to_file(ics_content, output_dir, filename)

# Step 4: Send invites (optional)
for attendee in meeting_data.get("participants", []):
    send_calendar_invite(attendee, ics_list)
```

---

## Troubleshooting

### Event not showing in calendar

1. Check UID is unique per event
2. Verify DTSTAMP is present and correct
3. Ensure CRLF line endings (not just LF)

### Timezone issues

1. Use timezone-aware datetimes for clarity
2. Verify VTIMEZONE block is present in .ics
3. Check calendar app supports the timezone

### Special characters not displaying

- Description: Use `\\n` for newlines
- Avoid `;` and `,` unescaped (module handles this automatically)

---

## License

Part of the Meeting to Project Pipeline skill. Internal use only.

## Changelog

### v1.0.0
- Initial release
- RFC 5545 compliant ICS generation
- Support for Apple Calendar, Google Calendar, Outlook
- Asia/Kolkata default timezone
- Attendee and organizer support