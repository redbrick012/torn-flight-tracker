import os
import json
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

# 🔑 MUST be full access (not readonly)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)

client = gspread.authorize(credentials)

def get_worksheet(sheet_name):
    sheet = client.open_by_key(SPREADSHEET_ID)
    return sheet.worksheet(sheet_name)

def get_sheet_values(sheet_name):
    ws = get_worksheet(sheet_name)
    return ws.get_all_values()

def write_message_id(sheet_name, message_id):
    ws = get_worksheet(sheet_name)
    ws.update("A1", [[str(message_id)]])
