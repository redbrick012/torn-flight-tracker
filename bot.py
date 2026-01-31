import os
import json
import requests
from datetime import datetime, timezone

from sheets import get_sheet_values, write_message_id

# =====================
# ENV
# =====================
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"  # Where to store the last Discord message ID

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
        "color": 0x3498db,  # Blue
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
# WEBHOOK POST/EDIT
# =====================
def send_webhook(embed, message_id=None):
    payload = {"embeds": [embed]}
    url = WEBHOOK_URL
    headers = {"Content-Type": "application/json"}

    # Edit existing message if message_id is provided
    if message_id:
        r = requests.patch(f"{WEBHOOK_URL}/messages/{message_id}", json=payload, headers=headers)
        if r.status_code == 404:
            print("⚠️ Edit failed (404), will post new message")
        elif not (200 <= r.status_code < 300):
            raise RuntimeError(f"❌ Discord API error {r.status_code}: {r.text}")
        else:
            return message_id

    # Post new message
    r = requests.post(url, json=payload, headers=headers)
    if not (200 <= r.status_code < 300):
        raise RuntimeError(f"❌ Discord API error {r.status_code}: {r.text}")
    data = r.json()
    return data["id"]

# =====================
# MAIN
# =====================
def main():
    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows or len(rows) < 2:
        print("⚠️ No sheet data")
        return

    embed = build_embed(rows)

    # Retrieve last message ID from sheet
    last_msg_id = rows[0][0] if rows[0] else None
    try:
        new_msg_id = send_webhook(embed, message_id=last_msg_id)
        write_message_id(SPREADSHEET_SHEET, new_msg_id, cell=STATE_CELL)
        print(f"✅ Updated webhook message: {new_msg_id}")
    except Exception as e:
        print("❌ Exception during webhook update:", e)

if __name__ == "__main__":
    main()
