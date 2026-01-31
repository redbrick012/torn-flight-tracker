import os
import json
import requests
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id

# =====================
# ENV
# =====================
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
FLIGHT_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"  # cell where message ID is stored
print("JSON length:", len(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")))

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
# UPDATE LOGIC
# =====================
def update_flight_message():
    rows = get_sheet_values(FLIGHT_SHEET)
    if not rows or len(rows) < 2:
        print("⚠️ Sheet empty")
        return

    embed = build_embed(rows)

    # Read message ID from sheet
    posted_message_id = rows[0][0] if rows[0] else None

    payload = {"embeds": [embed]}

    # Try edit first
    if posted_message_id:
        r = requests.patch(
            f"{DISCORD_WEBHOOK_URL}/messages/{posted_message_id}?wait=true",
            json=payload,
            timeout=10
        )
        if r.status_code == 404:
            print("⚠️ Edit failed (404), posting new message")
            posted_message_id = None
        elif not (200 <= r.status_code < 300):
            raise RuntimeError(f"❌ Webhook edit failed: {r.status_code} {r.text}")
        else:
            print(f"🔁 Webhook message {posted_message_id} edited successfully")
            return

    # Post new message
    r = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json=payload, timeout=10)
    if not (200 <= r.status_code < 300):
        raise RuntimeError(f"❌ Webhook post failed: {r.status_code} {r.text}")

    new_message_id = r.json()["id"]
    write_message_id(FLIGHT_SHEET, new_message_id, cell=STATE_CELL)
    print(f"🆕 New webhook message posted ({new_message_id})")

# =====================
# MAIN
# =====================
def main():
    update_flight_message()

if __name__ == "__main__":
    main()
