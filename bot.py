import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone

# =====================
# ENV
# =====================
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
FLIGHT_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")

STATE_FILE = "state.json"

# =====================
# FLAGS (UNCHANGED)
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
# GOOGLE SHEETS
# =====================
def get_sheet_values():
    creds_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(FLIGHT_SHEET)
    return sheet.get_all_values()

# =====================
# STATE (MESSAGE ID)
# =====================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"message_id": None}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# =====================
# EMBED BUILDER (MATCHES ORIGINAL)
# =====================
def build_embed(rows):
    embed = {
        "title": "✈️ Smugglers Flight Paths",
        "color": 0x3498db,
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
            "value": (
                f"🛫 Out: **{outb}** "
                f"🛬 In: **{inbound}** "
                f"↩ Return: **{returning}**\n"
                f"📦 Item: **{purch}**"
            ),
            "inline": False
        })

    return embed

# =====================
# DISCORD WEBHOOK UPDATE
# =====================
def send_or_update(embed, state):
    payload = {"embeds": [embed]}

    if state["message_id"]:
        url = f"{WEBHOOK_URL}/messages/{state['message_id']}"
        r = requests.patch(url, json=payload)
    else:
        r = requests.post(WEBHOOK_URL, json=payload)
        r.raise_for_status()
        state["message_id"] = r.json()["id"]

    r.raise_for_status()

# =====================
# MAIN
# =====================
def main():
    rows = get_sheet_values()
    if not rows or len(rows) < 2:
        print("⚠️ Sheet empty")
        return

    state = load_state()
    embed = build_embed(rows)

    send_or_update(embed, state)
    save_state(state)

    print("✅ Flight message updated")

if __name__ == "__main__":
    main()
