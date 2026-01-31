import os
import json
import time
import requests
from datetime import datetime, timezone
import gspread

# =====================
# ENV
# =====================
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_NAME = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"  # Where to store the Discord message ID
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

# =====================
# GOOGLE SHEETS SETUP
# =====================
SERVICE_ACCOUNT = json.loads(SERVICE_ACCOUNT_JSON)
gc = gspread.service_account_from_dict(SERVICE_ACCOUNT)
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.worksheet(SHEET_NAME)

def get_rows():
    return ws.get_all_values()

def write_message_id(message_id):
    # Must be list of lists for gspread
    ws.update(STATE_CELL, [[str(message_id)]])

def read_message_id():
    val = ws.acell(STATE_CELL).value
    return int(val) if val and val.isdigit() else None

# =====================
# COUNTRY FLAGS
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

def country_emoji(country):
    return COUNTRY_EMOJIS.get(country, "🌍")

# =====================
# BUILD DISCORD EMBED
# =====================
def build_embed(rows):
from datetime import datetime, timezone

def build_embed(rows):
    now = datetime.now(timezone.utc)

    embed = {
        "title": "✈️ Smugglers Flight Paths",
        "color": 0x3498db,
        "timestamp": now.isoformat(),
        "fields": []
    }

    # skip header row
    for row in rows[2:]:
        if len(row) < 7:
            continue

        dest, outb, inbound, returning, purch, travsug, icc = row[:7]

        embed["fields"].append({
            "name": f"{country_emoji(dest)}{icc} {dest}",
            "value": (
                f"🛫 Out: **{outb or '-'}** "
                f"🛬 In: **{inbound or '-'}** "
                f"↩ Return: **{returning or '-'}**\n"
                f"📦 Item: **{purch or '-'}**"
            ),
            "inline": False
        })

    # 🔑 Forces visible update every run
    embed["footer"] = {
        "text": f"Last updated: {now.strftime('%H:%M:%S UTC')} • Auto-refresh 5m"
    }

    return embed


# =====================
# SEND OR EDIT WEBHOOK
# =====================
def send_webhook(embed):
    last_msg_id = read_message_id()
    payload = {"embeds": [embed]}

    headers = {"Content-Type": "application/json"}

    # Try to edit existing message
    if last_msg_id:
        edit_url = f"{WEBHOOK_URL}/messages/{last_msg_id}"
        r = requests.patch(edit_url, json=payload, headers=headers)
        if r.status_code == 200:
            print(f"🔁 Edited existing message {last_msg_id}")
            return last_msg_id
        else:
            print(f"⚠️ Edit failed ({r.status_code}), posting new message")

    # Post new message if edit failed or missing
    r = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    if r.status_code in (200, 204):
        new_msg_id = r.json().get("id") if r.status_code == 200 else None
        if new_msg_id:
            write_message_id(new_msg_id)
        print(f"🆕 Posted new message {new_msg_id}")
        return new_msg_id
    else:
        raise RuntimeError(f"❌ Discord API error {r.status_code}: {r.text}")

# =====================
# MAIN
# =====================
def main():
    rows = get_rows()
    if not rows or len(rows) < 2:
        print("⚠️ No rows in sheet")
        return

    embed = build_embed(rows)

    retries = 0
    while retries < 5:
        try:
            send_webhook(embed)
            break
        except Exception as e:
            print("❌ Exception during webhook update:", e)
            retries += 1
            time.sleep(2)
    else:
        print("❌ Failed after 5 retries")

if __name__ == "__main__":
    main()
