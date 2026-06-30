#!/usr/bin/env python3
"""
check_news.py — Brain News Gate Script

Reads brain_news.csv and determines:
  1. Whether the current week needs new news processing
  2. Which past articles have a review_date that's due today or earlier
     (meaning Claude should search for updates on those specific stories)

Outputs JSON to stdout so Claude Code can act on it.

Exit codes:
  0 — week already processed (SKIP), but Claude should still check pending_followups
  1 — week needs processing (PROCEED)
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

CSV_PATH = Path(__file__).parent / "brain_news.csv"


def get_week_bounds(date: datetime) -> tuple[str, str]:
    """Return (monday, sunday) of the given date's week as YYYY-MM-DD strings."""
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def load_csv() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    current_week_start, current_week_end = get_week_bounds(today)

    rows = load_csv()
    existing_urls = [row["url"] for row in rows if row.get("url")]
    weeks_already_processed = {row["week_start"] for row in rows if row.get("week_start")}

    already_done = current_week_start in weeks_already_processed

    # Find articles due for a follow-up search today or earlier.
    # review_date is set by Claude per article based on content
    # (e.g. "chip trial results expected in 10 weeks" → review_date = today + 70 days)
    # Group by notion_page so Claude knows which pages to update.
    followup_pages: dict[str, dict] = {}
    for row in rows:
        review_date = row.get("review_date", "").strip()
        if not review_date or review_date == "null":
            continue
        if review_date > today_str:
            continue  # not due yet

        page_id = row.get("notion_page_id", "").strip()
        if not page_id:
            continue

        if page_id not in followup_pages:
            followup_pages[page_id] = {
                "notion_page_id": page_id,
                "notion_page_title": row.get("notion_page_title", ""),
                "notion_page_url": row.get("notion_page_url", ""),
                "week_start": row.get("week_start", ""),
                "articles": [],
            }

        followup_pages[page_id]["articles"].append({
            "title": row.get("title", ""),
            "url": row.get("url", ""),
            "category": row.get("category", ""),
            "summary": row.get("summary", ""),
            "review_date": review_date,
        })

    result = {
        "should_process": not already_done,
        "week_start": current_week_start,
        "week_end": current_week_end,
        "existing_urls": existing_urls,
        "total_articles_in_db": len(rows),
        "weeks_processed": sorted(weeks_already_processed),
        # Articles due for a follow-up, grouped by their Notion page
        "pending_followups": list(followup_pages.values()),
    }

    print(json.dumps(result, indent=2))

    if already_done:
        print(f"\n[SKIP] Week {current_week_start} already processed.", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"\n[PROCEED] Week {current_week_start} needs new news.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
