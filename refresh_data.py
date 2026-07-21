#!/usr/bin/env python3
"""
Fetch the Wikimania 2026 schedule from eventyay and save it as wikimania2026_data.js.

Usage:
    python3 refresh_data.py          # fetch and save
    python3 refresh_data.py --dry-run  # print stats only, don't write
"""

import json
import sys
import os
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from collections import OrderedDict

SCHEDULE_URL = "https://wikimedia.eventyay.com/wm/wikimania2026/schedule/export/schedule.json"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wikimania2026_data.js")
USER_AGENT = "WikimaniaScheduleExplorer/1.0 (https://github.com/fuzheado/wikimania-2026)"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_LABELS = {
    "2026-07-21": "Tue 21 Jul",
    "2026-07-22": "Wed 22 Jul",
    "2026-07-23": "Thu 23 Jul",
    "2026-07-24": "Fri 24 Jul",
    "2026-07-25": "Sat 25 Jul",
}


def day_label(date_str):
    """Convert '2026-07-21' → 'Tue 21 Jul'."""
    if date_str in DAY_LABELS:
        return DAY_LABELS[date_str]
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{DAY_NAMES[dt.weekday()]} {dt.day} {dt.strftime('%b')}"
    except ValueError:
        return date_str


def fetch_schedule():
    """Fetch and parse the eventyay schedule JSON."""
    req = Request(SCHEDULE_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=30) as resp:
            source = json.load(resp)
    except HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    conference = source["schedule"]["conference"]
    return conference


def transform(conference):
    """Transform eventyay schedule into the WIKIMANIA_DATA format."""
    sessions = []
    tracks = set()
    types = set()
    languages = set()
    rooms = set()
    days = []

    for day in conference["days"]:
        date_str = day["date"]
        days.append({
            "value": date_str,
            "label": day_label(date_str),
        })

        for room_name, room_talks in day["rooms"].items():
            rooms.add(room_name)

            for talk in room_talks:
                # --- Extract track ---
                track = (talk.get("track") or {}).get("en") if isinstance(talk.get("track"), dict) else talk.get("track")
                if not track:
                    track = "Unspecified"
                tracks.add(track)

                # --- Extract type ---
                stype = (talk.get("type") or {}).get("en") if isinstance(talk.get("type"), dict) else talk.get("type")
                if stype:
                    types.add(stype)
                else:
                    stype = talk.get("type", "")

                # --- Language ---
                lang = (talk.get("language") or "en").lower()
                languages.add(lang)

                # --- Speakers ---
                speakers = []
                for person in talk.get("persons", []):
                    speakers.append({
                        "name": person.get("public_name") or person.get("name", ""),
                        "bio": person.get("biography", ""),
                        "url": person.get("url", ""),
                    })

                # --- Duration ---
                duration = talk.get("duration", "")
                # Convert "00:30" → "00:30"
                if duration and ":" not in str(duration):
                    mins = int(duration)
                    h, m = divmod(mins, 60)
                    duration = f"{h:02d}:{m:02d}"

                session = {
                    "id": talk["id"],
                    "title": talk.get("title", ""),
                    "track": track,
                    "type": stype,
                    "language": lang,
                    "room": room_name.replace("\U0001f310", "🌐"),  # normalize globe emoji
                    "day": date_str,
                    "start": talk.get("start", ""),
                    "duration": duration,
                    "abstract": talk.get("abstract") or talk.get("description", ""),
                    "recorded": not talk.get("do_not_record", False),
                    "url": talk.get("url", ""),
                    "speakers": speakers,
                    "day_label": day_label(date_str),
                }
                sessions.append(session)

    filters = {
        "tracks": sorted(tracks),
        "days": days,
        "languages": sorted(languages),
        "types": sorted(types),
        "rooms": sorted(rooms),
    }

    return {"sessions": sessions, "filters": filters}


def format_js(data, pretty=True):
    """Format the data as window.WIKIMANIA_DATA = {...};"""
    inner = json.dumps(data, ensure_ascii=False, separators=(",", ":") if not pretty else None)
    if pretty:
        inner = json.dumps(data, ensure_ascii=False, indent=2)
    return f"window.WIKIMANIA_DATA = {inner};"


def main():
    dry_run = "--dry-run" in sys.argv

    print("Fetching schedule from eventyay…")
    conference = fetch_schedule()

    print("Transforming data…")
    data = transform(conference)

    print(f"  Days:      {len(data['filters']['days'])}")
    print(f"  Sessions:  {len(data['sessions'])}")
    print(f"  Tracks:    {len(data['filters']['tracks'])}")
    print(f"  Types:     {len(data['filters']['types'])}")
    print(f"  Languages: {data['filters']['languages']}")
    print(f"  Rooms:     {len(data['filters']['rooms'])}")

    if dry_run:
        print("\n--dry-run: not writing file.")
        return

    js = format_js(data)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js)
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\nWritten {len(js):,} bytes ({size_kb:.0f} KB) → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
