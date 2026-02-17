# 🚀 Open Source Contribution: Dark Mode #373

**Direct Terminal Workflow with Cline + CharlieLabs**

---

## ✅ Setup Complete

```bash
# Location set up
/Volumes/MacExt/amiyc/oss-contributions/accomplish/
├── src/                    # Source code
├── WORKFLOW.md             # Detailed coordination doc
└── feature/dark-mode-373   # Working branch

# GitHub repo pushed
https://github.com/guglxni/amiyc-hackathon
```

---

## 🎯 Next Steps (Manual - Subagents hit rate limits)

### Step 1: Fork & Configure (GitHub Web)
1. Go to: https://github.com/accomplish-ai/accomplish
2. Click "Fork" → Create fork under your account
3. Add remote to local repo:
```bash
cd /Volumes/MacExt/amiyc/oss-contributions/accomplish
git remote add myfork https://github.com/guglxni/accomplish.git
git remote -v
```

### Step 2: Launch Cline TUI
```bash
cd /Volumes/MacExt/amiyc/oss-contributions/accomplish
cline
```

### Step 3: Give Cline the Task
In Cline's prompt, paste:

```
Implement Dark Mode feature for accomplish following issue #373 requirements:

Requirements:
1. Create a theme system supporting light/dark modes
2. Add a settings toggle to control dark mode
3. Detect system preference (prefers-color-scheme)
4. Persist preference to electron-store
5. Apply theme across all UI components

Key files to examine:
- src/shared/styles/theme.ts
- src/renderer/theme.ts
- src/main/store/ (for persistence)
- Any existing theme/styling code

Color palette suggestion:
- Background: #1a1a1a
- Surface: #2d2d2d
- Primary: #6366f1
- Text: #f5f5f5
- Text Muted: #a1a1aa
- Border: #3f3f46

Use CSS variables or styled-components approach. Make sure all components respect the theme.

First, examine the current codebase structure, then implement the theme system.
```

### Step 4: Enable YOLO Mode for Speed
In Cline TUI:
- **Shift+Tab** → Enable "Auto-approve all"
- **Tab** → Switch to ACT mode (from PLAN)

---

## 🤖 Multi-Agent Strategy

### Terminal 1: Cline (Primary Developer)
```bash
cd /Volumes/MacExt/amiyc/oss-contributions/accomplish
checkout feature/dark-mode-373
cline
# Paste the prompt above
```

### Terminal 2: Kimi (Testing & Review)
```bash
# Test the implementation
kimi -y "Review the dark mode implementation in /Volumes/MacExt/amiyc/oss-contributions/accomplish and suggest improvements"
```

### Terminal 3: CharlieLabs (via GitHub)
1. Charlie will see commits on your fork
2. Review PR when created
3. Provide inline comments

---

## 📊 Progress Tracker

### Completed ✅
- [x] Cloned accomplish repo
- [x] Created feature/dark-mode-373 branch
- [x] Set up multi-agent workflow doc
- [x] Pushed to GitHub
- [x] Cline authenticated and working

### In Progress 🔄
- [ ] Fork accomplish to guglxni
- [ ] Implement Dark Mode theme system
- [ ] Test theme toggle

### Pending ⏳
- [ ] Push to fork
- [ ] Create PR
- [ ] CharlieLabs review
- [ ] Address feedback
- [ ] Submit to hackathon

---

## 🎨 Implementation Approach

### Option A: CSS Variables (Recommended)
```typescript
// theme.ts
export const themes = {
  light: {
    '--bg-primary': '#ffffff',
    '--bg-secondary': '#f5f5f5',
    '--text-primary': '#171717',
    // ...
  },
  dark: {
    '--bg-primary': '#1a1a1a',
    '--bg-secondary': '#2d2d2d',
    '--text-primary': '#f5f5f5',
    // ...
  }
}
```

### Option B: Styled-Components ThemeProvider
```typescript
// If using styled-components
import { ThemeProvider } from 'styled-components'

const darkTheme = {
  background: '#1a1a1a',
  surface: '#2d2d2d',
  // ...
}
```

---

## 🧪 Testing Checklist

Run tests after Cline implements:
- [ ] Theme toggle works in Settings
- [ ] Persists after app restart
- [ ] Respects system preference on first launch
- [ ] All components switch correctly
- [ ] No visual glitches or flickering
- [ ] Accessibility contrast ratios pass

---

## 📝 Commit Strategy

```bash
# After Cline makes changes:
git add -A
git commit -m "feat: add dark mode support (#373)

- Add theme provider with light/dark modes
- Implement settings toggle
- Add system preference detection
- Persist preference to electron-store
- Apply theme across UI components

Closes #373"

git push myfork feature/dark-mode-373
```

---

## 🏆 Hackathon Submission

After PR is merged (or created):
1. Screenshot the PR
2. Document contribution in README
3. Add to HACKATHON_SUBMISSION.md
4. Submit to WeMakeDevs PR track

---

## 🛟 Troubleshooting

### Cline not responding?
- Check Cline TUI is open
- Use `cline task new "restart"` if stuck

### Theme not applying?
- Check CSS specificity
- Ensure ThemeProvider wraps app

### Charlie not reviewing?
- Add @CharlieHelps to PR description
- Post update on dashboard.charlielabs.ai

---

*Ready to start! Launch Cline and paste the prompt.*
