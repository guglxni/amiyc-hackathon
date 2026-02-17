#!/bin/bash
# Multi-Agent Coordinator Setup for AMIYC Hackathon
# Based on MULTI_AGENT_CLI_GUIDE.md patterns

set -e

echo "🚀 Setting up Multi-Agent Environment for AMIYC Hackathon"
echo "=========================================================="

# Base configuration
PROJECT_DIR="/Volumes/MacExt/amiyc/projects"
COORDINATOR_PORT=50052
CODER_PORT=50053
RESEARCHER_PORT=50054
DOC_PORT=50055

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        return 1
    fi
    return 0
}

# Setup coordinator agent
echo ""
echo "📋 Agent 1: Coordinator (Port $COORDINATOR_PORT)"
echo "   - Manages overall project"
echo "   - Orchestrates other agents"
echo "   - Tracks progress and blockers"
if check_port $COORDINATOR_PORT; then
    echo "   ✓ Port available"
else
    echo "   ⚠️  Port in use, will use default"
fi

# Setup coder agent
echo ""
echo "💻 Agent 2: Coder (Port $CODER_PORT)"
echo "   - Builds automation skills"
echo "   - Handles file operations"
echo "   - Implements core logic"
if check_port $CODER_PORT; then
    echo "   ✓ Port available"
else
    echo "   ⚠️  Port in use, will use default"
fi

# Setup researcher agent
echo ""
echo "🔍 Agent 3: Researcher (Port $RESEARCHER_PORT)"
echo "   - Researches Accomplish.ai APIs"
echo "   - Finds documentation"
echo "   - Explores example skills"
if check_port $RESEARCHER_PORT; then
    echo "   ✓ Port available"
else
    echo "   ⚠️  Port in use, will use default"
fi

# Setup documentation agent
echo ""
echo "📝 Agent 4: Documenter (Port $DOC_PORT)"
echo "   - Writes README files"
echo "   - Creates usage guides"
echo "   - Generates demo scripts"
if check_port $DOC_PORT; then
    echo "   ✓ Port available"
else
    echo "   ⚠️  Port in use, will use default"
fi

echo ""
echo "=========================================================="
echo "✅ Multi-Agent Environment Ready!"
echo ""
echo "Next steps:"
echo "  1. Choose a hackathon idea from HACKATHON_IDEAS.md"
echo "  2. Start agents with specific tasks"
echo "  3. Monitor progress and coordinate"
echo ""
echo "Quick start commands:"
echo "  cline task new 'Build file organizer skill' -m act -y"
echo "  kimi --session research --prompt 'Research Accomplish file API'"
echo ""
