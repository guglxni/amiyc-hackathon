"""
Meeting to Project Pipeline Automation Skill.

Transforms meeting notes into actionable project artifacts including
calendar events, task lists, folder structures, and follow-up emails.
"""

from __future__ import annotations

import re
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from enum import Enum


# =============================================================================
# Exceptions
# =============================================================================

class MeetingPipelineError(Exception):
    """Base exception for meeting pipeline errors."""
    pass


class MeetingParseError(MeetingPipelineError):
    """Raised when meeting notes cannot be parsed."""
    pass


class ValidationError(MeetingPipelineError):
    """Raised when input validation fails."""
    pass


class CalendarGenerationError(MeetingPipelineError):
    """Raised when calendar file generation fails."""
    pass


class FileSystemError(MeetingPipelineError):
    """Raised when file system operations fail."""
    pass


# =============================================================================
# Data Models
# =============================================================================

class Priority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Attendee:
    """Represents a meeting attendee."""
    name: str
    email: Optional[str] = None
    
    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Attendee name cannot be empty")


@dataclass(frozen=True)
class ActionItem:
    """Represents an action item extracted from meeting notes."""
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    
    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValidationError("Action item description cannot be empty")


@dataclass(frozen=True)
class Decision:
    """Represents a decision made during the meeting."""
    description: str
    context: Optional[str] = None
    
    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValidationError("Decision description cannot be empty")


@dataclass
class Meeting:
    """Represents a parsed meeting with all extracted information."""
    title: str
    date: datetime
    attendees: list[Attendee] = field(default_factory=list)
    discussion_points: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    raw_notes: str = ""
    
    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValidationError("Meeting title cannot be empty")


@dataclass
class PipelineOutput:
    """Container for all pipeline-generated artifacts."""
    meeting: Meeting
    calendar_path: Optional[Path] = None
    task_list_path: Optional[Path] = None
    folder_path: Optional[Path] = None
    email_drafts: list[str] = field(default_factory=list)


# =============================================================================
# Parser
# =============================================================================

class MeetingParser:
    """Parses meeting notes text into structured Meeting objects."""
    
    # Regex patterns for extraction
    MEETING_TITLE_PATTERN = re.compile(r"^[Mm]eeting:\s*(.+)$", re.MULTILINE)
    DATE_PATTERN = re.compile(r"^[Dd]ate:\s*(.+)$", re.MULTILINE)
    ATTENDEES_PATTERN = re.compile(r"^[Aa]ttendees?:\s*(.+)$", re.MULTILINE)
    ACTION_ITEM_PATTERN = re.compile(
        r"^\s*(?:\d+\.\s*\[([ xX])\]\s*|[-*]\s*\[([ xX])\]\s*|[-*]\s*)?"
        r"(.+?)(?:\s*[-–]\s*(\w+))?(?:\s*[-–]\s*[Dd]ue\s*(.+?))?$",
        re.MULTILINE
    )
    
    def __init__(self, default_year: Optional[int] = None) -> None:
        self.default_year = default_year or datetime.now().year
    
    def parse(self, notes: str) -> Meeting:
        """Parse meeting notes text into a Meeting object."""
        if not notes or not notes.strip():
            raise MeetingParseError("Meeting notes cannot be empty")
        
        meeting = Meeting(
            title=self._extract_title(notes),
            date=self._extract_date(notes),
            attendees=self._extract_attendees(notes),
            discussion_points=self._extract_discussion(notes),
            action_items=self._extract_action_items(notes),
            decisions=self._extract_decisions(notes),
            raw_notes=notes
        )
        
        return meeting
    
    def _extract_title(self, notes: str) -> str:
        """Extract meeting title from notes."""
        match = self.MEETING_TITLE_PATTERN.search(notes)
        if match:
            return match.group(1).strip()
        
        # Fallback: use first line
        first_line = notes.strip().split("\n")[0]
        return first_line[:50] if first_line else "Untitled Meeting"
    
    def _extract_date(self, notes: str) -> datetime:
        """Extract meeting date from notes."""
        match = self.DATE_PATTERN.search(notes)
        if match:
            date_str = match.group(1).strip()
            return self._parse_date(date_str)
        
        # Default to today
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        date_formats = [
            "%b %d, %Y",
            "%B %d, %Y",
            "%Y-%m-%d",
            "%d %b %Y",
            "%d %B %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%b %d",  # Year omitted
            "%B %d",  # Year omitted
            "%d %b",  # Year omitted
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # If year not in format, use default year
                if "%Y" not in fmt:
                    parsed = parsed.replace(year=self.default_year)
                return parsed
            except ValueError:
                continue
        
        # If all parsing fails, try to extract month/day/year manually
        return self._fuzzy_parse_date(date_str)
    
    def _fuzzy_parse_date(self, date_str: str) -> datetime:
        """Attempt to parse date with fuzzy matching."""
        # Try to find month name and day
        month_names = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
            "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        date_lower = date_str.lower()
        month = None
        day = None
        year = self.default_year
        
        # Find month
        for name, num in month_names.items():
            if name in date_lower:
                month = num
                break
        
        # Find day (number)
        day_match = re.search(r"\b(\d{1,2})\b", date_str)
        if day_match:
            day = int(day_match.group(1))
        
        # Find year (4-digit number)
        year_match = re.search(r"\b(20\d{2})\b", date_str)
        if year_match:
            year = int(year_match.group(1))
        
        if month and day:
            try:
                return datetime(year, month, day)
            except ValueError:
                pass
        
        raise MeetingParseError(f"Could not parse date: {date_str}")
    
    def _extract_attendees(self, notes: str) -> list[Attendee]:
        """Extract attendees from notes."""
        match = self.ATTENDEES_PATTERN.search(notes)
        if not match:
            return []
        
        attendees_str = match.group(1).strip()
        # Split by comma or 'and'
        names = re.split(r",\s*|\s+and\s+", attendees_str)
        
        attendees = []
        for name in names:
            name = name.strip()
            if name:
                try:
                    attendees.append(Attendee(name=name))
                except ValidationError:
                    continue
        
        return attendees
    
    def _extract_discussion(self, notes: str) -> list[str]:
        """Extract discussion points from notes."""
        # Look for Discussion section
        discussion_match = re.search(
            r"[Dd]iscussion:?\s*\n((?:[-*].*\n?)+)",
            notes
        )
        
        points = []
        if discussion_match:
            discussion_text = discussion_match.group(1)
            for line in discussion_text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    point = line[1:].strip()
                    if point:
                        points.append(point)
        
        return points
    
    def _extract_action_items(self, notes: str) -> list[ActionItem]:
        """Extract action items from notes."""
        action_items = []
        
        # Look for Action Items section
        action_section_match = re.search(
            r"[Aa]ction\s*[Ii]tems?:?\s*\n(.*?)(?:\n[A-Z]|\Z)",
            notes,
            re.DOTALL
        )
        
        if action_section_match:
            section = action_section_match.group(1)
            
            for line in section.split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                # Check for numbered or bullet format with checkbox
                match = self.ACTION_ITEM_PATTERN.match(line)
                if match:
                    checkbox1, checkbox2, desc, assignee, due = match.groups()
                    checkbox = checkbox1 or checkbox2 or ""
                    completed = checkbox.lower() in ("x", "✓")
                    
                    if desc and desc.strip():
                        due_date = None
                        if due and due.strip():
                            try:
                                due_date = self._parse_date(due.strip())
                            except MeetingParseError:
                                pass
                        
                        try:
                            action_items.append(ActionItem(
                                description=desc.strip(),
                                assignee=assignee.strip() if assignee else None,
                                due_date=due_date,
                                completed=completed
                            ))
                        except ValidationError:
                            continue
        
        # Also scan discussion for implied action items
        for point in self._extract_discussion(notes):
            # Look for patterns like "X will do Y" or "X to do Y"
            match = re.search(r"(\w+)\s+(?:will|to)\s+(.+)", point, re.IGNORECASE)
            if match:
                assignee = match.group(1)
                action_desc = match.group(2)
                
                # Extract due date if mentioned
                due_date = None
                due_match = re.search(r"by\s+(.+?)(?:$|\.|,)", point, re.IGNORECASE)
                if due_match:
                    try:
                        due_date = self._parse_date(due_match.group(1).strip())
                    except MeetingParseError:
                        pass
                
                try:
                    action_items.append(ActionItem(
                        description=action_desc.strip(),
                        assignee=assignee,
                        due_date=due_date
                    ))
                except ValidationError:
                    continue
        
        return action_items
    
    def _extract_decisions(self, notes: str) -> list[Decision]:
        """Extract decisions from meeting notes."""
        decisions = []
        
        # Look for explicit decisions section
        decisions_match = re.search(
            r"[Dd]ecisions?:?\s*\n((?:[-*].*\n?)+)",
            notes
        )
        
        if decisions_match:
            decisions_text = decisions_match.group(1)
            for line in decisions_text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    desc = line[1:].strip()
                    if desc:
                        try:
                            decisions.append(Decision(description=desc))
                        except ValidationError:
                            continue
        
        # Also scan discussion for decision patterns
        for point in self._extract_discussion(notes):
            # Patterns that indicate decisions
            decision_patterns = [
                r"[Aa]pproved\s+for\s+(.+)",
                r"[Bb]udget\s+approved",
                r"[Dd]ecided\s+(?:to|on)\s+(.+)",
                r"[Aa]greed\s+(?:to|on)\s+(.+)",
            ]
            
            for pattern in decision_patterns:
                if re.search(pattern, point, re.IGNORECASE):
                    try:
                        decisions.append(
                            Decision(description=point, context="From discussion")
                        )
                    except ValidationError:
                        pass
                    break
        
        return decisions


# =============================================================================
# Generators
# =============================================================================

class CalendarGenerator:
    """Generates ICS calendar files from meeting data."""
    
    DEFAULT_DURATION_MINUTES = 60
    
    def generate(
        self,
        meeting: Meeting,
        output_path: Path,
        duration_minutes: int = DEFAULT_DURATION_MINUTES
    ) -> Path:
        """Generate ICS calendar file for the meeting."""
        if not meeting:
            raise ValidationError("Meeting cannot be None")
        
        try:
            ics_content = self._create_ics_content(meeting, duration_minutes)
            output_path.write_text(ics_content, encoding="utf-8")
            return output_path
        except OSError as e:
            raise CalendarGenerationError(f"Failed to write calendar file: {e}") from e
    
    def _create_ics_content(
        self,
        meeting: Meeting,
        duration_minutes: int
    ) -> str:
        """Create ICS format calendar content."""
        uid = uuid.uuid4()
        created = datetime.now()
        
        start_time = meeting.date
        if start_time.hour == 0 and start_time.minute == 0:
            # Default to 9 AM if no time specified
            start_time = start_time.replace(hour=9, minute=0)
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Format dates for ICS (UTC format)
        dtstamp = created.strftime("%Y%m%dT%H%M%SZ")
        dtstart = start_time.strftime("%Y%m%dT%H%M%S")
        dtend = end_time.strftime("%Y%m%dT%H%M%S")
        
        attendees_str = "\n".join([
            f"ATTENDEE;CN={a.name}:MAILTO:"
            for a in meeting.attendees
        ])
        
        description_parts = [meeting.title]
        if meeting.discussion_points:
            description_parts.append("\nDiscussion:")
            description_parts.extend([f"- {p}" for p in meeting.discussion_points])
        if meeting.action_items:
            description_parts.append("\nAction Items:")
            for item in meeting.action_items:
                status = "[x]" if item.completed else "[ ]"
                assignee = f" ({item.assignee})" if item.assignee else ""
                description_parts.append(f"{status} {item.description}{assignee}")
        
        description = "\\n".join(description_parts)
        description = description.replace(",", "\\,")
        
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Meeting Pipeline//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;TZID=Local:{dtstart}",
            f"DTEND;TZID=Local:{dtend}",
            f"SUMMARY:{meeting.title}",
            f"DESCRIPTION:{description}",
        ]
        
        if attendees_str:
            ics_lines.append(attendees_str)
        
        ics_lines.extend([
            "END:VEVENT",
            "END:VCALENDAR"
        ])
        
        return "\n".join(ics_lines)


class TaskListGenerator:
    """Generates Markdown task list documents."""
    
    def generate(self, meeting: Meeting, output_path: Path) -> Path:
        """Generate Markdown task list file."""
        if not meeting:
            raise ValidationError("Meeting cannot be None")
        
        try:
            md_content = self._create_markdown_content(meeting)
            output_path.write_text(md_content, encoding="utf-8")
            return output_path
        except OSError as e:
            raise FileSystemError(f"Failed to write task list file: {e}") from e
    
    def _create_markdown_content(self, meeting: Meeting) -> str:
        """Create Markdown formatted task list."""
        lines = [
            f"# {meeting.title}",
            "",
            f"**Date:** {meeting.date.strftime('%B %d, %Y')}",
            "",
            f"**Attendees:** {', '.join(a.name for a in meeting.attendees)}",
            "",
            "---",
            "",
            "## Discussion Points",
            ""
        ]
        
        for point in meeting.discussion_points:
            lines.append(f"- {point}")
        
        if not meeting.discussion_points:
            lines.append("_No discussion points recorded_")
        
        lines.extend([
            "",
            "## Decisions",
            ""
        ])
        
        for decision in meeting.decisions:
            if decision.context:
                lines.append(f"- **{decision.description}** _(Context: {decision.context})_")
            else:
                lines.append(f"- {decision.description}")
        
        if not meeting.decisions:
            lines.append("_No decisions recorded_")
        
        lines.extend([
            "",
            "## Action Items",
            ""
        ])
        
        # Group by assignee
        by_assignee: dict[str, list[ActionItem]] = {}
        unassigned: list[ActionItem] = []
        
        for item in meeting.action_items:
            if item.assignee:
                if item.assignee not in by_assignee:
                    by_assignee[item.assignee] = []
                by_assignee[item.assignee].append(item)
            else:
                unassigned.append(item)
        
        # Output grouped items
        for assignee, items in sorted(by_assignee.items()):
            lines.append(f"### {assignee}")
            lines.append("")
            for item in items:
                status = "[x]" if item.completed else "[ ]"
                due = f" (Due: {item.due_date.strftime('%b %d')})" if item.due_date else ""
                priority = f" [{item.priority.value.upper()}]" if item.priority != Priority.MEDIUM else ""
                lines.append(f"- {status} {item.description}{due}{priority}")
            lines.append("")
        
        if unassigned:
            lines.append("### Unassigned")
            lines.append("")
            for item in unassigned:
                status = "[x]" if item.completed else "[ ]"
                due = f" (Due: {item.due_date.strftime('%b %d')})" if item.due_date else ""
                lines.append(f"- {status} {item.description}{due}")
            lines.append("")
        
        if not meeting.action_items:
            lines.append("_No action items_")
        
        # Add summary
        lines.extend([
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Total Action Items:** {len(meeting.action_items)}",
            f"- **Completed:** {sum(1 for i in meeting.action_items if i.completed)}",
            f"- **Pending:** {sum(1 for i in meeting.action_items if not i.completed)}",
            f"- **Decisions Made:** {len(meeting.decisions)}",
        ])
        
        return "\n".join(lines)


class FolderGenerator:
    """Generates project folder structure."""
    
    DEFAULT_STRUCTURE = [
        "documents",
        "documents/notes",
        "documents/reports",
        "tasks",
        "resources",
        "resources/references",
        "archive"
    ]
    
    def generate(
        self,
        meeting: Meeting,
        base_path: Path,
        structure: Optional[list[str]] = None
    ) -> Path:
        """Generate project folder structure."""
        if not meeting:
            raise ValidationError("Meeting cannot be None")
        
        # Create folder name from meeting title
        folder_name = self._sanitize_folder_name(meeting.title)
        project_path = base_path / folder_name
        
        try:
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            dirs_to_create = structure or self.DEFAULT_STRUCTURE
            for subdir in dirs_to_create:
                (project_path / subdir).mkdir(parents=True, exist_ok=True)
            
            # Create a README in the project folder
            readme_content = self._create_project_readme(meeting)
            (project_path / "README.md").write_text(readme_content, encoding="utf-8")
            
            return project_path
        except OSError as e:
            raise FileSystemError(f"Failed to create folder structure: {e}") from e
    
    def _sanitize_folder_name(self, title: str) -> str:
        """Convert meeting title to safe folder name."""
        # Remove or replace unsafe characters
        safe = re.sub(r'[<>:"/\\|?*]', "-", title)
        safe = re.sub(r'\s+', "_", safe)
        safe = safe.strip("._-")
        
        # Add date prefix for organization
        date_prefix = datetime.now().strftime("%Y%m%d")
        return f"{date_prefix}_{safe}" if safe else f"{date_prefix}_meeting"
    
    def _create_project_readme(self, meeting: Meeting) -> str:
        """Create project README content."""
        lines = [
            f"# {meeting.title}",
            "",
            f"**Meeting Date:** {meeting.date.strftime('%B %d, %Y')}",
            "",
            "**Attendees:**",
        ]
        
        for attendee in meeting.attendees:
            lines.append(f"- {attendee.name}")
        
        lines.extend([
            "",
            "## Project Structure",
            "",
            "```",
            ".",
            "├── documents/        # Meeting notes, reports, documentation",
            "│   ├── notes/        # Raw meeting notes",
            "│   └── reports/      # Generated reports",
            "├── tasks/            # Task lists and tracking",
            "├── resources/        # Reference materials",
            "│   └── references/   # External references and links",
            "└── archive/          # Archived/deprecated items",
            "```",
            "",
            "## Quick Links",
            "",
            "- [Task List](tasks/README.md)",
            "",
            "---",
            "",
            "_Generated by Meeting Pipeline_"
        ])
        
        return "\n".join(lines)


class EmailDraftGenerator:
    """Generates follow-up email drafts."""
    
    def generate(self, meeting: Meeting) -> list[str]:
        """Generate email drafts for the meeting follow-up."""
        if not meeting:
            raise ValidationError("Meeting cannot be None")
        
        emails = []
        
        # Group action items by assignee
        by_assignee: dict[str, list[ActionItem]] = {}
        for item in meeting.action_items:
            if item.assignee:
                if item.assignee not in by_assignee:
                    by_assignee[item.assignee] = []
                by_assignee[item.assignee].append(item)
        
        # Generate individual emails for each assignee
        for assignee, items in by_assignee.items():
            email = self._create_individual_email(meeting, assignee, items)
            emails.append(email)
        
        # Generate summary email for all attendees
        summary_email = self._create_summary_email(meeting)
        emails.append(summary_email)
        
        return emails
    
    def _create_individual_email(
        self,
        meeting: Meeting,
        assignee: str,
        items: list[ActionItem]
    ) -> str:
        """Create personalized email for an assignee."""
        lines = [
            f"Subject: Action Items from {meeting.title}",
            f"To: {assignee}",
            "",
            f"Hi {assignee},",
            "",
            f"Thank you for attending the {meeting.title} meeting on {meeting.date.strftime('%B %d, %Y')}. Following up on the action items assigned to you:",
            "",
        ]
        
        for i, item in enumerate(items, 1):
            due = f" (Due: {item.due_date.strftime('%B %d, %Y')})" if item.due_date else ""
            lines.append(f"{i}. {item.description}{due}")
        
        lines.extend([
            "",
            "Please let me know if you have any questions or need clarification on any of these items.",
            "",
            "Best regards,",
            "",
            "[Your Name]"
        ])
        
        return "\n".join(lines)
    
    def _create_summary_email(self, meeting: Meeting) -> str:
        """Create summary email for all attendees."""
        lines = [
            f"Subject: Meeting Recap - {meeting.title}",
            f"To: {', '.join(a.name for a in meeting.attendees)}",
            "",
            f"Hello everyone,",
            "",
            f"Thank you for attending our meeting on {meeting.date.strftime('%B %d, %Y')}. Here's a summary of what we discussed and the action items:",
            "",
            "## Discussion Summary",
            ""
        ]
        
        for point in meeting.discussion_points[:5]:  # Limit to first 5
            lines.append(f"- {point}")
        
        if len(meeting.discussion_points) > 5:
            lines.append(f"- _... and {len(meeting.discussion_points) - 5} more items_")
        
        lines.extend([
            "",
            "## Key Decisions",
            ""
        ])
        
        for decision in meeting.decisions:
            lines.append(f"- {decision.description}")
        
        lines.extend([
            "",
            "## Action Items Summary",
            ""
        ])
        
        for item in meeting.action_items:
            assignee = f" ({item.assignee})" if item.assignee else ""
            due = f" - Due {item.due_date.strftime('%b %d')}" if item.due_date else ""
            status = "✓ " if item.completed else "○ "
            lines.append(f"{status}{item.description}{assignee}{due}")
        
        lines.extend([
            "",
            "Please review your assigned action items and reach out if you have any questions.",
            "",
            "Best regards,",
            "",
            "[Your Name]"
        ])
        
        return "\n".join(lines)


# =============================================================================
# Pipeline
# =============================================================================

class MeetingPipeline:
    """
    Main pipeline for transforming meeting notes into project artifacts.
    
    Usage:
        pipeline = MeetingPipeline(output_dir=Path("./output"))
        result = pipeline.process(meeting_notes_text)
    """
    
    def __init__(
        self,
        output_dir: Path,
        calendar_generator: Optional[CalendarGenerator] = None,
        task_generator: Optional[TaskListGenerator] = None,
        folder_generator: Optional[FolderGenerator] = None,
        email_generator: Optional[EmailDraftGenerator] = None
    ) -> None:
        """
        Initialize the pipeline with output directory and optional generators.
        
        Args:
            output_dir: Base directory for all output files
            calendar_generator: Optional custom calendar generator
            task_generator: Optional custom task list generator
            folder_generator: Optional custom folder generator
            email_generator: Optional custom email generator
        """
        self.output_dir = Path(output_dir)
        self.parser = MeetingParser()
        self.calendar_generator = calendar_generator or CalendarGenerator()
        self.task_generator = task_generator or TaskListGenerator()
        self.folder_generator = folder_generator or FolderGenerator()
        self.email_generator = email_generator or EmailDraftGenerator()
    
    def process(
        self,
        notes: str,
        generate_calendar: bool = True,
        generate_task_list: bool = True,
        generate_folder: bool = True,
        generate_emails: bool = True
    ) -> PipelineOutput:
        """
        Process meeting notes through the complete pipeline.
        
        Args:
            notes: Raw meeting notes text
            generate_calendar: Whether to generate calendar file
            generate_task_list: Whether to generate task list
            generate_folder: Whether to create folder structure
            generate_emails: Whether to generate email drafts
        
        Returns:
            PipelineOutput containing all generated artifacts
        
        Raises:
            MeetingParseError: If notes cannot be parsed
            ValidationError: If validation fails
            Various generation errors: If artifact generation fails
        """
        # Validate input
        if not notes or not notes.strip():
            raise ValidationError("Meeting notes cannot be empty")
        
        # Parse meeting
        meeting = self.parser.parse(notes)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        output = PipelineOutput(meeting=meeting)
        
        # Generate artifacts
        if generate_calendar:
            calendar_path = self.output_dir / f"{self._safe_filename(meeting.title)}.ics"
            output.calendar_path = self.calendar_generator.generate(meeting, calendar_path)
        
        if generate_task_list:
            task_path = self.output_dir / f"{self._safe_filename(meeting.title)}_tasks.md"
            output.task_list_path = self.task_generator.generate(meeting, task_path)
        
        if generate_folder:
            output.folder_path = self.folder_generator.generate(meeting, self.output_dir)
        
        if generate_emails:
            output.email_drafts = self.email_generator.generate(meeting)
        
        return output
    
    def _safe_filename(self, title: str) -> str:
        """Convert title to safe filename."""
        safe = re.sub(r'[<>:"/\\|?*]', "-", title)
        safe = re.sub(r'\s+', "_", safe)
        return safe.strip("._-") or "meeting"


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:
    """CLI entry point for the meeting pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Transform meeting notes into project artifacts"
    )
    parser.add_argument(
        "input",
        help="Path to meeting notes file (or '-' for stdin)"
    )
    parser.add_argument(
        "-o", "--output",
        default="./meeting-output",
        help="Output directory (default: ./meeting-output)"
    )
    parser.add_argument(
        "--no-calendar",
        action="store_true",
        help="Skip calendar generation"
    )
    parser.add_argument(
        "--no-tasks",
        action="store_true",
        help="Skip task list generation"
    )
    parser.add_argument(
        "--no-folder",
        action="store_true",
        help="Skip folder structure generation"
    )
    parser.add_argument(
        "--no-emails",
        action="store_true",
        help="Skip email draft generation"
    )
    
    args = parser.parse_args()
    
    # Read input
    if args.input == "-":
        import sys
        notes = sys.stdin.read()
    else:
        notes = Path(args.input).read_text(encoding="utf-8")
    
    # Run pipeline
    pipeline = MeetingPipeline(output_dir=Path(args.output))
    result = pipeline.process(
        notes=notes,
        generate_calendar=not args.no_calendar,
        generate_task_list=not args.no_tasks,
        generate_folder=not args.no_folder,
        generate_emails=not args.no_emails
    )
    
    # Report results
    print(f"✓ Processed meeting: {result.meeting.title}")
    print(f"  - Attendees: {len(result.meeting.attendees)}")
    print(f"  - Action Items: {len(result.meeting.action_items)}")
    print(f"  - Decisions: {len(result.meeting.decisions)}")
    
    if result.calendar_path:
        print(f"✓ Calendar: {result.calendar_path}")
    if result.task_list_path:
        print(f"✓ Task List: {result.task_list_path}")
    if result.folder_path:
        print(f"✓ Project Folder: {result.folder_path}")
    if result.email_drafts:
        print(f"✓ Generated {len(result.email_drafts)} email drafts")


if __name__ == "__main__":
    main()

