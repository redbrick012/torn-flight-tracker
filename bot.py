import os
import json
import time
import requests
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id, read_message_id

# =====================
# ENV
# =====================
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"  # cell to store Discord message ID

if not WEBHOOK_URL:
    raise RuntimeError("❌ DISCORD_WEBHOOK_URL not set")

# =====================
# FLAGS
# =====================
COUNTRY_EMOJIS = {
    "Torn": "<:city:1458205750617833596>",
    "Mexico": "<:mx:1458203844474572801>",
    "Cayman Islands": "<:ky:1458203876544221459>",
    "Canada": "<:ca:1458204026813415517>",
    "Hawaii": "<:ushi:1458203802342522981>",
    "United Kingdom": "<:gb:1458203934647910441>",
    "Argentina": "<:ar:1458204051970986170>",
    "Switzerland": "<:ch:1458203997964861590>",
    "Japan": "<:jp:1458203900594094270>",
    "China": "<:cn:1458203968059474042>",
    "UAE": "<:ae:1458203747749728610>",
    "South Africa": "<:za:1458204114524569640>",
}

def country_emoji(country: str) -> str:
    return COUNTRY_EMOJIS.get(country, "🌍")

# =====================
# EMBED BUILDER
# =====================
def build_embed(rows):
    embed = {
        "title": "✈️ Smugglers Flight Paths",
        "color": 3447003,  # blue
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [],
        "footer": {"text": "Auto-updates every 5 minutes"}
    }

    sorted_rows = sorted(
        rows[2:],  # skip headers
        key=lambda r: r[0].lower() if len(r) > 0 and r[0] else ""
    )

    for row in sorted_rows:
        if len(row) < 7:
            continue

        dest, outb, inbound, returning, purch, travsug, icc = row[:7]

        outb = outb or "-"
        inbound = inbound or "-"
        returning = returning or "-"
        purch = purch or "-"
        icc = icc or ""

        flag = country_emoji(dest)

        embed["fields"].append({
            "name": f"{flag}{icc} {dest}",
            "value": f"🛫 Out: **{outb}** 🛬 In: **{inbound}** ↩ Return: **{returning}**\n📦 Item: **{purch}**",
            "inline": False
        })

    return embed

# =====================
# MESSAGE POST/EDIT
# =====================
def send_webhook(embed):
    """Send or edit message via webhook, retrying if needed."""
    message_id = read_message_id(SPREADSHEET_SHEET, STATE_CELL)
    payload = {"embeds": [embed]}

    headers = {"Content-Type": "application/json"}

    for attempt in range(5):
        try:
            if message_id:
                url = f"{WEBHOOK_URL}/messages/{message_id}"
                r = requests.patch(url, headers=headers, json=payload)
                if r.status_code == 404:
                    print("⚠️ Edit failed (404), posting new message")
                    message_id = None
                    continue
                elif r.status_code >= 400:
                    print(f"❌ Discord API error {r.status_code}: {r.text}")
                    time.sleep(2)
                    continue
                print("🔁 Webhook message updated")
                return message_id
            else:
                r = requests.post(WEBHOOK_URL, headers=headers, json=payload)
                if r.status_code >= 400:
                    print(f"❌ Discord API error {r.status_code}: {r.text}")
                    time.sleep(2)
                    continue
                data = r.json()
                message_id = data["id"]
                write_message_id(SPREADSHEET_SHEET, message_id, STATE_CELL)
                print("🆕 New webhook message posted")
                return message_id
        except Exception as e:
            print("❌ Exception during webhook update:", e)
            time.sleep(2)

    raise RuntimeError("❌ Failed to send after 5 retries")

# =====================
# MAIN
# =====================
def main():
    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows or len(rows) < 2:
        print("⚠️ Sheet empty, skipping update")
        return

    embed = build_embed(rows)
    send_webhook(embed)

if __name__ == "__main__":
    main()
