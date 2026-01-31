import os
import json
import time
import requests
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id

# =====================
# ENVIRONMENT
# =====================
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"  # Cell to store last webhook message ID

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
        "color": 0x3498db,  # blue
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [],
        "footer": {"text": "Auto-updates every 5 minutes"},
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
# WEBHOOK SENDER
# =====================
def send_webhook(embed):
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    for attempt in range(5):
        try:
            r = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
            if r.status_code in (200, 201):
                data = r.json()
                return data["id"]
            elif r.status_code == 204:
                # Success but no content
                return None
            else:
                print(f"❌ Discord API error {r.status_code}: {r.text}")
        except Exception as e:
            print("❌ Exception during webhook send:", e)
        time.sleep(2)
    raise RuntimeError("❌ Failed to send after 5 retries")

# =====================
# MAIN
# =====================
def main():
    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows or len(rows) < 2:
        print("⚠️ No sheet data")
        return

    embed = build_embed(rows)

    # Send new webhook message every time
    new_msg_id = send_webhook(embed)

    # Store last webhook message ID in sheet
    if new_msg_id:
        write_message_id(SPREADSHEET_SHEET, new_msg_id, cell=STATE_CELL)
        print(f"✅ Webhook posted: {new_msg_id}")
    else:
        print("✅ Webhook posted (no ID returned)")

if __name__ == "__main__":
    main()
