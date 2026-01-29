import os
import json
import gspread
from google.oauth2.service_account import Credentials

# Get the service account JSON from GitHub secrets
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

# Authenticate with Google Sheets
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)

# =====================
# FUNCTIONS
# =====================
def get_sheet_values(sheet_name):
    """Get all values from a Google Sheet"""
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    return worksheet.get_all_values()

def write_message_id(sheet_name, message_id):
    """Write the Discord message ID to cell A1"""
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    worksheet.update("A1", [[str(message_id)]])
