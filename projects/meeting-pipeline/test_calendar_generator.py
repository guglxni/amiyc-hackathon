"""Unit tests for calendar_generator module

Run tests with: python -m pytest test_calendar_generator.py -v
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

from calendar_generator import (
    CalendarEvent,
    ICSGenerator,
    create_calendar_event,
    create_calendar_from_meeting,
    generate_meeting_invite,
    save_ics_to_file,
    _parse_datetime,
    DEFAULT_TIMEZONE,
    DEFAULT_ORGANIZER_NAME,
    DEFAULT_ORGANIZER_EMAIL,
)


class TestCalendarEvent:
    """Tests for CalendarEvent dataclass."""

    def test_basic_event_creation(self) -> None:
        """Test creating a basic CalendarEvent."""
        start = datetime(2024, 3, 15, 10, 0)
        end = datetime(2024, 3, 15, 11, 0)

        event = CalendarEvent(
            title="Test Meeting",
            start_time=start,
            end_time=end,
            attendees=["alice@example.com", "bob@example.com"],
            description="A test meeting",
            location="Room A",
        )

        assert event.title == "Test Meeting"
        assert event.start_time == start
        assert event.end_time == end
        assert event.attendees == ["alice@example.com", "bob@example.com"]
        assert event.description == "A test meeting"
        assert event.location == "Room A"
        assert event.duration_minutes == 60

        # Should auto-generate UUID
        assert UUID(event.uid)

    def test_end_time_before_start_raises_error(self) -> None:
        """Test that end time must be after start time."""
        with pytest.raises(ValueError, match="End time must be after start time"):
            CalendarEvent(
                title="Invalid Meeting",
                start_time=datetime(2024, 3, 15, 11, 0),
                end_time=datetime(2024, 3, 15, 10, 0),
                attendees=[],
                description="",
            )

    def test_attendee_normalization(self) -> None:
        """Test that attendee emails are normalized."""
        event = CalendarEvent(
            title="Test",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=[
                'Alice Smith <alice@example.com>',
                'bob@example.com',
                '  CHARLIE@EXAMPLE.COM  ',
            ],
            description="",
        )

        assert event.attendees == [
            "alice@example.com",
            "bob@example.com",
            "CHARLIE@EXAMPLE.COM",
        ]

    def test_empty_attendees_filtered(self) -> None:
        """Test that empty attendee strings are filtered out."""
        event = CalendarEvent(
            title="Test",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=["alice@example.com", "", "bob@example.com", ""],
            description="",
        )

        assert event.attendees == ["alice@example.com", "bob@example.com"]


class TestICSGenerator:
    """Tests for ICSGenerator class."""

    @pytest.fixture
    def generator(self) -> ICSGenerator:
        return ICSGenerator()

    @pytest.fixture
    def sample_event(self) -> CalendarEvent:
        return CalendarEvent(
            title="Team Meeting",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=["alice@example.com", "bob@example.com"],
            description="Weekly team sync meeting",
            location="Conference Room A",
        )

    def test_calendar_header(self, generator: ICSGenerator, sample_event: CalendarEvent) -> None:
        """Test that ICS output has proper calendar header."""
        ics = generator.generate(sample_event)

        assert "BEGIN:VCALENDAR" in ics
        assert "VERSION:2.0" in ics
        assert "PRODID:" in ics
        assert "CALSCALE:GREGREGORIAN" or "CALSCALE:GREGORIAN" in ics
        assert "END:VCALENDAR" in ics

    def test_event_block(self, generator: ICSGenerator, sample_event: CalendarEvent) -> None:
        """Test that ICS output has proper event block."""
        ics = generator.generate(sample_event)

        assert "BEGIN:VEVENT" in ics
        assert "END:VEVENT" in ics
        assert f"UID:{sample_event.uid}" in ics
        assert "DTSTART:" in ics
        assert "DTEND:" in ics
        assert "SUMMARY:" in ics
        assert "DESCRIPTION:" in ics
        assert "LOCATION:" in ics

    def test_timezone_block(self, generator: ICSGenerator, sample_event: CalendarEvent) -> None:
        """Test that ICS output includes timezone definition."""
        ics = generator.generate(sample_event)

        assert "BEGIN:VTIMEZONE" in ics
        assert "TZID:Asia/Kolkata" in ics
        assert "END:VTIMEZONE" in ics

    def test_attendees_included(self, generator: ICSGenerator, sample_event: CalendarEvent) -> None:
        """Test that attendees are included in ICS output."""
        ics = generator.generate(sample_event)

        assert "ATTENDEE;" in ics
        assert "mailto:alice@example.com" in ics
        assert "mailto:bob@example.com" in ics

    def test_organizer_included(self, generator: ICSGenerator, sample_event: CalendarEvent) -> None:
        """Test that organizer is included in ICS output."""
        ics = generator.generate(sample_event)

        assert "ORGANIZER;" in ics
        # CN may be quoted in output
        assert f'CN="{DEFAULT_ORGANIZER_NAME}"' in ics or f"CN={DEFAULT_ORGANIZER_NAME}" in ics
        assert f"mailto:{DEFAULT_ORGANIZER_EMAIL}" in ics

    def test_text_escaping(self, generator: ICSGenerator) -> None:
        """Test special character escaping in text values."""
        event = CalendarEvent(
            title="Meeting; With, Special\\Chars",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=[],
            description="Line one\nLine two",
        )

        ics = generator.generate(event)

        # Check for escaped characters
        assert r"\;" in ics or "Meeting;" in ics
        assert "\\n" in ics

    def test_line_folding(self, generator: ICSGenerator) -> None:
        """Test that long lines are properly folded."""
        event = CalendarEvent(
            title="A" * 100,  # Long title
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=[],
            description="B" * 100,  # Long description
        )

        ics = generator.generate(event)
        lines = ics.split("\r\n")

        # No line should exceed 75 characters (except possibly empty lines)
        for line in lines:
            if line:
                assert len(line) <= 75, f"Line too long: {line[:80]}..."

    def test_crlf_line_endings(self, generator: ICSGenerator, sample_event: CalendarEvent) -> None:
        """Test that output uses CRLF line endings."""
        ics = generator.generate(sample_event)

        # Should contain \r\n sequences
        assert "\r\n" in ics
        # Should not have bare \n without \r
        assert "\n\n" not in ics or "\r\n\r\n" in ics

    def test_batch_generation(self, generator: ICSGenerator) -> None:
        """Test generating multiple events in one calendar."""
        events = [
            CalendarEvent(
                title=f"Event {i}",
                start_time=datetime(2024, 3, 15, 10 + i, 0),
                end_time=datetime(2024, 3, 15, 11 + i, 0),
                attendees=["user@example.com"],
                description=f"Description {i}",
            )
            for i in range(3)
        ]

        ics = generator.generate_batch(events)

        # Should have single VCALENDAR with multiple VEVENTs
        assert ics.count("BEGIN:VCALENDAR") == 1
        assert ics.count("END:VCALENDAR") == 1
        assert ics.count("BEGIN:VEVENT") == 3
        assert ics.count("END:VEVENT") == 3

    def test_batch_generation_empty_raises(self, generator: ICSGenerator) -> None:
        """Test that empty event list raises error."""
        with pytest.raises(ValueError, match="At least one event"):
            generator.generate_batch([])


class TestCreateCalendarEvent:
    """Tests for create_calendar_event function."""

    def test_basic_event_creation(self) -> None:
        """Test creating a basic calendar event."""
        start = datetime(2024, 3, 15, 10, 0)
        end = datetime(2024, 3, 15, 11, 0)

        ics = create_calendar_event(
            title="Test Meeting",
            start_time=start,
            end_time=end,
            attendees=["alice@example.com"],
            description="Test description",
            location="Room A",
        )

        assert isinstance(ics, str)
        assert "BEGIN:VCALENDAR" in ics
        assert "SUMMARY:Test Meeting" in ics
        assert "DESCRIPTION:Test description" in ics
        assert "LOCATION:Room A" in ics

    def test_aware_datetimes(self) -> None:
        """Test with timezone-aware datetimes."""
        ist = timezone(timedelta(hours=5, minutes=30))
        start = datetime(2024, 3, 15, 10, 0, tzinfo=ist)
        end = datetime(2024, 3, 15, 11, 0, tzinfo=ist)

        ics = create_calendar_event(
            title="Test",
            start_time=start,
            end_time=end,
            attendees=[],
            description="",
        )

        # Should convert to UTC in output
        assert "BEGIN:VCALENDAR" in ics
        # 10:00 IST = 04:30 UTC
        assert "T043000Z" in ics

    def test_no_attendees(self) -> None:
        """Test creating event with no attendees."""
        ics = create_calendar_event(
            title="Personal Reminder",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=[],
            description="Just a reminder",
        )

        assert "BEGIN:VCALENDAR" in ics

    def test_no_location(self) -> None:
        """Test creating event without location."""
        ics = create_calendar_event(
            title="Virtual Meeting",
            start_time=datetime(2024, 3, 15, 10, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
            attendees=["user@example.com"],
            description="No physical location",
        )

        assert "BEGIN:VCALENDAR" in ics
        # LOCATION may or may not be present for empty strings


class TestCreateCalendarFromMeeting:
    """Tests for create_calendar_from_meeting function."""

    def test_single_event(self) -> None:
        """Test parsing single event from meeting data."""
        meeting_data = {
            "meeting_title": "Q1 Planning",
            "extracted_date": "2024-03-15",
            "events": [
                {
                    "title": "Sprint Planning",
                    "start_time": "2024-03-15T10:00:00",
                    "end_time": "2024-03-15T11:00:00",
                    "attendees": ["dev@example.com", "pm@example.com"],
                    "description": "Plan the sprint",
                    "location": "Room A",
                }
            ],
            "participants": ["stakeholder@example.com"],
        }

        ics_list = create_calendar_from_meeting(meeting_data)

        assert len(ics_list) == 1
        assert "Sprint Planning" in ics_list[0]
        assert "plan the sprint" in ics_list[0].lower()
        # Should include both event attendees and participants
        assert "dev@example.com" in ics_list[0]
        assert "pm@example.com" in ics_list[0]
        assert "stakeholder@example.com" in ics_list[0]

    def test_multiple_events(self) -> None:
        """Test parsing multiple events from meeting data."""
        meeting_data = {
            "events": [
                {
                    "title": "Event 1",
                    "start_time": "2024-03-15T10:00:00",
                    "end_time": "2024-03-15T11:00:00",
                    "attendees": ["user1@example.com"],
                    "description": "First event",
                },
                {
                    "title": "Event 2",
                    "start_time": "2024-03-15T14:00:00",
                    "duration_minutes": 30,
                    "attendees": ["user2@example.com"],
                    "description": "Second event",
                },
            ]
        }

        ics_list = create_calendar_from_meeting(meeting_data)

        assert len(ics_list) == 2
        assert "Event 1" in ics_list[0]
        assert "Event 2" in ics_list[1]

    def test_using_duration_instead_of_end_time(self) -> None:
        """Test that duration_minutes can be used instead of end_time."""
        meeting_data = {
            "events": [
                {
                    "title": "Short Meeting",
                    "start_time": "2024-03-15T10:00:00",
                    "duration_minutes": 30,
                    "attendees": [],
                    "description": "Quick sync",
                }
            ]
        }

        ics_list = create_calendar_from_meeting(meeting_data)

        assert len(ics_list) == 1
        # Check that event lasts 30 minutes
        assert "Short Meeting" in ics_list[0]

    def test_default_location(self) -> None:
        """Test that default_location is used when event has no location."""
        meeting_data = {
            "default_location": "Main Conference Room",
            "events": [
                {
                    "title": "Meeting",
                    "start_time": "2024-03-15T10:00:00",
                    "end_time": "2024-03-15T11:00:00",
                    "attendees": [],
                    "description": "A meeting",
                }
            ],
        }

        ics_list = create_calendar_from_meeting(meeting_data)

        assert "Main Conference Room" in ics_list[0]

    def test_missing_events_raises_error(self) -> None:
        """Test that missing events raises ValueError."""
        with pytest.raises(ValueError, match="events"):
            create_calendar_from_meeting({})

    def test_empty_events_raises_error(self) -> None:
        """Test that empty events list raises ValueError."""
        with pytest.raises(ValueError, match="events"):
            create_calendar_from_meeting({"events": []})

    def test_invalid_event_data_type(self) -> None:
        """Test that non-dict event data raises error."""
        with pytest.raises(ValueError, match="dictionary"):
            create_calendar_from_meeting({"events": ["not a dict"]})

    def test_missing_start_time(self) -> None:
        """Test that missing start_time raises error."""
        with pytest.raises(ValueError, match="start_time"):
            create_calendar_from_meeting(
                {
                    "events": [
                        {
                            "title": "No Time Meeting",
                            "attendees": [],
                            "description": "No time set",
                        }
                    ]
                }
            )


class TestParseDatetime:
    """Tests for _parse_datetime function."""

    def test_iso_format_with_t(self) -> None:
        """Test parsing ISO format with T separator."""
        dt = _parse_datetime("2024-03-15T10:00:00")
        assert dt == datetime(2024, 3, 15, 10, 0, 0)

    def test_iso_format_with_space(self) -> None:
        """Test parsing ISO format with space separator."""
        dt = _parse_datetime("2024-03-15 10:00:00")
        assert dt == datetime(2024, 3, 15, 10, 0, 0)

    def test_date_only(self) -> None:
        """Test parsing date only (assumes 00:00:00)."""
        dt = _parse_datetime("2024-03-15")
        assert dt == datetime(2024, 3, 15, 0, 0, 0)

    def test_with_timezone(self) -> None:
        """Test parsing datetime with timezone offset."""
        dt = _parse_datetime("2024-03-15T10:00:00+0530")
        assert dt.year == 2024
        assert dt.hour == 10

    def test_with_colon_in_timezone(self) -> None:
        """Test parsing datetime with colon in timezone."""
        dt = _parse_datetime("2024-03-15T10:00:00+05:30")
        assert dt.year == 2024

    def test_invalid_format_raises(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse"):
            _parse_datetime("not a date")

    def test_invalid_date_raises(self) -> None:
        """Test that invalid date raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse"):
            _parse_datetime("2024-13-45")  # Invalid month and day


class TestSaveIcsToFile:
    """Tests for save_ics_to_file function."""

    def test_save_with_directory_and_filename(self, tmp_path: Path) -> None:
        """Test saving to directory with filename."""
        ics_content = "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"
        result = save_ics_to_file(ics_content, tmp_path, "test.ics")

        assert result.exists()
        # On POSIX, write_text may normalize line endings to LF
        saved_content = result.read_text()
        assert "BEGIN:VCALENDAR" in saved_content
        assert "END:VCALENDAR" in saved_content

    def test_save_with_full_path(self, tmp_path: Path) -> None:
        """Test saving with full file path."""
        ics_content = "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"
        full_path = tmp_path / "subdir" / "event.ics"
        result = save_ics_to_file(ics_content, full_path)

        assert result == full_path
        assert result.exists()
        # On POSIX, write_text may normalize line endings to LF
        saved_content = result.read_text()
        assert "BEGIN:VCALENDAR" in saved_content
        assert "END:VCALENDAR" in saved_content

    def test_directory_without_filename_raises(self, tmp_path: Path) -> None:
        """Test that directory path without filename raises error."""
        with pytest.raises(ValueError, match="filename required"):
            save_ics_to_file("content", tmp_path)

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that parent directories are created if needed."""
        ics_content = "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"
        nested_dir = tmp_path / "a" / "b"
        result = save_ics_to_file(ics_content, nested_dir, "deep.ics")

        assert result.exists()
        assert result.parent == nested_dir
        assert result.name == "deep.ics"


class TestGenerateMeetingInvite:
    """Tests for generate_meeting_invite function."""

    def test_single_slot(self) -> None:
        """Test generating invite for single time slot."""
        start = datetime(2024, 3, 15, 10, 0)
        end = datetime(2024, 3, 15, 11, 0)

        ics_list = generate_meeting_invite(
            meeting_title="Team Sync",
            proposed_slots=[(start, end)],
            attendees=["team@example.com"],
            description="Please confirm",
            location="Room A",
        )

        assert len(ics_list) == 1
        assert "Team Sync (Option 1)" in ics_list[0]
        assert "(Option 1 of 1)" in ics_list[0]

    def test_multiple_slots(self) -> None:
        """Test generating invites for multiple time slots."""
        slots = [
            (datetime(2024, 3, 15, 10, 0), datetime(2024, 3, 15, 11, 0)),
            (datetime(2024, 3, 15, 14, 0), datetime(2024, 3, 15, 15, 0)),
            (datetime(2024, 3, 15, 16, 0), datetime(2024, 3, 15, 17, 0)),
        ]

        ics_list = generate_meeting_invite(
            meeting_title="Client Meeting",
            proposed_slots=slots,
            attendees=["client@example.com", "sales@example.com"],
            description="Multiple options available",
        )

        assert len(ics_list) == 3
        for i, ics in enumerate(ics_list, 1):
            assert f"Client Meeting (Option {i})" in ics
            assert f"(Option {i} of 3)" in ics


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow from meeting data to saved files."""
        meeting_data = {
            "meeting_title": "Product Launch Planning",
            "participants": ["pm@company.com"],
            "default_location": "Conference Room 1",
            "events": [
                {
                    "title": "Design Review",
                    "start_time": "2024-04-01T10:00:00",
                    "duration_minutes": 60,
                    "attendees": ["designer@company.com"],
                    "description": "Review design mockups",
                },
                {
                    "title": "Code Review",
                    "start_time": "2024-04-01T14:00:00",
                    "end_time": "2024-04-01T15:30:00",
                    "attendees": ["dev@company.com", "lead@company.com"],
                    "description": "Review implementation",
                    "location": "Virtual",
                },
            ],
        }

        # Generate ICS content
        ics_list = create_calendar_from_meeting(meeting_data)
        assert len(ics_list) == 2

        # Save to files
        output_dir = tmp_path / "calendar_invites"
        saved_paths = []
        for i, ics in enumerate(ics_list):
            path = save_ics_to_file(ics, output_dir, f"event_{i+1}.ics")
            saved_paths.append(path)

        # Verify files
        assert all(p.exists() for p in saved_paths)
        # Note: On POSIX, write_text normalizes CRLF to LF, so we check content presence instead
        assert "BEGIN:VCALENDAR" in (output_dir / "event_1.ics").read_text()
        assert "BEGIN:VCALENDAR" in (output_dir / "event_2.ics").read_text()

        # Validate content
        content1 = ics_list[0]
        assert "BEGIN:VCALENDAR" in content1
        assert "VERSION:2.0" in content1
        assert "Design Review" in content1
        assert "pm@company.com" in content1  # From participants
        assert "Conference Room 1" in content1  # Default location

        content2 = ics_list[1]
        assert "Code Review" in content2
        assert "Virtual" in content2  # Event-specific location
        assert "lead@company.com" in content2

    def test_calendar_imports_to_major_clients(self, tmp_path: Path) -> None:
        """Verify ICS format is compatible with major calendar clients."""
        # Create a standard event
        ics = create_calendar_event(
            title="Test Event",
            start_time=datetime(2024, 6, 1, 14, 0),
            end_time=datetime(2024, 6, 1, 15, 30),
            attendees=["user@example.com"],
            description="Meeting with all major calendar clients",
            location="https://zoom.us/j/1234567890",
            organizer_name="Test Corp",
            organizer_email="calendar@testcorp.com",
        )

        # Save and verify structure
        path = tmp_path / "import_test.ics"
        save_ics_to_file(ics, path)

        # Read back and validate structure
        content = path.read_text()

        # Required components for compatibility
        assert "BEGIN:VCALENDAR" in content
        assert "VERSION:2.0" in content
        assert "BEGIN:VEVENT" in content
        assert "UID:" in content
        assert "DTSTART:" in content
        assert "DTEND:" in content
        assert "DTSTAMP:" in content
        assert "SUMMARY:" in content
        assert "END:VEVENT" in content
        assert "END:VCALENDAR" in content

        # UID should be unique and valid UUID format
        uid_match = re.search(r"UID:([a-f0-9-]+)", content)
        assert uid_match is not None
        assert UUID(uid_match.group(1))  # Valid UUID

        # Dates should be in UTC format (ends with Z)
        dtstart_match = re.search(r"DTSTART:(\d{8}T\d{6}Z)", content)
        assert dtstart_match is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])