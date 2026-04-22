#!/usr/bin/env python3
"""Convert all markdown files to standardized format.

Format: # Channel Name
        | # | Title | Date | URL |
        
(Simple: no metadata comments)
"""

import re
from pathlib import Path

def extract_channel_name(header_line):
    """Extract clean channel name from header."""
    # Remove markdown header and extras
    name = header_line.replace('#', '').strip()
    name = name.split(' – ')[0]  # Remove "– Recent YouTube Videos"
    return name

def convert_file(md_file):
    """Convert a markdown file to standard format."""
    try:
        content = md_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = md_file.read_text(encoding='latin-1')
        except:
            print(f"  ✗ {md_file.name}: encoding error")
            return False
    lines = content.split('\n')
    
    # Find channel name from first # header
    channel_name = None
    table_started = False
    table_rows = []
    
    for line in lines:
        # Skip empty lines and metadata comments
        if not line.strip() or line.startswith('*'):
            continue
        
        # Find channel name
        if line.startswith('# ') and not channel_name:
            channel_name = extract_channel_name(line)
            continue
        
        # Skip table header rows (contain ---)
        if '---' in line:
            table_started = True
            continue
        
        # Collect data rows
        if table_started and line.strip().startswith('|'):
            # Parse existing row: | # | Title | Date | URL | OR | # | Title | Date | URL |
            parts = [p.strip() for p in line.split('|')]
            
            # Filter out empty parts and reconstruct
            parts = [p for p in parts if p]  # Remove empty strings
            
            if len(parts) >= 4:
                # Assume: idx, title, (date), url
                # Try to identify which is which
                idx = parts[0]
                url = parts[-1] if parts[-1].startswith('http') else ''
                
                if url:
                    # Find date (YYYY-MM-DD format) and title (everything else)
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                    date = date_match.group() if date_match else ''
                    
                    # Title is whatever is between # and date or #  and URL
                    title_start = line.find('|', line.find('|') + 1) + 1
                    title_end = line.rfind('|') if date else line.rfind('|')
                    
                    # Extract title between the parts
                    if idx and url:
                        # Re-extract from original line more carefully
                        parts_orig = [p.strip() for p in line.split('|')]
                        # Remove leading/trailing empty parts
                        parts_orig = [p for p in parts_orig if p]
                        
                        if len(parts_orig) == 3:
                            # Format: # | Title | URL (no date yet)
                            idx, title, url = parts_orig[0], parts_orig[1], parts_orig[2]
                            date = ''
                        elif len(parts_orig) == 4:
                            # Format: # | Title | Date | URL
                            idx, title, date, url = parts_orig[0], parts_orig[1], parts_orig[2], parts_orig[3]
                        else:
                            continue
                        
                        # Build standard row
                        table_rows.append({
                            'idx': idx,
                            'title': title,
                            'date': date,
                            'url': url
                        })
    
    if not channel_name or not table_rows:
        print(f"  ✗ Could not parse {md_file.name}")
        return False
    
    # Build new file content
    new_content = f"# {channel_name}\n\n| # | Title | Date | URL |\n|---|-------|------|-----|\n"
    
    for row in table_rows:
        new_content += f"| {row['idx']} | {row['title']} | {row['date']} | {row['url']} |\n"
    
    # Write back with UTF-8
    md_file.write_text(new_content, encoding='utf-8')
    print(f"  ✓ {md_file.name}: {len(table_rows)} videos")
    return True

def main():
    md_dir = Path("stuff-to-summarize")
    if not md_dir.exists():
        print("✗ stuff-to-summarize/ not found")
        return
    
    print("Converting all markdown files to standard format...\n")
    
    md_files = sorted(md_dir.glob("*.md"))
    converted = 0
    
    for md_file in md_files:
        if convert_file(md_file):
            converted += 1
    
    print(f"\n{'='*60}")
    print(f"Converted: {converted}/{len(md_files)} files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
