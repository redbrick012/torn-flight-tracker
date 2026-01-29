import os
import json
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENV
# =====================
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

# Load service account JSON directly from secret
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)

# =====================
# FUNCTIONS
# =====================
def get_sheet_values(sheet_name):
    """Return all rows from a worksheet"""
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    return worksheet.get_all_values()


def write_message_id(sheet_name, message_id, cell="A1"):
    """Write Discord message ID to a cell"""
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    worksheet.update(cell, str(message_id))
