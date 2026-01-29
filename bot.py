import os
import requests
from datetime import datetime, timezone
from sheets import get_sheet_values, set_message_id

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = os.environ["FLIGHT_CHANNEL_ID"]
SHEET_NAME = os.environ.get("FLIGHT_SHEET", "travelDestinations")

API_BASE = "https://discord.com/api/v10"

COUNTRY_EMOJIS = {
    "Torn": "🏙️",
    "Mexico": "🇲🇽",
    "Cayman Islands": "🇰🇾",
    "Canada": "🇨🇦",
    "Hawaii": "🇺🇸",
    "United Kingdom": "🇬🇧",
    "Argentina": "🇦🇷",
    "Switzerland": "🇨🇭",
    "Japan": "🇯🇵",
    "China": "🇨🇳",
    "UAE": "🇦🇪",
    "South Africa": "🇿🇦",
}

def country_emoji(country: str) -> str:
    return COUNTRY_EMOJIS.get(country, "🌍")

def build_embed(rows):
    fields = []
    sorted_rows = sorted(rows[2:], key=lambda r: r[0].lower() if r and r[0] else "")
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
        "color": 3447003,
        "fields": fields,
        "footer": {"text": "Auto-updates every 5 minutes"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def discord_headers():
    return {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}

def edit_message(message_id, embed):
    url = f"{API_BASE}/channels/{CHANNEL_ID}/messages/{message_id}"
    r = requests.patch(url, json={"embeds": [embed]}, headers=discord_headers())
    return r.status_code == 200

def post_message(embed):
    url = f"{API_BASE}/channels/{CHANNEL_ID}/messages"
    r = requests.post(url, json={"embeds": [embed]}, headers=discord_headers())
    r.raise_for_status()
    return r.json()["id"]

def main():
    rows = get_sheet_values(SHEET_NAME)
    stored_message_id = rows[0][0] if rows and rows[0] else None
    embed = build_embed(rows)
    if stored_message_id:
        success = edit_message(stored_message_id, embed)
        if success:
            print("✅ Updated existing message")
            return
        else:
            print("⚠️ Stored message missing, posting new")
    new_id = post_message(embed)
    set_message_id(new_id, SHEET_NAME)
    print(f"🆕 Posted new message: {new_id}")

if __name__ == "__main__":
    main()
