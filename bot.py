import os
import json
import requests
import time
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id

# =====================
# ENV
# =====================
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
FLIGHT_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
STATE_CELL = "A1"
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds (exponential backoff multiplier applied)

# =====================
# FLAGS
# =====================
COUNTRY_EMOJIS = {
    "Torn": "<:city:1458205750617833596>",
    "Mexico": "<:mx:1458203844474572801>",
    "Cayman Islands": "<:ky:1458203876544221459>",
    "Canada": "<:ca:1458204026813415517>",
    "Hawaii": "<:ushi:1458203802342522981>",
    "United Kingdom": "<:gb:1458203934647917>",
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
    sorted_rows = sorted(
        rows[1:],  # skip headers
        key=lambda r: r[0].lower() if len(r) > 0 and r[0] else ""
    )

    fields = []
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
        "color": 3447003,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": fields,
        "footer": {"text": "Auto-updates every 5 minutes"}
    }
    return embed

# =====================
# SEND WITH RETRY
# =====================
def send_request(method, url, **kwargs):
    for attempt in range(MAX_RETRIES):
        r = requests.request(method, url, **kwargs)
        if r.status_code in (200, 201, 204):
            return r
        elif r.status_code == 429:  # rate limit
            retry_after = r.json().get("retry_after", RETRY_DELAY)
            print(f"⚠️ Rate limited. Waiting {retry_after:.1f}s before retry...")
            time.sleep(retry_after)
        else:
            print(f"❌ Discord API error {r.status_code}: {r.text}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    raise RuntimeError(f"❌ Failed to send after {MAX_RETRIES} retries")

# =====================
# UPDATE LOGIC
# =====================
def update_flight_webhook():
    rows = get_sheet_values(FLIGHT_SHEET)
    if not rows or len(rows) < 2:
        print("⚠️ No sheet data found")
        return

    embed = build_embed(rows)
    payload = {"embeds": [embed]}

    posted_message_id = rows[0][0] if rows[0] else None

    try:
        if posted_message_id:
            r = send_request("PATCH", f"{WEBHOOK_URL}/messages/{posted_message_id}", json=payload)
            print(f"🔁 Edited previous webhook message {posted_message_id}")
            return

        r = send_request("POST", WEBHOOK_URL, json=payload)
        msg_data = r.json() if r.content else {}
        new_msg_id = msg_data.get("id")
        if new_msg_id:
            write_message_id(FLIGHT_SHEET, new_msg_id, cell=STATE_CELL)
            print(f"🆕 Posted new webhook message {new_msg_id}")
        else:
            print("🆕 Posted new webhook message (ID not returned)")
    except Exception as e:
        print("❌ Exception during webhook update:", e)

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    update_flight_webhook()
