import os
import json
import base64
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

# Decode the Base64-encoded JSON secret
GOOGLE_SERVICE_ACCOUNT_JSON_B64 = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON_B64"]
SERVICE_ACCOUNT_INFO = json.loads(
    base64.b64decode(GOOGLE_SERVICE_ACCOUNT_JSON_B64).decode("utf-8")
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)

# =====================
# FUNCTIONS
# =====================
def get_sheet_values(sheet_name):
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    return worksheet.get_all_values()

def write_message_id(sheet_name, message_id, cell="A1"):
    """Write the Discord message ID to a specific cell"""
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    worksheet.update(cell, str(message_id))
