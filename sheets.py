import os
import json
import gspread
from google.oauth2.service_account import Credentials

# =====================
# SETUP SHEETS CLIENT
# =====================
GOOGLE_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if not GOOGLE_JSON:
    raise RuntimeError("❌ GOOGLE_SERVICE_ACCOUNT_JSON not set")

# Load JSON credentials
creds_dict = json.loads(GOOGLE_JSON)
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
if not SPREADSHEET_ID:
    raise RuntimeError("❌ SPREADSHEET_ID not set")


def get_sheet(sheet_name):
    """Open the sheet by name."""
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(sheet_name)
    return ws


# =====================
# SHEET HELPERS
# =====================
def get_sheet_values(sheet_name):
    """Return all rows from the sheet as a list of lists."""
    ws = get_sheet(sheet_name)
    return ws.get_all_values()


def write_message_id(sheet_name, message_id, cell="A1"):
    """Write Discord message ID to a specific cell."""
    ws = get_sheet(sheet_name)
    ws.update(cell, str(message_id))


def read_message_id(sheet_name, cell="A1"):
    """Read Discord message ID from a specific cell. Returns None if empty."""
    ws = get_sheet(sheet_name)
    val = ws.acell(cell).value
    return val if val else None
