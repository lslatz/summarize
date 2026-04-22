#!/usr/bin/env python3
"""Patch upload dates into markdown files using yt-dlp.

Usage:
  python patch-dates.py                 # Patch all files
  python patch-dates.py dwarkesh        # Patch one channel by ID
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

def get_video_date(video_url):
    """Get upload date for a single video using yt-dlp."""
    try:
        cmd = [
            "yt-dlp",
            "-j",
            "--no-warnings",
            "--skip-download",
            video_url
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                upload_date = data.get('upload_date')
                if upload_date:
                    # yt-dlp returns date as YYYYMMDD
                    return f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            except json.JSONDecodeError:
                pass
        
        return ""
    except Exception:
        return ""

def patch_markdown_file(md_file):
    """Add dates to videos in a markdown file."""
    if not md_file.exists():
        return 0, 0, 0
    
    content = md_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    patched = 0
    skipped = 0
    already_have = 0
    total = 0
    start_time = time.time()
    
    new_lines = []
    for line in lines:
        # Check if this is a table row with a URL
        if '| https://youtube.com/watch?v=' in line:
            # Parse the row: | # | Title | Date | URL |
            parts = [p.strip() for p in line.split('|')]
            
            if len(parts) >= 5:
                idx = parts[1]        # #
                title = parts[2]      # Title
                date_cell = parts[3]  # Date (should be empty)
                url = parts[4]        # URL
                
                # Check if date column is empty
                if date_cell == '':
                    total += 1
                    elapsed = time.time() - start_time
                    rate = total / max(elapsed, 0.1)
                    remaining = int((total / rate - elapsed)) if rate > 0 else 0
                    pct = int(total / 101 * 100) if total <= 101 else 100
                    
                    print(f"      [{pct:3d}%] {idx:3s}: {title[:32]:<32}", end=" ", flush=True)
                    date = get_video_date(url)
                    
                    if date:
                        # Rebuild row with date in correct position
                        new_line = f"| {idx} | {title} | {date} | {url} |"
                        new_lines.append(new_line)
                        patched += 1
                        print(f"✓ {date} ETA: {remaining}s")
                    else:
                        # Keep original row
                        new_lines.append(line)
                        skipped += 1
                        print(f"⚠ ETA: {remaining}s")
                    
                    # Rate limiting
                    time.sleep(3)
                else:
                    # Already has a date (skip)
                    already_have += 1
                    new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write back with UTF-8
    new_content = '\n'.join(new_lines)
    md_file.write_text(new_content, encoding='utf-8')
    
    return patched, skipped, already_have

def main():
    # Get list of markdown files
    md_dir = Path("stuff-to-summarize")
    if not md_dir.exists():
        print("✗ stuff-to-summarize/ not found")
        return
    
    # Load feeds.json to map filenames to channel IDs
    feeds_path = Path("feeds.json")
    if not feeds_path.exists():
        print("✗ feeds.json not found")
        return
    
    with open(feeds_path) as f:
        feeds = json.load(f)
    
    # Get channel ID from args (optional)
    channel_id = sys.argv[1].lower() if len(sys.argv) > 1 else None
    
    # Find matching channels
    if channel_id == "all":
        channels = feeds['channels']
    elif channel_id:
        channels = [ch for ch in feeds['channels'] if ch['id'] == channel_id]
        if not channels:
            print(f"✗ Channel '{channel_id}' not found")
            return
    else:
        channels = feeds['channels']
    
    print(f"Patching dates for {len(channels)} channel(s)...\n")
    
    total_patched = 0
    total_skipped = 0
    total_already = 0
    
    for channel in channels:
        name = channel['name']
        md_file = md_dir / channel['markdown_file']
        
        if not md_file.exists():
            print(f"  {name}... ⚠ file not found")
            continue
        
        print(f"  {name}...")
        patched, skipped, already_have = patch_markdown_file(md_file)
        
        total_patched += patched
        total_skipped += skipped
        total_already += already_have
        
        if patched > 0 or skipped > 0:
            print(f"    → {patched} patched, {skipped} skipped, {already_have} already have dates\n")
        elif already_have > 0:
            print(f"    → all {already_have} videos already dated\n")
        else:
            print(f"    → (no videos)\n")
    
    print(f"{'='*60}")
    print(f"Patched: {total_patched} (newly found dates)")
    print(f"Skipped: {total_skipped} (couldn't find dates)")
    print(f"Already dated: {total_already}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
