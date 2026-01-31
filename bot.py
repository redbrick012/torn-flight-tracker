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
STATE_CELL = "A1"  # where we store the last message ID

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
# BUILD EMBED
# =====================
def build_payload(rows):
    """Returns JSON payload for Discord webhook."""
    embed = {
        "title": "✈️ Smugglers Flight Paths",
        "color": 3447003,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [],
        "footer": {"text": "Auto-updates every 5 minutes"}
    }

    for row in rows[2:]:  # skip headers
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
    return {"embeds": [embed]}

# =====================
# SEND / EDIT MESSAGE
# =====================
def send_flight_update():
    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows or len(rows) < 2:
        print("⚠️ Sheet empty, nothing to send")
        return

    payload = build_payload(rows)
    # Read last message ID from sheet
    last_message_id = rows[0][0] if rows[0] else None

    try:
        if last_message_id:
            # Try to edit existing webhook message
            r = requests.patch(
                f"{WEBHOOK_URL}/messages/{last_message_id}",
                json=payload
            )
            if r.status_code == 404:
                print("⚠️ Previous message not found, posting new message")
                last_message_id = None
            elif r.status_code >= 400:
                print(f"❌ Discord API error {r.status_code}: {r.text}")
                last_message_id = None
            else:
                print("🔁 Edited existing message")
                return
        # Post new message if needed
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code in (200, 204):
            msg_id = r.json()["id"]
            write_message_id(SPREADSHEET_SHEET, msg_id, cell=STATE_CELL)
            print("🆕 Posted new message")
        else:
            print(f"❌ Discord API error {r.status_code}: {r.text}")
    except Exception as e:
        print("❌ Exception during webhook update:", e)

# =====================
# RUN
# =====================
if __name__ == "__main__":
    send_flight_update()
