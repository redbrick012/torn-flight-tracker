import os
import requests
from datetime import datetime, timezone

from sheets import get_sheet_values, write_message_id

# =====================
# ENV
# =====================
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
FLIGHT_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"  # where message_id is stored in the sheet

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
    fields = []

    sorted_rows = sorted(
        rows[2:],  # skip state + headers
        key=lambda r: r[0].lower() if r and r[0] else ""
    )

    for row in sorted_rows:
        if len(row) < 7:
            continue

        dest, outb, inbound, returning, purch, travsug, icc = row[:7]

        fields.append({
            "name": f"{country_emoji(dest)}{icc or ''} {dest}",
            "value": (
                f"🛫 Out: **{outb or '-'}** "
                f"🛬 In: **{inbound or '-'}** "
                f"↩ Return: **{returning or '-'}**\n"
                f"📦 Item: **{purch or '-'}**"
            ),
            "inline": False
        })

    return {
        "title": "✈️ Smugglers Flight Paths",
        "color": 0x3498DB,
        "fields": fields,
        "footer": {"text": "Auto-updates every 5 minutes"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# =====================
# MAIN
# =====================
def main():
    rows = get_sheet_values(FLIGHT_SHEET)

    if not rows or len(rows) < 3:
        print("⚠️ Sheet empty or invalid")
        return

    embed = build_embed(rows)
    payload = {"embeds": [embed]}

    # Read stored message ID
    message_id = rows[0][0] if rows[0] else None

    # Try EDIT first
    if message_id:
        edit_url = f"{DISCORD_WEBHOOK_URL}/messages/{message_id}"
        r = requests.patch(edit_url, json=payload, timeout=10)

        if r.status_code == 200:
            print("🔁 Webhook message updated")
            return

        print(f"⚠️ Edit failed ({r.status_code}), posting new message")

    # POST new message
    r = requests.post(
        DISCORD_WEBHOOK_URL,
        json=payload,
        timeout=10
    )

    if r.status_code != 200:
        raise RuntimeError(f"❌ Webhook post failed: {r.status_code} {r.text}")

    new_message_id = r.json()["id"]
    write_message_id(FLIGHT_SHEET, new_message_id, cell=STATE_CELL)

    print(f"🆕 New webhook message posted ({new_message_id})")

# =====================
# RUN
# =====================
if __name__ == "__main__":
    main()
