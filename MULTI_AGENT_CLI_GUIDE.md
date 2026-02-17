# 🤖 Multi-Agent CLI Guide: Cline + Kimi Code for Hackathon Success

> **Complete reference for building AI-powered automation during the "Automate Me If You Can" Hackathon (Feb 16-22, 2026)**

---

## 📑 Table of Contents

1. [Quick Start](#quick-start)
2. [Cline CLI Complete Reference](#cline-cli-complete-reference)
3. [Kimi Code CLI Complete Reference](#kimi-code-cli-complete-reference)
4. [Multi-Agent Workflow Patterns](#multi-agent-workflow-patterns)
5. [Combined Cline + Kimi Workflows](#combined-cline--kimi-workflows)
6. [Hackathon Automation Templates](#hackathon-automation-templates)
7. [Best Practices](#best-practices)

---

## 🚀 Quick Start

### Your Multi-Agent Hackathon Setup

```bash
# Terminal 1: Agent Coordinator (Cline)
cline task new "Coordinate hackathon project" -m act

# Terminal 2: File Specialist (Cline - different instance)
cline instance new file-agent --address localhost:50053
cline task new "Build file organization automation" -m act --address localhost:50053

# Terminal 3: Research Agent (Kimi)
kimi --prompt "Research Accomplish.ai file management capabilities"

# Terminal 4: Documentation (Kimi)
kimi --prompt "Create README for the automation skill"
```

---

## 📦 Cline CLI Complete Reference

### Core Commands Overview

```bash
cline [prompt] [flags]              # Main entry point
cline task [command]                 # Task management
cline instance [command]             # Multi-instance management
cline config [command]               # Configuration
cline auth [command]                 # Authentication
cline logs [command]                 # Log management
```

### Global Flags

| Flag | Short | Description | Example |
|------|-------|-------------|---------|
| `--address` | - | Cline Core gRPC address | `--address localhost:50052` |
| `--file` | `-f` | Attach files | `-f hackathon_ideas.md` |
| `--image` | `-i` | Attach image files | `-i screenshot.png` |
| `--mode` | `-m` | Mode: act or plan | `-m act` |
| `--no-interactive` | - | Yolo mode (non-interactive) | `--no-interactive` |
| `--oneshot` | `-o` | Full autonomous mode | `-o` |
| `--output-format` | `-F` | Output: rich, json, plain | `-F json` |
| `--setting` | `-s` | Task settings (key=value) | `-s aws-region=us-west-2` |
| `--verbose` | `-v` | Verbose output | `-v` |
| `--yolo` | `-y` | Enable yolo mode | `-y` |

### Mode: Act vs Plan

| Mode | Description | Use Case |
|------|-------------|----------|
| `plan` (default) | Propose changes, ask for approval | New features, risky operations |
| `act` | Execute autonomously | Fast iteration, trusted operations |

---

### 📋 Task Management Commands

```bash
# Create new task
cline task new <prompt> [flags]
cline task new "Create automation skill for file organization" -f HACKATHON_IDEAS.md

# Shortcut
cline task n "Build document generator"

# Options:
#   --address string    Specific instance address
#   -f, --file strings  Attach files
#   -i, --image strings Attach images
#   -m, --mode string   act|plan mode
#   -s, --setting       Task settings
#   -y, --yolo          Non-interactive
```

#### Task Sub-commands

```bash
cline task chat           # Chat with current task (interactive mode)
cline task list           # List recent task history
cline task new           # Create new task
cline task open <id>     # Open task by ID
cline task pause          # Pause current task
cline task restore <id>  # Restore to checkpoint
cline task send          # Send followup message
cline task view          # View conversation
```

#### Task Workflow Example

```bash
# Start new task
cline task new "Build file organizer skill"

# Check task status
cline task list

# View conversation
cline task view <task-id>

# Send followup
cline task send "Add date-based categorization"

# Pause if needed
cline task pause
```

---

### 🖥️ Instance Management (Multi-Agent!)

```bash
# List all instances
cline instance list

# Create new instance (different agent!)
cline instance new my-agent --address localhost:50053

# Set default instance
cline instance default my-agent

# Kill instance
cline instance kill <address>

# Use specific instance for task
cline task new "Task for agent 2" --address localhost:50053
```

#### Multi-Agent Setup

```bash
# Create 3 separate agents for hackathon
cline instance new coordinator --address localhost:50052
cline instance new coder --address localhost:50053
cline instance new researcher --address localhost:50054

# Coordinate: Use coordinator to manage others
cline task new "Orchestrate: have coder build X, researcher find docs for Y" -m act --address localhost:50052
```

---

### ⚙️ Configuration Commands

```bash
# List all settings
cline config list

# Get specific value
cline config get model

# Set value
cline config set default-model gpt-4
cline config set max-tokens 4000
```

---

### 📊 Log Management

```bash
# View logs
cline logs view

# Clear logs
cline logs clear

# Export logs
cline logs export > hackathon_logs.txt
```

---

## 🧠 Kimi Code CLI Complete Reference

### Core Commands Overview

```bash
kimi [OPTIONS] COMMAND [ARGS]...
```

### Global Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--version` | `-V` | Show version | `-V` |
| `--verbose` | - | Verbose output | `--verbose` |
| `--debug` | - | Debug logging | `--debug` |
| `--work-dir` | `-w` | Working directory | `-w /project` |
| `--session` | `-S` | Resume session | `-S session-123` |
| `--continue` | `-C` | Continue previous | `-C` |
| `--config` | - | Config TOML/JSON string | `--config "{...}"` |
| `--config-file` | - | Config file path | `--config-file config.json` |
| `--model` | `-m` | LLM model to use | `-m k1` |
| `--thinking` | - | Enable thinking mode | `--thinking` |
| `--yolo` | `-y` | Auto-approve all | `-y` |
| `--prompt` | `-p` | User prompt | `-p "Research X"` |
| `--print` | - | Print mode (non-interactive) | `--print` |
| `--agent` | - | Builtin agent: default, okabe | `--agent okabe` |
| `--agent-file` | - | Custom agent spec file | `--agent-file myagent.yaml` |
| `--mcp-config-file` | - | MCP config file | `--mcp-config-file mcp.json` |
| `--skills-dir` | - | Skills directory | `--skills-dir ./skills` |
| `--max-steps-per-turn` | - | Max steps (default from config) | `--max-steps-per-turn 10` |
| `--max-retries-per-step` | - | Max retries | `--max-retries-per-step 3` |
| `--quiet` | - | Quiet mode | `--quiet` |

### Commands

```bash
kimi login     # Login to Kimi account
kimi logout    # Logout
kimi term      # Run Toad TUI (terminal UI)
kimi acp       # Run ACP server
kimi info      # Show version info
kimi mcp       # Manage MCP servers
kimi web       # Run web interface
```

---

### 🔧 MCP Server Management

```bash
# Add MCP server
kimi mcp add <server-name> <config>

# Remove MCP server
kimi mcp remove <server-name>

# List all MCP servers
kimi mcp list

# Authorize OAuth
kimi mcp auth <server-name>

# Reset auth tokens
kimi mcp reset-auth <server-name>

# Test connection
kimi mcp test <server-name>
```

---

### 👤 Agent Specifications

Kimi Code supports different agent types:

| Agent | Use Case |
|-------|----------|
| `default` | General purpose coding |
| `okabe` | Specialized for certain tasks |

#### Custom Agent Files

```bash
# Use custom agent specification
kimi --agent-file custom_agent.yaml --prompt "Your task"
```

---

### 🔄 Session Management

```bash
# Start new session (default)
kimi --prompt "Build something"

# Continue previous session
kimi --continue --prompt "Add more features"

# Resume specific session
kimi --session session-abc123 --prompt "Continue work"

# Work in specific directory
kimi --work-dir /path/to/project --prompt "Fix bug"
```

---

### 🎯 Interactive vs Non-Interactive

```bash
# Interactive (default)
kimi "Build a Python script"

# Non-interactive (print mode - useful for scripts)
kimi --print "What is 2+2?"

# Quiet mode (non-interactive, text output)
kimi --quiet "Explain async/await"
```

---

## 🔀 Multi-Agent Workflow Patterns

### Pattern 1: Cline Instance-Based Multi-Agent

```bash
# Setup: Create 4 agent instances
cline instance new coordinator --address localhost:50052
cline instance new file-agent --address localhost:50053  
cline instance new browser-agent --address localhost:50054
cline instance new doc-agent --address localhost:50055

# Agent 1: Coordinator - manages overall project
cline task new "Create automation skill that organizes files by type and date" -m act --address localhost:50052

# Agent 2: File specialist - handles file operations
cline task new "Build file categorization system: images->Images, docs->Documents, code->Projects" -m act --address localhost:50053

# Agent 3: Browser agent - web research
cline task new "Research Accomplish.ai browser automation API documentation" -m act --address localhost:50054

# Agent 4: Documentation agent  
cline task new "Write README with usage examples for the file organizer skill" -m act --address localhost:50055
```

### Pattern 2: Kimi Code Session-Based Agents

```bash
# Agent 1: Research (new session)
kimi --session research-1 --prompt "Find all Accomplish.ai skills documentation"

# Agent 2: Continue research
kimi --session research-1 --continue --prompt "Also find file management capabilities"

# Agent 3: Different work, new session
kimi --session coding-1 --work-dir ./my-skill --prompt "Create skill.yaml for file organizer"

# Agent 4: Documentation
kimi --session docs-1 --prompt "Generate API documentation from skill.yaml"
```

### Pattern 3: Parallel Execution

```bash
# Run multiple agents in background
cline task new "Build core file organizer" -m act &
cline task new "Create test suite" -m act &
kimi --prompt "Research alternatives" &

# Wait for completion
wait
```

### Pattern 4: Sequential Handoff

```bash
# Step 1: Research
kimi --prompt "Research Accomplish.ai calendar integration" --print > research.md

# Step 2: Build (use research)
cline task new "Build calendar automation using research.md" -f research.md

# Step 3: Document (use output)
kimi --prompt "Create documentation from the calendar automation skill"
```

---

## 🔗 Combined Cline + Kimi Workflows

### Recommended Task Distribution

| Task | Best Tool | Reason |
|------|-----------|--------|
| File operations | **Cline** | Full terminal access |
| Code execution | **Cline** | Native execution |
| Web research | **Kimi** | Strong browsing |
| Documentation | **Kimi** | Better writing |
| Multi-file editing | **Cline** | Batch operations |
| Brainstorming | **Kimi** | Creative thinking |
| API integration | **Cline** | Full control |

### Combined Workflow Example: Meeting to Project Pipeline

```bash
# ===============================
# Phase 1: Research (Kimi)
# ===============================
kimi --session meeting-pipeline --prompt "Research Accomplish.ai calendar integration capabilities and create summary"

# ===============================
# Phase 2: Build Core (Cline)
# ===============================
# After research is done...
cline task new "Build skill that:
1. Reads meeting notes from input
2. Extracts action items and dates
3. Creates calendar events
4. Creates project folder structure
5. Generates task document" -m act

# ===============================
# Phase 3: Test & Refine (Cline)
# ===============================
cline task new "Create test meeting notes and verify the skill works end-to-end"

# ===============================
# Phase 4: Documentation (Kimi)
# ===============================
kimi --session docs --prompt "Create comprehensive README including:
- Installation steps
- Usage examples
- Demo video script
- Troubleshooting guide"

# ===============================
# Phase 5: Final Review (Cline)
# ===============================
cline task new "Review all files, verify completeness, prepare submission"
```

---

## 🏆 Hackathon Automation Templates

### Template 1: Quick Start Multi-Agent Setup

```bash
#!/bin/bash
# hackathon-setup.sh - One-command multi-agent setup

# Create agent instances
cline instance new coordinator --address localhost:50052 2>/dev/null || echo "Coordinator ready"
cline instance new coder --address localhost:50053 2>/dev/null || echo "Coder ready"
cline instance new researcher --address localhost:50054 2>/dev/null || echo "Researcher ready"

echo "🚀 Multi-agent environment ready!"
echo "Run 'cline task list' to see all agents"
```

### Template 2: Parallel Development Workflow

```bash
# Terminal 1: Core development
cline task new "Build meeting-to-project automation skill" -m act

# Terminal 2: Test development  
cline task new "Create comprehensive test suite for meeting skill" -m act

# Terminal 3: Documentation
kimi --work-dir ./skill --prompt "Write README.md for the meeting automation skill"

# Terminal 4: Research improvements
kimi --prompt "Research ways to enhance the skill - find similar projects"
```

### Template 3: PR Contribution Workflow (Cline Only)

```bash
# 1. Claim issue
cline task new "Comment on GitHub issue #373 (Dark Mode) that I'm working on it"

# 2. Fork and setup
cline task new "Fork accomplish-ai/accomplish, clone locally, create feat/dark-mode branch"

# 3. Implement
cline task new "Implement dark mode feature - add dark color palette, settings toggle, apply to UI components"

# 4. Test
cline task new "Test dark mode locally, take screenshots"

# 5. Submit PR
cline task new "Push branch, create PR with description, screenshots, and test steps"
```

### Template 4: Kimi Code Research + Cline Build

```bash
# Step 1: Kimi researches
kimi --print --prompt "Research Accomplish.ai skill format and create example skill.yaml" > skill_template.md

# Step 2: Cline builds using template
cline task new "Create file organizer skill using skill_template.md as reference" -f skill_template.md

# Step 3: Kimi creates docs
kimi --prompt "Create user documentation from the file organizer skill"
```

---

## 💡 Best Practices

### 🎯 General Guidelines

1. **Use appropriate mode**: `plan` for new/untrusted tasks, `act` for iteration
2. **Leverage instances**: Separate concerns with different Cline instances
3. **Use sessions in Kimi**: Continue context with `--session` and `--continue`
4. **Attach relevant files**: Use `-f` flag to provide context
5. **Set boundaries**: Use `--max-steps-per-turn` to control costs

### ⚡ Performance Tips

```bash
# Faster execution
cline task new "Task" -m act --no-interactive

# Use specific model for speed
kimi -m k1-fast "Quick task"

# Batch operations in Cline
cline task new "Process all files: rename, categorize, organize"
```

### 🛡️ Safety Guidelines

```bash
# Safe: Ask before executing
cline task new "Review code but don't modify"

# Moderate: Auto-approve within bounds
cline task new "Fix bugs in existing files" -y

# Risky: Full autonomy only for trusted tasks
cline task new "Refactor entire codebase" -o
```

### 📝 Documentation Best Practices

1. **Use Kimi for writing**: `kimi --prompt "Write documentation for X"`
2. **Generate from code**: `kimi --prompt "Create docs from this skill.yaml"`
3. **Use print mode**: For automated documentation generation
4. **Separate sessions**: Keep research and writing separate

---

## 🎬 Demo Script Template

```bash
# Quick demo of multi-agent workflow
#!/bin/bash

echo "=== Multi-Agent Hackathon Demo ==="

echo "1. Starting Research Agent (Kimi)..."
kimi --print --prompt "What are the 3 best automation ideas from HACKATHON_IDEAS.md?" > ideas.txt

echo "2. Building with Cline..."
cline task new "Build a simple file organizer based on ideas.txt" -y

echo "3. Documenting..."
kimi --prompt "Create README for the file organizer"

echo "✅ Demo complete!"
```

---

## 📞 Quick Reference Card

### Cline CLI

```bash
# New task
cline task new "prompt" -m act -f file.md

# Multi-agent
cline instance new name --address PORT
cline task new "prompt" --address PORT

# Modes
-m plan   # Ask first
-m act    # Just do it
-y        # Yolo (non-interactive)
```

### Kimi Code

```bash
# Simple prompt
kimi "prompt"

# With options
kimi -m k1 -y --thinking "prompt"

# Session management
kimi -S session-id --continue "more"

# Non-interactive
kimi --print "prompt"
```

---

## 🔗 Useful Links

| Resource | Link |
|----------|------|
| Cline Docs | (use `man cline`) |
| Kimi CLI Docs | https://moonshotai.github.io/kimi-cli/ |
| Hackathon Ideas | See `HACKATHON_IDEAS.md` |
| Accomplish.ai | https://github.com/accomplish-ai/accomplish |

---

*Created for the "Automate Me If You Can" Hackathon - February 16-22, 2026*
*Good luck! 🎩✨
