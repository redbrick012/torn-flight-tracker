import os
import json
import base64
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENV
# =====================
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
GOOGLE_SERVICE_ACCOUNT_JSON_B64 = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# decode the base64 JSON
SERVICE_ACCOUNT_INFO = json.loads(base64.b64decode(GOOGLE_SERVICE_ACCOUNT_JSON_B64))

# =====================
# GOOGLE SHEETS CLIENT
# =====================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)

# =====================
# FUNCTIONS
# =====================
def get_worksheet(sheet_name):
    """Return the worksheet object"""
    sheet = client.open_by_key(SPREADSHEET_ID)
    return sheet.worksheet(sheet_name)

def get_sheet_values(sheet_name):
    """Get all values from a sheet"""
    ws = get_worksheet(sheet_name)
    return ws.get_all_values()

def write_message_id(sheet_name, message_id):
    """Write the Discord message ID to cell A1"""
    ws = get_worksheet(sheet_name)
    ws.update("A1", [[str(message_id)]])
