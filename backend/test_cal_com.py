#!/usr/bin/env python3
"""Standalone smoke test for the cal.com slot-lookup wrapper.

Usage (from backend/):
    python test_cal_com.py                        # default: 14 days
    python test_cal_com.py --days 3               # next 3 days only
    python test_cal_com.py --event-type-id 123    # specific event type

What it does:
    1. Loads CAL_COM_API_KEY, CAL_COM_USERNAME from .env
    2. Creates a CalComClient
    3. Calls get_slots(days=N)
    4. Pretty-prints the raw response so you can see the slot shape
"""

import json
import os
import sys

# Load .env manually (minimal — avoids requiring python-dotnet or similar).
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

# Parse CLI
DAYS = 14
EVENT_TYPE_ID = None
argv = sys.argv[1:]
i = 0
while i < len(argv):
    if argv[i] == "--days" and i + 1 < len(argv):
        DAYS = int(argv[i + 1])
        i += 2
    elif argv[i] == "--event-type-id" and i + 1 < len(argv):
        EVENT_TYPE_ID = int(argv[i + 1])
        i += 2
    else:
        i += 1

from api.integrations.cal_com_client import CalComClient

print("=" * 70)
print("Cal.com Slot Lookup — Live Smoke Test")
print("=" * 70)

# Check creds
api_key = os.getenv("CAL_COM_API_KEY", "")
username = os.getenv("CAL_COM_USERNAME", "")
if not api_key:
    print("\n❌ CAL_COM_API_KEY not found in .env")
    sys.exit(1)
if not username:
    print("\n❌ CAL_COM_USERNAME not found in .env")
    sys.exit(1)

print(f"\n  Username:      {username}")
print(f"  API key:       {api_key[:12]}...{api_key[-4:]}")
print(f"  Days to query: {DAYS}")
if EVENT_TYPE_ID:
    print(f"  Event type ID: {EVENT_TYPE_ID}")
print()

client = CalComClient(
    api_key=api_key,
    username=username,
    default_event_type_id=EVENT_TYPE_ID or 0,
)

try:
    slots = client.get_slots(
        event_type_id=EVENT_TYPE_ID,
        days=DAYS,
    )
except Exception as e:
    print(f"\n❌ Call failed: {e}")
    sys.exit(1)

if not slots:
    print("ℹ️  No slots returned (maybe no availability, or wrong event type ID).")
    sys.exit(0)

print(f"✅ Got slots for {len(slots)} date(s):\n")

for date_str in sorted(slots.keys()):
    day_slots = slots[date_str]
    print(f"  ── {date_str} ({len(day_slots)} slot(s)) ──")
    for s in day_slots:
        print(f"     ⏰ {s['start']}  →  {s['end']}")
        print(f"        🔗 {s['booking_url']}")
    print()

# Also dump the full structure as pretty JSON so you can see the shape.
print("─" * 70)
print("Full data structure (JSON):")
print("─" * 70)
print(json.dumps(slots, indent=2, default=str))

print(f"\n✅ Done — {sum(len(v) for v in slots.values())} total slots across {len(slots)} days.")
