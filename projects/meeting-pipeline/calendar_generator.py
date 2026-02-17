"""Calendar Integration Module for Meeting to Project Pipeline

Generates .ics (iCalendar) files compatible with Apple Calendar, Google Calendar,
and Microsoft Outlook. Supports timezone handling and calendar invites with attendees.

Usage:
    from calendar_generator import create_calendar_event, create_calendar_from_meeting

    # Create a single event
    ics_content = create_calendar_event(
        title="Project Kickoff",
        start_time=datetime(2024, 3, 15, 10, 0),
        end_time=datetime(2024, 3, 15, 11, 0),
        attendees=["alice@example.com", "bob@example.com"],
        description="Kickoff meeting for the new project",
        location="Conference Room A"
    )

    # Write to file
    with open("event.ics", "w") as f:
        f.write(ics_content)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import formataddr
from pathlib import Path
from typing import Any

# Default timezone for the organization
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_ORGANIZER_NAME = "Meeting Pipeline"
DEFAULT_ORGANIZER_EMAIL = "meetings@company.com"


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class CalendarEvent:
    """Represents a single calendar event."""

    title: str
    start_time: datetime
    end_time: datetime
    attendees: list[str] = field(default_factory=list)
    description: str = ""
    location: str = ""
    organizer_name: str = DEFAULT_ORGANIZER_NAME
    organizer_email: str = DEFAULT_ORGANIZER_EMAIL
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=_utc_now)
    sequence: int = 0

    def __post_init__(self) -> None:
        # Validate times
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")

        # Normalize attendees to email format
        self.attendees = [self._normalize_email(a) for a in self.attendees if a]

    @staticmethod
    def _normalize_email(email: str) -> str:
        """Normalize email address."""
        email = email.strip()
        if "<" in email and ">" in email:
            # Extract email from "Name <email@example.com>" format
            return email[email.find("<") + 1 : email.find(">")]
        return email

    @property
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


class ICSGenerator:
    """Generates iCalendar (.ics) format content."""

    # iCalendar line wrapping limit (RFC 5545)
    LINE_LIMIT = 75

    # CR LF required by iCalendar spec
    CRLF = "\r\n"

    def __init__(
        self,
        timezone: str = DEFAULT_TIMEZONE,
        prod_id: str = "-//MeetingPipeline//Meeting to Project Pipeline//EN",
    ):
        self.timezone = timezone
        self.prod_id = prod_id

    def _fold_line(self, line: str) -> str:
        """
        Fold long lines according to RFC 5545.
        Lines longer than 75 characters must be folded.
        """
        if len(line) <= self.LINE_LIMIT:
            return line

        result = []
        while line:
            if len(line) <= self.LINE_LIMIT:
                result.append(line)
                break
            result.append(line[: self.LINE_LIMIT])
            line = " " + line[self.LINE_LIMIT :]

        return self.CRLF.join(result)

    def _escape_text(self, text: str) -> str:
        """Escape special characters in iCalendar text values."""
        if not text:
            return ""
        # Escape backslash first, then other characters
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "")
        return text

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime in UTC for iCalendar (basic format for max compatibility)."""
        # For maximum compatibility, use UTC format
        return dt.strftime("%Y%m%dT%H%M%SZ")

    def _format_datetime_local(self, dt: datetime) -> str:
        """Format datetime in local time."""
        return dt.strftime("%Y%m%dT%H%M%S")

    def _format_date(self, dt: datetime) -> str:
        """Format date only."""
        return dt.strftime("%Y%m%d")

    def generate(self, event: CalendarEvent) -> str:
        """
        Generate .ics content for a single event.

        Args:
            event: CalendarEvent to convert to ICS format

        Returns:
            String containing valid iCalendar content
        """
        lines = []

        # Calendar header
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append(f"PRODID:{self.prod_id}")
        lines.append("CALSCALE:GREGORIAN")
        lines.append("METHOD:REQUEST")

        # Timezone definition for Asia/Kolkata (GMT+5:30)
        lines.extend(self._get_timezone_definition())

        # Event start
        lines.append("BEGIN:VEVENT")

        # Unique identifier
        lines.append(f"UID:{event.uid}")

        # Timestamps
        lines.append(f"DTSTAMP:{self._format_datetime(event.created_at)}")
        lines.append(f"CREATED:{self._format_datetime(event.created_at)}")
        lines.append(f"LAST-MODIFIED:{self._format_datetime(datetime.now(timezone.utc))}")

        # Event times - using UTC for maximum compatibility
        lines.append(f"DTSTART:{self._format_datetime(event.start_time)}")
        lines.append(f"DTEND:{self._format_datetime(event.end_time)}")

        # Sequence number for updates
        lines.append(f"SEQUENCE:{event.sequence}")

        # Event details
        lines.append(f"SUMMARY:{self._escape_text(event.title)}")

        if event.description:
            lines.append(f"DESCRIPTION:{self._escape_text(event.description)}")

        if event.location:
            lines.append(f"LOCATION:{self._escape_text(event.location)}")

        # Status and priority
        lines.append("STATUS:CONFIRMED")
        lines.append("TRANSP:OPAQUE")

        # Organizer
        organizer = formataddr((event.organizer_name, event.organizer_email))
        organizer_escaped = organizer.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'ORGANIZER;CN="{event.organizer_name}":mailto:{event.organizer_email}')

        # Attendees
        for attendee in event.attendees:
            lines.append(f"ATTENDEE;ROLE=REQ-PARTICIPANT;RSVP=TRUE:mailto:{attendee}")

        # Classification
        lines.append("CLASS:PUBLIC")

        # Apple Calendar specific for better compatibility
        lines.append("X-APPLE-TRAVEL-ADVISORY-BEWARE;ACKNOWLEDGED=0:")

        # Event end
        lines.append("END:VEVENT")

        # Calendar end
        lines.append("END:VCALENDAR")

        # Fold lines and join
        folded_lines = [self._fold_line(line) for line in lines]
        return self.CRLF.join(folded_lines) + self.CRLF

    def _get_timezone_definition(self) -> list[str]:
        """
        Get VTIMEZONE block for Asia/Kolkata.

        Returns timezone definition compatible with major calendar apps.
        """
        # Asia/Kolkata uses IST (Indian Standard Time) - GMT+5:30 all year
        # No DST transitions
        return [
            "BEGIN:VTIMEZONE",
            "TZID:Asia/Kolkata",
            "X-LIC-LOCATION:Asia/Kolkata",
            "BEGIN:STANDARD",
            "DTSTART:19700101T000000",
            "TZOFFSETFROM:+0530",
            "TZOFFSETTO:+0530",
            "TZNAME:IST",
            "END:STANDARD",
            "END:VTIMEZONE",
        ]

    def generate_batch(self, events: list[CalendarEvent]) -> str:
        """
        Generate .ics content for multiple events in a single calendar.

        Args:
            events: List of CalendarEvent objects

        Returns:
            String containing valid iCalendar content with multiple events
        """
        if not events:
            raise ValueError("At least one event is required")

        lines = []

        # Calendar header
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append(f"PRODID:{self.prod_id}")
        lines.append("CALSCALE:GREGORIAN")
        lines.append("METHOD:PUBLISH")

        # Timezone definition
        lines.extend(self._get_timezone_definition())

        # Add each event
        for event in events:
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{event.uid}")
            lines.append(f"DTSTAMP:{self._format_datetime(event.created_at)}")
            lines.append(f"CREATED:{self._format_datetime(event.created_at)}")
            lines.append(f"LAST-MODIFIED:{self._format_datetime(datetime.now(timezone.utc))}")
            lines.append(f"DTSTART:{self._format_datetime(event.start_time)}")
            lines.append(f"DTEND:{self._format_datetime(event.end_time)}")
            lines.append(f"SEQUENCE:{event.sequence}")
            lines.append(f"SUMMARY:{self._escape_text(event.title)}")

            if event.description:
                lines.append(f"DESCRIPTION:{self._escape_text(event.description)}")

            if event.location:
                lines.append(f"LOCATION:{self._escape_text(event.location)}")

            lines.append("STATUS:CONFIRMED")
            lines.append("TRANSP:OPAQUE")
            lines.append(
                f'ORGANIZER;CN="{event.organizer_name}":mailto:{event.organizer_email}'
            )

            for attendee in event.attendees:
                lines.append(f"ATTENDEE;ROLE=REQ-PARTICIPANT:mailto:{attendee}")

            lines.append("CLASS:PUBLIC")
            lines.append("END:VEVENT")

        # Calendar end
        lines.append("END:VCALENDAR")

        # Fold lines and join
        folded_lines = [self._fold_line(line) for line in lines]
        return self.CRLF.join(folded_lines) + self.CRLF


def create_calendar_event(
    title: str,
    start_time: datetime,
    end_time: datetime,
    attendees: list[str],
    description: str,
    location: str = "",
    organizer_name: str = DEFAULT_ORGANIZER_NAME,
    organizer_email: str = DEFAULT_ORGANIZER_EMAIL,
) -> str:
    """
    Create an .ics calendar event string.

    Args:
        title: Event title/summary
        start_time: Event start datetime (naive assumed local, aware used as-is)
        end_time: Event end datetime
        attendees: List of attendee email addresses
        description: Event description
        location: Optional location string
        organizer_name: Name of the event organizer
        organizer_email: Email of the event organizer

    Returns:
        String containing valid iCalendar (.ics) content

    Raises:
        ValueError: If end_time is not after start_time

    Example:
        >>> from datetime import datetime
        >>> ics = create_calendar_event(
        ...     title="Team Meeting",
        ...     start_time=datetime(2024, 3, 15, 10, 0),
        ...     end_time=datetime(2024, 3, 15, 11, 0),
        ...     attendees=["alice@example.com", "bob@example.com"],
        ...     description="Weekly team sync",
        ...     location="Zoom"
        ... )
        >>> with open("meeting.ics", "w") as f:
        ...     f.write(ics)
    """
    # Handle naive datetimes - assume UTC if not timezone aware
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=__import__("datetime").timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=__import__("datetime").timezone.utc)

    # Convert to UTC for consistent output
    from datetime import timezone

    start_utc = start_time.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_time.astimezone(timezone.utc).replace(tzinfo=None)

    event = CalendarEvent(
        title=title,
        start_time=start_utc,
        end_time=end_utc,
        attendees=attendees,
        description=description,
        location=location,
        organizer_name=organizer_name,
        organizer_email=organizer_email,
    )

    generator = ICSGenerator()
    return generator.generate(event)


def create_calendar_from_meeting(
    meeting_data: dict[str, Any],
    organizer_name: str = DEFAULT_ORGANIZER_NAME,
    organizer_email: str = DEFAULT_ORGANIZER_EMAIL,
) -> list[str]:
    """
    Generate multiple .ics calendar events from meeting data dictionary.

    Supports extracting multiple events from a meeting transcript or analysis.
    Each extracted event becomes a separate .ics file content.

    Expected meeting_data structure:
    {
        "meeting_title": "Q1 Planning Session",
        "extracted_date": "2024-03-15",
        "events": [
            {
                "title": "Sprint Planning",
                "start_time": "2024-03-15T10:00:00",
                "end_time": "2024-03-15T11:30:00",
                "attendees": ["dev1@example.com", "pm@example.com"],
                "description": "Plan the next sprint",
                "location": "Conference Room A"
            },
            {
                "title": "Client Review",
                "start_time": "2024-03-15T14:00:00",
                "duration_minutes": 60,
                "attendees": ["client@example.com", "pm@example.com"],
                "description": "Review progress with client",
                "location": "https://zoom.us/j/123456"
            }
        ],
        "participants": ["alice@example.com", "bob@example.com"],
        "default_location": "Conference Room B"
    }

    Args:
        meeting_data: Dictionary containing meeting information and extracted events
        organizer_name: Name of the event organizer
        organizer_email: Email of the event organizer

    Returns:
        List of .ics content strings, one per event

    Example:
        >>> meeting_data = {
        ...     "events": [
        ...         {
        ...             "title": "Follow-up",
        ...             "start_time": "2024-03-15T10:00:00",
        ...             "end_time": "2024-03-15T11:00:00",
        ...             "attendees": ["team@example.com"],
        ...             "description": "Follow-up meeting"
        ...         }
        ...     ]
        ... }
        >>> ics_list = create_calendar_from_meeting(meeting_data)
        >>> for i, ics in enumerate(ics_list):
        ...     with open(f"event_{i}.ics", "w") as f:
        ...         f.write(ics)

    Raises:
        ValueError: If meeting_data doesn't contain events or has invalid structure
    """
    if not isinstance(meeting_data, dict):
        raise ValueError("meeting_data must be a dictionary")

    events_data = meeting_data.get("events", [])
    if not events_data:
        raise ValueError("meeting_data must contain 'events' list with at least one event")

    # Default attendees from meeting participants if available
    default_attendees = meeting_data.get("participants", [])
    default_location = meeting_data.get("default_location", "")

    ics_contents: list[str] = []
    generator = ICSGenerator()

    for event_data in events_data:
        if not isinstance(event_data, dict):
            raise ValueError(f"Each event must be a dictionary, got {type(event_data)}")

        # Parse start time
        start_time_str = event_data.get("start_time")
        if not start_time_str:
            raise ValueError("Each event must have a 'start_time'")
        start_time = _parse_datetime(start_time_str)

        # Parse end time or calculate from duration
        end_time_str = event_data.get("end_time")
        duration = event_data.get("duration_minutes")

        if end_time_str:
            end_time = _parse_datetime(end_time_str)
        elif duration:
            end_time = start_time + timedelta(minutes=duration)
        else:
            # Default to 1 hour if no end time or duration specified
            end_time = start_time + timedelta(hours=1)

        # Collect attendees (event specific + defaults)
        event_attendees = event_data.get("attendees", [])
        all_attendees = list(set(event_attendees + default_attendees))

        # Determine location (event specific with fallback to default)
        location = event_data.get("location", default_location)

        # Build description with context
        description = event_data.get("description", "")
        meeting_title = meeting_data.get("meeting_title", "")
        if meeting_title:
            description = f"From: {meeting_title}\\n\\n{description}"

        event = CalendarEvent(
            title=event_data.get("title", "Untitled Event"),
            start_time=start_time,
            end_time=end_time,
            attendees=all_attendees,
            description=description,
            location=location,
            organizer_name=organizer_name,
            organizer_email=organizer_email,
        )

        ics_content = generator.generate(event)
        ics_contents.append(ics_content)

    return ics_contents


def _parse_datetime(dt_str: str) -> datetime:
    """
    Parse datetime from various string formats.

    Supports:
    - ISO 8601: "2024-03-15T10:00:00"
    - With timezone: "2024-03-15T10:00:00+05:30"
    - Date only: "2024-03-15" (assumes 00:00:00)

    Args:
        dt_str: Datetime string to parse

    Returns:
        datetime object (naive, assumed UTC if timezone not specified)

    Raises:
        ValueError: If string cannot be parsed
    """
    from datetime import timezone

    dt_str = dt_str.strip()

    # Try ISO format with timezone
    formats_with_tz = ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z"]

    # Try ISO format without timezone
    formats_without_tz = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    # First try formats with timezone
    for fmt in formats_with_tz:
        try:
            # Handle the colon in timezone offset (2024-03-15T10:00:00+05:30)
            dt_normalized = dt_str
            if len(dt_normalized) > 6 and dt_normalized[-3] == ":" and (
                dt_normalized[-6] == "+" or dt_normalized[-6] == "-"
            ):
                dt_normalized = dt_normalized[:-3] + dt_normalized[-2:]
            return datetime.strptime(dt_normalized, fmt)
        except ValueError:
            continue

    # Then try without timezone (assume UTC)
    for fmt in formats_without_tz:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt
        except ValueError:
            continue

    raise ValueError(f"Cannot parse datetime string: {dt_str}")


def save_ics_to_file(
    ics_content: str, filepath: str | Path, filename: str | None = None
) -> Path:
    """
    Save .ics content to a file.

    Args:
        ics_content: The .ics content string
        filepath: Directory path or full file path
        filename: Optional filename (required if filepath is directory)

    Returns:
        Path object of the saved file

    Raises:
        ValueError: If filepath is directory and filename not provided

    Example:
        >>> path = save_ics_to_file(ics_content, "/tmp/calendar", "meeting.ics")
        >>> print(path)
        PosixPath('/tmp/calendar/meeting.ics')
    """
    filepath = Path(filepath)

    # Check if filepath is an existing directory OR if filename is provided
    # (implies filepath is intended as directory)
    if filename or (filepath.exists() and filepath.is_dir()):
        if not filename:
            raise ValueError("filename required when filepath is a directory")
        filepath = filepath / filename

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write content (text mode with proper line endings)
    filepath.write_text(ics_content, encoding="utf-8")

    return filepath


def generate_meeting_invite(
    meeting_title: str,
    proposed_slots: list[tuple[datetime, datetime]],
    attendees: list[str],
    description: str = "",
    location: str = "",
) -> list[str]:
    """
    Generate multiple .ics files for proposed meeting slots.
    Useful for sending multiple time options to attendees.

    Args:
        meeting_title: Base title for all invitations
        proposed_slots: List of (start_time, end_time) tuples
        attendees: List of attendee email addresses
        description: Event description
        location: Meeting location

    Returns:
        List of .ics content strings, one per proposed slot

    Example:
        >>> from datetime import datetime, timedelta
        >>> slots = [
        ...     (datetime(2024, 3, 15, 10, 0), datetime(2024, 3, 15, 11, 0)),
        ...     (datetime(2024, 3, 15, 14, 0), datetime(2024, 3, 15, 15, 0)),
        ... ]
        >>> ics_options = generate_meeting_invite(
        ...     "Team Sync",
        ...     slots,
        ...     ["team@example.com"],
        ...     description="Please choose one slot"
        ... )
    """
    ics_contents = []

    for idx, (start_time, end_time) in enumerate(proposed_slots, 1):
        title = f"{meeting_title} (Option {idx})"
        desc = f"{description}\n\n(Option {idx} of {len(proposed_slots)})"

        ics = create_calendar_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            description=desc,
            location=location,
        )
        ics_contents.append(ics)

    return ics_contents


# Export public API
__all__ = [
    "CalendarEvent",
    "ICSGenerator",
    "create_calendar_event",
    "create_calendar_from_meeting",
    "save_ics_to_file",
    "generate_meeting_invite",
    "DEFAULT_TIMEZONE",
    "DEFAULT_ORGANIZER_NAME",
    "DEFAULT_ORGANIZER_EMAIL",
]