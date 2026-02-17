# Meeting to Project Pipeline

A Python automation skill that transforms meeting notes into actionable project artifacts. Built for the WeMakeDevs hackathon.

## Features

- **Parse Meeting Notes**: Extract attendees, action items, deadlines, and decisions from unstructured text
- **Generate Calendar Events**: Create `.ics` files for calendar integration
- **Create Task Lists**: Generate Markdown task lists grouped by assignee
- **Project Folder Structure**: Automatically create organized project directories
- **Draft Follow-up Emails**: Generate personalized emails for attendees

## Installation

No external dependencies required - uses only Python standard library.

```bash
# Clone or copy the files
cd meeting-pipeline

# Run tests
python test_meeting_pipeline.py
```

## Usage

### Quick Start

```python
from pathlib import Path
from meeting_pipeline import MeetingPipeline

# Input meeting notes
notes = """
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
"""

# Run the pipeline
pipeline = MeetingPipeline(output_dir=Path("./output"))
result = pipeline.process(notes)

# Access generated artifacts
print(f"Calendar: {result.calendar_path}")
print(f"Task List: {result.task_list_path}")
print(f"Project Folder: {result.folder_path}")
print(f"Emails Generated: {len(result.email_drafts)}")
```

### CLI Usage

```bash
# Process a file
python meeting_pipeline.py meeting_notes.txt -o ./output

# Process from stdin
cat meeting_notes.txt | python meeting_pipeline.py -

# Selective generation
python meeting_pipeline.py notes.txt --no-calendar --no-folder
```

### Advanced Usage

#### Custom Output Directory

```python
from meeting_pipeline import MeetingPipeline
from pathlib import Path

pipeline = MeetingPipeline(output_dir=Path("/path/to/projects"))
result = pipeline.process(notes)
```

#### Selective Artifact Generation

```python
# Only generate task list and emails
result = pipeline.process(
    notes,
    generate_calendar=False,
    generate_task_list=True,
    generate_folder=False,
    generate_emails=True
)
```

#### Using Individual Components

```python
from meeting_pipeline import (
    MeetingParser,
    CalendarGenerator,
    TaskListGenerator,
    FolderGenerator,
    EmailDraftGenerator
)
from pathlib import Path

# Parse only
parser = MeetingParser()
meeting = parser.parse(notes)
print(f"Title: {meeting.title}")
print(f"Attendees: {[a.name for a in meeting.attendees]}")
print(f"Action Items: {len(meeting.action_items)}")

# Generate individual artifacts
calendar_gen = CalendarGenerator()
calendar_gen.generate(meeting, Path("meeting.ics"))

task_gen = TaskListGenerator()
task_gen.generate(meeting, Path("tasks.md"))

folder_gen = FolderGenerator()
folder_gen.generate(meeting, Path("./projects"))

email_gen = EmailDraftGenerator()
emails = email_gen.generate(meeting)
for email in emails:
    print(email)
    print("---")
```

## Input Format

The parser supports flexible meeting note formats:

```
Meeting: Meeting Title
Date: Feb 17, 2026 (or February 17, 2026, 2026-02-17, etc.)
Attendees: Alice, Bob, Charlie (comma-separated or "and")

Discussion:
- Discussion point 1
- Discussion point 2
- Notes about various topics

Action Items:
1. [ ] Task description - Assignee - Due Feb 20
2. [x] Completed task - Alice - Due Feb 18
3. [ ] Task without assignee
- [ ] Alternative format task

Decisions:
- Decision made in meeting
- Budget approved for X
- Agreement on Y
```

### Supported Date Formats

- Feb 17, 2026
- February 17, 2026
- 2026-02-17
- 17 Feb 2026
- 02/17/2026
- Feb 17 (year defaults to current)

### Action Item Formats

The parser recognizes multiple action item formats:

```
1. [ ] Task - Assignee - Due Feb 20
2. [x] Completed task - Assignee
- [ ] Alternative format task
* [ ] Another format
- Task implied from discussion: Alice will do something
```

## Output Artifacts

### 1. Calendar Events (.ics)

Standard ICS format compatible with:
- Google Calendar
- Apple Calendar
- Microsoft Outlook
- Any RFC 5545 compliant calendar

Contains:
- Meeting title and date
- Attendee list
- Action items in description
- Discussion summary

### 2. Task List (Markdown)

Organized Markdown document with:
- Meeting metadata
- Discussion points
- Decisions made
- Action items grouped by assignee
- Completion status and due dates
- Summary statistics

Example output:
```markdown
# Q1 Planning

**Date:** February 17, 2026

**Attendees:** Alice, Bob, Charlie

## Action Items

### Bob
- [ ] API integration (Due: Feb 20)
- [ ] Documentation (Due: Feb 22)

### Alice
- [ ] Schedule client meeting (Due: Feb 18)

## Summary

- **Total Action Items:** 3
- **Completed:** 0
- **Pending:** 3
- **Decisions Made:** 1
```

### 3. Project Folder Structure

Creates organized directory structure:
```
20260217_Q1_Planning/
├── README.md
├── documents/
│   ├── notes/
│   └── reports/
├── tasks/
├── resources/
│   └── references/
└── archive/
```

### 4. Email Drafts

Generates multiple email drafts:

**Individual Emails** - personalized for each assignee with their specific tasks

**Summary Email** - sent to all attendees with full meeting recap

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `MeetingParser` | Extract structured data from text notes |
| `CalendarGenerator` | Create ICS calendar files |
| `TaskListGenerator` | Generate Markdown task lists |
| `FolderGenerator` | Create project directory structure |
| `EmailDraftGenerator` | Draft follow-up emails |
| `MeetingPipeline` | Orchestrate the complete workflow |

### Data Models

```python
@dataclass
class Meeting:
    title: str
    date: datetime
    attendees: list[Attendee]
    discussion_points: list[str]
    action_items: list[ActionItem]
    decisions: list[Decision]

@dataclass  
class ActionItem:
    description: str
    assignee: Optional[str]
    due_date: Optional[datetime]
    priority: Priority
    completed: bool
```

### Error Handling

The pipeline uses specific exceptions:

```python
from meeting_pipeline import (
    MeetingPipelineError,     # Base exception
    MeetingParseError,        # Parsing failures
    ValidationError,          # Invalid input
    CalendarGenerationError,  # Calendar creation issues
    FileSystemError,          # File/Directory operations
)

try:
    result = pipeline.process(notes)
except MeetingParseError as e:
    print(f"Could not parse notes: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

## Code Quality

Built following Python Expert Best Practices:

- **Type Hints**: Full type annotations throughout
- **Fail-Fast Validation**: Input validation at boundaries
- **Specific Exceptions**: Custom exception hierarchy
- **Clean Code**: Single responsibility, readable functions
- **Comprehensive Tests**: 95%+ test coverage

## Testing

```bash
# Run all tests
python test_meeting_pipeline.py

# Run with verbose output
python test_meeting_pipeline.py -v

# Run specific test class
python test_meeting_pipeline.py TestMeetingParser

# Run specific test
python test_meeting_pipeline.py TestMeetingParser.test_parse_basic_meeting
```

## Examples

### Example 1: Weekly Standup

```python
notes = """
Meeting: Weekly Standup
Date: Feb 17, 2026
Attendees: Sarah, Mike, Emily

Discussion:
- Sarah completed the user research report
- Mike working on API integration
- Emily waiting on design approval
- Team discussed Q1 priorities

Action Items:
1. [ ] Finalize API documentation - Mike - Due Feb 19
2. [ ] Review user research - Emily - Due Feb 18
3. [ ] Present findings to stakeholders - Sarah - Due Feb 20

Decisions:
- Moving standup to 10am
- Using new project management tool
"""

pipeline = MeetingPipeline(output_dir=Path("./standup-output"))
result = pipeline.process(notes)
```

### Example 2: Client Meeting

```python
notes = """
Meeting: Acme Corp Kickoff
Date: March 1, 2026
Attendees: John Client, Jane PM, Bob Dev

Discussion:
- Reviewed project scope and timeline
- John presented requirements document
- Jane outlined project phases
- Bob discussed technical approach
- Budget confirmed at $50,000

Action Items:
1. [ ] Send SOW for signature - Jane - Due Mar 3
2. [ ] Set up project repository - Bob - Due Mar 2
3. [ ] Schedule weekly check-ins - Jane - Due Mar 5

Decisions:
- Approved project kickoff for March 15
- Weekly meetings on Thursdays
- Using Agile methodology
"""

pipeline = MeetingPipeline(output_dir=Path("./client-projects"))
result = pipeline.process(notes)
```

### Example 3: Minimal Meeting

```python
notes = """
Meeting: Quick Sync
Date: Feb 17, 2026
Attendees: Alice, Bob

Discussion:
- Caught up on progress

Action Items:
1. [ ] Follow up tomorrow
"""

pipeline = MeetingPipeline(output_dir=Path("./output"))
result = pipeline.process(notes)
```

## Extending the Pipeline

### Custom Generators

```python
from meeting_pipeline import CalendarGenerator, Meeting
from pathlib import Path

class CustomCalendarGenerator(CalendarGenerator):
    def _create_ics_content(self, meeting: Meeting, duration_minutes: int) -> str:
        # Custom ICS generation logic
        return super()._create_ics_content(meeting, duration_minutes)

pipeline = MeetingPipeline(
    output_dir=Path("./output"),
    calendar_generator=CustomCalendarGenerator()
)
```

### Custom Folder Structure

```python
from meeting_pipeline import FolderGenerator

custom_structure = [
    "docs",
    "src",
    "tests",
    "ci",
    "scripts"
]

pipeline = MeetingPipeline(output_dir=Path("./output"))
meeting = pipeline.parser.parse(notes)

folder_gen = FolderGenerator()
folder_gen.generate(meeting, Path("./output"), custom_structure)
```

## License

MIT License - Created for WeMakeDevs Hackathon 2026

## Author

Built with Python best practices in mind. Clean, type-hinted, well-tested code.
