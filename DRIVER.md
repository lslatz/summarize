# Summarize Hub – Driver

**Last updated:** April 20, 2026  
**Status:** Live & Optimized

## Your Setup

### Channels (stuff-to-summarize/)
**10 curated channels, 650+ videos, all dated (YYYY-MM-DD format)**

| Channel | Count | Status |
|---------|-------|--------|
| Dwarkesh Patel Podcast | 101 | ✅ Dated |
| Simnett Nutrition | 78 | ✅ Dated |
| PlantStrong Podcast | 149 | ✅ Dated |
| Plant-Based with Jane Esselstyn | 100 | ✅ Dated |
| No Priors Podcast | 59 | ✅ Dated |
| Lex Fridman Podcast | 10 | ✅ Dated |
| Joel Fuhrman | 87 | ✅ Dated |
| Derek Sarno Chef | 91 | ✅ Dated |
| NutritionFacts (Dr. Greger) | 50 | ✅ Dated |
| Rich Roll | 50 | ✅ Dated |

**To add a new channel:** `/add-channel ChannelName` (Copilot slash command)

---

## Workflow

### 1. Refresh Videos (Optional)
Keep channels up to date with latest from YouTube:
```bash
python refresh-channels.py               # List available channels
python refresh-channels.py dwarkesh      # Refresh one channel
python refresh-channels.py all           # Refresh all channels
```
**Smart:** Preserves existing dates when merging new videos.

### 2. Patch Missing Dates (Optional)
If you refresh and get new videos without dates:
```bash
python patch-dates.py dwarkesh           # Patch one channel (shows progress %)
python patch-dates.py all                # Patch all (skips already-dated)
```
**Smart:** Only fetches missing dates, shows ETA, skips videos that already have dates.

### 3. Browse
Open any `*.md` file in `stuff-to-summarize/`. Find something interesting. Copy the URL.

### 4. Summarize
```bash
pnpm summarize "https://youtube.com/watch?v=Hrbq66XqtCo"
```

### 5. Read
Summary lands in `summaries/{channel-name}/`. Organized by source.

---

## Key Files

| File | Purpose |
|------|---------|
| `SUMMARIZE-SYSTEM.md` | Philosophy & system design |
| `stuff-to-summarize/` | Your channel queue (you maintain) |
| `summaries/` | Auto-created, holds all summaries |
| `pnpm summarize` | Your one tool |

---

## Slash Commands

| Command | What it does |
|---------|------------|
| `/add-channel ChannelName` | Fetch channel, create markdown, wire it up |

---

## Stats

- **Channels:** 11
- **Total videos queued:** 491+
- **All videos:** Dated (YYYY-MM-DD format)
- **Summaries generated:** Ready when you need them

---

## Next Steps

- Start summarizing from your queue: `pnpm summarize "URL"`
- Add new channels as you find them: `/add-channel`
- Summaries auto-organize by source

---

## Philosophy

**One tool. No complexity. Your inputs, your control.**

## Channel Video Counts

- **Dwarkesh Patel Podcast**: 101 videos
- **Simnett Nutrition**: 116 videos
- **PlantStrong Podcast**: 150 videos
- **Plant-Based with Jane Esselstyn and Ann Esselstyn**: 102 videos
- **No Priors Podcast**: 100 videos
- **Lex Fridman Podcast**: 61 videos
- **Joel Fuhrman**: 0 videos
- **Derek Sarno Chef**: 100 videos
- **NutritionFacts (Dr. Michael Greger)**: 50 videos
- **Rich Roll**: 50 videos

**Total**: 830 videos

**Last updated**: April 20, 2026
