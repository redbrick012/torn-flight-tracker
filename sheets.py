import os
import json
import gspread
from google.oauth2.service_account import Credentials

# =====================
# CONFIG
# =====================
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

# Allow read and write
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# =====================
# AUTH
# =====================
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)

client = gspread.authorize(creds)

# =====================
# READ SHEET
# =====================
def get_sheet_values(sheet_name):
    sh = client.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(sheet_name)
    return worksheet.get_all_values()

# =====================
# WRITE MESSAGE ID (serverless state)
# =====================
def set_message_id(message_id: str, sheet_name="travelDestinations"):
    """
    Writes the Discord message ID to cell A1
    """
    sh = client.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(sheet_name)
    worksheet.update("E1", message_id)
