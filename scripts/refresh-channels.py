#!/usr/bin/env python3
"""Refresh channels with latest videos from YouTube.

Usage:
  python refresh-channels.py                 # List all channels
  python refresh-channels.py dwarkesh        # Refresh one channel by ID
  python refresh-channels.py all             # Refresh all channels
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_latest_date_from_file(md_file):
    """Extract the most recent date from the markdown file."""
    if not md_file.exists():
        return None
    
    try:
        content = md_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            # Look for: | # | Title | Date | URL |
            if '| https://youtube.com/watch?v=' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5 and parts[3]:  # Has a date
                    try:
                        return datetime.strptime(parts[3], '%Y-%m-%d')
                    except ValueError:
                        pass
        return None
    except:
        return None

def get_channel_videos_until_duplicate(channel_url, existing_urls):
    """Fetch videos from channel until we find one we already have."""
    try:
        cmd = [
            "yt-dlp",
            "-j",
            "--flat-playlist",
            "--playlist-end", "100",
            channel_url + "/videos",  # only the Videos tab, not Shorts
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return []
        
        videos = []
        consecutive_duplicates = 0
        checked = 0
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                title = data.get('title', 'Unknown')
                video_id = data.get('id')
                
                if video_id:
                    checked += 1
                    url = f"https://youtube.com/watch?v={video_id}"
                    
                    # Show progress every 5 videos
                    if checked % 5 == 0:
                        title_preview = title[:40].replace('\n', ' ') + ('...' if len(title) > 40 else '')
                        print(f"[{checked}]", end=" ", flush=True)
                    
                    # If we find a video we already have, stop fetching
                    if url in existing_urls:
                        consecutive_duplicates += 1
                        if consecutive_duplicates >= 2:  # Stop after 2 duplicates in a row
                            break
                    else:
                        consecutive_duplicates = 0
                        videos.append({'title': title, 'url': url})
            except json.JSONDecodeError:
                continue
        
        return videos  # YouTube returns newest first, so newest at top
    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        return []

def update_markdown_file(md_file, channel_name, videos):
    """Update markdown file, appending new videos at bottom with stable IDs."""
    if not videos:
        return 0, 0
    
    # Load old file to preserve dates and existing IDs
    old_entries = {}  # url -> (id, title, date)
    max_id = 0
    if md_file.exists():
        try:
            old_content = md_file.read_text(encoding='utf-8')
            for line in old_content.split('\n'):
                if '| https://youtube.com/watch?v=' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 5:
                        try:
                            vid_id = int(parts[1])
                            url = parts[4]
                            title = parts[2]
                            date = parts[3]
                            if url:
                                old_entries[url] = (vid_id, title, date)
                                max_id = max(max_id, vid_id)
                        except ValueError:
                            pass
        except:
            pass
    
    # Build markdown: old videos first (with IDs and dates), then new videos (with next IDs, no dates)
    header = f"# {channel_name}\n\n| # | Title | Date | URL |\n|---|-------|------|-----|\n"
    rows = []
    
    # Add old videos first (preserve their IDs and dates)
    for url, (vid_id, title, date) in old_entries.items():
        row = f"| {vid_id} | {title} | {date} | {url} |"
        rows.append(row)
    
    # Add new videos at bottom (with next sequential IDs, no dates yet)
    next_id = max_id + 1
    for video in videos:
        title = video['title'].replace('|', '\\|')
        row = f"| {next_id} | {title} |  | {video['url']} |"
        rows.append(row)
        next_id += 1
    
    content = header + "\n".join(rows) + "\n"
    md_file.write_text(content, encoding='utf-8')
    
    return len(videos), len(old_entries)

def main():
    # Load feeds.json
    feeds_path = Path("feeds.json")
    if not feeds_path.exists():
        print("✗ feeds.json not found")
        return
    
    with open(feeds_path) as f:
        feeds = json.load(f)
    
    # Get channel ID from args
    if len(sys.argv) < 2:
        # List all channels
        print("Available channels:\n")
        for ch in feeds['channels']:
            print(f"  {ch['id']:<20} {ch['name']}")
        print(f"\nUsage: python refresh-channels.py <channel-id|all>")
        return
    
    channel_id = sys.argv[1].lower()
    
    # Find matching channels
    if channel_id == "all":
        channels = feeds['channels']
    else:
        channels = [ch for ch in feeds['channels'] if ch['id'] == channel_id]
        if not channels:
            print(f"✗ Channel '{channel_id}' not found")
            return
    
    # Ensure stuff-to-summarize exists
    Path("stuff-to-summarize").mkdir(exist_ok=True)
    
    print(f"Refreshing {len(channels)} channel(s)...\n")
    
    total_new = 0
    total_existing = 0
    updated = 0
    
    for channel in channels:
        name = channel['name']
        url = channel['url']
        md_file = Path("stuff-to-summarize") / channel['markdown_file']
        
        # Load existing URLs to know when to stop fetching
        existing_urls = set()
        if md_file.exists():
            try:
                content = md_file.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if '| https://youtube.com/watch?v=' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 5:
                            existing_urls.add(parts[4])
            except:
                pass
        
        print(f"  {name}...", end=" ", flush=True)
        sys.stdout.flush()
        videos = get_channel_videos_until_duplicate(url, existing_urls)
        
        if videos:
            new_count, old_count = update_markdown_file(md_file, name, videos)
            total_new += new_count
            total_existing += old_count
            updated += 1
            if new_count > 0:
                print(f"✓ {new_count} new, {old_count} existing")
            else:
                print(f"✓ (no new videos)")
        else:
            print(f"✓ (up to date)")
    
    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(channels)} channels")
    if total_new > 0:
        print(f"New videos: {total_new} (run: patch-dates.py)")
        print(f"Total in queue: {total_new + total_existing}")
    else:
        print(f"All channels up to date")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
