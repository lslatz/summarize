# Summarize Hub – Copilot Instructions

## Core Rules

### Keep MD Files Clean
- NO code snippets, bash commands, or instructions in `stuff-to-summarize/` MD files
- Just: header and clean table (# | Title | URL)
- If there's a note to add, ask first
- Keep it minimal and visual

### One Tool, No Complexity
- User has one command: `pnpm summarize "URL"`
- No watch scripts, no batch runners, no automation scripts
- Simple, focused, builder style
- Avoid premature optimization

### Learn & Document Preferences
- When user says "I don't like X", note it and apply it going forward
- Update these instructions with their preferences
- Don't repeat mistakes

---

## Operations

### Add Channel
- Fetch YouTube channel videos (last 50)
- Create markdown file in `stuff-to-summarize/`
- Update DRIVER.md with stats
- Keep file clean (header + table only)

### Refresh Channels
- Refetch videos for existing channels
- Update markdown files
- Update DRIVER.md stats

### Summarize
- Run: `pnpm summarize "URL"`
- Auto-saves to `summaries/{channel-name}/`
- That's it

---

## Files to Maintain

- **feeds.json** — Channel registry (id, name, url, markdown_file mapping)
- **DRIVER.md** — Current state (channels, stats, next steps)
- **stuff-to-summarize/*.md** — Channel queues (clean tables only)
- **summaries/** — Output (auto-generated, organized by source)

**When adding/refreshing channels:**
1. Update feeds.json with channel info
2. Create/update markdown file in stuff-to-summarize/
3. Update DRIVER.md stats

---

## NO:
- Detours. No "nice-to-haves"
- Code in MD files
- Over-engineering
- Multi-step workflows
