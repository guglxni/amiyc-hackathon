"""
Unit tests for the Meeting Pipeline automation skill.

Tests cover:
- MeetingParser: parsing various meeting note formats
- CalendarGenerator: ICS file generation
- TaskListGenerator: Markdown task list generation
- FolderGenerator: Project folder structure creation
- EmailDraftGenerator: Email draft generation
- MeetingPipeline: End-to-end integration
"""

from __future__ import annotations

import unittest
import tempfile
from datetime import datetime
from pathlib import Path

from meeting_pipeline import (
    # Exceptions
    MeetingPipelineError,
    MeetingParseError,
    ValidationError,
    CalendarGenerationError,
    FileSystemError,
    # Models
    Attendee,
    ActionItem,
    Decision,
    Meeting,
    Priority,
    # Generators
    MeetingParser,
    CalendarGenerator,
    TaskListGenerator,
    FolderGenerator,
    EmailDraftGenerator,
    MeetingPipeline,
)


# =============================================================================
# Test Fixtures
# =============================================================================

SAMPLE_MEETING_NOTES = """
Meeting: Q1 Planning
Date: Feb 17, 2026
Attendees: Alice, Bob, Charlie

Discussion:
- Need to finish API integration by Feb 20
- Bob will prepare documentation
- Alice to schedule client meeting next week
- Budget approved for $5000

Action Items:
1. [ ] API integration - Bob - Due Feb 20
2. [ ] Documentation - Bob - Due Feb 22
3. [ ] Schedule client meeting - Alice - Due Feb 18

Decisions:
- Budget approved for cloud infrastructure
- Moving to bi-weekly sprints
"""

MINIMAL_MEETING = """
Meeting: Standup
Date: 2026-02-17
Attendees: Alice

Discussion:
- Work in progress

Action Items:
1. [ ] Complete tasks
"""

COMPLEX_MEETING = """
Meeting: Product Strategy Review - Q1 2026
Date: March 15, 2026
Attendees: Sarah Johnson, Michael Chen, Emily Rodriguez, David Kim

Discussion:
- Sarah presented the competitive analysis report
- Michael outlined technical constraints for new features
- Emily shared user research findings from Q4
- David discussed budget allocation for the upcoming quarter
- Team discussed timeline for mobile app redesign
- Reviewed customer feedback from recent survey
- Michael will research third-party integrations by end of month
- Sarah to present updated roadmap by March 20

Action Items:
1. [ ] Complete competitive analysis - Sarah - Due Mar 18
2. [ ] Draft technical specification - Michael - Due Mar 22
3. [ ] Update user journey maps - Emily - Due Mar 25
4. [ ] Prepare budget proposal - David - Due Mar 20
5. [x] Send meeting invites for next review - Sarah - Due Mar 15

Decisions:
- Approved $25,000 budget for Q1 initiatives
- Decided to prioritize mobile experience over desktop
- Agreed on weekly check-ins for critical milestones
- Selected React Native for cross-platform development
"""


# =============================================================================
# MeetingParser Tests
# =============================================================================

class TestMeetingParser(unittest.TestCase):
    """Tests for the MeetingParser class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.parser = MeetingParser(default_year=2026)
    
    def test_parse_basic_meeting(self) -> None:
        """Test parsing a basic meeting note."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        self.assertEqual(meeting.title, "Q1 Planning")
        self.assertEqual(meeting.date.month, 2)
        self.assertEqual(meeting.date.day, 17)
        self.assertEqual(meeting.date.year, 2026)
    
    def test_parse_attendees(self) -> None:
        """Test attendee extraction."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        self.assertEqual(len(meeting.attendees), 3)
        attendee_names = [a.name for a in meeting.attendees]
        self.assertIn("Alice", attendee_names)
        self.assertIn("Bob", attendee_names)
        self.assertIn("Charlie", attendee_names)
    
    def test_parse_discussion_points(self) -> None:
        """Test discussion point extraction."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        self.assertGreaterEqual(len(meeting.discussion_points), 4)
        # Check that specific points were captured
        point_texts = [p.lower() for p in meeting.discussion_points]
        self.assertTrue(
            any("api integration" in p for p in point_texts)
        )
    
    def test_parse_action_items(self) -> None:
        """Test action item extraction."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        self.assertGreaterEqual(len(meeting.action_items), 3)
        
        # Check for specific action items
        descriptions = [i.description.lower() for i in meeting.action_items]
        self.assertTrue(any("api integration" in d for d in descriptions))
        self.assertTrue(any("documentation" in d for d in descriptions))
    
    def test_parse_action_item_assignees(self) -> None:
        """Test action item assignee extraction."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        bob_items = [i for i in meeting.action_items if i.assignee == "Bob"]
        alice_items = [i for i in meeting.action_items if i.assignee == "Alice"]
        
        self.assertGreaterEqual(len(bob_items), 2)
        self.assertGreaterEqual(len(alice_items), 1)
    
    def test_parse_action_item_due_dates(self) -> None:
        """Test due date extraction from action items."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        items_with_dates = [i for i in meeting.action_items if i.due_date]
        self.assertGreaterEqual(len(items_with_dates), 3)
        
        # Check specific due date
        api_item = next(
            (i for i in meeting.action_items if "API integration" in i.description),
            None
        )
        self.assertIsNotNone(api_item)
        self.assertIsNotNone(api_item.due_date)
        self.assertEqual(api_item.due_date.day, 20)
        self.assertEqual(api_item.due_date.month, 2)
    
    def test_parse_decisions(self) -> None:
        """Test decision extraction."""
        meeting = self.parser.parse(SAMPLE_MEETING_NOTES)
        
        self.assertGreaterEqual(len(meeting.decisions), 1)
        decision_texts = [d.description.lower() for d in meeting.decisions]
        self.assertTrue(any("budget" in t for t in decision_texts))
    
    def test_parse_complex_meeting(self) -> None:
        """Test parsing a complex meeting with many elements."""
        meeting = self.parser.parse(COMPLEX_MEETING)
        
        self.assertEqual(meeting.title, "Product Strategy Review - Q1 2026")
        self.assertEqual(len(meeting.attendees), 4)
        self.assertGreaterEqual(len(meeting.action_items), 5)
        self.assertGreaterEqual(len(meeting.decisions), 3)
    
    def test_parse_empty_notes_raises_error(self) -> None:
        """Test that empty notes raises an error."""
        with self.assertRaises(MeetingParseError):
            self.parser.parse("")
        
        with self.assertRaises(MeetingParseError):
            self.parser.parse("   \n\n   ")
    
    def test_parse_missing_title(self) -> None:
        """Test parsing notes without explicit title."""
        notes = "Date: Feb 17, 2026\nAttendees: Alice"
        meeting = self.parser.parse(notes)
        
        # Should use first line as title
        self.assertIsNotNone(meeting.title)
    
    def test_parse_various_date_formats(self) -> None:
        """Test parsing various date formats."""
        formats = [
            ("Feb 17, 2026", 2, 17, 2026),
            ("February 17, 2026", 2, 17, 2026),
            ("2026-02-17", 2, 17, 2026),
            ("17 Feb 2026", 2, 17, 2026),
            ("02/17/2026", 2, 17, 2026),
        ]
        
        for date_str, month, day, year in formats:
            notes = f"Meeting: Test\nDate: {date_str}\nAttendees: Alice"
            meeting = self.parser.parse(notes)
            self.assertEqual(meeting.date.month, month, f"Failed for: {date_str}")
            self.assertEqual(meeting.date.day, day, f"Failed for: {date_str}")
            self.assertEqual(meeting.date.year, year, f"Failed for: {date_str}")


# =============================================================================
# Data Model Tests
# =============================================================================

class TestDataModels(unittest.TestCase):
    """Tests for data model validation."""
    
    def test_attendee_empty_name_raises(self) -> None:
        """Test that empty attendee name raises ValidationError."""
        with self.assertRaises(ValidationError):
            Attendee(name="")
        
        with self.assertRaises(ValidationError):
            Attendee(name="   ")
    
    def test_attendee_valid_creation(self) -> None:
        """Test valid attendee creation."""
        attendee = Attendee(name="Alice", email="alice@example.com")
        self.assertEqual(attendee.name, "Alice")
        self.assertEqual(attendee.email, "alice@example.com")
    
    def test_action_item_empty_description_raises(self) -> None:
        """Test that empty action item description raises ValidationError."""
        with self.assertRaises(ValidationError):
            ActionItem(description="")
        
        with self.assertRaises(ValidationError):
            ActionItem(description="   ")
    
    def test_action_item_default_priority(self) -> None:
        """Test action item default priority is MEDIUM."""
        item = ActionItem(description="Test task")
        self.assertEqual(item.priority, Priority.MEDIUM)
        self.assertFalse(item.completed)
    
    def test_decision_empty_description_raises(self) -> None:
        """Test that empty decision description raises ValidationError."""
        with self.assertRaises(ValidationError):
            Decision(description="")
    
    def test_meeting_empty_title_raises(self) -> None:
        """Test that empty meeting title raises ValidationError."""
        with self.assertRaises(ValidationError):
            Meeting(title="", date=datetime.now())


# =============================================================================
# CalendarGenerator Tests
# =============================================================================

class TestCalendarGenerator(unittest.TestCase):
    """Tests for the CalendarGenerator class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.generator = CalendarGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self) -> None:
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_ics_file(self) -> None:
        """Test ICS file generation."""
        meeting = Meeting(
            title="Test Meeting",
            date=datetime(2026, 2, 17, 10, 0),
            attendees=[Attendee(name="Alice")],
            action_items=[ActionItem(description="Test task")]
        )
        
        output_path = Path(self.temp_dir) / "test.ics"
        result_path = self.generator.generate(meeting, output_path)
        
        self.assertTrue(result_path.exists())
        content = result_path.read_text()
        
        # Check ICS structure
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("END:VCALENDAR", content)
        self.assertIn("BEGIN:VEVENT", content)
        self.assertIn("END:VEVENT", content)
        self.assertIn("Test Meeting", content)
    
    def test_ics_contains_action_items(self) -> None:
        """Test that action items are included in ICS description."""
        meeting = Meeting(
            title="Test Meeting",
            date=datetime(2026, 2, 17),
            action_items=[
                ActionItem(description="Task 1", assignee="Bob"),
                ActionItem(description="Task 2", completed=True)
            ]
        )
        
        output_path = Path(self.temp_dir) / "test.ics"
        self.generator.generate(meeting, output_path)
        content = output_path.read_text()
        
        self.assertIn("Task 1", content)
        self.assertIn("Task 2", content)
        self.assertIn("[ ]", content)
        self.assertIn("[x]", content)
    
    def test_ics_attendees(self) -> None:
        """Test that attendees are included in ICS."""
        meeting = Meeting(
            title="Test Meeting",
            date=datetime(2026, 2, 17),
            attendees=[Attendee(name="Alice"), Attendee(name="Bob")]
        )
        
        output_path = Path(self.temp_dir) / "test.ics"
        self.generator.generate(meeting, output_path)
        content = output_path.read_text()
        
        self.assertIn("Alice", content)
        self.assertIn("Bob", content)
    
    def test_generate_with_none_meeting_raises(self) -> None:
        """Test that None meeting raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.generator.generate(None, Path(self.temp_dir) / "test.ics")


# =============================================================================
# TaskListGenerator Tests
# =============================================================================

class TestTaskListGenerator(unittest.TestCase):
    """Tests for the TaskListGenerator class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.generator = TaskListGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self) -> None:
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_markdown_file(self) -> None:
        """Test Markdown task list generation."""
        meeting = Meeting(
            title="Test Meeting",
            date=datetime(2026, 2, 17),
            attendees=[Attendee(name="Alice")],
            discussion_points=["Point 1", "Point 2"],
            action_items=[
                ActionItem(description="Task 1", assignee="Bob", due_date=datetime(2026, 2, 20)),
                ActionItem(description="Task 2", completed=True)
            ],
            decisions=[Decision(description="Decision 1")]
        )
        
        output_path = Path(self.temp_dir) / "tasks.md"
        result_path = self.generator.generate(meeting, output_path)
        
        self.assertTrue(result_path.exists())
        content = result_path.read_text()
        
        # Check structure
        self.assertIn("# Test Meeting", content)
        self.assertIn("**Date:** February 17, 2026", content)
        self.assertIn("## Discussion Points", content)
        self.assertIn("## Action Items", content)
        self.assertIn("## Decisions", content)
        self.assertIn("## Summary", content)
        
        # Check content
        self.assertIn("Point 1", content)
        self.assertIn("Task 1", content)
        self.assertIn("Bob", content)
        self.assertIn("Due: Feb 20", content)
        self.assertIn("Decision 1", content)
    
    def test_group_by_assignee(self) -> None:
        """Test that tasks are grouped by assignee."""
        meeting = Meeting(
            title="Test Meeting",
            date=datetime(2026, 2, 17),
            action_items=[
                ActionItem(description="Task 1", assignee="Alice"),
                ActionItem(description="Task 2", assignee="Bob"),
                ActionItem(description="Task 3", assignee="Alice"),
            ]
        )
        
        output_path = Path(self.temp_dir) / "tasks.md"
        self.generator.generate(meeting, output_path)
        content = output_path.read_text()
        
        self.assertIn("### Alice", content)
        self.assertIn("### Bob", content)
    
    def test_summary_section(self) -> None:
        """Test that summary section contains correct counts."""
        meeting = Meeting(
            title="Test Meeting",
            date=datetime(2026, 2, 17),