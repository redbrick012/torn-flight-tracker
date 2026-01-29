import os
import requests
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = os.environ["FLIGHT_CHANNEL_ID"]
SHEET_NAME = os.environ.get("FLIGHT_SHEET", "travelDestinations")

DISCORD_API = "https://discord.com/api/v10"

HEADERS = {
    "Authorization": f"Bot {DISCORD_TOKEN}",
    "Content-Type": "application/json"
}

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

def country_emoji(country):
    return COUNTRY_EMOJIS.get(country, "🌍")

def build_embed(rows):
    embed = {
        "title": "✈️ Smugglers Flight Paths",
        "color": 3447003,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Auto-updates every 5 minutes"},
        "fields": []
    }

    for row in sorted(rows[2:], key=lambda r: r[0].lower() if r and r[0] else ""):
        if len(row) < 7:
            continue

        dest, outb, inbound, returning, purch, travsug, icc = row[:7]

        field = {
            "name": f"{country_emoji(dest)}{icc or ''} {dest}",
            "value": (
                f"🛫 Out: **{outb or '-'}** "
                f"🛬 In: **{inbound or '-'}** "
                f"↩ Return: **{returning or '-'}**\n"
                f"📦 Item: **{purch or '-'}**"
            ),
            "inline": False
        }

        embed["fields"].append(field)

    return embed

def main():
    rows = get_sheet_values(SHEET_NAME)

    message_id = None
    if rows and rows[0] and rows[0][0].isdigit():
        message_id = rows[0][0]

    embed = build_embed(rows)

    payload = {"embeds": [embed]}

    if message_id:
        r = requests.patch(
            f"{DISCORD_API}/channels/{CHANNEL_ID}/messages/{message_id}",
            headers=HEADERS,
            json=payload
        )

        if r.status_code == 200:
            print("✅ Updated embed")
            return
        else:
            print("⚠️ Failed to edit, posting new")

    r = requests.post(
        f"{DISCORD_API}/channels/{CHANNEL_ID}/messages",
        headers=HEADERS,
        json=payload
    )

    r.raise_for_status()
    new_id = r.json()["id"]
    write_message_id(SHEET_NAME, new_id)

    print(f"🆕 Posted new embed {new_id}")

if __name__ == "__main__":
    main()
