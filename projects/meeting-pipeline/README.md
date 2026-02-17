# 📅 Meeting to Project Pipeline

> Transform meeting notes into complete project setup — calendar events, task lists, email drafts, and folder structure in seconds.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What It Does

Takes messy meeting notes like this:
```
Meeting: Q1 Planning
Date: Feb 17, 2026
Attendees: Alice, Bob, Charlie

Action Items:
1. [ ] API integration - Bob - Due Feb 20
2. [ ] Documentation - Bob - Due Feb 22
3. [ ] Schedule client meeting - Alice - Due Feb 18
```

And automatically generates:

### 📅 Calendar Events (.ics files)
- Auto-scheduled based on parsed dates
- Attendee invites for each action item
- Compatible with Apple, Google, Outlook

### ✅ Task Lists (Markdown)
```markdown
# Q1 Planning - Action Items

## High Priority
- [ ] API integration - @Bob - Due: Feb 20, 2026
- [ ] Schedule client meeting - @Alice - Due: Feb 18, 2026

## Medium Priority  
- [ ] Documentation - @Bob - Due: Feb 22, 2026
```

### 📧 Email Drafts
Personalized follow-up emails for each stakeholder with their specific action items.

### 📁 Project Folder Structure
```
Q1_Planning/
├── meetings/
│   └── 2026-02-17_Q1_Planning_notes.txt
├── action_items/
│   └── task_list.md
├── calendar/
│   └── events.ics
└── drafts/
    └── followup_emails.txt
```

---

## 🚀 Quick Start

```bash
# Parse meeting notes
python meeting_pipeline.py --input meeting_notes.txt --output ./project_setup/
```

Or use as a Python module:
```python
from meeting_pipeline import MeetingPipeline

pipeline = MeetingPipeline()
result = pipeline.process("meeting_notes.txt", output_dir="./project/")
```

---

## 📊 Time Savings

| Manual Work | Automated | Savings |
|------------|-----------|---------|
| 45 min admin work | 10 sec automation | **99.6% faster** |

For a 10-person team: **200+ hours/year saved**

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Meeting Notes  │
└────────┬────────┘
         │
    ┌────┴────┐
    │  Parser │
    └────┬────┘
         │
    ┌────┴────┐
┌───┐ ┌───┐ ┌───┐
│📅 │ │✅ │ │📧 │
│Cal│ │Task│ │Email│
└───┘ └───┘ └───┘
```

**Components:**
- `MeetingParser` - Extracts attendees, dates, action items
- `CalendarGenerator` - Creates .ics files with timezone support
- `TaskListGenerator` - Markdown task lists with priorities
- `EmailDraftGenerator` - Personalized email drafts
- `FolderGenerator` - Project folder structure

---

## 📁 Files

| File | Size | Description |
|------|------|-------------|
| `meeting_pipeline.py` | 34 KB | Core parser and pipeline |
| `calendar_generator.py` | 21 KB | ICS generation module |
| `test_*.py` | ~40 KB | Unit tests |
| `examples/` | 21 KB | Sample inputs/outputs |

---

## 🎯 Hackathon Submission

See [HACKATHON_SUBMISSION.md](HACKATHON_SUBMISSION.md) for:
- Problem statement
- Solution overview
- Demo video script
- Time savings calculation

---

*Built with multi-agent AI development workflow*
