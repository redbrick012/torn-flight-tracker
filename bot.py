import os
import requests
from sheets import get_sheet_values, write_message_id

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = os.environ["FLIGHT_CHANNEL_ID"]
SHEET_NAME = os.environ.get("FLIGHT_SHEET", "travelDestinations")

DISCORD_API = "https://discord.com/api/v10"

HEADERS = {
    "Authorization": f"Bot {DISCORD_TOKEN}",
    "Content-Type": "application/json"
}

def build_message(rows):
    lines = []

    for row in rows[1:]:
        if any(cell.strip() for cell in row):
            lines.append(" | ".join(cell.strip() for cell in row))

    if not lines:
        return "No flight data available."

    return "\n".join(lines)

def main():
    rows = get_sheet_values(SHEET_NAME)

    # 🔒 Read a SINGLE valid message ID from A1
    message_id = None
    if rows and rows[0]:
        cell = rows[0][0].strip()
        if cell.isdigit():
            message_id = cell

    content = build_message(rows)

    payload = {
        "content": f"✈️ **Flight Updates**\n```{content}```"
    }

    # 🔁 Attempt update FIRST
    if message_id:
        response = requests.patch(
            f"{DISCORD_API}/channels/{CHANNEL_ID}/messages/{message_id}",
            headers=HEADERS,
            json=payload
        )

        if response.status_code == 200:
            print(f"✅ Updated existing message {message_id}")
            return
        else:
            print(f"⚠️ Failed to update message {message_id}, posting new")

    # 🆕 Post ONE new message
    response = requests.post(
        f"{DISCORD_API}/channels/{CHANNEL_ID}/messages",
        headers=HEADERS,
        json=payload
    )

    response.raise_for_status()

    new_message_id = response.json()["id"]
    write_message_id(SHEET_NAME, new_message_id)

    print(f"🆕 Posted new message {new_message_id} and saved to sheet")

if __name__ == "__main__":
    main()
