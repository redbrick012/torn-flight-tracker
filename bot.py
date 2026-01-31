import os
import json
import requests
from datetime import datetime, timezone

from sheets import get_sheet_values

# =====================
# ENV
# =====================
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
FLIGHT_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")

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
        rows[2:],  # skip headers + state row
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

        fields.append({
            "name": f"{flag}{icc} {dest}",
            "value": (
                f"🛫 Out: **{outb}** "
                f"🛬 In: **{inbound}** "
                f"↩ Return: **{returning}**\n"
                f"📦 Item: **{purch}**"
            ),
            "inline": False
        })

    embed = {
        "title": "✈️ Smugglers Flight Paths",
        "color": 0x3498DB,
        "fields": fields,
        "footer": {
            "text": "Auto-updates every 5 minutes"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return embed

# =====================
# MAIN
# =====================
def main():
    rows = get_sheet_values(FLIGHT_SHEET)

    if not rows or len(rows) < 3:
        print("⚠️ Sheet empty or malformed")
        return

    embed = build_embed(rows)

    payload = {
        "embeds": [embed]
    }

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=payload,
        timeout=10
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"❌ Discord webhook failed: {response.status_code} {response.text}"
        )

    print("✅ Flight embed sent/updated successfully")

# =====================
# RUN
# =====================
if __name__ == "__main__":
    main()
